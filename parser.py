class AccCluster:
	def __init__(self, name, dmas, accs, baseAddress):
		self.name = name
		self.dmas = dmas
		self.accs = accs
		self.clusterBaseAddress = baseAddress
		self.clusterTopAddress = baseAddress
		self.processConfig()

	def processConfig(self):
		dmaClass = []
		accClass = []
		topAddress = self.clusterBaseAddress

		for dma in self.dmas:
			for i in dma['DMA']:
				dmaClass.append(Dma(i['Name'], i['Size'], topAddress))
				topAddress = topAddress + int(i['Size'])
		for acc in self.accs:

			name = None
			localConnections = []
			busConnections = []
			variables = []
			streamVariables = []
			pioAddress = None

			for i in acc['Accelerator']:
				if 'PIO' in i:
					pioAddress = topAddress
					topAddress = topAddress + i['PIO']
				if 'Name' in i:
					name = i['Name']
				if 'LocalPorts' in i:
					localConnections.extend((i['LocalPorts'].split(',')))
				if 'Bus' in i:
					busConnections.extend((i['Bus'].split(',')))
				if 'Var' in i:
					for j in i['Var']:
						if "SPM" in j['Type']:
							variables.append(Variable(j['Name'], int(j['Size']),
								j['Type'], j['Ports'], topAddress))
							topAddress = topAddress + int(j['Size'])
						if "Stream" in j['Type']:
							streamVariables.append(StreamVariable(j['Name'],
								j['Type'], j['DMA'], int(j['StreamSize']),
								j['BufferSize'], j['Direction'].split(','), topAddress))
							topAddress = topAddress + int(j['StreamSize'])
			accClass.append(Accelerator(name, localConnections, busConnections,
				pioAddress, variables, streamVariables))

		self.accs = accClass
		self.dmas = dmaClass
		self.clusterTopAddress = topAddress

class Accelerator:
	def __init__(self, name, localConnections, busConnections, address, variables = None, streamVariables = None):
		self.name = name
		self.localConnections = localConnections
		self.busConnections = busConnections
		self.address = address
		self.variables = variables
		self.streamVariables = streamVariables

	def genConfig(self, clusterName):
		lines = []
		lines.append("acc = " + self.name)
		lines.append("config = hw_path + acc + \".ini\"")
		lines.append("ir = hw_path + acc + \".ll\"")
		lines.append("system." + clusterName + ".top = CommInterface(devicename=acc, gic=gic)")
		lines.append("AccConfig(system." + clusterName + \
			".top, config, ir)")
		#Need to add connections here. Below is an example
		for i in self.busConnections:
			if "Local" in i:
				lines.append("system." + clusterName + "._connect_hwacc(system." + clusterName + "." + self.name + ")")
		for i in self.localConnections:
			lines.append("system." + clusterName + "." + self.name + ".pio " +
				"=" " system." + clusterName + "." + i + ".local")
		#Need to add variables here
		return lines

class Dma:
	def __init__(self, name, size, address):
		self.name = name
		self.size = size
		self.address = address
	#Need to add genConfig

class StreamVariable:
	def __init__ (self, name, type, connection, streamSize,
		bufferSize, direction, address):
		self.name = name
		self.type = type
		self.connection = connection
		self.streamSize = streamSize
		self.bufferSize = bufferSize
		self.direction = direction
		self.address = address
	#Need to add genConfig

class Variable:
	def __init__ (self, name, size, type, ports, address = None):
		self.name = name
		self.size = size
		self.type = type
		self.ports = ports
		self.address = address
	#Need to add genConfig