#!/usr/bin/env python

import json
import os
import hashlib
import xml.etree.ElementTree as etree
import sys
import re
from dateutil import parser
import time
import re


def get_cxa(app):

    if app.upper() == 'FUSION':
       return os.environ.get('COMPAT_CXA','unified.cxa.rb')
    elif app.upper() == 'ISR2D':
       return os.environ.get('COMPAT_CXA','cxa/isr_unified_prof.cxa.rb')
    elif app.upper() == 'ISR3D':
       return os.environ.get('COMPAT_CXA','cxa/isr_unified_prof.cxa.rb')
    elif app.upper() == 'BAC':
       return ''
    else:
       return ''

def generate_kernel_hash(app, kernel, prefix, cxa):
    files=[]

    if cxa =="":
        cxa = get_cxa(app)

    #print "cxa ", cxa
    
    if app.upper() == 'FUSION':
       files.append(cxa)
    
       choices = {'gem_kernelB' : prefix + 'gem-ref.xml', 'chease_kernelB' : prefix + 'chease.xml', 'ets_kernelB' : prefix +'ets.xml', 'imp4dv_kernelB' : ''}
       files.append(choices.get(kernel,''))

    elif app.upper() == 'BAC':
       files.append(cxa) 

    elif app.upper() == 'ISR2D':
       files.append(cxa)
       

    elif app.upper() == 'MATERIALS':
        files = ['nanoscale_state/in/data/'+f for f in os.listdir('nanoscale_state/in/data') if os.path.isfile('nanoscale_state/in/data/'+f)]
    else:
       files = [f for f in os.listdir('.') if os.path.isfile(f)]
       #add all files?
       
    #print(files)

    content=[]
    for f in files:
        if os.path.isfile(f):
           content.append(open(f).read())

    #print(content)

    return hashlib.md5((''.join(content)).encode('utf-8')).hexdigest()


def get_dict_field_val(inDict, fields):
    """
    Shows the value of the field given by the ordered list of field keys passed
    in

    Args:
        inDict (dict): Dictionary of JSON values to look into
        fields (list): Ordered list of key names in the JSON dictionary to
            look into

    Returns:
        Nothing
    """
    assert isinstance(inDict, dict)
    assert isinstance(fields, list)

    outVal = inDict
    tried = ""
    for field in fields:
        try:
            tried += str(field) + ", "
            outVal = outVal[field]
        except KeyError:
            print("Field '" + tried + "' not found")
            return None
    return outVal
#### End of function get_dict_field_val



def query_notes(string, key):
    for pair in string.split(':'):
        p = pair.split('=')
        if p[0].strip() == key:
            return p[1].strip()
    return "Unknown"

def find_one_xml(root, attribute):
  results = root.findall('.//' + attribute)
  if len(results) < 1:
    return "Unknown"
  else:
    return results[0].text.strip()

def find_cxa_value(string, variable):
    regexp = '\$env\[".*"\]\s*=\s*.*'
    for match in re.finditer(regexp, string):
        m = match.group(0).split('#')[0]
        regexp2 = '\[".*"\]'
        if re.findall(regexp2, m)[0][2:-2].strip() == variable:
            return match.group(0).split('#')[0].split('=')[1].strip()

    regexp = '\$env\[\'.*\'\]\s*=\s*.*'
    for match in re.finditer(regexp, string):
        m = match.group(0).split('#')[0]
        regexp2 = '\[\'.*\'\]'
        if re.findall(regexp2, m)[0][2:-2].strip() == variable:
            return match.group(0).split('#')[0].split('=')[1].strip()

    return "Unknown"


def round_strain(number):
    return round(float(number), 7)
    


def get_app_params(sample, app, jsonDict):

    cxa = get_cxa(app)

    if app.upper() == 'FUSION':
      
      sample['parameters']['its_start'] = os.environ.get('MUSCLE_FUSION_START','0') 
      sample['parameters']['its_stop'] = os.environ.get('MUSCLE_FUSION_STOP','0') 
      if sample['kernel_name'] == "gem_kernelB" and os.path.isfile("gem.xml"):
        with open("gem.xml", 'r') as fd:
          root = etree.parse(fd)

        sample['parameters']['nx00'] = find_one_xml(root, "nx00")
        sample['parameters']['ny00'] = find_one_xml(root, "ny00")
        sample['parameters']['ns00'] = find_one_xml(root, "ns00")
        #sample['parameters']['npesx'] = find_one_xml(root, "npesx")
        #sample['parameters']['npess'] = find_one_xml(root, "npess")
        sample['parameters']['nftubes'] = find_one_xml(root, "nftubes")
        sample['parameters']['nstep'] = find_one_xml(root, "nstep")
 
      if sample['kernel_name'] == "ets_kernelB" and os.path.isfile("ets.xml"):
        with open("ets.xml", 'r') as fd:
          root = etree.parse(fd)

        sample['parameters']['heating_multiplier'] = find_one_xml(root, "ohmic_heating_multiplier")

    elif app.upper() == 'ISR2D':
      if os.path.isfile(cxa):
        with open(cxa, 'r') as fd:
          string = fd.read()
          sample['parameters']['global_steps'] = find_cxa_value(string, "max_timesteps")
          if sample['kernel_name'] == "FlowController":
            sample['parameters']['T'] = find_cxa_value(string, "bf:T")
            sample['parameters']['dt'] = find_cxa_value(string, "bf:dt")
            sample['parameters']['convergence'] = find_cxa_value(string, "bf:convergence_limit")
          elif sample['kernel_name'] == "ICgenerator":
            sample['parameters']['T'] = find_cxa_value(string, "ic:T")
            sample['parameters']['dt'] = find_cxa_value(string, "ic:dt")
          elif sample['kernel_name'] == "SMCController":
            sample['parameters']['T'] = find_cxa_value(string, "smc:T")
            sample['parameters']['dt'] = find_cxa_value(string, "smc:dt")

	print "sample ", sample

    elif app.upper() == 'MATERIALS':
      commandline = get_dict_field_val(jsonDict, ["data", "applicationDetails", "commandLine"])
      commandParams = commandline.split(" ")
      params = len(commandParams)

      # Lammps has 7 parameters we want 2 and 5
     
      matfile = commandParams[params-3]+"/"+commandParams[params-7]+"."+commandParams[params-6]+".upstrain"

      if os.path.isfile(matfile):
      
        with open(matfile) as fd:
          string = fd.read()
          strain = string.splitlines()
 
        
          sample['parameters']['strain_tensor'] = {}
          sample['parameters']['strain_tensor']['eps00'] = round_strain(strain[0])
          sample['parameters']['strain_tensor']['eps01'] = round_strain(strain[1])
          sample['parameters']['strain_tensor']['eps02'] = round_strain(strain[2])
          sample['parameters']['strain_tensor']['eps11'] = round_strain(strain[3])
          sample['parameters']['strain_tensor']['eps12'] = round_strain(strain[4])
          sample['parameters']['strain_tensor']['eps22'] = round_strain(strain[5])


    elif app.upper() == "BAC":
      if os.path.isfile("input/build/complex.top"):
        with open("input/build/complex.top") as fd:
          string = fd.read()
          lines = string.splitlines()
          sample['parameters']['cells'] = lines[6].lstrip().split(" ")[0]

       

def process_json(jsonDict, app):
# Read in the JSON as a dictionary

    name    = get_dict_field_val(jsonDict, ["data", "applicationDetails", "exeName"])
    runtime = get_dict_field_val(jsonDict, ["data", "applicationDetails", "time", "plain"])
    
    starttime = get_dict_field_val(jsonDict, ["data", "applicationDetails", "startDate"])

    notes = get_dict_field_val(jsonDict, ["data", "applicationDetails", "notes"])

    system = query_notes(notes, "COMPAT_HPC_SYSTEM")


    #MUSCLE2
    m2send = get_dict_field_val(jsonDict, ["data", "muscle2", "sendduration", "total"])
    m2recv = get_dict_field_val(jsonDict, ["data", "muscle2", "receiveduration", "total"])
    m2bar  = get_dict_field_val(jsonDict, ["data", "muscle2", "barrierduration", "total"])
    if m2send is None:
      m2tot = 0
    else:
      m2tot = m2send + m2recv + m2bar

    #MPI
    mpi = get_dict_field_val(jsonDict, ["data", "overview", "mpi", "percent"])
    mpitot = (mpi * runtime)/100.0

    #Energy
    if system.upper() == "SUPERMUC":
      energy = get_dict_field_val(jsonDict, ["data", "compat", "supermuc", "energy", "total"])
    else:
      energywh = get_dict_field_val(jsonDict, ["data", "energy", "total", "plain"])
      if energywh is None:
        energy=0
      else:
        energy=energywh*60*60

    #Cores
    cores = get_dict_field_val(jsonDict, ["data", "applicationDetails", "processes", "plain"])

    #Print
    #print("<name> <processes> <runtime (s)> <mpi (s)> <muscle2 (s)> <energy (j)>")
    sample_str = '{ "kernel_name" : "", "kernel_cores" : 0, "kernel_runtime" : 0.0, "kernel_mpi" : 0.0, "kernel_muscle" : 0.0, "kernel_energy" : 0.0, "node_system" : "", "node_type" : "", "kernel_hash" : "", "parameters" : {}}'
    sample = json.loads(sample_str)


    sample['kernel_name'] = str(name)
    sample['kernel_cores'] = cores
    sample['kernel_runtime'] = runtime
    sample['kernel_mpi'] = mpitot
    sample['kernel_muscle'] = m2tot
    sample['kernel_energy'] = energy
    sample['node_system'] = system
    node = re.split("[; :]", query_notes(notes, "COMPAT_HPC_NODE_TYPE"))
    sample['node_type'] = node[0]
    sample['kernel_hash'] = generate_kernel_hash(app, sample['kernel_name'],"","")
    sample['kernel_io'] = get_dict_field_val(jsonDict, ["data", "overview", "io", "percent"]) * runtime / 100 
    sample['memory'] = get_dict_field_val(jsonDict, ["data", "memory", "peak"])  
    sample['time_start'] = time.mktime(parser.parse(starttime,fuzzy=True).timetuple())
    sample['time_end'] = sample['time_start'] + runtime

    get_app_params(sample, app, jsonDict)

    return sample


if __name__ == "__main__":
    #parser = argparse.ArgumentParser(description="Utility to show the value " +
    #        "stored at a given field in a JSON file")
    # Add a file to read input from
    #parser.add_argument("infile", help="JSON file to read information from",
    #    type=argparse.FileType('r'))

    kernel = json.loads('{ "run_app" : "", "run_cores" : 0, "kernels" : []}')

    #kernel['run_app'] = os.environ['COMPAT_APP']
    #kernel['run_cores'] = os.environ['QCG_PROCESSES']


    #for l in get_dict_field_val(jsonDict, ["data", "applicationDetails", "notes"]):
	
    if len(sys.argv) < 3:
       print ("Not enough Parameters") 
       print (str(sys.argv))
       sys.exit(1)



    infile = sys.argv[1]

    jsonDict = json.load(open(infile))
    notes = get_dict_field_val(jsonDict, ["data", "applicationDetails", "notes"])
    kernel['run_app'] = query_notes(notes, "COMPAT_APP")
    kernel['run_cores'] = query_notes(notes, "COMPAT_NTASKS")
    kernel['job_ID'] = query_notes(notes, "COMPAT_JOBID")
    kernel['kernels'].append(process_json(jsonDict, kernel['run_app']))    


    with open(sys.argv[2], 'w') as outfile:
       json.dump(kernel, outfile)
