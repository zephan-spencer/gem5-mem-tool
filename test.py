import m5
from m5.objects import *
from m5.util import *
import ConfigParser
from HWAccConfig import *

def buildSystemVal(options, system, clstr):

	hw_path = options.accpath + "/" + options.accbench + "/hw/"
	system.SystemVal.AccCluster()
	local_low = 0x10020000
	local_high = 0x100218c0
	external_range = [AddrRange(0x00000000, local_low-1), AddrRange(local_high+1, 0xFFFFFFFF)]
	system.SystemVal._attach_bridges(system, local_range, external_range)
	system.SystemVal._connect_caches(system, options, l2coherent=False)
	gic = system.realview.gic

	acc = top
	config = hw_path + acc + ".ini"
	ir = hw_path + acc + ".ll"
	system.systemval.top = CommInterface(devicename=acc, gic=gic)
	AccConfig(system.systemval.top, config, ir)
	system.systemval._connect_hwacc(system.systemval.top)
	
	acc = bench
	config = hw_path + acc + ".ini"
	ir = hw_path + acc + ".ll"
	system.systemval.top = CommInterface(devicename=acc, gic=gic)
	AccConfig(system.systemval.top, config, ir)
	system.systemval.bench.pio = system.systemval.top.local
	
	addr = 0x100200c0
	spmRange = AddrRange(addr, addr + 0x800)
	system.matrix0. = ScratchpadMemory(range = spmRange)
	system.matrix0.conf_table_reported = False
	system.matrix0.ready_mode = True
	system.matrix0.port.system.local_bus.master
	
	addr = 0x100208c0
	spmRange = AddrRange(addr, addr + 0x800)
	system.matrix1. = ScratchpadMemory(range = spmRange)
	system.matrix1.conf_table_reported = False
	system.matrix1.ready_mode = True
	system.matrix1.port.system.local_bus.master
	
	addr = 0x100210c0
	spmRange = AddrRange(addr, addr + 0x800)
	system.matrix2. = ScratchpadMemory(range = spmRange)
	system.matrix2.conf_table_reported = False
	system.matrix2.ready_mode = True
	system.matrix2.port.system.local_bus.master
	
	system.systemval.clusterdma.NoncoherentDma(pio_addr=0x10020000, pio_size = 21, gic=gic, int_num=123)
	system.systemval.clusterdma.cluster_dma = system.systemval.local_bus.slave
	system.systemval.clusterdma.dma = system.systemval.coherency_bus.slave
	system.systemval.clusterdma.pio = system.systemval.top.local
	system.systemval.clusterdma.max_req_size = 4
	system.systemval.clusterdma.buffer_size = 128
