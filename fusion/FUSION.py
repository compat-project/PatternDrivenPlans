import numpy as np
from kernel_postprocess import find_one_xml, find_cxa_value, generate_kernel_hash, get_dict_field_val
import os
from costFunctions import *
import tarfile
from lxml import etree

def get_parameters(cxa_path, kernel, xmlfile, ev):
    
    parameters = {}

    with open(xmlfile, 'r') as fd:
      root = etree.parse(fd)

    if (kernel.upper() == "GEM_KERNELB"):
      parameters['nx00'] = find_one_xml(root, "nx00")
      parameters['ny00'] = find_one_xml(root, "ny00")
      parameters['ns00'] = find_one_xml(root, "ns00")
      parameters['nftubes'] = find_one_xml(root, "nftubes")
      parameters['nstep'] = find_one_xml(root, "nstep")
    elif (kernel.upper() == "ETS_KERNELB"):
      parameters['heating_multiplier'] = find_one_xml(root, "ohmic_heating_multiplier")
    parameters['its_stop'] = ev['MUSCLE_FUSION_STOP']
    parameters['its_start'] = ev['MUSCLE_FUSION_START']  

    return parameters

def get_scale(params):
       return (float(params['its_stop']) - float(params['its_start']) + 1)

def calc_time(kernelNames, fdss, model_time, s):

   for j in xrange( 0,len(kernelNames) ):
   	exec("%s = %f" % (kernelNames[j],float(fdss[j][0]['kernel_time'])))

   s.setSubmodelsTimes([transp, turb])

   total_time = eval(model_time)
   s.setTotalTime(total_time)
   return total_time


def calc_eff(s):
   primary_idx = 1
   eff = calculateEfficiency(s, primary_idx)
   s.setEfficiency(eff)
   return eff

def calc_energy(kernelNames, fdss, model_time, total_time, s):
   for j in xrange( 0,len(kernelNames) ):
	exec("%s = %f" % (kernelNames[j],float(fdss[j][0]['energy'])))

   s.setSubmodelsEnergy([transp, turb])
   total_energy = (turb + transp) * total_time #eval(model_time)* total_time 

   s.setTotalEnergy(total_energy)
   return total_energy

def post_operations(formula, helpers, inputs):
   tar_inputs(inputs)
   map_kernel_names = ["ets_kernelB", "gem_kernelB", "chease_kernelB","imp4dv_kernelB"]
   core_kernel_names= ["transp","turb","equil"]
   map_kernel_type = ["k","k","h","h"]
   xmlfiles = ["tmp/ets.xml", "tmp/gem-ref.xml","tmp/chease.xml","tmp/ets.xml"]

   return map_kernel_names, core_kernel_names, map_kernel_type, xmlfiles

def tar_inputs(inputs):
   # Get access to gem-ref.xml
   #print "inputs ",inputs
   tar = tarfile.open(inputs)
   tar.extractall(path='tmp')
   tar.close()

