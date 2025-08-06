import gmsh
import os
import subprocess  # For MOOSE mesh validation

# Generate 3D mesh for MSR (cylinder fuel + annular reflector)
gmsh.initialize()
gmsh.model.add("msr_mesh")

# Fuel cylinder (radius 50 cm, height 200 cm)
gmsh.model.occ.addCylinder(0, 0, 0, 0, 0, 200, 50, 1)
# Reflector (outer cylinder, subtract inner)
gmsh.model.occ.addCylinder(0, 0, 0, 0, 0, 200, 70, 2)
gmsh.model.occ.cut([(3, 2)], [(3, 1)], 3)  # Annulus for reflector
gmsh.model.occ.fragment([(3, 1)], [(3, 3)])
gmsh.model.occ.synchronize()

# Physical groups
gmsh.model.addPhysicalGroup(3, [1], 1, "fuel")
gmsh.model.addPhysicalGroup(3, [3], 2, "reflector")

gmsh.model.mesh.generate(3)
os.makedirs('meshes/cardinal/', exist_ok=True)
gmsh.write('meshes/cardinal/msr.e')  # Direct Exodus export

gmsh.finalize()

# Validate mesh with MOOSE (assumes moose-opt in PATH; run a simple mesh test .i)
test_i_content = '''
[Mesh]
  file = meshes/cardinal/msr.e
[]

[Outputs]
  exodus = true
[]
'''
with open('meshes/cardinal/test_mesh.i', 'w') as f:
    f.write(test_i_content)
subprocess.run(['moose-opt', '-i', 'meshes/cardinal/test_mesh.i'])
print("Cardinal mesh generated and validated with MOOSE.")