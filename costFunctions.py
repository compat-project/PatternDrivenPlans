from xml.dom import minidom
import random, sys, getopt, heapq, os.path
import numpy as np
import parser
from scenarios import sortScenarios, printScenarios

def shortestTime(scenarios,number): #number is how many plans to return
	'''
	Shortest time function returns the n plans, which has least time
	'''
	sorted_scenarios = sortScenarios(scenarios,0)
	fastest_scenarios = []
	#print number
	if (number == -1):
		number = len(sorted_scenarios)
	for i in range(0,min(number,len(sorted_scenarios))):
		fastest_scenarios.append(sorted_scenarios[i])


	return fastest_scenarios

def maximumEfficiency(scenarios,number): #number is how many plans to return
	sorted_scenarios = sortScenarios(scenarios,1)
	efficient_scenarios = []
	if (number == -1):
		number = len(sorted_scenarios)
	for i in range(0,min(number,len(sorted_scenarios))):
		efficient_scenarios.append(sorted_scenarios[i])
		#print sorted_scenarios[i].getEfficiency()

	return efficient_scenarios

def minimumResourceUsage(scenarios,number):
	sorted_scenarios = sortScenarios(scenarios,4)
	efficient_scenarios = []
	if (number == -1):
		number = len(sorted_scenarios)
	for i in range(0,min(number,len(sorted_scenarios))):
		efficient_scenarios.append(sorted_scenarios[i])

	return efficient_scenarios
	

def efficiencyBetween(scenarios,number_e1, number_e2,number): #number_e{1,2} are the effies, number is how many plans to return
	sorted_scenarios = sortScenarios(scenarios,1)	
	temp_scenarios = filter(lambda x: x.Efficiency >= number_e1 and x.Efficiency <= number_e2, sorted_scenarios)
	efficient_scenarios = []
	if (number == -1):
		number = len(temp_scenarios)
	for i in range(0,min(number,len(sorted_scenarios))):
		efficient_scenarios.append(temp_scenarios[i])

	return efficient_scenarios

def leastResourceUsage(scenarios,number): #number is how many plans to return
	sorted_scenarios = sortScenarios(scenarios,2)
	fastest_scenarios = []
	if (number == -1):
		number = len(sorted_scenarios)
	for i in range(0,min(number,len(sorted_scenarios))):
		fastest_scenarios.append(sorted_scenarios[i])


	return fastest_scenarios

def minimumEnergy(scenarios,number): #number is how many plans to return                                                                   
        sorted_scenarios = sortScenarios(scenarios,3)
        energatic_scenarios = []
        if (number == -1):
                number = len(sorted_scenarios)
        for i in range(0,min(number,len(sorted_scenarios))):
                energatic_scenarios.append(sorted_scenarios[i])

        return energatic_scenarios

def calculateEfficiency(s,idx_p):

        Npr = s.getCores()[idx_p]
	Tpr = s.getSubmodelsTimes()[idx_p] 

	idx_a = range(0,len(s.getSubmodelsTimes()))
        if (idx_p != -1):
            idx_a.remove(idx_p)

	Naux = 0
        Taux = 0
        for idx in idx_a:
                Naux   = Naux  + s.getCores()[idx]
		Taux   = Taux + s.getSubmodelsTimes()[idx]

        N  = Npr + Naux 
        T = s.getTotalTime()

        eff = ((Npr * Tpr) + (Naux * Taux)) / (N * T)

        return eff

def calculateEfficiency_HMC(s,rPc):
	eff = ( (s.getSubmodelsTimes()[0]/s.getNumberOfCores()) * rPc ) /1.0
	if eff > 1:
		eff = 1 * rPc
	return eff
	

