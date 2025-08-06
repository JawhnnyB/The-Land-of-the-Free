# Python script to automate generation of a Cardinal input file for an SFR
# Based on SFR pincell tutorial structure (partial extract adapted)

def generate_cardinal_sfr_file(filename='sfr_cardinal.i'):
    cardinal_input = '''
inlet_T = 573.0
power = 1e3
Re = 500.0
outlet_P = 1e6

height = 0.5
Df = 0.00825
pin_diameter = 0.0097
pin_pitch = 0.0128

mu = 8.8e-5
rho = 723.6
Cp = 5512.0

Rf = ${fparse Df / 2.0}

flow_area = ${fparse pin_pitch * pin_pitch - pi * pin_diameter * pin_diameter / 4.0}
wetted_perimeter = ${fparse pi * pin_diameter}
hydraulic_diameter = ${fparse 4.0 * flow_area / wetted_perimeter}

U_ref = ${fparse Re * mu / rho / hydraulic_diameter}
mdot = ${fparse rho * U_ref * flow_area}
dT = ${fparse power / mdot / Cp}

[Mesh]
  [solid]
    type = FileMeshGenerator
    file = solid_in.e  # Assume mesh file
  []
[]

[AuxVariables]
  [material_id]
    family = MONOMIAL
    order = CONSTANT
  []
  [cell_temperature]
    family = MONOMIAL
    order = CONSTANT
  []
  [cell_density]
    family = MONOMIAL
    order = CONSTANT
  []
[]

[AuxKernels]
  [material_id]
    type = CellMaterialIDAux
    variable = material_id
  []
  [cell_temperature]
    type = CellTemperatureAux
    variable = cell_temperature
  []
  [cell_density]
    type = CellDensityAux
    variable = cell_density
  []
  [density]
    type = FluidDensityAux
    variable = density
    p = ${outlet_P}
    T = nek_temp
    fp = sodium
    execute_on = timestep_end
  []
[]

[FluidProperties]
  [sodium]
    type = SodiumProperties
  []
[]

[Problem]
  type = OpenMCCellAverageProblem
  power = ${power}
  temperature_blocks = 'fuel clad coolant'
  density_blocks = 'coolant'
  tally_type = cell
  tally_blocks = 'fuel'
  cell_level = 0
  initial_properties = xml
  normalize_by_global = true
[]

[MultiApps]
  [thm]
    type = TransientMultiApp
    app_type = ThermalHydraulicsApp
    execute_on = timestep_end
    input_files = 'thm.i'  # Assume separate THM file
  []
  [bison]
    type = TransientMultiApp
    app_type = BisonApp
    execute_on = timestep_end
    input_files = 'bison.i'  # Assume separate Bison file
  []
  [nek]
    type = TransientMultiApp
    app_type = CardinalApp
    execute_on = timestep_end
    input_files = 'nek.i'  # Assume separate NekRS file
  []
[]

[Transfers]
  # Transfers to/from THM, Bison, NekRS would be added here
  # Omitted for brevity; see tutorial for full
[]

[Executioner]
  type = Transient
  num_steps = 10
  dt = 0.1
[]

[Outputs]
  exodus = true
[]
'''
    with open(filename, 'w') as f:
        f.write(cardinal_input)

# Call the function to generate the file
generate_cardinal_sfr_file()