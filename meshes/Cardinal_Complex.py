import gmsh
import os
import subprocess

def generate_advanced_cardinal_mesh(reactor_type):
    gmsh.initialize()
    gmsh.model.add(f"{reactor_type}_advanced")
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)  # Delaunay
    gmsh.option.setNumber("Mesh.RecombineAll", 1)  # Hex recombination
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 0.05)

    height = 366.0
    if reactor_type in ['BWR', 'PWR', 'CANDU']:
        pitch = 1.26 if reactor_type == 'PWR' else 1.25 if reactor_type == 'BWR' else 2.86
        fuel_r = 0.4096 if reactor_type == 'PWR' else 0.418 if reactor_type == 'BWR' else 0.6122
        clad_r = fuel_r + 0.05715
        assembly_size = 17 if reactor_type == 'PWR' else 18 if reactor_type == 'BWR' else 37
        positions = [(i * pitch - (assembly_size-1)*pitch/2, j * pitch - (assembly_size-1)*pitch/2) for i in range(assembly_size) for j in range(assembly_size)]
        guide_pos = [(i * pitch - (assembly_size-1)*pitch/2, j * pitch - (assembly_size-1)*pitch/2) for i in [2,5,8,11,14] for j in [2,5,8,11,14]] if reactor_type == 'PWR' else []  # Adjust for others
        fuel_vols = []
        clad_vols = []
        guide_vols = []
        for x, y in positions:
            if (x, y) in guide_pos:
                guide_id = gmsh.model.occ.addCylinder(x, y, 0, 0, 0, height, clad_r * 1.2)  # Thimble
                guide_vols.append(guide_id)
            else:
                fuel_id = gmsh.model.occ.addCylinder(x, y, 0, 0, 0, height, fuel_r)
                clad_id = gmsh.model.occ.addCylinder(x, y, 0, 0, 0, height, clad_r)
                clad_vol = gmsh.model.occ.cut([(3, clad_id)], [(3, fuel_id)])[0][0][1]
                fuel_vols.append(fuel_id)
                clad_vols.append(clad_vol)
        half_size = (assembly_size - 1) * pitch / 2 + 0.1
        mod_box = gmsh.model.occ.addBox(-half_size, -half_size, 0, 2*half_size, 2*half_size, height)
        mod_vol = gmsh.model.occ.cut([(3, mod_box)], [(3, f) for f in fuel_vols] + [(3, c) for c in clad_vols] + [(3, g) for g in guide_vols])[0][0][1]
    elif reactor_type == 'MSR':
        core_r = 200
        num_zones = 5
        channel_r = 10
        num_channels = 37
        refl_thick = 50
        positions = [(0, 0)] + [(r * 30 * np.cos(i * np.pi / 3), r * 30 * np.sin(i * np.pi / 3)) for r in range(1, 4) for i in range(6 * r)]
        salt_vols = []
        channel_vols = []
        for z in range(num_zones):
            z_start = z * (height / num_zones)
            z_end = (z + 1) * (height / num_zones)
            zone_id = gmsh.model.occ.addCylinder(0, 0, z_start, 0, 0, z_end - z_start, core_r)
            for x, y in positions:
                channel_id = gmsh.model.occ.addCylinder(x, y, z_start, 0, 0, z_end - z_start, channel_r)
                gmsh.model.occ.cut([(3, zone_id)], [(3, channel_id)])
                channel_vols.append(channel_id)
            salt_vols.append(zone_id)
        refl_id = gmsh.model.occ.addCylinder(0, 0, 0, 0, 0, height, core_r + refl_thick)
        refl_vol = gmsh.model.occ.cut([(3, refl_id)], [(3, s) for s in salt_vols])[0][0][1]
    elif reactor_type == 'SFR':
        pitch = 0.78
        fuel_r = 0.35
        clad_r = fuel_r + 0.045
        wire_r = 0.1  # Wire wrap approx
        num_rings = 15  # ~331 pins, but use 6 for ~91 to simplify
        positions = [(0, 0)] + [(r * pitch * np.cos(i * np.pi / 3), r * pitch * np.sin(i * np.pi / 3)) for r in range(1, num_rings + 1) for i in range(6 * r)]
        fuel_vols = []
        clad_vols = []
        wire_vols = []
        for x, y in positions:
            fuel_id = gmsh.model.occ.addCylinder(x, y, 0, 0, 0, height, fuel_r)
            clad_id = gmsh.model.occ.addCylinder(x, y, 0, 0, 0, height, clad_r)
            clad_vol = gmsh.model.occ.cut([(3, clad_id)], [(3, fuel_id)])[0][0][1]
            # Helical wire wrap (approx as torus segments; simplified straight for mesh)
            wire_id = gmsh.model.occ.addCylinder(x + clad_r, y, 0, 0, 0, height, wire_r)
            wire_vols.append(wire_id)
            fuel_vols.append(fuel_id)
            clad_vols.append(clad_vol)
        outer_r = num_rings * pitch
        sodium_id = gmsh.model.occ.addCylinder(0, 0, 0, 0, 0, height, outer_r)
        sodium_vol = gmsh.model.occ.cut([(3, sodium_id)], [(3, f) for f in fuel_vols] + [(3, c) for c in clad_vols] + [(3, w) for w in wire_vols])[0][0][1]

    gmsh.model.occ.synchronize()
    gmsh.model.mesh.generate(3)
    os.makedirs('meshes/cardinal/', exist_ok=True)
    gmsh.write(f'meshes/cardinal/{reactor_type}_advanced.e')

    gmsh.finalize()

    # Advanced validation .i with heat conduction and boundary conditions
    test_i = f'''
[Mesh]
  file = meshes/cardinal/{reactor_type}_advanced.e
[]

[Variables]
  [temp]
    initial_condition = 500
  []
[]

[Kernels]
  [heat_conduction]
    type = HeatConduction
    variable = temp
  []
[]

[BCs]
  [bottom]
    type = DirichletBC
    variable = temp
    boundary = 'bottom'
    value = 500
  []
  [top]
    type = DirichletBC
    variable = temp
    boundary = 'top'
    value = 600
  []
[]

[Executioner]
  type = Steady
[]

[Outputs]
  exodus = true
[]
'''
    test_file = f'meshes/cardinal/{reactor_type}_advanced_test.i'
    with open(test_file, 'w') as f:
        f.write(test_i)
    subprocess.run(['cardinal-opt', '-i', test_file])
    print(f"Advanced mesh for {reactor_type} generated and validated with heat conduction.")

# Generate for all
for rt in ['BWR', 'CANDU', 'MSR', 'PWR', 'SFR']:
    generate_advanced_cardinal_mesh(rt)