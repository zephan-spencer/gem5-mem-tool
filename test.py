import m5
from m5.objects import *
from m5.util import *
import ConfigParser
from HWAccConfig import *

def buildSysVal(options, system, clstr):

	hw_path = options.accpath + "/" + options.accbench + "/hw/"
	local_low = 0x10020000
	local_high = 0x100208c9
	external_range = [AddrRange(0x00000000, local_low-1), AddrRange(local_high+1, 0xFFFFFFFF)]
	clstr._attach_bridges(system, local_range, external_range)
	clstr._connect_caches(system, options, l2coherent=False)
	gic = system.realview.gic

	# Noncoherent DMA
	clstr.dma.NoncoherentDma(pio_addr=0x10020000, pio_size = 21, gic=gic, int_num=123)
	clstr.dma.cluster_dma = clstr.local_bus.slave
	clstr.dma.max_req_size = 4
	clstr.dma.buffer_size = 128
	clstr._connect_dma(system, clstr.dma)
	
	# Stream DMA
	clstr.streamdma0.StreamDma(pio_addr=0x10020080, pio_size = 32, gic=gic, max_pending = 32)
	clstr.streamdma0.stream_addr = 0x10020080 + 32
	clstr.streamdma0.stream_size = 8
	clstr.streamdma0.pio_delay = '1ns'
	clstr.streamdma0.rd_int = 124
	clstr.streamdma0.wr_int = 125
	clstr._connect_dma(system, clstr.streamdma0)
	
	# Accelerator
	acc = top
	config = hw_path + acc + ".ini"
	ir = hw_path + acc + ".ll"
	clstr.top = CommInterface(devicename=acc, gic=gic)
	AccConfig(clstr.top, config, ir)
	clstr._connect_hwacc(clstr.top)
	
	# Accelerator
	acc = bench
	config = hw_path + acc + ".ini"
	ir = hw_path + acc + ".ll"
	clstr.bench = CommInterface(devicename=acc, gic=gic)
	AccConfig(clstr.bench, config, ir)
	clstr.bench.pio = clstr.top.local
	
	# Variable
	addr = 0x100200c8
	spmRange = AddrRange(addr, addr + 0x800)
	clstr.matrix0 = ScratchpadMemory(range = spmRange)
	clstr.matrix0.conf_table_reported = False
	clstr.matrix0.ready_mode = True
	clstr.matrix0.port = clstr.local_bus.master
	
	# Stream Variable
	addr = 0x100208c8
	clstr.matrix3 = StreamBuffer(stream_address = addr, stream_size = 1, buffer_size = 8)
	clstr.top.stream = clstr.matrix3.stream_in
	clstr.bench.stream = clstr.matrix3.stream_out
	
def makeHWAcc(options, system):

	system.sysval = AccCluster()
	buildSysVal(options, system, system.sysval)

