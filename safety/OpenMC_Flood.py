import openmc

# Detailed Description:
# This script simulates a cylindrical waste canister with inner fissile material, flooded by water, and outer steel wall.
# - Materials: Pure U-235 (simplified fissile), water, and iron (for steel).
# - Geometry: Concentric cylinders for fissile, water, and steel; axial planes for height.
# - Settings: Eigenvalue mode to compute k_eff increase due to flooding.
# - Plots/Tallies: Point-like tally at center for detector simulation.
# - Execution: Run script, then 'openmc'.
# Best Practices: Vary water density or add absorbers for parametric studies; use mesh tallies for spatial dose in real scenarios.

# Define materials
fissile = openmc.Material(name='Fissile Material')
fissile.add_nuclide('U235', 1.0)  # Simplified pure U-235
fissile.set_density('g/cm3', 15.0)

water = openmc.Material(name='Flood Water')
water.add_nuclide('H1', 2.0)
water.add_nuclide('O16', 1.0)
water.set_density('g/cm3', 1.0)

steel = openmc.Material(name='Steel Wall')
steel.add_element('Fe', 1.0)  # Simplified iron
steel.set_density('g/cm3', 7.8)

# Define geometry (cylindrical canister)
inner_radius = openmc.ZCylinder(r=20.0)  # Inner fissile radius
outer_radius = openmc.ZCylinder(r=21.0)  # Outer steel radius
bottom = openmc.ZPlane(-50.0)  # Bottom plane (height 100 cm)
top = openmc.ZPlane(50.0)  # Top plane

fissile_cell = openmc.Cell(name='Fissile', fill=fissile, region=-inner_radius & +bottom & -top)  # Inner fissile
water_cell = openmc.Cell(name='Water', fill=water, region=+inner_radius & -outer_radius & +bottom & -top)  # Flooded region
steel_cell = openmc.Cell(name='Steel', fill=steel, region=+outer_radius & +bottom & -top)  # Outer wall
outer_void = openmc.Cell(name='Void', region=~(-outer_radius & +bottom & -top))  # Vacuum outside

root_universe = openmc.Universe(cells=[fissile_cell, water_cell, steel_cell, outer_void])

# Define settings
settings = openmc.Settings()
settings.run_mode = 'eigenvalue'
settings.batches = 200
settings.inactive = 40
settings.particles = 20000

uniform_dist = openmc.stats.Box((-20, -20, -50), (20, 20, 50), only_fissionable=True)
settings.source = openmc.IndependentSource(space=uniform_dist)

# Define tallies (e.g., point detector at center)
tally = openmc.Tally(name='Point Detector')
tally.filters = [openmc.DistribcellFilter(fissile_cell)]  # Approximate point via cell
tally.scores = ['flux']
tallies = openmc.Tallies([tally])

# Optional plot
plot = openmc.Plot()
plot.basis = 'xz'
plot.origin = (0, 0, 0)
plot.width = (50, 110)
plot.pixels = (300, 300)
plots = openmc.Plots([plot])

# Export to XML
openmc.Geometry(root_universe).export_to_xml()
settings.export_to_xml()
tallies.export_to_xml()
plots.export_to_xml()