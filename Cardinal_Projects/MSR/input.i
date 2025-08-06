# Python script to automate generation of a Cardinal input file for an MSR
# Based on MSFR tutorial structure (partial extract adapted)

def generate_cardinal_msr_file(filename='msr_cardinal.i'):
    cardinal_input = '''
[Mesh]
  [mesh]
    type = FileMeshGenerator
    file = msr.e  # Assume mesh file
  []
[]

[ICs]
  [temp]
    type = ConstantIC
    variable = temp
    value = 948.0
  []
  [density]
    type = ConstantIC
    variable = density
    value = '${fparse -0.882*948+4983.6}'
  []
[]

[AuxVariables]
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
  [cell_temperature]
    type = CellTemperatureAux
    variable = cell_temperature
  []
  [cell_density]
    type = CellDensityAux
    variable = cell_density
  []
  [density]
    type = ParsedAux
    variable = density
    expression = '-0.882*temp+4983.6'
    coupled_variables = temp
    execute_on = timestep_begin
  []
[]

[Problem]
  type = OpenMCCellAverageProblem
  verbose = true
  reuse_source = true
  scaling = 100.0
  density_blocks = '1'
  temperature_blocks = '1'
  cell_level = 0
  power = 300.0e6
  relaxation = dufek_gudowski
  first_iteration_particles = 5000
  skinner = moab
  [Tallies]
    [heat_source]
      type = MeshTally
      mesh_template = 'msr.e'  # Assume
      score = kappa_fission
    []
  []
[]

[MultiApps]
  [nek]
    type = TransientMultiApp
    app_type = CardinalApp
    execute_on = timestep_end
    input_files = 'nek.i'  # Assume separate NekRS file
  []
[]

[Transfers]
  # Transfers to/from NekRS would be added here
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
generate_cardinal_msr_file()
