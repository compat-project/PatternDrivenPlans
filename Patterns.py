from costFunctions import *
import random, sys, getopt, heapq, os.path
#import matplotlib
import numpy as np
from scenarios import *
from models import *
from plans import *
from QCG_ScriptGen import QCG_script_ptrn
from muscleCxaGen import generateCxaTemplate
#from plotter import plot_SB, plotScenarios
import subprocess
import os
import sys
from query import performanceEstimator
#sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + 'PerformanceEstimation'))
#from performanceEstimator_min import PE


def pattern(output_filename, multiscaleDoc, matrixDoc, args, nodeDescription, ptrn):
	if not args.quiet:
		print "** This application is ", ptrn, " **"

	dir_name = os.path.dirname(os.path.abspath(output_filename))
	multiscale_topology, submodels_all = getElements(matrixDoc,multiscaleDoc)
	kernelNames, helpers, kernel_helpers = getInstances(multiscale_topology,submodels_all)
	nodeTypesPerSubmodel = getNodeTypesPerSubmodel(submodels_all, kernelNames)
	hostNamesPerSubmodel = getHostNamesPerSubmodel(submodels_all, kernelNames)
	restrictionPerSubmodel = getRestrictionPerSubmodel(submodels_all, kernelNames)

	if(ptrn == "ES"):
		kernel_minCoresX, kernel_maxCoresX, overall_min, overall_max = getCoresES(multiscaleDoc,submodels_all,kernelNames)
		args.Local = True
	elif(ptrn == "RC" or ptrn == "HMC"):
		kernel_minCoresX, kernel_maxCoresX, overall_min, overall_max = getCoresRC(multiscaleDoc,submodels_all,kernelNames)

	formula = getModelFormula(multiscaleDoc)

 

	kernel_minCores = []
	kernel_maxCores = []
	for i in xrange(0,len(restrictionPerSubmodel)):
		mini, maxi = convertMinMax(kernel_minCoresX[i], kernel_maxCoresX[i], restrictionPerSubmodel[i])
		kernel_minCores.append(mini)
		kernel_maxCores.append(maxi)

	if not args.quiet:	
		print "** In this submodel the kernels are", kernelNames, "**"
		if(len(helpers)!=0):
			print "** In this submodel the helpers are", helpers, "**"
		print "** In this multiscle run min number of cores per submodel is", kernel_minCores, "**"
		print "** In this multiscle run max number of cores per submodel is", kernel_maxCores, "**"
		print "** In this multiscle run the overall number of cores is between [",overall_min," , ", overall_max,"] **"

		if (args.reservation):
                	print "** In this run you requested the following reservation(s)",args.reservation," **"

		print "** Generating plans ..." 



	if args.benchmark:
		benchmark(ptrn, kernelNames, helpers, kernel_helpers, kernel_minCoresX, kernel_maxCoresX, nodeTypesPerSubmodel, hostNamesPerSubmodel, nodeDescription, restrictionPerSubmodel, args, output_filename, dir_name, multiscaleDoc)
		

	else:
		scenarios = []
		scenarios = initScenarios(kernelNames, kernel_minCoresX, kernel_maxCoresX, nodeTypesPerSubmodel, hostNamesPerSubmodel, nodeDescription, restrictionPerSubmodel)

		## remove all scienarios exceed the resource limit by the user
		scenarios = refineScenarios(scenarios, restrictionPerSubmodel, kernel_minCores, kernel_maxCores, overall_min, overall_max)

		## do some filteration #
		scenarios = filter(args, scenarios)

		print "** Number of generated scenarios (after refine): ", len(scenarios)

		scenarios = performanceEstimator(multiscaleDoc, scenarios, kernelNames, helpers, formula, dir_name, args.benchmark, args.multiscale)
		updateScenarios(scenarios, args.time)
		

		fastest_scenarios = shortestTime(scenarios, args.M)

	        if args.Efficiency:
			fastest_scenarios = shortestTime(scenarios, -1)
			fastest_scenarios = maximumEfficiency(fastest_scenarios, args.M)

		if args.energy:
        	        fastest_scenarios = shortestTime(scenarios, -1)
        	        fastest_scenarios = minimumEnergy(fastest_scenarios, args.M)

		if args.Resourceusage:
        	        fastest_scenarios = shortestTime(scenarios, -1)
        	        fastest_scenarios = minimumResourceUsage(fastest_scenarios, args.M)

		Plans = getBestPlans(fastest_scenarios, args.M)
                
		print
	        print " ****************** Plans ******************** "
		printPlans(Plans)
		print " ****************** Plans ******************** "
		print
        
		if not args.quiet:	
			print "** Generating QCG scipt ..." 
	
		QCG_script_ptrn(ptrn, output_filename, multiscaleDoc, args, kernelNames, helpers, kernel_helpers, Plans, args.mc)

		if not args.quiet:
			print "** done ..."

def benchmark(ptrn, kernelNames, helpers, kernel_helpers, kernel_minCoresX, kernel_maxCoresX, nodeTypesPerSubmodel, hostNamesPerSubmodel, nodeDescription, restrictionPerSubmodel, args, output_filename, dir_name, multiscaleDoc):
	#### generate for benchmark ####
	scenarios_B = []
	scenarios_B = initScenarios(kernelNames, kernel_minCoresX, kernel_maxCoresX, nodeTypesPerSubmodel, hostNamesPerSubmodel, nodeDescription, restrictionPerSubmodel)
	
	## do some filteration #        
        scenarios_B = filter(args, scenarios_B)

	if not args.quiet:
		print "** (Benchmark) Number of generated scenarios: ", len(scenarios_B)

	P = getBestPlansB(scenarios_B, -1, args.time)

	bcount=0
	for bplan in P:
		output_filename="benchmark_out"+str(bcount)+".xml"
		output_filepath=dir_name+"/"+output_filename

		QCG_script_ptrn(ptrn, output_filename, multiscaleDoc, args, kernelNames, helpers, kernel_helpers, [bplan], args.mc)

		bcount = bcount+1
		if args.Submit:
			print("Submitting "+output_filename+" through the middleware...")
			cmdline = ["qcg-sub","-Q","-X",output_filepath]
			try:
				proc = subprocess.check_output(cmdline, stderr=subprocess.STDOUT)
				print(proc+"\nDONE")
			except subprocess.CalledProcessError:
  				# Error: command exited with non-zero code
				print(proc+"\nFAILED")
	if not args.quiet and not args.Submit:
		print "** The benchmark output files (benchmark_out*.xml) are generated"

	sys.exit(0)

def filter(args, scenarios):	
	if args.host:
		if len(args.host) == 1:
			scenarios = sameHostScenarios(scenarios, args.host[0])
	if args.nodetype:
		if len(args.nodetype) == 1:
			scenarios = sameTypeScenarios(scenarios, args.nodetype[0])

	if args.Local:
		scenarios = localScenarios(scenarios)

	return scenarios

