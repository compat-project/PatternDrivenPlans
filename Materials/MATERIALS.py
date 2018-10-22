import numpy as np
from kernel_postprocess import find_one_xml, find_cxa_value, generate_kernel_hash, get_dict_field_val
import os
from costFunctions import *
import tarfile
from lxml import etree
import math

def get_scale(params):
	return 1

def post_operations(formula, helpers, inputs):

   map_kernel_names = ["single_md"]
   core_kernel_names= ["dealammps"]
   map_kernel_type = ["k"]
   xmlfiles = [['nanoscale_state/in/data/'+f for f in os.listdir('Materials/nanoscale_state/in/data') if os.path.isfile('Materials/nanoscale_state/in/data/'+f)]]
   return map_kernel_names, core_kernel_names, map_kernel_type, xmlfiles 

def get_parameters(cxa_path, map_kernel_name, xmlfile, environment):
   parameters = {}
   parameters['strain_tensor'] = {}
   parameters['strain_tensor']['eps00'] = 0
   parameters['strain_tensor']['eps01'] = 0
   parameters['strain_tensor']['eps02'] = 0
   parameters['strain_tensor']['eps11'] = 0
   parameters['strain_tensor']['eps12'] = 0
   parameters['strain_tensor']['eps22'] = 0

   return parameters

def calc_time(kernelNames, fdss, model_time, s):
   
   avg_num_micros = 200
   number_of_motifs = 50
   total_cores = s.getNumberOfCores()
   kernel_time = float(fdss[0][0]['kernel_time'])
   kernel_core = fdss[0][0]['cores']

   total_time = number_of_motifs * ( avg_num_micros / math.ceil(total_cores/ kernel_core) ) * kernel_time

   s.setSubmodelsTimes([kernel_time])
   s.setTotalTime(total_time)

   return total_time

def calc_eff(s):
   primary_idx = 1
   rPc = 9.671338425521 #time of average run per core (0.9)
   eff = calculateEfficiency_HMC(s, rPc)
   s.setEfficiency(eff)

   return eff

def calc_energy(kernelNames, fdss, model_time, total_time, s):

   avg_num_micros = 200
   total_cores = s.getNumberOfCores()
   kernel_energy = fdss[0][0]['energy']
   kernel_core = fdss[0][0]['cores']

   s.setSubmodelsEnergy(kernel_energy)
   total_energy = ( avg_num_micros / math.ceil(total_cores/ kernel_core) ) * kernel_energy 

   s.setTotalEnergy(total_energy)
   return total_energy
