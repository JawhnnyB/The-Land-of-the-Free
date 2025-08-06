# Python script to automate generation of a simple Cardinal input file for a CANDU
# Adapted from PWR: heavy water properties, natural U

def generate_cardinal_candu_file(filename='candu_cardinal.i'):
    cardinal_input = '''
inlet_T = 560.0  # K
power = 1e7
Re = 10000.0
outlet_P = 10e6  # CANDU pressure

height = 5.0  # m
Df = 0.012  # Fuel diameter m
pin_diameter = 0.013
pin_pitch = 0.0286  # Bundle spacing approx

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
    fp = d2o  # Assume heavy water properties
  []
[]

[FluidProperties]
  [d2o]
    type = HeavyWaterFluidProperties  # If available, or custom
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
generate_cardinal_candu_file()