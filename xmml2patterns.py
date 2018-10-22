#!/usr/bin/python
################################################################################
## This script is part of the ComPat Pattern Services                         ##
## It translates an XMML description of a multiscale model into a set of      ##
## skeleton input files for the Pattern Performance Service                   ##
## @author: olivier.hoenen@ipp.mpg.de                                         ##
################################################################################
from lxml import etree
import argparse
import copy
import numpy as np

'''
argp = argparse.ArgumentParser(prog="xmml2patterns.py",
                               description="This program generates inputs skeleton for the Pattern Service of ComPat, given XMML description of the targeted multiscale model.")
argp.add_argument('xmmlfile',type=argparse.FileType('r'),
                  help='XMML file')
argp.add_argument('-b','--benchmark',action='store_true',
                  help="Add placeholder for benchmark section")
argp.add_argument('-u','--usecase',action='store_true',
                  help="Add placeholder for use-case specific section")
argp.add_argument('-m','--muscle',action='store_true',
                  help="Add placeholder for a MUSCLE2 use-case section")
argp.add_argument('-matrix',default='matrix-skeleton.xml',metavar=('FILE'),
                  help="Specifies output file for describing single scale submodels (default: %(default)s)")
argp.add_argument('-multiscale',default='multiscale-skeleton.xml',metavar=('FILE'),
                  help="Specifies output file for describing multiscale application (default: %(default)s)")
args = argp.parse_args()
'''

def getModel(couplings, submodels, subm2inst, mappers):

    kn = []

    # 1) get kernel names and start kernel
    start = ''
    for s in submodels:
	kn.append(subm2inst[s.attrib['id']])
	keys= s.keys()
	if 'start' in keys:
		start = subm2inst[s.attrib['id']]
    ms = []
    for m in mappers:
	ms.append(subm2inst[m.attrib['id']])

	if start is '':
		raise Exception("You have to specify ONE start kernel")

    start_id = kn.index(start)

    # prepare coupling
    for c in couplings:
    	c.attrib['to'] = c.attrib['to'].split('.')[0]
    	c.attrib['from'] = c.attrib['from'].split('.')[0]


    #print "The submodels are ", kn
    #print "And it should start ", start," with id ", start_id 
 

    active = [start]
    done = []
    connect = []
    while len(active) > 0:
	a = active[0]
	active.remove(a)
	done.append(a)

	next = nextSet(a,couplings)

	for n in next:
		if n in active or n in done:
			continue
		connect.append({a:n})
		active.append(n)

    
    D = 0
    kn_d = {start:D}
    knn = kn[:]
    knn.remove(start)
    for k in knn:
	p = getParent(k,connect)
	D = 1
	while p != start:
		#c = p
		p = getParent(p,connect)
		if p is None:
			break
		D = D + 1
	kn_d.update({k:D})

    S = calcModel(kn_d)
    return S

def nextSet(a,couplings):
    to_ = []
    for c in couplings:
	if c.attrib['from'] == a:
		to_.append(c.attrib['to'])

    to_ = list(set(to_))
    return to_

def getParent(k,connect):
    for c in connect:
        if c.values()[0] == k:
		return c.keys()[0]


def calcModel(kn_d):
    i = 0
    s =[]
    max_ = []

    kn_tmp = kn_d.keys()[:]
    while len(kn_tmp) > 0 and i < len(kn_d.items())+1:
	for k,v in kn_d.items():
		if  v == i:
			max_.append(k)
	if len(max_) < 1:
		i = i + 1
		continue
	elif len(max_) == 1:
		s.append(max_[0])
	else:
		string = 'max( '
		for m in max_:
			if max_.index(m) == 0:
				string = string + m
			else:
				string = string +' , ' + m
			kn_tmp.remove(m)

		string = string + ' )'
		s.append(string)
	
	i = i + 1
	
	max_ = []

    S =' + '.join(s)

    return S

def xmmlRead(file):
    xmmlns = file.read()
    xmml = xmmlns.replace('xmlns="http://www.mapper-project.eu/xmml"','')

    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.XML(xmml,parser)

    mappers = root.findall(".//mapper")
    submodels = root.findall(".//submodel")
    instances = root.findall("./topology/instance")
    couplings = root.findall("./topology/coupling")
    subm2inst = { i.values()[1]:i.values()[0] for i in instances}
    inst2subm = { i.values()[0]:i.values()[1] for i in instances}

    # matrix tree section ###########################################################
    mod = etree.Element("submodels", #"model",
                           attrib={'id':root.attrib['id'],
                                   'name':root.attrib['name'],
                                   'xmml_version':root.attrib['xmml_version']})

    # because of duplicates!
    submodels2 = copy.deepcopy(submodels)

    for s in submodels:
        [s.remove(c) for c in s.getchildren()]
        inst = etree.SubElement(s,"instance",attrib={'id':subm2inst[s.attrib['id']],'class':'','type':''})
        restr = etree.SubElement(inst,"restrictions")
        etree.SubElement(restr,"cpu",attrib={'number':'','min':'','max':''})
        avrsrc = etree.SubElement(inst,"available_resources")
        etree.SubElement(avrsrc,"resource",attrib={'name':'','nodeType':''})
        mod.append(s)
    
    for m in mappers:
        [m.remove(c) for c in m.getchildren()]
        mod.append(m)
    
    matrix = etree.ElementTree(mod)
    matrix.write("single_scale.xml",pretty_print=True,xml_declaration=True)
        
    for c in couplings:
        c.attrib['to'] = c.attrib['to'].split('.')[0]
        c.attrib['from'] = c.attrib['from'].split('.')[0]
    
    S = getModel(couplings, submodels, subm2inst, mappers)
        
    # multiscale tree section #######################################################
    mult = etree.Element("multiscale")
    
    info = etree.SubElement(mult,"info")
    job = etree.SubElement(info,"job",attrib={'appID':root.attrib['id'],
                                              'project':'compatpsnc2'})
    job.append(etree.Comment(text='Values for "computing" tag is either: ES, HMC or RC'))
    etree.SubElement(job,"computing").text='ES' #should be named pattern?
    etree.SubElement(job,"modeltime").text=S 
    
    task = etree.SubElement(job,"task",attrib={'persistent':'true','taskId':'task'})
    cores = etree.SubElement(task,"numberofcores")
    etree.SubElement(cores,"max").text=''
    etree.SubElement(cores,"min").text=''
    etree.SubElement(job,"totaliterations").text='0'

    topo = etree.SubElement(mult,"topology")

    topo.append(etree.Comment(text='instances for each submodel'))
    for i in instances:
        topo.append(i)

    topo.append(etree.Comment(text='coupling of instances'))
    for c in couplings:
        c.attrib['to'] = c.attrib['to'].split('.')[0]
        c.attrib['from'] = c.attrib['from'].split('.')[0]
        topo.append(c)

    multiscale = etree.ElementTree(mult)
    multiscale.write("multi_scale.xml",pretty_print=True,xml_declaration=True,
                     with_comments=True)
    return

