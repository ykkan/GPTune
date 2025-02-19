#! /usr/bin/env python3
# GPTune Copyright (c) 2019, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory (subject to receipt of any
# required approvals from the U.S.Dept. of Energy) and the University of
# California, Berkeley.  All rights reserved.
#
# If you have questions about your rights to use or distribute this software,
# please contact Berkeley Lab's Intellectual Property Office at IPO@lbl.gov.
#
# NOTICE. This Software was developed under funding from the U.S. Department
# of Energy and the U.S. Government consequently retains certain rights.
# As such, the U.S. Government has been granted for itself and others acting
# on its behalf a paid-up, nonexclusive, irrevocable, worldwide license in
# the Software to reproduce, distribute copies to the public, prepare
# derivative works, and perform publicly and display publicly, and to permit
# other to do so.
#
################################################################################
"""
Example of invocation of this script:
python superlu_MLA_RCI.py -nprocmin_pernode 1 -nrun 800 -obj time

where:
	-nprocmin_pernode is the minimum number of MPIs per node for launching the application code
    -nrun is the number of calls per task 
	-obj is the tuning objective: "time" or "memory"
"""
 
################################################################################

import sys
import os
import numpy as np
import argparse
import pickle

# import mpi4py
from array import array
import math

sys.path.insert(0, os.path.abspath(__file__ + "/../../../GPTune/"))

from gptune import * # import all


from autotune.problem import *
from autotune.space import *
from autotune.search import *

# from callopentuner import OpenTuner
# from callhpbandster import HpBandSter
import math

################################################################################
def objectives(point):                          
	print('objective is not needed when options["RCI_mode"]=True')
	
def cst1(NSUP,NREL):
	return NSUP >= NREL
def cst2(lg2npernode,nprows,nodes):
	return nodes * 2**lg2npernode >= nprows

def main():

	# Parse command line arguments
	args   = parse_args()

	# Extract arguments

	nprocmin_pernode = args.nprocmin_pernode
	optimization = args.optimization
	nrun = args.nrun
	obj = args.obj
	target=obj
	(machine, processor, nodes, cores) = GetMachineConfiguration()
	print ("machine: " + machine + " processor: " + processor + " num_nodes: " + str(nodes) + " num_cores: " + str(cores))


	TUNER_NAME = 'GPTune'
	os.environ['MACHINE_NAME'] = machine

	
	nprocmax = nodes*cores


	# matrices = ["big.rua", "g4.rua", "g20.rua"]
	# matrices = ["Si2.bin", "SiH4.bin", "SiNa.bin", "Na5.bin", "benzene.bin", "Si10H16.bin", "Si5H12.bin", "SiO.bin", "Ga3As3H12.bin","H2O.bin"]
	matrices = ["big.rua","g20.rua","Si2.bin", "SiH4.bin", "SiNa.bin", "Na5.bin", "benzene.bin", "Si10H16.bin", "Si5H12.bin", "SiO.bin", "Ga3As3H12.bin", "GaAsH6.bin", "H2O.bin", "matrix-A-kei-1178508.bin"]

	# Task parameters
	matrix    = Categoricalnorm (matrices, transform="onehot", name="matrix")

	# Input parameters
	COLPERM   = Categoricalnorm (['2', '4'], transform="onehot", name="COLPERM")
	LOOKAHEAD = Integer     (5, 20, transform="normalize", name="LOOKAHEAD")
	nprows    = Integer     (1, nprocmax, transform="normalize", name="nprows")
	lg2npernode     = Integer     (int(math.log2(nprocmin_pernode)), int(math.log2(cores)), transform="normalize", name="lg2npernode")
	NSUP      = Integer     (30, 300, transform="normalize", name="NSUP")
	NREL      = Integer     (10, 40, transform="normalize", name="NREL")

	if(target=='time'):			
		result   = Real        (float("-Inf") , float("Inf"),name="time")
	if(target=='memory'):	
		result   = Real        (float("-Inf") , float("Inf"),name="memory")

	IS = Space([matrix])
	PS = Space([COLPERM, LOOKAHEAD, lg2npernode, nprows, NSUP, NREL])
	OS = Space([result])

	constraints = {"cst1" : cst1, "cst2" : cst2}
	models = {}
	constants={"nodes":nodes,"cores":cores}

	# """ Print all input and parameter samples """	
	# print(IS, PS, OS, constraints, models)




	problem = TuningProblem(IS, PS, OS, objectives, constraints, None, constants=constants)
	computer = Computer(nodes = nodes, cores = cores, hosts = None)  

	""" Set and validate options """	
	options = Options()
	options['RCI_mode'] = True
	options['model_processes'] = 1
	# options['model_threads'] = 1
	options['model_restarts'] = 1
	# options['search_multitask_processes'] = 1
	# options['model_restart_processes'] = 1
	options['distributed_memory_parallelism'] = False
	options['shared_memory_parallelism'] = False
	options['model_class'] = 'Model_LCM' # 'Model_LCM'
	options['verbose'] = False

	options.validate(computer = computer)
	
	# """ Building MLA with the given list of tasks """
	# giventask = [[np.random.choice(matrices,size=1)[0]] for i in range(ntask)]
	giventask = [["big.rua"],["g20.rua"]]		
	# giventask = [["matrix-A-kei-1178508.bin"]]		
	# giventask = [["Si2.bin"]]	
	# giventask = [["Si2.bin"],["SiH4.bin"], ["SiNa.bin"], ["Na5.bin"], ["benzene.bin"], ["Si10H16.bin"], ["Si5H12.bin"]]	
	data = Data(problem)



	if(TUNER_NAME=='GPTune'):
		gt = GPTune(problem, computer=computer, data=data, options=options, driverabspath=os.path.abspath(__file__))        
		
		NI = len(giventask)
		NS = nrun
		(data, model, stats) = gt.MLA(NS=NS, NI=NI, Tgiven=giventask, NS1=max(NS//2, 1))
		# print("stats: ", stats)

		""" Print all input and parameter samples """	
		for tid in range(NI):
			print("tid: %d"%(tid))
			print("    matrix:%s"%(data.I[tid][0]))
			print("    Ps ", data.P[tid])
			print("    Os ", data.O[tid].tolist())
			print('    Popt ', data.P[tid][np.argmin(data.O[tid])], 'Oopt ', min(data.O[tid])[0], 'nth ', np.argmin(data.O[tid]))


def parse_args():

	parser = argparse.ArgumentParser()

	# Problem related arguments
	parser.add_argument('-obj', type=str, default='time', help='Tuning objective (time or memory)')	
	# Machine related arguments
	parser.add_argument('-nodes', type=int, default=1, help='Number of machine nodes')
	parser.add_argument('-cores', type=int, default=1, help='Number of cores per machine node')
	parser.add_argument('-nprocmin_pernode', type=int, default=1,help='Minimum number of MPIs per machine node for the application code')
	parser.add_argument('-machine', type=str, help='Name of the computer (not hostname)')
	# Algorithm related arguments
	parser.add_argument('-optimization', type=str,default='GPTune',help='Optimization algorithm (opentuner, hpbandster, GPTune)')
	parser.add_argument('-nrun', type=int, help='Number of runs per task')


	args   = parser.parse_args()
	return args


if __name__ == "__main__":
 
	main()
