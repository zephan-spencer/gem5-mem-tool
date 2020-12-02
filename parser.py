# Need to rename define difference between system and cluster in all genconfigs

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
				# Need to handle not having interrupt numbers
				dmaClass.append(Dma(i['Name'], topAddress, i['InterruptNum'], i['Size'], i['MaxReq']))
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

	def genConfig(self):
		lines = []
		# Need to add some customization here. Consider this a placeholder
		# Also need to edit AccCluster.py's addresses to match the gem5 supported ones
		lines.append("def build" + self.name + "(options, system, clstr):" + "\n")
		lines.append("	hw_path = options.accpath + \"/\" + options.accbench + \"/hw/\"")
		lines.append("	local_low = " + hex(self.clusterBaseAddress))
		lines.append("	local_high = " + hex(self.clusterTopAddress))
		lines.append("	external_range = [AddrRange(0x00000000, local_low-1), AddrRange(local_high+1, 0xFFFFFFFF)]")
		lines.append("	clstr._attach_bridges(system, local_range, external_range)")
		# Need to define l2coherency in the YAML file?
		lines.append("	clstr._connect_caches(system, options, l2coherent=False)")
		lines.append("	gic = system.realview.gic")
		lines.append("")

		return lines

class Accelerator:

	def __init__(self, name, localConnections, busConnections, address, variables = None, streamVariables = None):
		self.name = name.lower()
		self.localConnections = localConnections
		self.busConnections = busConnections
		self.address = address
		self.variables = variables
		self.streamVariables = streamVariables

	def genConfig(self, clusterName):
		lines = []
		lines.append("acc = " + self.name)
		# Need to add a user defined path & user defined interrupts here
		lines.append("config = hw_path + acc + \".ini\"")
		lines.append("ir = hw_path + acc + \".ll\"")
		lines.append("clstr." + self.name +" = CommInterface(devicename=acc, gic=gic)")
		lines.append("AccConfig(clstr." + self.name + ", config, ir)")

		# Add connections to memory buses
		for i in self.busConnections:
			# Might need to add more options here... only option now is connecting to local membus
			if "Local" in i:
				lines.append("clstr._connect_hwacc(clstr." + self.name + ")")
		
		# Add connections from pio to local
		for i in self.localConnections:
			lines.append("clstr." + self.name + ".pio " +
				"=" " clstr." + i + ".local")

		lines.append("")

		# Add scratchpad variables
		for i in self.variables:
			lines = i.genConfig(lines)

		# Add Stream Variables

		return lines

# Need to add a Stream DMA Class

class Dma:
	def __init__(self, name, address, int_num = None, size = 64, MaxReq = 4):
		self.name = name.lower()
		self.size = size
		self.address = address
		self.int_num = int_num
		self.MaxReq = MaxReq
	# Probably could apply the style used here in other genConfigs
	def genConfig(self, clusterName):
		lines = []
		dmaPath = "clstr." + self.name + "."
		systemPath = "clstr."
		# Is pio size always 21
		lines.append(dmaPath + "NoncoherentDma(pio_addr=" 
			+ hex(self.address) + ", pio_size = " + "21" + ", gic=gic, int_num=" + str(self.int_num) +")")
		lines.append(dmaPath + "cluster_dma = " + systemPath + "local_bus.slave")
		lines.append(dmaPath + "dma = " + systemPath + "coherency_bus.slave")
		lines.append(dmaPath + "pio = " + systemPath + "top.local")
		lines.append(dmaPath + "max_req_size = " + str(self.MaxReq))
		lines.append(dmaPath + "buffer_size = " + str(self.size))
		lines.append("")

		return lines

class StreamVariable:
	# Need to add read and write interrupts
	def __init__ (self, name, type, connection, streamSize,
		bufferSize, direction, address):
		self.name = name.lower()
		self.type = type
		self.connection = connection
		self.streamSize = streamSize
		self.bufferSize = bufferSize
		self.direction = direction
		self.address = address
	#Need to add genConfig

class Variable:
	def __init__ (self, name, size, type, ports, address = None):
		self.name = name.lower()
		self.size = size
		self.type = type
		self.ports = ports
		self.address = address

	def genConfig(self, lines):
		lines.append("addr = " + hex(self.address))
		lines.append("spmRange = AddrRange(addr, addr + " + hex(self.size) + ")")
		# Choose a style with the "."s and pick it
		lines.append("clstr." + self.name + " = ScratchpadMemory(range = spmRange)")
		# Probably need to add table and read mode to the YAML File
		lines.append("clstr." + self.name + "." + "conf_table_reported = False")
		lines.append("clstr." + self.name + "." + "ready_mode = True")
		lines.append("clstr." + self.name + "." + "port" + " = " + "clstr.local_bus.master")
		lines.append("")

		return lines