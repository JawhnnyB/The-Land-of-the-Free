import openmc
import os

def generate_and_run_openmc_model(reactor_type, u235_fraction, dimension, temperature, power):
    if reactor_type == 'MSR':
        # Density for FLiBe
        density_kgm3 = 2415.6 - 0.49072 * temperature
        density = density_kgm3 / 1000  # g/cm3
        # Uranium ao adjusted
        u_total = 0.003
        u235_ao = u235_fraction * u_total
        u238_ao = (1 - u235_fraction) * u_total
        salt = openmc.Material(name='Molten Salt')
        salt.add_nuclide('Li7', 2.0, 'ao')
        salt.add_element('Be', 1.0, 'ao')
        salt.add_element('F', 4.0, 'ao')
        salt.add_nuclide('U235', u235_ao, 'ao')
        salt.add_nuclide('U238', u238_ao, 'ao')
        salt.set_density('g/cm3', density)
        salt.add_s_alpha_beta('c_FLiBe')
        salt.temperature = temperature  # Set material temperature

        graphite = openmc.Material(name='Graphite')
        graphite.add_element('C', 1.0)
        graphite.set_density('g/cm3', 1.9)
        graphite.add_s_alpha_beta('c_Graphite')
        graphite.temperature = temperature

        materials = openmc.Materials([salt, graphite])

        fuel_cyl = openmc.ZCylinder(r=dimension)
        refl_cyl = openmc.ZCylinder(r=dimension + 20.0, boundary_type='vacuum')

        fuel_cell = openmc.Cell(fill=salt, region=-fuel_cyl)
        refl_cell = openmc.Cell(fill=graphite, region=+fuel_cyl & -refl_cyl)
        universe = openmc.Universe(cells=[fuel_cell, refl_cell])
        geometry = openmc.Geometry(universe)

    elif reactor_type == 'Heatpipe':
        # Density for sodium
        density_kgm3 = 1011.8 - 0.2205 * temperature - 1.9226e-4 * temperature**2 + 6.5074e-7 * temperature**3
        sodium_density = density_kgm3 / 1000
        fuel = openmc.Material(name='UO2')
        fuel.add_nuclide('U235', u235_fraction)
        fuel.add_nuclide('U238', 1 - u235_fraction)
        fuel.add_element('O', 2.0)
        fuel.set_density('g/cm3', 10.5)
        fuel.temperature = temperature

        sodium = openmc.Material(name='Sodium')
        sodium.add_element('Na', 1.0)
        sodium.set_density('g/cm3', sodium_density)
        sodium.temperature = temperature

        steel = openmc.Material(name='Steel')
        steel.add_element('Fe', 1.0)
        steel.set_density('g/cm3', 7.8)
        steel.temperature = temperature

        materials = openmc.Materials([fuel, sodium, steel])

        fuel_cyl = openmc.ZCylinder(r=dimension)
        hp_cyl = openmc.ZCylinder(r=dimension + 0.1)
        core_cyl = openmc.ZCylinder(r=dimension * 200, boundary_type='vacuum')

        fuel_cell = openmc.Cell(fill=fuel, region=-fuel_cyl)
        hp_cell = openmc.Cell(fill=sodium, region=+fuel_cyl & -hp_cyl)
        mod_cell = openmc.Cell(fill=steel, region=+hp_cyl & -core_cyl)
        universe = openmc.Universe(cells=[fuel_cell, hp_cell, mod_cell])
        geometry = openmc.Geometry(universe)

    elif reactor_type == 'HTGR':
        # Helium density, P=7 MPa
        P = 7e6
        M = 0.004
        R = 8.314
        density_kgm3 = (P * M) / (R * temperature)
        helium_density = density_kgm3 / 1000
        fuel = openmc.Material(name='TRISO Fuel')
        fuel.add_nuclide('U235', u235_fraction * 0.2)
        fuel.add_nuclide('U238', (1 - u235_fraction) * 0.2)
        fuel.add_element('O', 0.4)
        fuel.add_element('C', 0.4)
        fuel.set_density('g/cm3', 10.5)
        fuel.temperature = temperature

        helium = openmc.Material(name='Helium')
        helium.add_element('He', 1.0)
        helium.set_density('g/cm3', helium_density)
        helium.temperature = temperature

        graphite = openmc.Material(name='Graphite')
        graphite.add_element('C', 1.0)
        graphite.set_density('g/cm3', 1.9)
        graphite.add_s_alpha_beta('c_Graphite')
        graphite.temperature = temperature

        materials = openmc.Materials([fuel, helium, graphite])

        fuel_cyl = openmc.ZCylinder(r=dimension)
        cool_cyl = openmc.ZCylinder(r=dimension + 0.5)
        block_cyl = openmc.ZCylinder(r=dimension * 50, boundary_type='vacuum')

        fuel_cell = openmc.Cell(fill=fuel, region=-fuel_cyl)
        cool_cell = openmc.Cell(fill=helium, region=+fuel_cyl & -cool_cyl)
        mod_cell = openmc.Cell(fill=graphite, region=+cool_cyl & -block_cyl)
        universe = openmc.Universe(cells=[fuel_cell, cool_cell, mod_cell])
        geometry = openmc.Geometry(universe)

    elif reactor_type == 'SmallPWR':
        # Water density approx at 15 MPa: rho ≈ 1.0 - 0.00095 * (T - 293)
        water_density = 1.0 - 0.00095 * (temperature - 293)
        fuel = openmc.Material(name='UO2')
        fuel.add_nuclide('U235', u235_fraction)
        fuel.add_nuclide('U238', 1 - u235_fraction)
        fuel.add_element('O', 2.0)
        fuel.set_density('g/cm3', 10.5)
        fuel.temperature = temperature

        clad = openmc.Material(name='Steel')
        clad.add_element('Fe', 0.7)
        clad.add_element('Cr', 0.2)
        clad.add_element('Ni', 0.1)
        clad.set_density('g/cm3', 7.8)
        clad.temperature = temperature

        water = openmc.Material(name='Water')
        water.add_element('H', 2.0)
        water.add_element('O', 1.0)
        water.set_density('g/cm3', water_density)
        water.add_s_alpha_beta('c_H_in_H2O')
        water.temperature = temperature

        materials = openmc.Materials([fuel, clad, water])

        fuel_cyl = openmc.ZCylinder(r=dimension)
        clad_cyl = openmc.ZCylinder(r=dimension + 0.1)
        core_cyl = openmc.ZCylinder(r=dimension * 75, boundary_type='vacuum')

        fuel_cell = openmc.Cell(fill=fuel, region=-fuel_cyl)
        clad_cell = openmc.Cell(fill=clad, region=+fuel_cyl & -clad_cyl)
        water_cell = openmc.Cell(fill=water, region=+clad_cyl & -core_cyl)
        universe = openmc.Universe(cells=[fuel_cell, clad_cell, water_cell])
        geometry = openmc.Geometry(universe)

    else:
        raise ValueError("Invalid reactor type")

    # Common settings (power not directly used in eigenvalue; could add tallies for normalization)
    settings = openmc.Settings()
    settings.run_mode = 'eigenvalue'
    settings.batches = 250
    settings.inactive = 50
    settings.particles = 5000
    settings.source = openmc.IndependentSource(space=openmc.stats.Point((0, 0, 0)))

    # Export
    materials.export_to_xml()
    geometry.export_to_xml()
    settings.export_to_xml()

    # Run
    openmc.run()

# Main script
print("Available reactor types: MSR, Heatpipe, HTGR, SmallPWR")
reactor_type = input("Enter reactor type: ").strip().upper()
u235_fraction = float(input("Enter U-235 fraction (0-1): "))
dimension = float(input("Enter main dimension (e.g., fuel radius in cm): "))
temperature = float(input("Enter temperature (K): "))
power = float(input("Enter power (MW): "))

generate_and_run_openmc_model(reactor_type, u235_fraction, dimension, temperature, power)
print("OpenMC simulation completed.")