import m5
from m5.objects import *
from m5.util import *
import ConfigParser
from HWAccConfig import *

def buildSysVal(options, system, clstr):

	local_low = 0x10020000
	local_high = 0x100218c0
	local_range = AddrRange(local_low, local_high)
	external_range = [AddrRange(0x00000000, local_low-1), AddrRange(local_high+1, 0xFFFFFFFF)]
	system.iobus.master = clstr.local_bus.slave
	clstr._connect_caches(system, options, l2coherent=False)
	gic = system.realview.gic

	# Noncoherent DMA
	clstr.clusterdma = NoncoherentDma(pio_addr=0x10020000, pio_size = 21, gic=gic, int_num=123)
	clstr.clusterdma.cluster_dma = clstr.local_bus.slave
	clstr.clusterdma.max_req_size = 4
	clstr.clusterdma.buffer_size = 128
	clstr._connect_dma(system, clstr.clusterdma)
	
	# Accelerator
	acc = "top"
	config = "/home/he-man/gem5-SALAM/benchmarks/sys_validation/gemm/hw/top.ini"
	ir = "/home/he-man/gem5-SALAM/benchmarks/sys_validation/gemm/hw/top.ll"
	clstr.top = CommInterface(devicename=acc, gic=gic)
	AccConfig(clstr.top, config, ir)
	clstr._connect_hwacc(clstr.top)
	
	# Accelerator
	acc = "gemm"
	config = "/home/he-man/gem5-SALAM/benchmarks/sys_validation/gemm/hw/gemm.ini"
	ir = "/home/he-man/gem5-SALAM/benchmarks/sys_validation/gemm/hw/gemm.ll"
	clstr.gemm = CommInterface(devicename=acc, gic=gic)
	AccConfig(clstr.gemm, config, ir)
	clstr.gemm.pio = clstr.top.local
	
	# Variable
	addr = 0x100200c0
	spmRange = AddrRange(addr, addr + 0x800)
	clstr.matrix0 = ScratchpadMemory(range = spmRange)
	clstr.matrix0.conf_table_reported = False
	clstr.matrix0.ready_mode = True
	clstr.matrix0.port = clstr.local_bus.master
	for i in range(2):
		clstr.gemm.spm = clstr.matrix0.spm_ports
	
	# Variable
	addr = 0x100208c0
	spmRange = AddrRange(addr, addr + 0x800)
	clstr.matrix1 = ScratchpadMemory(range = spmRange)
	clstr.matrix1.conf_table_reported = False
	clstr.matrix1.ready_mode = True
	clstr.matrix1.port = clstr.local_bus.master
	for i in range(2):
		clstr.gemm.spm = clstr.matrix1.spm_ports
	
	# Variable
	addr = 0x100210c0
	spmRange = AddrRange(addr, addr + 0x800)
	clstr.matrix2 = ScratchpadMemory(range = spmRange)
	clstr.matrix2.conf_table_reported = False
	clstr.matrix2.ready_mode = True
	clstr.matrix2.port = clstr.local_bus.master
	for i in range(2):
		clstr.gemm.spm = clstr.matrix2.spm_ports
	
def makeHWAcc(options, system):

	system.sysval = AccCluster()
	buildSysVal(options, system, system.sysval)

