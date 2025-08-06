import openmc
import h5py
import os
import re
import json
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.utils.data import Dataset, DataLoader
try
    import exodus  # For Cardinal Exodus files; pip install if needed
except ImportError
    print(exodus library not found; install pyexodus for Cardinal parsing.)

# Global dataset for ML list of dicts with params and outputs
dataset = []

class ReactorDataset(Dataset)
    def __init__(self, data)
        self.inputs = []
        self.outputs = []
        for entry in data
            inp_vec = [entry['enrichment_u235'], entry['fuel_radius_cm'], entry['clad_radius_cm'],
                       entry['temperature_k'], entry['power_mw'], entry.get('moderator_density_g_cm3', 0),
                       entry.get('coolant_density_g_cm3', 0), entry.get('salt_density_g_cm3', 0)]
            out_vec = [entry['k_eff'], entry['efpd']]
            self.inputs.append(inp_vec)
            self.outputs.append(out_vec)
        self.inputs = torch.tensor(self.inputs, dtype=torch.float32)
        self.outputs = torch.tensor(self.outputs, dtype=torch.float32)

    def __len__(self)
        return len(self.inputs)

    def __getitem__(self, idx)
        return self.inputs[idx], self.outputs[idx]

class DeepMLP(nn.Module)
    def __init__(self, input_size=8, hidden_size=128, output_size=2)
        super(DeepMLP, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size  2)
        self.fc3 = nn.Linear(hidden_size  2, hidden_size  2)
        self.fc4 = nn.Linear(hidden_size  2, hidden_size)
        self.fc5 = nn.Linear(hidden_size, output_size)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.2)

    def forward(self, x)
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.relu(self.fc3(x))
        x = self.dropout(x)
        x = self.relu(self.fc4(x))
        x = self.fc5(x)
        return x

def collect_inputs(sim_type, reactor_type)
    
    Collect input parameters for the reactor and simulation type, save as JSON.
    
    base_params = {
        'sim_type' sim_type,
        'reactor_type' reactor_type,
        'enrichment_u235' float(input(fEnter U-235 enrichment (fraction) for {reactor_type} )),
        'fuel_radius_cm' float(input(fEnter fuel radius (cm) for {reactor_type} )),
        'clad_radius_cm' float(input(fEnter clad outer radius (cm) for {reactor_type} )),
        'temperature_k' float(input(fEnter average temperature (K) for {reactor_type} )),
        'power_mw' float(input(fEnter power (MW) for {reactor_type} )),
        'burnup_target_gwd_t' float(input(fEnter target burnup (GWdt) for EFPD calculation )),
    }
    if reactor_type == 'MSR'
        base_params['salt_density_g_cm3'] = float(input(Enter salt density (gcm3) ))
    elif reactor_type in ['BWR', 'PWR', 'CANDU']
        base_params['moderator_density_g_cm3'] = float(input(Enter moderator density (gcm3) ))
    elif reactor_type == 'SFR'
        base_params['coolant_density_g_cm3'] = float(input(Enter coolant density (gcm3) ))

    dir_path = fAI_Projects{sim_type}_Datainputs
    os.makedirs(dir_path, exist_ok=True)
    input_file = os.path.join(dir_path, f{reactor_type}_params.json)
    with open(input_file, 'w') as f
        json.dump(base_params, f, indent=4)
    return base_params

def parse_output(sim_type, reactor_type, output_file)
    
    Parse output based on simulation type for k-eff and estimate EFPD.
    
    if sim_type == 'OPENMC'
        with openmc.StatePoint(output_file) as sp
            k_eff = sp.keff.nominal_value
            k_eff_unc = sp.keff.std_dev
    elif sim_type == 'MCNP'
        with open(output_file, 'r') as f
            content = f.read()
        match = re.search(r'combined collisionabsorptiontrack-length k-effs=s(d+.d+)s+-s(d+.d+)', content)
        if match
            k_eff = float(match.group(1))
            k_eff_unc = float(match.group(2))
        else
            raise ValueError(k-eff not found in MCNP output.)
    elif sim_type == 'CARDINAL'
        exo = exodus.exodus(output_file)
        if 'k' in exo.get_global_variable_names()
            k_eff = exo.get_global_variable_values('k')[-1]
        else
            k_eff = None
        k_eff_unc = 0.0  # Placeholder
        if k_eff is None
            log_file = output_file.replace('.e', '_console.out')
            with open(log_file, 'r') as f
                content = f.read()
            match = re.search(r'k-effs=s(d+.d+)s(s(d+.d+)s)', content)
            if match
                k_eff = float(match.group(1))
                k_eff_unc = float(match.group(2))
        exo.close()
    else
        raise ValueError(Invalid simulation type.)

    # EFPD estimation
    input_file = fAI_Projects{sim_type}_Datainputs{reactor_type}_params.json
    with open(input_file, 'r') as f
        params = json.load(f)
    fuel_volume_cm3 = np.pi  params['fuel_radius_cm']2  100  # Assume 1m height
    fuel_mass_t = (fuel_volume_cm3  10.5)  1e6  # Density approx
    burnup_mwd_t = params['burnup_target_gwd_t']  1000
    efpd = burnup_mwd_t  params['power_mw'] if params['power_mw']  0 else 0

    results = {
        'k_eff' k_eff,
        'k_eff_uncertainty' k_eff_unc,
        'efpd' efpd,
    }
    dir_path = fAI_Projects{sim_type}_Dataoutputs
    os.makedirs(dir_path, exist_ok=True)
    result_file = os.path.join(dir_path, f{os.path.basename(output_file)}_results.json)
    with open(result_file, 'w') as f
        json.dump(results, f, indent=4)

    # Add to global dataset for ML
    entry = {params, results}
    dataset.append(entry)
    return results

def train_deep_model()
    
    Train a deep MLP on collected data to predict k-eff and EFPD from inputs.
    
    if len(dataset)  2
        print(Insufficient data for training. Need at least 2 entries.)
        return

    train_dataset = ReactorDataset(dataset)
    dataloader = DataLoader(train_dataset, batch_size=2, shuffle=True)

    model = DeepMLP()
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(100)  # Train for 100 epochs
        for inputs, targets in dataloader
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
        if epoch % 10 == 0
            print(fEpoch {epoch}, Loss {loss.item()})

    torch.save(model.state_dict(), AI_Projectsmodel.pth)
    print(Model trained and saved.)

# Main loop
while True
    sim_type = input(Enter simulation type (OpenMC, MCNP, Cardinal, or 'exit' to stop) ).upper()
    if sim_type == 'EXIT'
        break
    reactor_type = input(Enter reactor type (BWR, CANDU, MSR, PWR, SFR) ).upper()
    collect_inputs(sim_type, reactor_type)
    output_file = input(fEnter output file path for {sim_type} {reactor_type} )
    parse_output(sim_type, reactor_type, output_file)

train_deep_model()