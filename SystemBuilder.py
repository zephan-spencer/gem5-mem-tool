import yaml
import os
import textwrap
import shutil
import argparse

from parser import *

imports = "import m5\nfrom m5.objects import *\nfrom m5.util import *\nimport ConfigParser\nfrom HWAccConfig import *\n\n"

parser = argparse.ArgumentParser(description="SALAM System Builder")

parser.add_argument('-name', help="System Name", required=True)
parser.add_argument('-benchDir', help="Path to Benchmark Directory", required=True)
parser.add_argument('-config', help="Name of Config File", required=True)

args=parser.parse_args()

fileName = args.name

workingDirectory = args.benchDir

stream = open(workingDirectory + args.config + '.yml', "r")

clusters = []

variables = []

baseAddress = 0x10020000
maxAddress = 0x13ffffff

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

# Write out config file
with open("/home/he-man/gem5-SALAM/configs/SALAM/" + fileName + ".py", 'w') as f:
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
with open(workingDirectory + fileName + ".h", 'w') as f:
	for i in clusters:
		f.write("//Cluster: " + j.name.upper() + "\n")
		for j in i.dmas:
			if j.dmaType == "NonCoherent":
				f.write("//" + j.dmaType + "DMA" + "\n")
				f.write("#define " + j.name.upper() + "_Flags " + hex(j.address) + "\n")
				f.write("#define " + j.name.upper() + "_RdAddr " + hex(j.address + 1) + "\n")
				f.write("#define " + j.name.upper() + "_WrAddr " + hex(j.address + 9) + "\n")
				f.write("#define " + j.name.upper() + "_CopyLen " + hex(j.address + 17) + "\n")
			elif j.dmaType == "Stream":
				f.write("//" + j.dmaType + "DMA" + "\n")
				f.write("#define " + j.name.upper() + "_Flags " + hex(j.address) + "\n")
				f.write("#define " + j.name.upper() + "_RdAddr " + hex(j.address + 4) + "\n")
				f.write("#define " + j.name.upper() + "_WrAddr " + hex(j.address + 12) + "\n")
				f.write("#define " + j.name.upper() + "_RdFrameSize " + hex(j.address + 20) + "\n")
				f.write("#define " + j.name.upper() + "_NumRdFrames " + hex(j.address + 24) + "\n")
				f.write("#define " + j.name.upper() + "_RdFrameBufSize " + hex(j.address + 25) + "\n")
				f.write("#define " + j.name.upper() + "_WrFrameSize " + hex(j.address + 26) + "\n")
				f.write("#define " + j.name.upper() + "_NumWrFrames " + hex(j.address + 30) + "\n")
				f.write("#define " + j.name.upper() + "_WrFrameBufSize " + hex(j.address + 31) + "\n")
		for j in i.accs:
			f.write("//Accelerator: " + j.name.upper() + "\n")
			f.write("#define " + j.name.upper() + " " + hex(j.address) + "\n")
			for k in j.variables:
				f.write("#define " + k.name.upper() + " " + hex(k.address) + "\n")

# print(workingDirectory + fileName + ".h")

shutil.copyfile("fs_template.py","/home/he-man/gem5-SALAM/configs/SALAM/fs_" + fileName + ".py")

# Generate full system
f = open("/home/he-man/gem5-SALAM/configs/SALAM/fs_" + fileName + ".py", "r")

fullSystem = f.readlines()

fullSystem[69] = "import " + fileName
fullSystem[239] = "		" + fileName + ".makeHWAcc(options, test_sys)"

f = open("/home/he-man/gem5-SALAM/configs/SALAM/fs_" + fileName + ".py", "w")

f.writelines(fullSystem)

print(hex(clusters[-1].clusterTopAddress))

if(clusters[-1].clusterTopAddress>maxAddress):
    print("WARNING: Address range is greater than defined for gem5")