import numpy as np
from kernel_postprocess import find_one_xml, find_cxa_value, generate_kernel_hash, get_dict_field_val
import os
from costFunctions import *

def get_parameters(cxa, kname, xmlfile, environment):
      sample = {} 
      if os.path.isfile(cxa):
        with open(cxa, 'r') as fd:
          string = fd.read()
          sample['global_steps'] = find_cxa_value(string, "max_timesteps")
          if kname == "FlowController":
            sample['T'] = find_cxa_value(string, "bf:T")
            sample['dt'] = find_cxa_value(string, "bf:dt")
            sample['convergence'] = find_cxa_value(string, "bf:convergence_limit")
          elif kname == "ICgenerator":
            sample['T'] = find_cxa_value(string, "ic:T")
            sample['dt'] = find_cxa_value(string, "ic:dt")
          elif kname == "SMCController":
            sample['T'] = find_cxa_value(string, "smc:T")
            sample['dt'] = find_cxa_value(string, "smc:dt")

      return sample


def get_scale(params):
	return eval(params['global_steps'])


def calc_time(kernelNames, fdss, model_time, s):
   for j in xrange( 0,len(kernelNames) ):
   	exec("%s = %f" % (kernelNames[j],float(fdss[j][0]['kernel_time'])))
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
   map_kernel_names = ["SMCController", "FlowController"]
   core_kernel_names = ["smc","bf"]
   map_kernel_type = ["k","k"]
   xmlfiles = ["",""]
   return map_kernel_names, core_kernel_names, map_kernel_type, xmlfiles


