import openmc

# Assume materials.xml, geometry.xml, and settings.xml are in the current working directory
# No need to load or parse them manually; OpenMC reads them automatically when run() is called

openmc.run()

print("OpenMC simulation completed using materials.xml, geometry.xml, and settings.xml.")