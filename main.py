import yaml
import os
import textwrap
from parser import *

imports = "import m5\nfrom m5.objects import *\nfrom m5.util import *\nimport ConfigParser\nfrom HWAccConfig import *\n\n"

stream = open(r'config.yml')

clusters = []

variables = []

baseAddress = 0x10020000
# maxAddress = 0x13ffffff

config = yaml.load_all(stream, Loader=yaml.FullLoader)

# Initial processing
for section in config:
	clusterName = None
	dmas = []
	accs = []
	for k,v in section.items():
		for i in v:
			if "Name" in i:
				clusterName = i['Name']
				# print("Adding Cluster: " + clusterName)
			if "DMA" in i:
				dmas.append(i)
			if "Accelerator" in i:
				accs.append(i)

	clusters.append(AccCluster(clusterName, dmas, accs, baseAddress))
	baseAddress = clusters[-1].clusterTopAddress + 1

print('Cluster 0 Base Address: 0x{0:08X}'.format(clusters[0].clusterBaseAddress))
print('Cluster 0 Top Address: 0x{0:08X}'.format(clusters[0].clusterTopAddress))
# print('Matrix 0 Address: 0x{0:08X}'.format(clusters[0].accs[1].variables[0].address))

# print('Cluster 1 Base Address: 0x{0:08X}'.format(clusters[1].clusterBaseAddress))
# print('Cluster 1: 0x{0:08X}'.format(clusters[1].clusterTopAddress))
# print('Matrix 1 Address: 0x{0:08X}'.format(clusters[1].accs[0].variables[0].address))
# filepath = os.getcwd()

# Write out the file

# Write out config file
with open("test.py", 'w') as f:
	f.write(imports)
	for i in clusters:
		for j in i.genConfig():
			f.write(j + "\n")
		#Add cluster definitions here
		for j in i.dmas:
			for k in j.genConfig():
				f.write("	" + k + "\n")
		for j in i.accs:
			for k in j.genConfig():
				f.write("	" + k + "\n")
	f.write("def makeHWAcc(options, system):\n\n")
	for i in clusters:
		f.write("	system." + i.name.lower() + " = AccCluster()" + "\n")
		f.write("	build" + i.name + "(options, system, system." + i.name.lower() + ")\n\n")

# Write out header
with open("test.h", 'w') as f:
	for i in clusters:
		f.write("//Cluster: " + j.name.upper() + "\n")
		for j in i.dmas:
			f.write("#define " + j.name.upper() + " " + hex(j.address) + "\n")
		for j in i.accs:
			f.write("//Accelerator: " + j.name.upper() + "\n")
			f.write("#define " + j.name.upper() + " " + hex(j.address) + "\n")
			for k in j.variables:
				f.write("#define " + k.name.upper() + " " + hex(k.address) + "\n")
# if(topAddress>maxAddress):
#     print("WARNING: Address range is greater than defined for gem5")