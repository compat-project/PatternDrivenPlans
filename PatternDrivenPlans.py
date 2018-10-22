###!/usr/bin/python
from xml.dom import minidom
import random, sys, getopt, heapq, os, inspect
import numpy as np
import argparse
from Patterns import pattern
from models import updateDescription, readDescription
import subprocess
from xmml2patterns import xmmlRead


argp = argparse.ArgumentParser(prog="patterns",
                               description="Pattern-Driven Planner maps submodels to the required architecture to abstract this complexity from user. It [benchmark|submit] multiscale applications to middleware")

argp.add_argument('singlescale',type=argparse.FileType('r'), default="matrix.xml",
                  help='singlescale description (xml file)')

argp.add_argument('multiscale',type=argparse.FileType('r'), default="multiscale.xml",
                  help='multiscale description (xml file)')

argp.add_argument('-xmml',type=argparse.FileType('r'),
                  help="Specifies input xmml file to generate output files for PatternsDrivenPlanner")

argp.add_argument('-H','--host', nargs='+', type=str, choices=["supermuc", "supermuc-p2", "eagle", "neale"],
                  help="specifies the required host [or set of hosts] to run this simulation. Host can be Supermuc (or supermuc phase 2), Eagle and/ or Neale",
		  metavar='Host')

argp.add_argument('-n','--nodetype', nargs='+',type=str, choices=["supermuc:fat","supermuc:thin","supermuc:haswell","eagle:haswell_128","eagle:haswell_64","eagle:haswell_256"],
                  help="specifies the required node type [or set of node types] to run this simulation. Node type can be supermuc:fat, supermuc:thin and/or eagle:haswell_128", metavar='Node type')

argp.add_argument('-e','--energy',action='store_true',
                  help="choose plans based on energy efficiency (least energy usage)")

argp.add_argument('-b','--benchmark',action='store_true',
                  help="will be used to run and store benchmark data")

argp.add_argument('-p','--profile',action='store_true',
		  help="adds stage-out step to retrieve and upload performance profiles measurements (automatically turned on when running in benchmark mode)")

argp.add_argument('-t','--time', type=int, default=1800,
                  help="specifies time limit in seconds (wallclock time for benchmark scenarios or added safety time for optimized scenarios) default is 1800 seconds")

argp.add_argument('--notifications',type=str,
                  help="email for notifications (middleware compatable)")

argp.add_argument('-M',type=int, default=3,
                  help="maximum number of plans (default is 3)")

argp.add_argument('--reservation', nargs='*',type=str,
                  help="reservation for resources, the reservation is in format arc:reservation_id (supermuc:srv03-ib.49.r)")

argp.add_argument('-E','--Efficiency',action='store_true',
                  help="choose plans based on Parallel efficiency (least resource usage)")

argp.add_argument('-r','--Resourceusage',action='store_true',
                  help="choose plans based resource usage")

argp.add_argument('-L','--Local', action='store_true',
		  help="use only local runs (same node types)")

argp.add_argument('-np','--nopreference', action='store_true',
		  help="do not store plans preferences")

argp.add_argument('-S','--Submit', action='store_true',
		  help="directly submit the chosen multiscale setup / benchmarks to the middleware")

argp.add_argument('-nd','--nodedescription',type=str,
                  help="node description can be either path of node description xml or qcg - default is using QCG ")

argp.add_argument('-mc',action='store_true',
                  help="new QCG multi-crateria file")

argp.add_argument('-j','--jobID',action='store_true',
		  help="append subdir with name $JOB_ID to all staged-out targets")

argp.add_argument('-o','--output',default="out.xml",
		  help="specifies output filename")

argp.add_argument('-q','--quiet', action='store_true',
		  help="do not show print messages")

argp.add_argument('-v','--verbose', action='store_true',
		  help="show print messages")

args = argp.parse_args()




######################### start here #############################################################################

#deine xmml file
if args.xmml:
	sys.argv[1] = 'matrix.xml'
	sys.argv[2] = 'multiscale.xml'
	file = args.xmml
	xmmlRead(file)
	if not args.quiet:
		print " ============ Pattern Driven Planner ========"
		print " ** multiscale and single scale files are generated **"
		print " ** please use these files as input files for the PatternDrivenPlanner **"
	sys.exit(0)

#define file names and parsing handlers

matrixFile = args.singlescale #sys.argv[1]
matrixDoc = minidom.parse(matrixFile);

multiscaleFile = args.multiscale #sys.argv[2]
multiscaleDoc = minidom.parse(multiscaleFile);

dir_name= "."

if not args.quiet:
	print " ============ Pattern Driven Planner ========"


if args.host and not args.quiet:
	print "** In this run the requested hosts are ", args.host , "**"
if args.nodetype and not args.quiet:
	print "** In this run the requested nodes are ", args.nodetype , "**"


main_dir = os.getenv("COMPAT_OPTIMISATIONPART_DIR")

u = args.nodedescription

if ( not u ):
	u = main_dir + "/nodeDescription.xml"
	nodeDescription = readDescription(u)	
	#nodeDescription = updateDescription(args.quiet,main_dir)

elif ( u.endswith('xml') ):
	nodeDescription = readDescription(u)

elif ( u.strip() == "qcg" or u.strip() == "QCG"):
    nodeDescription = updateDescription(args.quiet,main_dir)

else:
	print "no node description"
	raise error   
#print "nodeDescription ", nodeDescription

output_filename = dir_name+"/"+args.output;

ptrn = ""
NV = multiscaleDoc.getElementsByTagName('computing')[0].firstChild
if (NV is not None):
	ptrn = NV.nodeValue.strip()

if (ptrn != ""):
	pattern(output_filename, multiscaleDoc, matrixDoc, args, nodeDescription, ptrn)
else:
	print("The pattern type is not detected")

if args.Submit:
	if not output_filename=="":
		print("Now submitting the generated script "+output_filename+" through the middleware...")
		cmdline = ["qcg-sub","-Q","-X",output_filename]
		try:
			proc = subprocess.check_output(cmdline, stderr=subprocess.STDOUT)
			print(proc+"\nDONE")
		except subprocess.CalledProcessError:
  			# Error: command exited with non-zero code
			print(proc+"\nFAILED")


