from database_upload import Run, NodeType, Kernel, KernelPerf
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os
import imp
import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")

from scipy.optimize import curve_fit
import numpy as np
import json
import sys
import hashlib
from kernel_postprocess import find_one_xml, find_cxa_value, generate_kernel_hash, get_dict_field_val
from lxml import etree
import subprocess
from models import *
from costFunctions import *
import importlib

def uniq_cores(x):
    s = set(x)
    #print "set", s, len(s)
    return len(s) 

def time_model(x, a, b):
    return a * (1.0 / x) + b

def time_model_2(x, a):
    return a * (1.0 / x)

def mpi_model(x, a, b, c, d ):
    return a + (b * x) + (c * x**2) + (d * np.log2(x)) #+ (e * x**4) 

def mpi_model_3(x, a, b, c):
    return a * x + b * np.log2(x) + c

def mpi_model_2(x, a, b):
    return a * x + b

def linear_model(x, a):
    return a

def fit_time(historical, core_counts):
    x = [p[0] for p in historical]
    y = [p[1] for p in historical]
    if len(historical) > 1:
        popt, pcov = curve_fit(time_model, x, y, p0=(1, 1),bounds=([0, 0], [np.inf, np.inf])) ## check for fusion
        return [time_model(core_count, popt[0], popt[1]) for core_count in core_counts]
    elif len(historical) == 1:
        popt, pcov = curve_fit(time_model_2, x, y, p0=(1,),bounds=(0, np.inf))
        return [time_model_2(core_count, popt[0]) for core_count in core_counts]
    else:
        raise ValueError

def fit_mpi(historical, core_counts):
    x = [p[0] for p in historical]
    y = [p[1] for p in historical]
    sz = uniq_cores(x)
    if sz > 5:
        popt, pcov = curve_fit(mpi_model, x, y, p0=(1, 1, 1, 1))
        #popt, pcov = curve_fit(mpi_model, x, y, p0=(1, 1, 1),bounds=([0, 0, 0], [np.inf, np.inf, np.inf]))
        #print "== popt mpimodel  == ", popt
        return [mpi_model(core_count, popt[0], popt[1], popt[2], popt[3]) for core_count in core_counts]
    elif sz >= 3:
        popt, pcov = curve_fit(mpi_model_3, x, y, p0=(1, 1,1))
        #print "== popt mpi_model 3== ", popt
        return [mpi_model_3(core_count, popt[0], popt[1], popt[2]) for core_count in core_counts]
    elif sz == 2:
        popt, pcov = curve_fit(mpi_model_2, x, y, p0=(1, 1))
        #print "== popt mpi_model 2== ", popt
        return [mpi_model_2(core_count, popt[0], popt[1]) for core_count in core_counts]
    else:
        popt, pcov = curve_fit(linear_model, x, y, p0=(1))
        return [linear_model(core_count, popt[0]) for core_count in core_counts]
        #raise ValueError

def fitter(data, core_counts):
    cores = [entry['cores'] for entry in data]
    cpu_time = [entry['cpu_time'] for entry in data]
    mpi_time = [entry['mpi_time'] for entry in data]
    energy = [entry['energy'] for entry in data]
    fitted_cpu_time = fit_time(zip(cores, cpu_time), core_counts)
    fitted_energy = fit_time(zip(cores, energy), core_counts)
    fitted_mpi_time = fit_mpi(zip(cores, mpi_time), core_counts)

    return [{'core_count' : p[0], 'cpu_time' : p[1], 'mpi_time' : p[2], 'energy' : p[3]} 
            for p in zip(core_counts, fitted_cpu_time, fitted_mpi_time, fitted_energy)]
    
def fetch_and_untar(path): 
    os.mkdir("_" + os.path.split(path)[1])
    tar = tarfile.open('r_' + os.path.split(path)[1], 'r:gz')
    tar.extractall("_" + os.path.split(path)[1])
    

def db_start():
    engine = create_engine('mysql://performance_update:password@129.187.255.55/performance')
    #engine = create_engine('sqlite:////home/operks/Projects/Compat/python/perf.db')
    #engine = create_engine('sqlite:////home/saad/Desktop/compat/F2FAms/perf.db')
    #engine = create_engine('sqlite:////home/saad/COMPAT-Patterns-Software/OptimisationPart/perf.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


############ branching functions ##########################

def scale_app_parameters(my_module, app, session, cxa_path, xmlfile, environment, map_kernel_name, nodeType, hostName, cores):
      parameters = my_module.get_parameters(cxa_path, map_kernel_name, xmlfile, environment)
      fds = scale_perf(my_module, session, app, map_kernel_name , nodeType, hostName, cores, parameters)

      return fds

def calc_time(my_module, app, kernelNames, fdss, model_time, s):
   total_time = my_module.calc_time(kernelNames, fdss, model_time, s)
   s.setResourceUsage(s.getNumberOfCores(), s.getTotalTime())
   return total_time

def calc_eff(my_module, app, s):
   eff = my_module.calc_eff(s)
   return eff


def calc_energy(my_module, app, kernelNames, fdss, model_time, total_time, s):
   total_energy = my_module.calc_energy(kernelNames, fdss, model_time, total_time, s)
   return total_energy

def post_operations_app(my_module, app, inputs, formula, helpers):
   model_time = getModelTime(formula, helpers)
   map_kernel_names, core_kernel_names, map_kernel_type, xmlfiles = my_module.post_operations(formula, helpers, inputs)
   return map_kernel_names, core_kernel_names, map_kernel_type, xmlfiles, model_time

def get_scale(my_module, app, kname, params):
   return my_module.get_scale(params)
   
##############################################################################################

def scale_perf(my_module, session, app, kname, nname, nhost, cores, parameters):
    fds = []
    inscale = get_scale(my_module, app, kname, parameters)
    #print session.query(NodeType).filter(NodeType.name==nname).filter(NodeType.host==nhost)
    instance = session.query(NodeType).filter(NodeType.name==nname).filter(NodeType.host==nhost).first()
    if instance is None:
       ds = []
       return ds

    nid = instance.id

    # Query for all records
    ds = []
    query = session.query(KernelPerf, Kernel).join(Kernel).filter((Kernel.id == KernelPerf.kernel_id) & (KernelPerf.node_type_id == nid) & (Kernel.id.in_(session.query(Kernel.id).filter(Kernel.name == kname))))
    for row in query.all():
        params = json.loads(row.Kernel.config_parameters)
        #print kname, nid, params
        scale = get_scale(my_module, app, kname, params)
        cpu_time = row.KernelPerf.runtime - (row.KernelPerf.mpi_time + row.KernelPerf.muscle_time)
        #print instance.energy, instance.runtime, instance.cores, scale
        energy = row.KernelPerf.energy / float(row.KernelPerf.runtime*row.KernelPerf.cores)
        ds.append({'cores' : row.KernelPerf.cores, 'cpu_time' : cpu_time / scale,
                   'mpi_time' : row.KernelPerf.mpi_time / scale, 'energy' : energy })

    if (len(ds) == 0):
        return ds

    #print ds

    for fit in fitter(ds, cores):
        fds.append({'node_name' : nname, 'host_name' : nhost, 'cores' : fit['core_count'], 'kernel_time' : inscale * (fit['cpu_time'] + fit['mpi_time']), 'energy' : fit['energy']*fit['core_count']})
      
        #print "fds", fds
    return fds

def performanceEstimator(multiscaleDoc, scenarios, kernelNames, helpers, formula, dir_name, benchmark, multiscaleFile):

    app, cxa_path, inputs, environment, ptrn = getInfo(multiscaleDoc)
    
    
    my_module = my_import(multiscaleFile, app)

    #print load_from_file( os.path.abspath(os.path.dirname(multiscaleFile.name) +"/"+ app+".py") )

    session = db_start()
   
    if(ptrn == "ES"):

	map_kernel_names, core_kernel_names, map_kernel_type, xmlfiles, model_time = post_operations_app(my_module, app, inputs, formula, helpers) 
	for s in scenarios:
	   fdss = create_scale_fd(my_module, app, session, cxa_path, xmlfiles, environment, map_kernel_names, map_kernel_type, s)
   	
	   if( length(fdss) ):
		
	   	# calculate time
		total_time = calc_time(my_module, app, core_kernel_names, fdss, model_time, s)
                
                # calculate Efficiency
		efficiency = calc_eff(my_module, app, s)

	   	# calculate energy
		total_energy = calc_energy(my_module, app, core_kernel_names, fdss, model_time, total_time, s)
		
    elif(ptrn == "RC" or ptrn == "HMC"):

	map_kernel_names, core_kernel_names, map_kernel_type, xmlfiles, model_time = post_operations_app(my_module, app, inputs, formula, helpers)
	for s in scenarios:
	   fdss = create_scale_fd(my_module, app, session, cxa_path, xmlfiles, environment, map_kernel_names, map_kernel_type, s)

	   if( length(fdss) ):
		
	   	# calculate time
		total_time = calc_time(my_module, app, core_kernel_names, fdss, model_time, s)
                
                # calculate Efficiency
		efficiency = calc_eff(my_module,app, s)

	   	# calculate energy
		total_energy = calc_energy(my_module, app, core_kernel_names, fdss, model_time, total_time, s)
	
    #print "len scenarios ", len(scenarios)
    y = [s for s in scenarios if s.getTotalTime() > 0]
    #print "len y  ", len(y)

    return y

def getInfo(multiscaleDoc):

   app = multiscaleDoc.getElementsByTagName("job")[0].attributes["appID"].value
   NV = multiscaleDoc.getElementsByTagName('computing')[0].firstChild
   if (NV is not None):
	ptrn = NV.nodeValue.strip()

   # get them directly from the multiscale doc, but now just static
   stageIO = multiscaleDoc.getElementsByTagName("middleware")[0].getElementsByTagName("execution")[0].getElementsByTagName("stageInOut")[0]
   stageI = [i for i in stageIO.getElementsByTagName("file") if i.attributes["type"].value=="in"]

   cxa_path = "xx"
   inputs = "xx"
   for i in stageI:
       if "cxa.rb" in i.attributes["name"].value:
           cxa_path = i.getElementsByTagName("location")[0].firstChild.nodeValue.replace("gsiftp://qcg.man.poznan.pl/",'')

       elif ".tgz" in i.attributes["name"].value:
           inputs = i.getElementsByTagName("location")[0].firstChild.nodeValue.replace("gsiftp://qcg.man.poznan.pl/",'')

   environment = {}  

   ev = multiscaleDoc.getElementsByTagName("middleware")[0].getElementsByTagName("execution")[0].getElementsByTagName("environment")[0].getElementsByTagName("variable")
   for e in ev:
      nm = e.attributes["name"].value
      vl = e.firstChild.nodeValue
      environment[nm] = vl
    
   return app, cxa_path, inputs, environment, ptrn

def length(fdss):
   ok = True
   for j in xrange( 0,len(fdss) ):
   	if len(fdss[j]) == 0:
		ok = False
   return ok

def create_scale_fd(my_module, app, session, cxa_path, xmlfiles, environment, map_kernel_names, map_kernel_type, s):
   n = 0
   fdss = [dict() for x in range(len(map_kernel_names))]

   for j in xrange( 0,len(map_kernel_names) ):
	if map_kernel_type[j] == "k":
		fdss[j] = scale_app_parameters(my_module, app, session, cxa_path, xmlfiles[j], environment, map_kernel_names[j], s.getNodeType()[j], s.getHostName()[j], [s.getCores()[j]])
		n = n + 1
	elif map_kernel_type[j] == "h":
		fdss[j] = scale_app_parameters(my_module, app, session, cxa_path, xmlfiles[j], environment, map_kernel_names[j], s.getNodeType()[n-1], s.getHostName()[0], [1])
   return fdss

def load_from_file(filepath):
    class_inst = None
    expected_class = '*'

    mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])

    if file_ext.lower() == '.py':
        py_mod = imp.load_source(mod_name, filepath)

    elif file_ext.lower() == '.pyc':
        py_mod = imp.load_compiled(mod_name, filepath)

    if hasattr(py_mod, expected_class):
        class_inst = getattr(py_mod, expected_class)()

    return class_inst

def my_import(multiscaleFile, app):
    print "path ", os.path.abspath(os.path.abspath(os.path.dirname(multiscaleFile.name) ))

    sys.path.append(os.path.abspath(os.path.abspath(os.path.dirname(multiscaleFile.name) ))) #+"/"+ app+".py"


    my_module = importlib.import_module(app.upper()) #+".py"
    return my_module

