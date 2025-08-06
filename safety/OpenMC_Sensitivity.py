import openmc

# Detailed Description:
# This script models an infinite slab of enriched uranium for basic sensitivity analysis using tally perturbations.
# - Materials: Enriched uranium slab.
# - Geometry: Infinite slab in x (bounded by planes); reflective in y/z for infinity.
# - Settings: Eigenvalue mode with perturbations on density for sensitivity.
# - Plots/Tallies: Flux tally with perturbation (e.g., ±1% density change).
# - Execution: Run script, then 'openmc'; analyze sp.h5 for sensitivity.
# Best Practices: For nuclear data sensitivity, integrate with tools like OpenMC's mgxs or external scripts; GPT-Free method can be implemented via custom tallies for reactions.
# Note: Full KSEN-like sensitivity requires extensions (see OpenMC discourse).

# Define materials
uranium = openmc.Material(name='Uranium Slab')
uranium.add_nuclide('U235', 0.05)  # 5% enriched
uranium.add_nuclide('U238', 0.95)
uranium.set_density('g/cm3', 10.0)

# Define geometry (infinite slab)
left = openmc.XPlane(-5.0, boundary_type='reflective')  # Reflective for infinite
right = openmc.XPlane(5.0, boundary_type='reflective')  # Slab thickness 10 cm
slab_cell = openmc.Cell(name='Slab', fill=uranium, region=+left & -right)  # Slab region
root_universe = openmc.Universe(cells=[slab_cell])

# Define settings
settings = openmc.Settings()
settings.run_mode = 'eigenvalue'
settings.batches = 250
settings.inactive = 50
settings.particles = 10000

uniform_dist = openmc.stats.Box((-5, -100, -100), (5, 100, 100), only_fissionable=True)  # Large in y/z for infinite
settings.source = openmc.IndependentSource(space=uniform_dist)

# Define tallies with perturbation for sensitivity (e.g., to density)
tally = openmc.Tally(name='Flux with Perturbation')
tally.filters = [openmc.CellFilter(slab_cell)]
tally.scores = ['flux']
tally.perturbations = [openmc.Perturbation(pert_type='density', value=1.01, cells=[slab_cell]),  # +1%
                       openmc.Perturbation(pert_type='density', value=0.99, cells=[slab_cell])]  # -1%
tallies = openmc.Tallies([tally])

# Optional plot
plot = openmc.Plot()
plot.basis = 'xz'
plot.origin = (0, 0, 0)
plot.width = (15, 15)
plot.pixels = (300, 300)
plots = openmc.Plots([plot])

# Export to XML
openmc.Geometry(root_universe).export_to_xml()
settings.export_to_xml()
tallies.export_to_xml()
plots.export_to_xml()