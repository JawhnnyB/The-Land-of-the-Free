# Python script to automate generation of a Cardinal input file for a PWR
# Adapted from LWR concepts and SFR pincell structure (water instead of sodium)

def generate_cardinal_pwr_file(filename='pwr_cardinal.i'):
    cardinal_input = '''
inlet_T = 565.0
power = 1e7
Re = 10000.0
outlet_P = 15e6

height = 3.0
Df = 0.008
pin_diameter = 0.0095
pin_pitch = 0.0126

[Mesh]
  [solid]
    type = FileMeshGenerator
    file = solid_in.e  # Assume mesh
  []
[]

[AuxVariables]
  [cell_temperature]
    family = MONOMIAL
    order = CONSTANT
  []
  [density]
    family = MONOMIAL
    order = CONSTANT
  []
[]

[AuxKernels]
  [cell_temperature]
    type = CellTemperatureAux
    variable = cell_temperature
  []
  [density]
    type = FluidDensityAux
    variable = density
    p = ${outlet_P}
    T = temp
    fp = water
  []
[]

[FluidProperties]
  [water]
    type = Water97FluidProperties
  []
[]

[Problem]
  type = OpenMCCellAverageProblem
  power = ${power}
  temperature_blocks = 'fuel clad moderator'
  density_blocks = 'moderator'
  tally_type = cell
  tally_blocks = 'fuel'
  cell_level = 0
  initial_properties = xml
  normalize_by_global = true
[]

[Executioner]
  type = Transient
  num_steps = 10
  dt = 0.5
[]

[Outputs]
  exodus = true
[]
'''
    with open(filename, 'w') as f:
        f.write(cardinal_input)

# Call the function to generate the file
generate_cardinal_pwr_file()