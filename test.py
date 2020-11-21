import m5
from m5.objects import *
from m5.util import *
import ConfigParser
from HWAccConfig import *
def buildSystemValCluster(options, system, clstr):
	acc = top
	config = hw_path + acc + ".ini"
	ir = hw_path + acc + ".ll"
	system.systemvalcluster.top = CommInterface(devicename=acc, gic=gic)
	AccConfig(system.systemvalcluster.top, config, ir)
	system.systemvalcluster._connect_hwacc(system.systemvalcluster.top)

	acc = bench
	config = hw_path + acc + ".ini"
	ir = hw_path + acc + ".ll"
	system.systemvalcluster.top = CommInterface(devicename=acc, gic=gic)
	AccConfig(system.systemvalcluster.top, config, ir)
	system.systemvalcluster.bench.pio = system.systemvalcluster.top.local

def buildSecondGEMM(options, system, clstr):
	acc = GEMM2
	config = hw_path + acc + ".ini"
	ir = hw_path + acc + ".ll"
	system.secondgemm.top = CommInterface(devicename=acc, gic=gic)
	AccConfig(system.secondgemm.top, config, ir)
	system.secondgemm._connect_hwacc(system.secondgemm.GEMM2)

