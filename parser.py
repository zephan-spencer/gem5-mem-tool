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

		# Parse DMAs
		for dma in self.dmas:
			for i in dma['DMA']:
				# Decide whether the DMA is NonCoherent or Stream
				if 'NonCoherent' in i['Type'] :
					dmaClass.append(Dma(i['Name'], topAddress, i['Type'], i['InterruptNum'], i['Size'], i['MaxReq']))
					topAddress = topAddress + int(i['Size'])
				elif 'Stream' in i['Type']:
					dmaClass.append(StreamDma(i['Name'], i['PIO'], topAddress, i['Type'], i['ReadInt'], i['WriteInt'], i['Size']))
					topAddress = topAddress + int(i['Size'])

		# Parse Accelerators
		for acc in self.accs:

			name = None
			pioMasters = []
			busConnections = []
			localConnections = []
			variables = []
			streamVariables = []
			pioAddress = None
			IrPath = None
			configPath = None

			for i in acc['Accelerator']:
				if 'PIO' in i:
					pioAddress = topAddress
					topAddress = topAddress + i['PIO']
				if 'IrPath' in i:
					IrPath = i['IrPath']
				if 'ConfigPath' in i:
					configPath = i['ConfigPath']
				if 'Name' in i:
					name = i['Name']
				if 'PIOMaster' in i:
					pioMasters.extend((i['PIOMaster'].split(',')))
				if 'Bus' in i:
					busConnections.extend((i['Bus'].split(',')))
				if 'Local' in i:
					localConnections.extend((i['Local'].split(',')))
				if 'Var' in i:
					for j in i['Var']:
						if "SPM" in j['Type']:
							variables.append(Variable(j['Name'], int(j['Size']),
								j['Type'], j['Ports'], topAddress))
							topAddress = topAddress + int(j['Size'])
						if "Stream" in j['Type']:
							streamVariables.append(StreamVariable(j['Name'], j['InCon'], j['OutCon'],
								int(j['StreamSize']), j['BufferSize'],  topAddress))
							topAddress = topAddress + int(j['StreamSize'])
			accClass.append(Accelerator(name, pioMasters, busConnections, localConnections,
				pioAddress, configPath , IrPath, variables, streamVariables))

		self.accs = accClass
		self.dmas = dmaClass
		self.clusterTopAddress = topAddress

	def genConfig(self):
		lines = []
		# Need to add some customization here. Consider this a placeholder
		# Also need to edit AccCluster.py's addresses to match the gem5 supported ones
		lines.append("def build" + self.name + "(options, system, clstr):" + "\n")
		lines.append("	local_low = " + hex(self.clusterBaseAddress))
		lines.append("	local_high = " + hex(self.clusterTopAddress))
		lines.append("	local_range = AddrRange(local_low, local_high)")
		lines.append("	external_range = [AddrRange(0x00000000, local_low-1), AddrRange(local_high+1, 0xFFFFFFFF)]")
		lines.append("	system.iobus.master = clstr.local_bus.slave")
		# Need to define l2coherency in the YAML file?
		lines.append("	clstr._connect_caches(system, options, l2coherent=False)")
		lines.append("	gic = system.realview.gic")
		lines.append("")

		return lines

class Accelerator:

	def __init__(self, name, pioMasters, busConnections, localConnections, address, configPath, irPath, variables = None, streamVariables = None):
		self.name = name.lower()
		self.pioMasters = pioMasters
		self.busConnections = busConnections
		self.localConnections = localConnections
		self.address = address
		self.variables = variables
		self.streamVariables = streamVariables
		self.configPath = configPath
		self.irPath = irPath

	def genConfig(self):
		lines = []
		lines.append("# Accelerator")
		lines.append("acc = " + "\"" + self.name + "\"")
		# Need to add a user defined path & user defined interrupts here
		lines.append("config = " + "\"" + self.configPath + "\"")
		lines.append("ir = "  + "\"" + self.irPath + "\"")
		lines.append("clstr." + self.name +" = CommInterface(devicename=acc, gic=gic)")
		lines.append("AccConfig(clstr." + self.name + ", config, ir)")

		# Add connections to memory buses
		for i in self.busConnections:
			# Might need to add more options here... only option now is connecting to local membus
			if "Local" in i:
				lines.append("clstr._connect_hwacc(clstr." + self.name + ")")
		for i in self.localConnections:
				lines.append("clstr." + self.name + ".local = clstr." + i.lower() + ".pio")
		# Add connections from pio to local
		for i in self.pioMasters:
			lines.append("clstr." + self.name + ".pio " +
				"=" " clstr." + i + ".local")

		lines.append("")

		# Add scratchpad variables
		for i in self.variables:
			lines = i.genConfig(lines)
			lines.append("	clstr." + self.name + ".spm = " + "clstr." + i.name + ".spm_ports")
			lines.append("")

		# Add stream variables
		for i in self.streamVariables:
			lines = i.genConfig(lines)

		return lines

# Need to add a Stream DMA Class

class StreamDma:
	def __init__(self, name, pio, address, dmaType, rd_int = None, wr_int = None, size = 64):
		self.name = name.lower()
		self.pio = pio
		self.size = size
		self.address = address
		self.dmaType = dmaType
		self.rd_int = rd_int
		self.wr_int = wr_int
	# Probably could apply the style used here in other genConfigs
	def genConfig(self):
		lines = []
		dmaPath = "clstr." + self.name + "."
		systemPath = "clstr."
		# Need to fix max_pending?
		lines.append("# Stream DMA")
		lines.append(dmaPath + "StreamDma(pio_addr=" + hex(self.address) + ", pio_size = " + str(self.pio) + ", gic=gic, max_pending = " + str(self.pio) + ")")
		# Math is right here?
		lines.append(dmaPath + "stream_addr = " + hex(self.address) + " + " + str(self.pio))
		lines.append(dmaPath + "stream_size = " + str(self.size))
		lines.append(dmaPath + "pio_delay = '1ns'")
		lines.append(dmaPath + "rd_int = " + str(self.rd_int))
		lines.append(dmaPath + "wr_int = " + str(self.wr_int))
		# Probably need to fix this up
		lines.append("clstr." + self.name + ".dma = clstr.coherency_bus.slave")
		lines.append("")

		return lines


class Dma:
	def __init__(self, name, address, dmaType, int_num = None, size = 64, MaxReq = 4):
		self.name = name.lower()
		self.size = size
		self.address = address
		self.dmaType = dmaType
		self.int_num = int_num
		self.MaxReq = MaxReq
	# Probably could apply the style used here in other genConfigs
	def genConfig(self):
		lines = []
		dmaPath = "clstr." + self.name + "."
		systemPath = "clstr."
		# Is pio size always 21
		lines.append("# Noncoherent DMA")
		lines.append("clstr." + self.name + " = NoncoherentDma(pio_addr="
			+ hex(self.address) + ", pio_size = " + "21" + ", gic=gic, int_num=" + str(self.int_num) +")")
		lines.append(dmaPath + "cluster_dma = " + systemPath + "local_bus.slave")
		lines.append(dmaPath + "max_req_size = " + str(self.MaxReq))
		lines.append(dmaPath + "buffer_size = " + str(self.size))
		lines.append("clstr." + self.name + ".dma = clstr.coherency_bus.slave")
		lines.append("")

		return lines

class StreamVariable:
	# Need to add read and write interrupts
	def __init__ (self, name, inCon, outCon, streamSize,
		bufferSize, address):
		self.name = name.lower()
		self.inCon = inCon
		self.outCon = outCon
		self.streamSize = streamSize
		self.bufferSize = bufferSize
		self.address = address

	def genConfig(self, lines):
		lines.append("# Stream Variable")
		lines.append("addr = " + hex(self.address))
		lines.append("clstr." + self.name + " = StreamBuffer(stream_address = addr, stream_size = " + str(self.streamSize) + ", buffer_size = " + str(self.bufferSize) + ")")
		lines.append("clstr." + self.inCon + ".stream = " + "clstr." + self.name + ".stream_in")
		lines.append("clstr." + self.outCon + ".stream = " + "clstr." + self.name + ".stream_out")
		lines.append("")
		return lines

class Variable:
	def __init__ (self, name, size, type, ports, address = None):
		self.name = name.lower()
		self.size = size
		self.type = type
		self.ports = ports
		self.address = address


	def genConfig(self, lines):
		lines.append("# Variable")
		lines.append("addr = " + hex(self.address))
		lines.append("spmRange = AddrRange(addr, addr + " + hex(self.size) + ")")
		# Choose a style with the "."s and pick it
		lines.append("clstr." + self.name + " = ScratchpadMemory(range = spmRange)")
		# Probably need to add table and read mode to the YAML File
		lines.append("clstr." + self.name + "." + "conf_table_reported = False")
		lines.append("clstr." + self.name + "." + "ready_mode = False")
		lines.append("clstr." + self.name + "." + "port" + " = " + "clstr.local_bus.master")
		lines.append("for i in range(" + str(self.ports) + "):")

		return lines