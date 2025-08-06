# Advanced Nuclear Reactor Simulations

This repository showcases simulations of advanced nuclear reactors using open-source tools like OpenMC, MCNP (export-restricted aspects noted), and MOOSE/Cardinal. It demonstrates expertise in nuclear engineering, multiphysics modeling, and AI integration for reactor design and analysis. The project includes models for various reactor types (BWR, CANDU, MSR, PWR, SFR) and serves as a portfolio for educational and research purposes.

**Note:** Simulations using CASMO-4E and full MCNP are restricted due to U.S. Government export controls and are not included. This repo focuses on open-source alternatives.

## Disclaimer

All rights to the underlying simulation tools and frameworks (including OpenMC, MCNP, MOOSE/Cardinal, and related libraries) are reserved by their respective owners and developers. This repository uses these tools solely for modeling advanced reactors and does not claim any ownership or rights over them. Usage complies with all applicable licenses and export regulations. For official documentation and source code, refer to:
- [OpenMC GitHub](https://github.com/openmc-dev/openmc)
- [OpenMC Documentation](https://docs.openmc.org/en/stable/)
- [MCNP Tools GitHub](https://github.com/lanl/mcnptools)
- [Cardinal GitHub](https://cardinal.cels.anl.gov/)

This project is for educational and research purposes only. Always adhere to nuclear safety and regulatory standards.

## Key Features
- Multiphysics simulations of modern reactor types.
- Automation scripts for input generation and output parsing.
- AI/ML integration for predicting key parameters like k-eff and EFPD.
- Structured data collection for machine learning datasets.

## Technologies Used
- **Simulation Tools**: OpenMC (neutronics), MCNP (neutronics, restricted), Cardinal/MOOSE (multiphysics coupling).
- **Programming**: Python (with libraries like NumPy, PyTorch for ML).
- **AI/ML**: Deep learning models (MLP, LSTM, PINN) for optimization and prediction.

## Structure
- **`MOOSE_Projects/`**: Input (.i) files and outputs for MOOSE/Cardinal simulations, including multiphysics couplings (e.g., neutronics + heat transfer).
  - Example: `sfr_cardinal.i` for Sodium Fast Reactor models.
- **`OpenMC_Projects/`**: XML input files (materials.xml, geometry.xml, settings.xml) and outputs (e.g., StatePoint HDF5) for OpenMC simulations.
  - Example: BWR materials/geometry/settings XMLs.
- **`AI_Projects/`**: AI training data (JSON inputs/outputs), models (PyTorch scripts), and parsing utilities.
  - Subfolders: `OpenMC_Data/`, `MCNP_Data/`, `Cardinal_Data/` for sim-specific data.
  - Scripts: Unified parser and trainer for k-eff/EFPD prediction.
- **`scripts/`**: Automation scripts for generating/running simulations and parsing results.
  - Example: `unified_parser_trainer.py` for ML across tools.
- **`american_eagle.txt`**: ASCII art for terminal display (fun element).

## Getting Started

### Prerequisites
- Python 3.8+ with libraries: `openmc`, `torch`, `numpy`, `h5py`, `re` (install via `pip install -r requirements.txt` if added).
- OpenMC: Install from [official guide](https://docs.openmc.org/en/stable/).
- MCNP: Restricted; assume licensed access.
- MOOSE/Cardinal: Follow [installation instructions](https://cardinal.cels.anl.gov/install.html).
- For ML: PyTorch and optional `pyexodus` for Exodus files.

### Installation
1. Clone the repository: git clone https://github.com/JawhnnyB/The-Land-of-the-Free.git
cd The-Land-of-the-Free
2. Set up virtual environment (optional):
python -m venv env
source env/bin/activate
pip install -r requirements.txt  # Create this file with dependencies if not present
3. Run a sample simulation (e.g., OpenMC BWR):
cd OpenMC_Projects/BWR
openmc.run()

### Running AI/ML
- Collect data: Run simulations and parse outputs using `scripts/unified_parser_trainer.py`.
- Train model: Execute the script to load data and train the PINN/hybrid model.

## Contributing
Contributions are welcome! Fork the repo, create a branch, and submit a pull request. Focus on adding new reactor models, improving ML accuracy, or enhancing documentation.

## Future Work
- Expand dataset with more parametric studies.
- Integrate advanced AI like GANs for data augmentation and RL for optimization.
- Add visualization dashboards (e.g., via Streamlit).

## License
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Open Issues](https://img.shields.io/github/issues/JawhnnyB/The-Land-of-the-Free)](https://github.com/JawhnnyB/The-Land-of-the-Free/issues)