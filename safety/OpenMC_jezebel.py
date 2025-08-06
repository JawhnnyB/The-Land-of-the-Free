import openmc

# Detailed Description:
# This script creates a simple bare sphere of plutonium metal, mimicking the Jezebel experiment.
# - Materials: Defines a plutonium material with isotopic composition (95% Pu-239, 5% Pu-240 for simplicity; adjust for Ga alloy if needed).
# - Geometry: A single sphere surface bounds the fissile cell; the outer region is vacuum by default.
# - Settings: Eigenvalue mode for criticality, with batches, inactive cycles, and particles per batch to ensure convergence.
# - Plots/Tallies: Adds a basic tally for neutron flux in the sphere and a plot for visualization.
# - Execution: Run this script to generate XML files, then execute 'openmc' in the terminal.
# Best Practices: Increase particles for lower uncertainty (<0.001); check convergence with entropy diagnostic.

# Define materials
pu = openmc.Material(name='Plutonium')
pu.add_nuclide('Pu239', 0.95)  # Primary fissile isotope
pu.add_nuclide('Pu240', 0.05)  # Minor isotope for realism
pu.set_density('g/cm3', 19.7)  # Density in g/cm³ for metallic Pu

# Define geometry
sphere = openmc.Sphere(r=6.385, boundary_type='vacuum')  # Sphere radius in cm; vacuum boundary simulates bare configuration
inner_cell = openmc.Cell(name='Pu Sphere', fill=pu, region=-sphere)  # Fissile region inside sphere
root_universe = openmc.Universe(cells=[inner_cell])  # Root universe containing the cell

# Define settings for criticality calculation
settings = openmc.Settings()
settings.run_mode = 'eigenvalue'  # Specifies k-effective (eigenvalue) mode
settings.batches = 250  # Total batches (cycles) for statistics
settings.inactive = 50  # Inactive batches to discard for source convergence
settings.particles = 10000  # Particles per batch for good sampling
settings.entropy_dimension = [10, 10, 10]  # Optional: Shannon entropy mesh for convergence check

# Initial uniform source distribution (optional, defaults to fission sites after first batch)
uniform_dist = openmc.stats.Box((-6.385, -6.385, -6.385), (6.385, 6.385, 6.385), only_fissionable=True)
settings.source = openmc.IndependentSource(space=uniform_dist)

# Define tallies (e.g., neutron flux in the sphere)
tally = openmc.Tally(name='Flux Tally')
tally.filters = [openmc.CellFilter(inner_cell)]  # Filter to the Pu cell
tally.scores = ['flux']  # Score neutron flux
tallies = openmc.Tallies([tally])

# Optional: Create a plot for visualization
plot = openmc.Plot()
plot.basis = 'xz'  # Slice in x-z plane
plot.origin = (0, 0, 0)
plot.width = (15, 15)  # Width in cm
plot.pixels = (300, 300)
plots = openmc.Plots([plot])

# Export to XML files for OpenMC execution
openmc.Geometry(root_universe).export_to_xml()
settings.export_to_xml()
tallies.export_to_xml()
plots.export_to_xml()