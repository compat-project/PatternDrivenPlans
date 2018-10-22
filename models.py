from xml.dom import minidom
import random, sys, getopt, heapq, os.path
import numpy as np
import parser
from scenarios import *
import subprocess
import os
import re

def updateDescription(quiet,path):
    # READ FROM qcg-resources -N                                                                                                           
        cmdline = ["qcg-resources","-N"]                                                                                                      
        try:                                                                                                                                  
                outfile = open("./nt.txt", 'w+')                                                                                                 
                proc = subprocess.call(cmdline, stdout=outfile)                                                                               
                if (not quiet):            
			print("** reading NodeTypes from the middleware **")
                        nodeDescriptions = updatenodes(outfile)                                                                               

        except subprocess.CalledProcessError:                                                                                                 
                # Error: command exited with non-zero code                                                                   
		print("** can not read NodeTypes from the middleware, use the old node description file")                      
		raise error
	return nodeDescriptions

def updatenodes(outfile):

    outfile.seek(0)

    nodeDescriptions = []
    row = []
    for line in outfile:
        if re.match("---- CLUSTER: (.*)", line):
            row = []
            tmp = re.findall(r'\b\w+\b', line)
            hostName = tmp[1]
            row.append(hostName)
            
        elif re.match("Node Type: (.*)", line):
            tmp = re.findall(r'\b\w+\b', line)
            nodeType = tmp[2]
            row.append(nodeType)
                        
        elif re.match("               Nodes: (.*)", line):
            tmp = re.findall(r'\d+', line)
            numberOfNodes = tmp[0]
            row.append(numberOfNodes)
            
        elif re.match("      Cores per node: (.*)", line):
            tmp = re.findall(r'\d+', line)
            coresPerNode = -1
            
            if(len(tmp) > 0):
                coresPerNode = tmp[1]
            
            row.append(coresPerNode)
            
            if(len(row) < 4):
                row = []
                continue
                
            nodeDescription = [0,0,0]
            nodeDescription[0] = row[1]
            nodeDescription[1] = int(row[3])
            nodeDescription[2] = int(row[2]) * int(row[3])
            nodeDescriptions.append(nodeDescription)
            
            row.pop(); row.pop(); row.pop()
            
    return nodeDescriptions

def readDescription(u):
    
    descriptionFile = u
    decriptionDoc = minidom.parse(descriptionFile);
    # read from .xml file
    nodeDescriptions = []
    for i in decriptionDoc.getElementsByTagName("node"):
        nodeDescription = [0,0,0]
        nodeDescription[0] = i.attributes["type"].value
        nodeDescription[1] = int(i.attributes["coresInnode"].value)
        nodeDescription[2] = int(i.attributes["totalnodes"].value) * int(i.attributes["coresInnode"].value)
        nodeDescriptions.append(nodeDescription)
        
    return nodeDescriptions

def getElements(matrixDoc,multiscaleDoc):

	multiscale_topology = multiscaleDoc.getElementsByTagName("topology")[0]
	submodels_all = matrixDoc.getElementsByTagName('submodels')[0]

	return multiscale_topology, submodels_all


def getModelFormula(multiscaleDoc):
	formula = multiscaleDoc.getElementsByTagName('modeltime')[0].firstChild.nodeValue.strip()
	return formula

def getModelTime(formula,helpers):
	for i in range(0,len(helpers)):
		formula = formula.replace(helpers[i],'0')# replace helpers with 0
	model_time = parser.expr(formula).compile()
	return model_time

def getAuxModelTime(formula, kernelNames, primary_idx,helpers):
	for i in range(0,len(helpers)):
		formula = formula.replace(helpers[i],'0')# replace helpers with 0
	formula = formula.replace(kernelNames[primary_idx],'0')# replace the large with the primary detected -- max and +
	model_time = parser.expr(formula).compile()
	return model_time


def getInstances(multiscale_topology,submodels_all):
    
    k_instances = []
    h_instances = []
    
    kernel_helpers= []
    
    for i in multiscale_topology.getElementsByTagName("instance"):
        if (i.hasAttribute("submodel") ):
            k_instances.append(i.attributes["id"].value)
        elif(i.hasAttribute("mapper") ):
            h_instances.append(i.attributes["id"].value)
            
    for i in submodels_all.getElementsByTagName("instance"):
        if (i.attributes["type"].value == "helper" and i.attributes["id"].value in k_instances):
            k_instances.remove(i.attributes["id"].value)
            h_instances.append(i.attributes["id"].value)
    
    if(len(k_instances) == 1):
        kernel_helpers = k_instances[:]
        kernel_helpers.append(h_instances)

    else:
	    tmp_helpers = h_instances[:]

	    l1 = k_instances[:]
	    l2 = [[] for _ in xrange(len(l1))]
	    kernel_helpers = [None]*(len(l1)+len(l2))
	    kernel_helpers[::2] = l1
	    kernel_helpers[1::2] = l2

	    for i in multiscale_topology.getElementsByTagName("coupling"):
		f = i.attributes["from"].value
		t = i.attributes["to"].value

		if ( f in k_instances ):
			if ( t in tmp_helpers ):
				i = kernel_helpers.index(f)
				kernel_helpers[i+1].append(t)
				tmp_helpers.remove(t)

		elif ( t in k_instances ):
			if ( f in tmp_helpers ):
				i = kernel_helpers.index(t)
				kernel_helpers[i+1].append(f)
				tmp_helpers.remove(f)
		else:
			continue

	    while ( len(tmp_helpers) > 0 ):
		for i in multiscale_topology.getElementsByTagName("coupling"):
			f = i.attributes["from"].value
			t = i.attributes["to"].value
			if ( f in tmp_helpers ):
				n = 0
				for kh in kernel_helpers:
					if (t in kh):
						find = True
						break
					n = n + 1 
				if find:
					kernel_helpers[n].append(f)
					tmp_helpers.remove(f)
			elif ( t in tmp_helpers ):
				n = 0
				for kh in kernel_helpers:
					if (f in kh):
						find = True
						break
					n = n + 1 
				if find:
					kernel_helpers[n].append(t)
					tmp_helpers.remove(t)
			else:
				continue
	
    return  k_instances, h_instances, kernel_helpers

def getCoresES(multiscaleDoc,matrixDoc,kernelNames):

	multiscale_min_cores = int(multiscaleDoc.getElementsByTagName('min')[0].firstChild.nodeValue);
	multiscale_max_cores = int(multiscaleDoc.getElementsByTagName('max')[0].firstChild.nodeValue);
	kernel_minCoresX = []
	kernel_maxCoresX = []
	kernel_minCores = []
	kernel_maxCores = []
	kernel_number   = []
	for j in matrixDoc.getElementsByTagName('instance'):
		if (j.attributes["id"].value in kernelNames):
			n = j.getElementsByTagName('cpu')[0]
			kernel_minCoresX.append( int(n.attributes["min"].value) );
			kernel_maxCoresX.append( int(n.attributes["max"].value) );
			kernel_number.append( n.attributes["number"].value );


	for i in xrange(0,len(kernel_number)):
		mini, maxi = convertMinMax(kernel_minCoresX[i], kernel_maxCoresX[i], kernel_number[i])
		kernel_minCores.append(mini)
		kernel_maxCores.append(maxi)

	overall_min = max(multiscale_min_cores,sum(kernel_minCores))
	overall_max = min(multiscale_max_cores,sum(kernel_maxCores))

	return kernel_minCoresX, kernel_maxCoresX, overall_min, overall_max

def getCoresRC(multiscaleDoc,matrixDoc,kernelNames):

	multiscale_min_cores = 0
	multiscale_max_cores = 0
	for i in range(0,len(kernelNames) ):
		multiscale_min_cores = multiscale_min_cores + int(multiscaleDoc.getElementsByTagName('min')[i].firstChild.nodeValue);
		multiscale_max_cores = multiscale_max_cores + int(multiscaleDoc.getElementsByTagName('max')[i].firstChild.nodeValue);

	kernel_minCoresX = []
	kernel_maxCoresX = []
	kernel_number   = []
	kernel_minCores = []
	kernel_maxCores = []
	for j in matrixDoc.getElementsByTagName('instance'):
		if (j.attributes["id"].value in kernelNames):
			n = j.getElementsByTagName('cpu')[0]
			kernel_minCoresX.append( int(n.attributes["min"].value) );
			kernel_maxCoresX.append( int(n.attributes["max"].value) );
			kernel_number.append( n.attributes["number"].value );

	for i in xrange(0,len(kernel_number)):
		mini, maxi = convertMinMax(kernel_minCoresX[i], kernel_maxCoresX[i], kernel_number[i])
		kernel_minCores.append(mini)
		kernel_maxCores.append(maxi)

	kernel_minCores = [min(i,multiscale_min_cores) for i in kernel_minCores];
	kernel_maxCores = [max(i,multiscale_max_cores) for i in kernel_maxCores];

	overall_min = max(multiscale_min_cores,sum(kernel_minCores))
	overall_max = min(multiscale_max_cores,sum(kernel_maxCores))

	return kernel_minCoresX, kernel_maxCoresX, overall_min, overall_max

def getHostNamesPerSubmodel(submodels_all, kernelNames):
	submodels_nodes = []

	for i in submodels_all.getElementsByTagName('instance'):
		submodel_nodes = []
		if (i.attributes["id"].value in kernelNames):
			for j in i.getElementsByTagName('resource'):
				submodel_nodes.append(j.attributes["name"].value)
			submodels_nodes.append(submodel_nodes)
	return submodels_nodes

def getNodeTypesPerSubmodel(submodels_all, kernelNames):
	submodels_hosts = []

	for i in submodels_all.getElementsByTagName('instance'):
		submodel_hosts = []
		if (i.attributes["id"].value in kernelNames):
			for j in i.getElementsByTagName('resource'):
				submodel_hosts.append(j.attributes["nodeType"].value)
			submodels_hosts.append(submodel_hosts)
	return submodels_hosts

def getRestrictionPerSubmodel(submodels_all, kernelNames):
	submodels_rest = []

	for i in submodels_all.getElementsByTagName('instance'):
		if (i.attributes["id"].value in kernelNames):
			n = i.getElementsByTagName('cpu')[0]
			submodels_rest.append(n.attributes["number"].value)
	return submodels_rest

def convertMinMax(minimum, maximum, number):
	if (number == "1"):
		mini = 1
		maxi = 1
	elif (number == "N/A"):
		mini = minimum
		maxi = maximum
	else:
		x = minimum
		formula = parser.expr(number).compile()
		mini = eval(formula)	

		x = maximum
		formula = parser.expr(number).compile()
		maxi = eval(formula)
	
	return mini, maxi
