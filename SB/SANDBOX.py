import numpy as np
from kernel_postprocess import find_one_xml, find_cxa_value, generate_kernel_hash, get_dict_field_val
import os
from costFunctions import *

def get_parameters(cxa, kname, xmlfile, environment):
      sample = {} 
      if os.path.isfile(cxa):
        with open(cxa, 'r') as fd:
          string = fd.read()
          sample['global_steps'] = find_cxa_value(string, "repeat")
          if kname == "large":
            sample['c'] = find_cxa_value(string, "large:collisions")
          elif kname == "small":
            sample['c'] = find_cxa_value(string, "small:collisions")
          elif kname == "small2":
            sample['c'] = find_cxa_value(string, "small2:collisions")

      return sample


def get_scale(params):
	return params['global_steps']


def calc_time(kernelNames, fdss, model_time, s):
   for j in xrange( 0,len(kernelNames) ):
   	exec("%s = %f" % (kernelNames[j],float(fdss[j][0]['kernel_time'])))
   print kernelNames
   s.setSubmodelsTimes([smc, bf])
   total_time = eval(model_time) # or you can use smc + bf
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
   s.setSubmodelsEnergy([smc, bf])
   total_energy = eval(model_time)* total_time 
   s.setTotalEnergy(total_energy)
   return total_energy

def post_operations(formula, helpers, inputs):
   map_kernel_names = ["large", "small1","small2"] #["tube_muscle2_large", "tube_muscle2_small","tube_muscle2_small2"]
   core_kernel_names = ["large01","small1","small2"]
   map_kernel_type = ["k","k","k"]
   xmlfiles = ["","",""]
   return map_kernel_names, core_kernel_names, map_kernel_type, xmlfiles


