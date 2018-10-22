from xml.dom import minidom
import numpy as np
import itertools
from itertools import repeat
from plans import *
import parser
import math
from costFunctions import *
from models import *

class scenario:

    def __init__(self, cores, hostName, nodeType, time ,TotalTime, energy, totalEnergy, numberOfNodes, Efficiency):
        self.cores = cores
        self.hostName = hostName
        self.nodeType = nodeType
        self.time = time
        self.TotalTime = TotalTime
        self.energy = energy
        self.totalEnergy = totalEnergy
        self.numberOfNodes = numberOfNodes 
        self.Efficiency = Efficiency

    def getCores(self):
        return self.cores
        
    def getNumberOfCores(self):
        return sum(self.cores)
    
    def getTotalTime(self):
        return self.TotalTime

    def setTotalTime(self, time):
        self.TotalTime = time
    
    def getSubmodelsTimes(self):
        return self.time

    def setSubmodelsTimes(self, times):
        self.time = times

    ###############################################################################
    def getTotalEnergy(self):
        return self.totalEnergy

    def setTotalEnergy(self, energy):
        self.totalEnergy = energy
    
    def getSubmodelsEnergy(self):
        return self.energy

    def setSubmodelsEnergy(self, energy):
        self.energy = energy
    ###############################################################################
    
    def getEfficiency(self):
        return self.Efficiency

    def setEfficiency(self, eff):
        self.Efficiency = eff
    
    def getTotalNumberOfNodes(self):
        return sum(self.numberOfNodes)
    
    def getNumberOfNodes(self):
        return self.numberOfNodes
    
    def getHostName(self):
        return self.hostName
    
    def getNodeType(self):
        return self.nodeType
    
    def hasSameHost(self):
        if( len(set(self.hostName)) == 1 ):
            return 1
        return 0
    
    def hasSameType(self):
        if( len(set(self.nodeType)) == 1 ):
            return 1
        return 0
    
    def setResourceUsage(self, numberOfNodes, totalTime):
	self.Ru = numberOfNodes * totalTime

    def getResourceUsage(self):
        return self.Ru

    '''    
    def getRealResourceUsage(self):
        return sum(self.Ru)
    
    def getTheoreticalResourceUsagePerSubmodel(self):
        return [self.TotalTime * b for b in self.numberOfNodes]
    
    def getTheoreticalResourceUsage(self):
        return sum([self.TotalTime * b for b in self.numberOfNodes])
    '''



def initScenarios(kernelNames, kernel_minCoresX, kernel_maxCoresX, nodeTypesPerSubmodel, hostNamesPerSubmodel, nodeDescription, restrictionPerSubmodel):

	kernel_minCores = []
	kernel_maxCores = []
	for i in xrange(0,len(restrictionPerSubmodel)):
		mini, maxi = convertMinMax(kernel_minCoresX[i], kernel_maxCoresX[i], restrictionPerSubmodel[i])
		kernel_minCores.append(mini)
		kernel_maxCores.append(maxi)

	scenarios = []

	cores_all = []
	names_all = []	
	types_all = []

	nodes = []
	number= [] #restriction per kernel N/A, x^2, ...

	for i in range(0,len(nodeDescription)):
		nodes.append(nodeDescription[i][0])

	temp_zeros = [0] * len(kernelNames)

	for n in range(0,len(kernelNames)):

		coresPerType = []
		types = []
		names = []
		
		number = restrictionPerSubmodel[n] # restriction of this submodel

		minimum = 0 
		maximum = 0
		
		types = nodeTypesPerSubmodel[n]
		names = hostNamesPerSubmodel[n]

		for j in range( 0,len(nodeTypesPerSubmodel[n]) ):

			cores = []
			idx = nodes.index(nodeTypesPerSubmodel[n][j])

			minimum = max(kernel_minCoresX[n],1)# 1 is the least value
			maximum = min(kernel_maxCoresX[n],nodeDescription[idx][2])
			if (number == "1"):
				cores = [1]

			elif (number == "N/A" or number == "x"):
				if ( nodeDescription[idx][1] < kernel_maxCoresX[n]):
					cores1 = range(minimum, nodeDescription[idx][1]+1, 1)
					cores2 = range(2*nodeDescription[idx][1], maximum+1, nodeDescription[idx][1])
					cores = cores1 + cores2
				else:
					cores = range(minimum, maximum+1, 1)

			else:
				formula = parser.expr(number).compile()
				if minimum == 1:
					minimum = 0
				cores = [eval(formula) for x in range( minimum , maximum +1 ) ] 

		
			coresPerType.append(cores)

		cores_all.append(coresPerType)
		types_all.append(types)
		names_all.append(names)
	
	temp_cores  = list(itertools.product(*cores_all))
	temp_names  = list(itertools.product(*names_all))
	temp_types  = list(itertools.product(*types_all))

	
	for i in range(0,len(temp_cores)):
		temp2_cores = list(itertools.product(*temp_cores[i]))
		for j in range(0,len(temp2_cores)):

			temp2_nodes = [None] * len(temp_types[i])

			for n in range(0,len(temp_types[i])):			
				idx = nodes.index(temp_types[i][n])
				temp2_nodes[n] =  math.ceil( float(temp2_cores[j][n]) / float(nodeDescription[idx][1]) )
			s = scenario(temp2_cores[j],temp_names[i],temp_types[i],temp_zeros,0,temp_zeros,0,temp2_nodes,0)
                        
			scenarios.append(s)

			
	return scenarios

def sortScenarios(ss,i):
    '''
    i; 0 -> Time; 1 -> Efficiency
    2 -> number of nodes; 3 -> Energy 4 -> resource usage
    '''

    if (i == 0):
	ss2 = sorted(ss, key=lambda x: x.TotalTime, reverse=False)
    elif (i == 1):
	ss2 = sorted(ss, key=lambda x: x.Efficiency, reverse=True)
    elif (i == 2):
	ss2 = sorted(ss, key=lambda x: x.numberOfNodes, reverse=False)
    elif (i == 3):
        ss2 = sorted(ss, key=lambda x: x.totalEnergy, reverse=False)
    elif (i == 4):
        ss2 = sorted(ss, key=lambda x: x.Ru, reverse=False)

    return ss2

def refineScenarios(scenarios, restrictionPerSubmodel, kernel_minCores, kernel_maxCores, overall_min, overall_max):

	ss = []

	for s in scenarios:

		if(s.getNumberOfCores() <= overall_max and s.getNumberOfCores() >= overall_min):
			k = 0
			for i in range(0,len(s.getCores())): 
				if(s.getCores()[i] <= kernel_maxCores[i] and s.getCores()[i] >= kernel_minCores[i]):
					k=k+1
			if(k == len(s.getCores())):
				ss.append(s)

	return ss

def updateScenarios(scenarios, timeLimit):
	for s in scenarios:
		s.setTotalTime(s.getTotalTime() + timeLimit)
		s.setResourceUsage(s.getNumberOfCores(), s.getTotalTime())
	return scenarios
def sameHostScenarios(ss,host):
    ss2 = []

    for s in ss:
        if s.hasSameHost():
		s_tmp = set(s.getHostName())
		if (list(s_tmp)[0] == host):
            		ss2.append(s)
    return ss2

def sameTypeScenarios(ss,t):
    ss2 = []

    for s in ss:
	if s.hasSameType():
		t_tmp = t.split(':')[1]
		s_tmp = set(s.getNodeType())
		if (list(s_tmp)[0] == t_tmp):
			ss2.append(s)
    return ss2

def sameNodeTypeScenarios(ss,t):
    ss2 = []
    for s in ss:
	if s.hasSameType():
		s_tmp = set(s.getNodeType())
		if (list(s_tmp)[0] == t):
			ss2.append(s)
    return ss2

def filterScenariosByHostsPerSubmodel(ss,hosts):#hosts is per submodel
	ss2 = []
	for s in ss:
		n = 0 # if n == len(hosts), then take it, otherwise no
		for i in range(0,len(hosts)):
			if (s.getHostName()[i] in hosts[i]):
				n = n + 1
		if n == len(hosts):		
			ss2.append(s)
	return ss2

def filterScenariosByTypesPerSubmodel(ss,types):#types is per submodel
	ss2 = []
	for s in ss:
		n = 0 # if n == len(types), then take it, otherwise no
		for i in range(0,len(types)):
			if (s.getNodeType()[i] in types[i]):
				n = n + 1
		if n == len(types):		
			ss2.append(s)
	return ss2

def localScenarios(scenarios):
	ss = []

	for s in scenarios:
		if s.hasSameType():
			ss.append(s)
	
	return ss

def printScenarios(scenarios):
	print "cores \t node types \t total time \t submodels times \t number of nodes \t Resource usage"
	for i in range(0,len(scenarios)):
		print scenarios[i].getCores()," - ", scenarios[i].getNodeType()," - ", scenarios[i].getTotalTime()," - ", scenarios[i].getSubmodelsTimes()," - ", scenarios[i].getNumberOfNodes()," - ", round(float(scenarios[i].getResourceUsage())/3600.,2),"\n"
