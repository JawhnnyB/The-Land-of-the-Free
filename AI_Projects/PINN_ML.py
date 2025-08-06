import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import json
import os
import re
import h5py
try:
    import exodus
except ImportError:
    print("exodus library not found; install pyexodus for Cardinal parsing.")

# Unified PINN Model: Physics-Informed Neural Network for nuclear parameters prediction
# Incorporates neutron diffusion equation as physics loss: ∇·D∇φ - Σ_a φ + νΣ_f φ = 0 (simplified for k-eff ~ νΣ_f / Σ_a)
# Distinguishes data from OpenMC, MCNP, Cardinal via loading parsed JSONs
# Trains on combined dataset, with physics regularization

class NuclearPINN(nn.Module):
    def __init__(self, input_size=8, hidden_size=128, output_size=2):  # Outputs: k-eff, EFPD
        super(NuclearPINN, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size * 2)
        self.fc3 = nn.Linear(hidden_size * 2, hidden_size)
        self.fc_out = nn.Linear(hidden_size, output_size)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.relu(self.fc3(x))
        return self.fc_out(x)

def physics_loss(model, inputs, outputs):
    """
    Physics-informed loss: Approximate k-eff = nu * Sigma_f / (Sigma_a + D * grad^2)
    Simplified: Enforce k-eff ≈ enrichment * power / (temp factor); derivative-based
    """
    inputs.requires_grad = True
    pred = model(inputs)
    k_eff_pred = pred[:, 0]

    # Compute gradient wrt inputs (e.g., wrt radius or temp as proxy for diffusion)
    grad_k = torch.autograd.grad(k_eff_pred.sum(), inputs, create_graph=True)[0]
    diffusion_term = torch.mean(grad_k[:, :2]**2)  # Proxy for ∇^2 on geometry params

    # Nuclear physics constraint: k-eff ~ enrichment / absorption (temp-dependent)
    enrichment = inputs[:, 0]
    temp = inputs[:, 3]
    absorption_proxy = 1 / (1 + 0.001 * temp)  # Simplified Σ_a increase with temp
    physics_k = enrichment / absorption_proxy - 0.1 * diffusion_term  # Rough diffusion penalty

    phys_mse = nn.MSELoss()(k_eff_pred, physics_k)
    return phys_mse

def load_data(sim_type, reactor_type):
    """
    Load parsed outputs from JSON for given sim_type and reactor_type.
    """
    dir_path = f"AI_Projects/{sim_type}_Data/outputs/"
    results = []
    for file in os.listdir(dir_path):
        if reactor_type in file and file.endswith('_results.json'):
            with open(os.path.join(dir_path, file), 'r') as f:
                data = json.load(f)
            # Corresponding inputs
            input_file = file.replace('outputs', 'inputs').replace('_results', '_params')
            with open(os.path.join(dir_path.replace('outputs', 'inputs'), input_file), 'r') as fin:
                params = json.load(f)
            inp_vec = [params.get(k, 0) for k in ['enrichment_u235', 'fuel_radius_cm', 'clad_radius_cm', 'temperature_k',
                                                  'power_mw', 'moderator_density_g_cm3', 'coolant_density_g_cm3', 'salt_density_g_cm3']]
            out_vec = [data['k_eff'], data['efpd']]
            results.append((inp_vec, out_vec))
    return results

def train_pinn(sim_types=['OPENMC', 'MCNP', 'CARDINAL'], reactor_types=['BWR', 'CANDU', 'MSR', 'PWR', 'SFR']):
    all_data = []
    for sim_type in sim_types:
        for reactor_type in reactor_types:
            all_data.extend(load_data(sim_type, reactor_type))

    if not all_data:
        print("No data loaded. Run simulations and parse first.")
        return

    inputs = torch.tensor([d[0] for d in all_data], dtype=torch.float32)
    outputs = torch.tensor([d[1] for d in all_data], dtype=torch.float32)

    model = NuclearPINN()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()

    for epoch in range(500):
        optimizer.zero_grad()
        pred = model(inputs)
        data_loss = criterion(pred, outputs)
        phys_loss = physics_loss(model, inputs, outputs)
        total_loss = data_loss + 0.5 * phys_loss  # Balance data and physics
        total_loss.backward()
        optimizer.step()

        if epoch % 50 == 0:
            print(f"Epoch {epoch}, Data Loss: {data_loss.item()}, Phys Loss: {phys_loss.item()}, Total: {total_loss.item()}")

    torch.save(model.state_dict(), "AI_Projects/pinn_model.pth")
    print("PINN model trained and saved.")

if __name__ == "__main__":
    train_pinn()