import os

def generate_cardinal_file(reactor_type, u235_fraction, dimension, temperature, power):
    power_w = power * 1e6  # Convert MW to W
    if reactor_type == 'MSR':
        # For MSR, dimension is height (cm), use temperature for inlet_T
        height = dimension
        cardinal_input = f'''
[GlobalParams]
  power = {power_w}  # Power in W
  inlet_T = {temperature}  # K
  height = {height}  # cm
[]

[Mesh]
  type = GeneratedMesh
  dim = 3
  nx = 10
  ny = 10
  nz = 20
  xmin = -70
  xmax = 70
  ymin = -70
  ymax = 70
  zmin = -{height/2}
  zmax = {height/2}
[]

[Problem]
  type = OpenMCCellAverageProblem
  temperature_blocks = 'fuel reflector'
  density_blocks = 'fuel'
  tally_type = cell
  tally_blocks = 'fuel'
  cell_level = 0
  initial_properties = xml
  normalize_by_global = true
  solid_cell_level = 0
[]

[Executioner]
  type = Transient
  num_steps = 10
  dt = 0.1
[]

[Outputs]
  exodus = true
[]

[AuxVariables]
  [temp]
    initial_condition = ${{inlet_T}}
  []
  [heat_source]
    family = MONOMIAL
    order = CONSTANT
  []
[]

[Materials]
  [fuel]
    type = CoupledFeedbackNeutronicsMaterial
    block = fuel
    temperature = temp
  []
  [reflector]
    type = GenericMoltresMaterial
    block = reflector
    temperature = temp
  []
[]

[Postprocessors]
  [power_total]
    type = ElementIntegralVariablePostprocessor
    variable = heat_source
  []
[]
'''
    elif reactor_type == 'Heatpipe':
        height = dimension
        cardinal_input = f'''
[GlobalParams]
  power = {power_w}  # W
  inlet_T = {temperature}  # K
[]

[Mesh]
  type = GeneratedMesh
  dim = 3
  nx = 20
  ny = 20
  nz = 50
  xmin = -100
  xmax = 100
  ymin = -100
  ymax = 100
  zmin = -{height}
  zmax = {height}
[]

[Problem]
  type = OpenMCCellAverageProblem
  temperature_blocks = 'fuel heatpipe cladding'
  tally_type = cell
  tally_blocks = 'fuel'
  cell_level = 0
  initial_properties = xml
  normalize_by_global = true
[]

[MultiApps]
  [bison]
    type = TransientMultiApp
    app_type = BisonApp
    execute_on = timestep_end
    input_files = 'fuel_performance.i'  # Assume separate
  []
  [sockeye]
    type = TransientMultiApp
    app_type = SockeyeApp
    execute_on = timestep_end
    input_files = 'heatpipe.i'  # Assume separate
  []
[]

[Transfers]
  [to_bison_temp]
    type = MultiAppGeneralFieldNearestLocationTransfer
    to_multi_app = bison
    source_variable = temp
    variable = temp
  []
  [from_bison_power]
    type = MultiAppGeneralFieldNearestLocationTransfer
    from_multi_app = bison
    variable = power
    source_variable = power
  []
  [to_sockeye]
    type = MultiAppGeneralFieldShapeEvaluationTransfer
    to_multi_app = sockeye
    source_variable = heat_source
    variable = heat_flux
  []
[]

[Executioner]
  type = Transient
  num_steps = 20
  dt = 0.05
[]

[Outputs]
  exodus = true
[]
'''
    elif reactor_type == 'HTGR':
        height = dimension
        cardinal_input = f'''
power = {power_w}  # W
inlet_T = {temperature}  # K

height = {height}  # m

[Mesh]
  [solid]
    type = FileMeshGenerator
    file = mesh_in.e  # Assume generated mesh
  []
[]

[AuxVariables]
  [cell_temperature]
    family = MONOMIAL
    order = CONSTANT
  []
[]

[AuxKernels]
  [cell_temperature]
    type = CellTemperatureAux
    variable = cell_temperature
  []
[]

[Problem]
  type = OpenMCCellAverageProblem
  power = ${{power}}
  scaling = 100.0  # cm to m
  temperature_blocks = 'graphite compacts'
  cell_level = 1
  tally_type = cell
  tally_blocks = 'compacts'
  initial_properties = xml
  normalize_by_global = true
[]

[MultiApps]
  [solid]
    type = TransientMultiApp
    app_type = HeatTransferApp
    execute_on = timestep_end
    input_files = 'solid.i'  # Separate solid heat conduction
  []
[]

[Transfers]
  [heat_source]
    type = MultiAppGeneralFieldShapeEvaluationTransfer
    to_multi_app = solid
    source_variable = heat_source
    variable = power
    from_postprocessor_to_be_preserved = power_total
    to_postprocessor = power_received
  []
  [temperature]
    type = MultiAppGeneralFieldNearestLocationTransfer
    from_multi_app = solid
    source_variable = T
    variable = temp
  []
[]

[Executioner]
  type = Transient
  num_steps = 5
  dt = 1.0
[]

[Outputs]
  exodus = true
[]
'''
    elif reactor_type == 'SmallPWR':
        height = dimension
        cardinal_input = f'''
inlet_T = {temperature}  # K
power = {power_w}  # W for 10 MWe
Re = 10000.0  # Turbulent flow

height = {height}  # m
Df = 0.008  # Fuel diameter m
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
    p = 15e6  # PWR pressure Pa
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
  power = ${{power}}
  scaling = 100.0
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
    else:
        raise ValueError("Invalid reactor type")

    filename = f"{reactor_type.lower()}_cardinal.i"
    with open(filename, 'w') as f:
        f.write(cardinal_input)
    return filename

# Main script
print("Available reactor types: MSR, Heatpipe, HTGR, SmallPWR")
reactor_type = input("Enter reactor type: ").strip().upper()
u235_fraction = float(input("Enter U-235 fraction (0-1): "))
dimension = float(input("Enter main dimension (e.g., height in cm for Cardinal): "))
temperature = float(input("Enter temperature (K): "))
power = float(input("Enter power (MW): "))

filename = generate_cardinal_file(reactor_type, u235_fraction, dimension, temperature, power)
print(f"Generated {filename}")

# Run Cardinal (assumes cardinal-opt in PATH)
os.system(f"cardinal-opt -i {filename}")
print("Cardinal simulation completed.")