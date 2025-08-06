import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import json
import os
from torch.distributions import Normal  # For GAN

class UnifiedReactorDataset(Dataset):
    def __init__(self, sim_types=['OPENMC', 'MCNP', 'CARDINAL'], reactor_types=['BWR', 'CANDU', 'MSR', 'PWR', 'SFR']):
        self.inputs = []
        self.outputs = []  # [k_eff, efpd]
        self.sequences = []  # Simulated time-series for LSTM (e.g., burnup steps)
        for sim_type in sim_types:
            output_dir = f"AI_Projects/{sim_type}_Data/outputs/"
            if not os.path.exists(output_dir):
                continue
            for file in os.listdir(output_dir):
                if file.endswith('_results.json'):
                    with open(os.path.join(output_dir, file), 'r') as f:
                        data = json.load(f)
                    # Input vector: enrichment, fuel_radius, etc. (assume loaded from corresponding input JSON)
                    input_file = file.replace('outputs', 'inputs').replace('_results', '_params')
                    with open(os.path.join(output_dir.replace('outputs', 'inputs'), input_file), 'r') as fin:
                        params = json.load(fin)
                    inp_vec = [params.get('enrichment_u235', 0), params.get('fuel_radius_cm', 0), params.get('clad_radius_cm', 0),
                               params.get('temperature_k', 0), params.get('power_mw', 0), params.get('moderator_density_g_cm3', 0),
                               params.get('coolant_density_g_cm3', 0), params.get('salt_density_g_cm3', 0)]
                    out_vec = [data['k_eff'], data['efpd']]
                    # Simulated sequence: e.g., burnup over 5 steps (expand with real data)
                    seq = np.linspace(0, data['efpd'], 5) + np.random.normal(0, 0.1, 5)
                    self.inputs.append(inp_vec)
                    self.outputs.append(out_vec)
                    self.sequences.append(seq)

        self.inputs = torch.tensor(self.inputs, dtype=torch.float32)
        self.outputs = torch.tensor(self.outputs, dtype=torch.float32)
        self.sequences = torch.tensor(self.sequences, dtype=torch.float32).unsqueeze(2)  # [batch, seq_len, features=1]

    def __len__(self):
        return len(self.inputs)

    def __getitem__(self, idx):
        return self.inputs[idx], self.outputs[idx], self.sequences[idx]

class HybridDeepModel(nn.Module):
    def __init__(self, input_size=8, hidden_size=128, lstm_layers=2, output_size=2):
        super(HybridDeepModel, self).__init__()
        self.mlp = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, hidden_size * 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU()
        )
        self.lstm = nn.LSTM(input_size=1, hidden_size=hidden_size, num_layers=lstm_layers, batch_first=True)
        self.fc_out = nn.Linear(hidden_size * 2, output_size)  # Combine MLP and LSTM outputs

    def forward(self, static_inp, seq_inp):
        mlp_out = self.mlp(static_inp)
        lstm_out, _ = self.lstm(seq_inp)
        lstm_out = lstm_out[:, -1, :]  # Last time step
        combined = torch.cat((mlp_out, lstm_out), dim=1)
        return self.fc_out(combined)

# GAN Class (for synthetic data generation; expand as needed)
class GAN(nn.Module):
    def __init__(self, latent_size=100, output_size=8):  # Output synthetic input vectors
        super(GAN, self).__init__()
        self.generator = nn.Sequential(
            nn.Linear(latent_size, 256),
            nn.ReLU(),
            nn.Linear(256, output_size)
        )
        self.discriminator = nn.Sequential(
            nn.Linear(output_size, 256),
            nn.ReLU(),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )

    # Training loop stub (call in main)
    def train_gan(self, dataloader, epochs=100):
        optimizer_g = optim.Adam(self.generator.parameters(), lr=0.0002)
        optimizer_d = optim.Adam(self.discriminator.parameters(), lr=0.0002)
        criterion = nn.BCELoss()
        for epoch in range(epochs):
            for real_inputs, _, _ in dataloader:
                batch_size = real_inputs.size(0)
                real_labels = torch.ones(batch_size, 1)
                fake_labels = torch.zeros(batch_size, 1)
                noise = torch.randn(batch_size, 100)
                fake_inputs = self.generator(noise)

                # Train discriminator
                optimizer_d.zero_grad()
                d_real = self.discriminator(real_inputs)
                d_fake = self.discriminator(fake_inputs.detach())
                loss_d = criterion(d_real, real_labels) + criterion(d_fake, fake_labels)
                loss_d.backward()
                optimizer_d.step()

                # Train generator
                optimizer_g.zero_grad()
                d_fake = self.discriminator(fake_inputs)
                loss_g = criterion(d_fake, real_labels)
                loss_g.backward()
                optimizer_g.step()
            if epoch % 10 == 0:
                print(f"GAN Epoch {epoch}, D Loss: {loss_d.item()}, G Loss: {loss_g.item()}")

# RL Agent Stub (for optimization, e.g., using DQN; expand with gym env for reactor params)
class RLAgent:
    def __init__(self, state_size=8, action_size=5):  # Actions: adjust params
        self.model = nn.Sequential(
            nn.Linear(state_size, 128),
            nn.ReLU(),
            nn.Linear(128, action_size)
        )

    # Training stub (implement full RL loop)
    def train_rl(self):
        print("RL training placeholder: Optimize params for max EFPD with k-eff constraint.")

def train_hybrid_model():
    dataset_obj = UnifiedReactorDataset()
    dataloader = DataLoader(dataset_obj, batch_size=4, shuffle=True)
    model = HybridDeepModel()
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(200):
        for static_inp, targets, seq_inp in dataloader:
            optimizer.zero_grad()
            outputs = model(static_inp, seq_inp)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
        if epoch % 20 == 0:
            print(f"Hybrid Epoch {epoch}, Loss: {loss.item()}")

    torch.save(model.state_dict(), "AI_Projects/hybrid_model.pth")
    print("Hybrid model trained and saved.")

    # GAN integration for augmentation
    gan = GAN()
    gan.train_gan(dataloader)

    # RL integration
    rl_agent = RLAgent()
    rl_agent.train_rl()

if __name__ == "__main__":
    train_hybrid_model()