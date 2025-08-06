# Python script to automate generation of a simple Cardinal input file for a BWR
# Adapted from general LWR concepts: OpenMC for neutronics, basic heat and fluid (single phase approx for boiling)

def generate_cardinal_bwr_file(filename='bwr_cardinal.i'):
    cardinal_input = '''
inlet_T = 550.0  # K (boiling ~557K at 7MPa)
power = 1e7  # W approx
Re = 10000.0

height = 3.0  # m
Df = 0.0095  # Fuel diameter m
pin_diameter = 0.011
pin_pitch = 0.0125

[Mesh]
  type = GeneratedMesh
  dim = 2
  nx = 20
  ny = 20
  xmin = 0
  xmax = ${pin_pitch}
  ymin = 0
  ymax = ${pin_pitch}
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
    p = 7e6  # BWR pressure Pa
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
generate_cardinal_bwr_file()