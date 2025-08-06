import gmsh
import openmc
import os
import numpy as np

def generate_advanced_mesh(reactor_type):
    gmsh.initialize()
    gmsh.model.add(f"{reactor_type}_advanced")
    gmsh.option.setNumber("Mesh.Algorithm", 6)  # Frontal-Delaunay for quality
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 0.1)
    gmsh.option.setNumber("Mesh.Optimize", 1)

    height = 366.0  # Typical active core height cm
    if reactor_type in ['BWR', 'PWR', 'CANDU']:
        pitch = 1.26 if reactor_type == 'PWR' else 1.25 if reactor_type == 'BWR' else 2.86
        fuel_r = 0.4096 if reactor_type == 'PWR' else 0.418 if reactor_type == 'BWR' else 0.6122
        clad_r = fuel_r + 0.05715
        assembly_size = 17 if reactor_type == 'PWR' else 18 if reactor_type == 'BWR' else 37  # Pins per assembly
        # 17x17 array with 24 guide tubes (PWR example; simplify for others)
        positions = [(i * pitch - (assembly_size-1)*pitch/2, j * pitch - (assembly_size-1)*pitch/2) for i in range(assembly_size) for j in range(assembly_size)]
        guide_tube_pos = [(i * pitch - (assembly_size-1)*pitch/2, j * pitch - (assembly_size-1)*pitch/2) for i in [2,5,8,11,14] for j in [2,5,8,11,14]] + [(8*pitch - (assembly_size-1)*pitch/2, k) for k in [3*pitch - (assembly_size-1)*pitch/2, 13*pitch - (assembly_size-1)*pitch/2]]  # Example guides
        fuel_vols = []
        clad_vols = []
        guide_vols = []
        for x, y in positions:
            if (x, y) in guide_tube_pos:
                guide_id = gmsh.model.occ.addCylinder(x, y, 0, 0, 0, height, clad_r)  # Guide tube (empty)
                guide_vols.append(guide_id)
            else:
                fuel_id = gmsh.model.occ.addCylinder(x, y, 0, 0, 0, height, fuel_r)
                clad_id = gmsh.model.occ.addCylinder(x, y, 0, 0, 0, height, clad_r)
                clad_vol = gmsh.model.occ.cut([(3, clad_id)], [(3, fuel_id)])[0][0][1]
                fuel_vols.append(fuel_id)
                clad_vols.append(clad_vol)
        # Moderator: assembly box minus pins
        half_size = (assembly_size - 1) * pitch / 2 + 0.1
        mod_box = gmsh.model.occ.addBox(-half_size, -half_size, 0, 2*half_size, 2*half_size, height)
        mod_vol = gmsh.model.occ.cut([(3, mod_box)], [(3, f) for f in fuel_vols] + [(3, c) for c in clad_vols] + [(3, g) for g in guide_vols])[0][0][1]
    elif reactor_type == 'MSR':
        core_r = 200  # Larger core
        channel_r = 10
        num_channels = 37  # Hex pattern
        refl_thick = 50
        # Fuel salt with graphite channels (moderator blocks with holes)
        positions = [(0, 0)] + [(r * 20 * np.cos(i * np.pi / 3), r * 20 * np.sin(i * np.pi / 3)) for r in range(1, 4) for i in range(6)]
        channel_vols = []
        for x, y in positions:
            channel_id = gmsh.model.occ.addCylinder(x, y, 0, 0, 0, height, channel_r)  # Graphite channel
            channel_vols.append(channel_id)
        core_id = gmsh.model.occ.addCylinder(0, 0, 0, 0, 0, height, core_r)
        salt_vol = gmsh.model.occ.cut([(3, core_id)], [(3, c) for c in channel_vols])[0][0][1]
        # Reflector
        refl_id = gmsh.model.occ.addCylinder(0, 0, 0, 0, 0, height, core_r + refl_thick)
        refl_vol = gmsh.model.occ.cut([(3, refl_id)], [(3, salt_vol)])[0][0][1]
    elif reactor_type == 'SFR':
        pitch = 0.78  # Typical SFR pin pitch
        fuel_r = 0.35
        clad_r = fuel_r + 0.045
        num_rings = 6  # ~217 pins in hex assembly
        positions = [(0, 0)] + [(r * pitch * np.cos(i * np.pi / 3), r * pitch * np.sin(i * np.pi / 3)) for r in range(1, num_rings + 1) for i in range(6 * r)]
        fuel_vols = []
        clad_vols = []
        for x, y in positions:
            fuel_id = gmsh.model.occ.addCylinder(x, y, 0, 0, 0, height, fuel_r)
            clad_id = gmsh.model.occ.addCylinder(x, y, 0, 0, 0, height, clad_r)
            clad_vol = gmsh.model.occ.cut([(3, clad_id)], [(3, fuel_id)])[0][0][1]
            fuel_vols.append(fuel_id)
            clad_vols.append(clad_vol)
        # Sodium: hex prism enclosing assembly
        outer_r = num_rings * pitch
        sodium_id = gmsh.model.occ.addCylinder(0, 0, 0, 0, 0, height, outer_r)  # Approx cylinder for hex
        sodium_vol = gmsh.model.occ.cut([(3, sodium_id)], [(3, f) for f in fuel_vols] + [(3, c) for c in clad_vols])[0][0][1]

    gmsh.model.occ.synchronize()
    gmsh.model.mesh.generate(3)
    os.makedirs('meshes/openmc/', exist_ok=True)
    gmsh.write(f'meshes/openmc/{reactor_type}_advanced.msh')

    gmsh.finalize()

    # Convert to DAGMC HDF5 (run mbconvert or make_dagmc_h5m; assume tool available)
    os.system(f'mbconvert meshes/openmc/{reactor_type}_advanced.msh meshes/openmc/{reactor_type}_advanced.h5')
    print(f"Advanced DAGMC mesh for {reactor_type} generated.")

# Generate for all
for rt in ['BWR', 'CANDU', 'MSR', 'PWR', 'SFR']:
    generate_advanced_mesh(rt)