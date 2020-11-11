import yaml

class AccCluster:
	def __init__(self, cluster_name):
		self.cluster_name = cluster_name

class Accelerator:
	def __init__(self, name, connection, variables = None):
		self.name = name
		self.connection = connection
		if variables:
			self.variables = variables
class Dma:
	def __init__(self, name, size):
		self.name = name
		self.size = size
class Variable:
	def __init__ (self, name, size, type):
		self. name = name
		self. size = size
		self.type = type

stream = open(r'config.yml')

accs = yaml.load_all(stream, Loader=yaml.FullLoader)

for acc in accs:
	for k,v in acc.items():
		for i in v:
			if "DMA" in i:
				print("Found a DMA")
			if "Accelerator" in i:
				print("Found an Accelerator")


baseAddress = 0x10020000
topAddress = 0
maxAddress = 0x13ffffff

print('Base Address: 0x{0:08X}'.format(baseAddress))

size = 0

topAddress = baseAddress + size

if(topAddress>maxAddress):
    print("WARNING: Address range is greater than defined for gem5")

print('Max Address: 0x{0:08X}'.format(topAddress))