from xml.dom import minidom
import xml.dom
from xml.dom.minidom import Node

import json
from collections import OrderedDict

def QCG_script_ptrn(ptrn, output_filename, multiscaleDoc, args, kernelNames, helpers, kernel_helpers, Plans, mc):
	if ptrn == "ES":
		if args.mc:
			QCG_script_ES_mc(output_filename, multiscaleDoc, args, kernelNames, helpers, kernel_helpers, Plans)
		else:
			QCG_script_ES(output_filename, multiscaleDoc, args, kernelNames, helpers, kernel_helpers, Plans)

	elif ptrn == "RC":
		QCG_script_RC(output_filename, multiscaleDoc, args, kernelNames, helpers, kernel_helpers, Plans)

	elif ptrn == "HMC":
		QCG_script_HMC(output_filename, multiscaleDoc, args, kernelNames, helpers, kernel_helpers, Plans)	




def QCG_script_ES(output_filename, multiscaleDoc, args, kernelNames, helpers, kernel_helpers, Plans):

	### Execution Parameters (get from multiscale.xml) ###

	app_id, project = getAppProjectId(multiscaleDoc)
	taskId, persistent, execution_type = getTaskAttributes(multiscaleDoc)

	application_name, application_args = getAppInfo(multiscaleDoc)
	stdout_url, stderr_url, stage_ins, stage_out = getInOut(multiscaleDoc)
	env_variables = getEnv(multiscaleDoc)

	### Build QCG Script (Requirements) ###

	doc = minidom.Document()
	qcgJob = doc.createElement("qcgJob");
	qcgJob = setHeader(qcgJob, app_id, project)

	task = doc.createElement("task");
	task = setTask(task, persistent, taskId)

	if args.notifications:
		notifications = doc.createElement("notifications")
		consumer = doc.createElement("consumer")
		notifications, consumer = setNotification(notifications, consumer, args)

	requirements = doc.createElement("requirements");
	patternTopology = doc.createElement("patternTopology");
	kernels = doc.createElement("kernels");

	doc, kernels = addKernels(doc, kernels, kernelNames, kernel_helpers, helpers)

	classes = doc.createElement("classes");
	classes = setClasses(classes, doc)

	plans = doc.createElement("plans");
	xx = len(Plans)
	### doc = setPlans(doc, Plans[i], len(Plans))


	for i in range(len(Plans)):
		plan = doc.createElement("plan");
		plan.setAttribute("id", Plans[i].getPlanName());

		costs = doc.createElement("criteria");
		time = doc.createElement("time");
		if(not args.nopreference):
			energy = doc.createElement("preference");
		
		Time = timeConvert(Plans[i].getPlanScenario().getTotalTime())
		
		time.appendChild(doc.createTextNode(Time));
		if(not args.nopreference):
			energy.appendChild(doc.createTextNode( str(xx) ));
		costs.appendChild(time);
		if(not args.nopreference):
			costs.appendChild(energy);
		xx = xx - 1

	
		group = doc.createElement("group");

		for j in range(0, len(kernelNames)):
			kernel = doc.createElement("kernel");
			kernel.setAttribute("refid", kernelNames[j]);

			node = doc.createElement("class");

			ct = classtype(Plans[i].getPlanScenario().getNodeType()[j])
			
			node.setAttribute("refid", "c"+str(ct));

			cores = doc.createElement("cores");
			cores.appendChild(doc.createTextNode(str(Plans[i].getPlanScenario().getCores()[j])) );
			
			node.appendChild(cores);
			kernel.appendChild(node);
			

			group.appendChild(kernel);
		

		plan.appendChild(costs);
		plan.appendChild(group)
		plans.appendChild(plan);

	patternTopology.appendChild(kernels);
	patternTopology.appendChild(classes);
	patternTopology.appendChild(plans);
	
	if args.reservation:
		patternTopology = setReservation(patternTopology, args)

	requirements.appendChild(patternTopology);

	### Build QCG Script (Execution) ###

	execution = doc.createElement("execution");
	execution.setAttribute("type", execution_type);

	executable = doc.createElement("executable");
	application = doc.createElement("application");
	application.setAttribute("name", application_name);
	executable.appendChild(application);

	arguments = doc.createElement("arguments");
	value = doc.createElement("value");
	value.appendChild(doc.createTextNode(application_args));
	arguments.appendChild(value);

	stdout = doc.createElement("stdout");
	directory = doc.createElement("directory");
	location = doc.createElement("location");
	location.setAttribute("type", "URL");
        if args.benchmark or args.jobID:
		location.appendChild(doc.createTextNode(stdout_url+"/${JOB_ID}"));
	else:
		location.appendChild(doc.createTextNode(stdout_url));
	directory.appendChild(location);
	stdout.appendChild(directory);

	stderr = doc.createElement("stderr");
	directory = doc.createElement("directory");
	location = doc.createElement("location");
	location.setAttribute("type", "URL");
        if args.benchmark or args.jobID:
	        location.appendChild(doc.createTextNode(stderr_url+"/${JOB_ID}"));
	else:
		location.appendChild(doc.createTextNode(stderr_url));
	directory.appendChild(location);
	stderr.appendChild(directory);


	stageInOut = doc.createElement("stageInOut");

	for stageIn in stage_ins:
		file = doc.createElement("file");
		file.setAttribute("name", stageIn[0]);
		file.setAttribute("type", "in");
		location = doc.createElement("location");
		location.setAttribute("type", "URL");
		location.appendChild(doc.createTextNode(stageIn[1]));
		file.appendChild(location);
		stageInOut.appendChild(file);

	directory = doc.createElement("directory");
	directory.setAttribute("name", stage_out[0]);
	directory.setAttribute("type", "out");
	location = doc.createElement("location");
	location.setAttribute("type", "URL");
        if args.benchmark or args.jobID:
        	location.appendChild(doc.createTextNode(stage_out[1]+"/${JOB_ID}"));
	else:
		location.appendChild(doc.createTextNode(stage_out[1]));
	directory.appendChild(location);
	stageInOut.appendChild(directory);

	if args.benchmark or args.profile:
		directory = doc.createElement("directory");
		directory.setAttribute("name", "ArmResults");
		directory.setAttribute("type", "out");
		location = doc.createElement("location");
		location.setAttribute("type", "URL");
		location.appendChild(doc.createTextNode("gsiftp://qcg.man.poznan.pl//home/plgrid-groups/plggcompat/Common/ArmResults"));
		directory.appendChild(location);
		stageInOut.appendChild(directory);

	environment = doc.createElement("environment");


	for var in env_variables:
		env_var = doc.createElement("variable");
		env_var.setAttribute("name", var[0]);
		env_var.appendChild(doc.createTextNode(var[1]));
		environment.appendChild(env_var);

	execution.appendChild(executable);
	execution.appendChild(arguments);
	execution.appendChild(stdout);
	execution.appendChild(stderr);
	execution.appendChild(stageInOut);
	execution.appendChild(environment);

	#################################### last Build QCG Script ############################################

	if args.notifications:
		task.appendChild(notifications);

	task.appendChild(requirements);
	task.appendChild(execution);

	qcgJob.appendChild(task);

	doc.appendChild(qcgJob)


	writeXML(output_filename, doc)
	
	return

def QCG_script_RC(output_filename, multiscaleDoc, args, kernelNames, helpers, kernel_helpers, Plans):

	#################################### Execution Parameters (get from multiscale.xml) ############################################

	appId, project = getAppProjectId(multiscaleDoc)
	task_IDs, task_persistent,task_extension = getTasksAttributes(multiscaleDoc)

	doc = minidom.Document()
	qcgJob = doc.createElement("qcgJob")

	qcgJob = setHeader(qcgJob, appId, project)

	t = -1
	#Iterate over number of tasks
	for tid in range(len(task_IDs)):
		t += 1

		task = doc.createElement("task");
		task.setAttribute("taskId", task_IDs[tid]);

		note = doc.createElement("note");

		multiscale_info = multiscaleDoc.getElementsByTagName('info')[0]		
		if  len(multiscale_info.getElementsByTagName("note")) > 0:
			n = multiscale_info.getElementsByTagName("note")
			note.appendChild(doc.createTextNode(n[tid].firstChild.nodeValue));

		if(task_persistent[tid] is not None):
			task.setAttribute("persistent", task_persistent[tid]);

		if(task_extension[tid] is not None):
			task.setAttribute("extension", task_extension[tid]);
		#print args

		if args.notifications:
			notification = doc.createElement("notifications");
			consumer = doc.createElement("consumer");
			notifications, consumer = setNotification(notifications, consumer, args)		
	
		requirements = doc.createElement("requirements");

		patternTopology = doc.createElement("patternTopology");

		kernels = doc.createElement("kernels");

		kname = kernelNames[tid]
		kernel = doc.createElement("kernel");
		kernel.setAttribute("id", kname);
		kernels.appendChild(kernel);

		classes = doc.createElement("classes");
		
		cc_host = ["supermuc","eagle"]
		cc_type = [["thin","fat","haswell"],["haswell_128","haswell_64"]] 

		for j in range(0,len(cc_host) ):
			Class = doc.createElement("class");
			Class.setAttribute("id", "c"+str(j));
			for aa in range(0,len(cc_type[j])):
				nnode = doc.createElement("node");
				nnode.setAttribute("host", cc_host[j] );
				nnode.appendChild(doc.createTextNode(cc_type[j][aa]));
				Class.appendChild(nnode);
			

			classes.appendChild(Class);
	
		plans = doc.createElement("plans");

		xx = len(Plans)

		for i in range(len(Plans)):
			plan = doc.createElement("plan");
			plan.setAttribute("id", Plans[i].getPlanName());

			costs = doc.createElement("criteria");
			time = doc.createElement("time");
			if(not args.nopreference):
				energy = doc.createElement("preference");
			
			Time = timeConvert( Plans[i].getPlanScenario().getTotalTime() )
			time.appendChild(doc.createTextNode( Time ));
			if(not args.nopreference):
				energy.appendChild(doc.createTextNode( str(xx)  ));

			xx = xx - 1
			costs.appendChild(time);
			if(not args.nopreference):
				costs.appendChild(energy);
		
			group = doc.createElement("group");

			#Iterate over number of 
			kernel = doc.createElement("kernel");
			kernel.setAttribute("refid", kname);

			node = doc.createElement("class");
			ct = classtype2(Plans[i].getPlanScenario().getNodeType()[tid])
			node.setAttribute("refid", "c"+str(ct));
			#node.appendChild(doc.createTextNode(str(Plans[i].getPlanScenario().getNodeType()[tid])) );

			cores = doc.createElement("cores");
			cores.appendChild(doc.createTextNode(str(Plans[i].getPlanScenario().getCores()[tid])) );
		
			node.appendChild(cores);

			kernel.appendChild(node);
			

			group.appendChild(kernel);

			plan.appendChild(costs);
			plan.appendChild(group)
			plans.appendChild(plan);

		patternTopology.appendChild(kernels);
		patternTopology.appendChild(classes);
		patternTopology.appendChild(plans);

		if args.reservation:
			patternTopology = setReservation(patternTopology, args)
		
		requirements.appendChild(patternTopology);
		multiscale_info = multiscaleDoc.getElementsByTagName('info')[0]
		if  len(multiscale_info.getElementsByTagName("note")) > 0:
			task.appendChild(note);
		task.appendChild(requirements);
		qcgJob.appendChild(task);

		## middleware
		tasks_temp = multiscaleDoc.getElementsByTagName("middleware")[0]
		executions = tasks_temp.getElementsByTagName("execution")
		workflows = tasks_temp.getElementsByTagName("workflow")
		parametersSweeps = tasks_temp.getElementsByTagName("parametersSweep")[0]

		execution_type   = executions[t].attributes["type"].value

		application_name = executions[t].getElementsByTagName("application")[0].attributes["name"].value
		arg = executions[t].getElementsByTagName("arguments")[0]
		
		application_args = []
		for i in arg.getElementsByTagName("value"): 
	   		application_args.append( i )


		execution = doc.createElement("execution");
		execution.setAttribute("type", execution_type);

		executable = doc.createElement("executable");
		application = doc.createElement("application");
		application.setAttribute("name", application_name);
		executable.appendChild(application);

		arguments = doc.createElement("arguments");

		for i in range(0,len(application_args)):
			value = doc.createElement("value");
	    		value.appendChild(doc.createTextNode(application_args[i].firstChild.nodeValue));
			arguments.appendChild(value);

		stageInOutread   = remove_blanks(executions[t].getElementsByTagName("stageInOut")[0]);
		stageInOutread   = remove_blanks(stageInOutread) #remove_blanks(
		
		
		if ( t == 1 ):
			workflow = doc.createElement("workflow");
			parent = doc.createElement("parent");
			parent.setAttribute("triggerState", "FINISHED");
			parent.appendChild(doc.createTextNode(task_extension[tid]));
			workflow.appendChild(parent);
		
		execution.appendChild(executable)
		execution.appendChild(arguments)
		execution.appendChild(stageInOutread)

		if args.notifications:
			task.appendChild(notification);

		task.appendChild(requirements);
		task.appendChild(execution);
		if ( t == 1 ):
			task.appendChild(workflow);

		task.appendChild(remove_blanks(parametersSweeps));

	#################################### Build QCG Script (Execution Time) ############################################

	task = remove_blanks(task)
	qcgJob.appendChild(task);

	doc.appendChild(qcgJob)
	

	f = open(output_filename, 'w');


	doc.writexml( f, indent=" ", addindent=" ", newl="\n")

	doc.unlink();
	
def QCG_script_HMC(output_filename, multiscaleDoc, args, kernelNames, helpers, kernel_helpers, Plans):

	### Execution Parameters (get from multiscale.xml) #########
	appId, project = getAppProjectId(multiscaleDoc)
	task_IDs, task_persistent,task_extension = getTasksAttributes(multiscaleDoc)

	doc = minidom.Document()
	qcgJob = doc.createElement("qcgJob")
	qcgJob = setHeader(qcgJob, appId, project)

	t = -1
	#Iterate over number of tasks
	for tid in range(len(task_IDs)):
		t += 1

		task = doc.createElement("task");
		task.setAttribute("taskId", task_IDs[tid]);

		note = doc.createElement("note");

		multiscale_info = multiscaleDoc.getElementsByTagName('info')[0]		
		if  len(multiscale_info.getElementsByTagName("note")) > 0:
			n = multiscale_info.getElementsByTagName("note")
			note.appendChild(doc.createTextNode(n[tid].firstChild.nodeValue));

		if(task_persistent[tid] is not None):
			task.setAttribute("persistent", task_persistent[tid]);

		if(task_extension[tid] is not None):
			task.setAttribute("extension", task_extension[tid]);
		#print args

		if args.notifications:
			notification = doc.createElement("notifications");
			consumer = doc.createElement("consumer");
			notifications, consumer = setNotification(notifications, consumer, args)		
	
		requirements = doc.createElement("requirements");

		patternTopology = doc.createElement("patternTopology");

		kernels = doc.createElement("kernels");

		kname = kernelNames[tid]
		kernel = doc.createElement("kernel");
		kernel.setAttribute("id", kname);
		kernels.appendChild(kernel);

		classes = doc.createElement("classes");
		
		cc_host = ["supermuc","eagle"]
		cc_type = [["thin","fat","haswell"],["haswell_128","haswell_64"]] 

		for j in range(0,len(cc_host) ):
			Class = doc.createElement("class");
			Class.setAttribute("id", "c"+str(j));
			for aa in range(0,len(cc_type[j])):
				nnode = doc.createElement("node");
				nnode.setAttribute("host", cc_host[j] );
				nnode.appendChild(doc.createTextNode(cc_type[j][aa]));
				Class.appendChild(nnode);
			

			classes.appendChild(Class);
	
		plans = doc.createElement("plans");

		xx = len(Plans)

		for i in range(len(Plans)):
			plan = doc.createElement("plan");
			plan.setAttribute("id", Plans[i].getPlanName());

			costs = doc.createElement("criteria");
			time = doc.createElement("time");
			if(not args.nopreference):
				energy = doc.createElement("preference");
			
			Time = timeConvert( Plans[i].getPlanScenario().getTotalTime() )
			time.appendChild(doc.createTextNode( Time ));
			if(not args.nopreference):
				energy.appendChild(doc.createTextNode( str(xx)  ));

			xx = xx - 1
			costs.appendChild(time);
			if(not args.nopreference):
				costs.appendChild(energy);
		
			group = doc.createElement("group");

			#Iterate over number of 
			kernel = doc.createElement("kernel");
			kernel.setAttribute("refid", kname);

			node = doc.createElement("class");
			ct = classtype2(Plans[i].getPlanScenario().getNodeType()[tid])
			node.setAttribute("refid", "c"+str(ct));
			#node.appendChild(doc.createTextNode(str(Plans[i].getPlanScenario().getNodeType()[tid])) );

			cores = doc.createElement("nodes");
			cores.appendChild(doc.createTextNode(str(Plans[i].getPlanScenario().getCores()[tid])) );
		
			node.appendChild(cores);

			kernel.appendChild(node);
			

			group.appendChild(kernel);

			plan.appendChild(costs);
			plan.appendChild(group)
			plans.appendChild(plan);

		patternTopology.appendChild(kernels);
		patternTopology.appendChild(classes);
		patternTopology.appendChild(plans);

		if args.reservation:
			patternTopology = setReservation(patternTopology, args)
		
		
		requirements.appendChild(patternTopology);
		multiscale_info = multiscaleDoc.getElementsByTagName('info')[0]
		if  len(multiscale_info.getElementsByTagName("note")) > 0:
			task.appendChild(note);
		task.appendChild(requirements);
		qcgJob.appendChild(task);

		## middleware
		tasks_temp = multiscaleDoc.getElementsByTagName("middleware")[0]
		executions = tasks_temp.getElementsByTagName("execution")
		workflows = tasks_temp.getElementsByTagName("workflow")
		
		if len(tasks_temp.getElementsByTagName("parametersSweep") ) > 0:
			parametersSweeps = tasks_temp.getElementsByTagName("parametersSweep")[0]

		execution_type   = executions[t].attributes["type"].value

		application_name = executions[t].getElementsByTagName("application")[0].attributes["name"].value
		arg = executions[t].getElementsByTagName("arguments")[0]
		
		application_args = []
		for i in arg.getElementsByTagName("value"): 
	   		application_args.append( i )


		execution = doc.createElement("execution");
		execution.setAttribute("type", execution_type);

		executable = doc.createElement("executable");
		application = doc.createElement("application");
		application.setAttribute("name", application_name);
		executable.appendChild(application);

		arguments = doc.createElement("arguments");

		for i in range(0,len(application_args)):
			value = doc.createElement("value");
	    		value.appendChild(doc.createTextNode(application_args[i].firstChild.nodeValue));
			arguments.appendChild(value);

		stageInOutread   = remove_blanks(executions[t].getElementsByTagName("stageInOut")[0]);
		stageInOutread   = remove_blanks(stageInOutread) #remove_blanks(
	
		environment = doc.createElement("environment");

		env_node = minidom.parseString(multiscaleDoc.getElementsByTagName("environment")[0].toxml());
		env_variables = [[i.attributes["name"].value, i.firstChild.nodeValue] for i in env_node.getElementsByTagName("variable")];

		for var in env_variables:
			env_var = doc.createElement("variable");
			env_var.setAttribute("name", var[0]);
			env_var.appendChild(doc.createTextNode(var[1]));
			environment.appendChild(env_var);

		
		
		if ( t == 1 ):
			workflow = doc.createElement("workflow");
			parent = doc.createElement("parent");
			parent.setAttribute("triggerState", "FINISHED");
			parent.appendChild(doc.createTextNode(task_extension[tid]));
			workflow.appendChild(parent);
		
		execution.appendChild(executable)
		execution.appendChild(arguments)
		execution.appendChild(stageInOutread)
		execution.appendChild(environment);

		if args.notifications:
			task.appendChild(notification);

		task.appendChild(requirements);
		task.appendChild(execution);
		if ( t == 1 ):
			task.appendChild(workflow);

		if len(tasks_temp.getElementsByTagName("parametersSweep") ) > 0:
			task.appendChild(remove_blanks(parametersSweeps));

	#################################### Build QCG Script (Execution Time) ############################################

	task = remove_blanks(task)
	qcgJob.appendChild(task);

	doc.appendChild(qcgJob)
	

	f = open(output_filename, 'w');


	doc.writexml( f, indent=" ", addindent=" ", newl="\n")

	doc.unlink();
	


def fromprettyxml(input_xml): #cool name, but not the opposite of dom.toprettyxml()
    _dom = minidom.parseString(input_xml)
    output_xml = ''.join([line.strip() for line in _dom.toxml().splitlines()])
    _dom.unlink()
    return output_xml

def remove_blanks(node):
    i = -1
    for x in node.childNodes:
	i = i + 1
        if x.nodeType == Node.TEXT_NODE:
            if (x.toxml().strip() == ""):
		#print "yes ", x.toxml()
	    	node.removeChild(x)
		
        elif x.nodeType == Node.ELEMENT_NODE:
            remove_blanks(x)
    return node

def timeConvert(seconds):
	m, s = divmod(seconds, 60)
	h, m = divmod(m, 60)
	
	if(h < 24):
		Time = "PT"+str(int(h))+"H"+str(int(m))+"M"+str(int(s))+"S"
	else:
		d, h = divmod(h, 24)
		if(d < 30):
			Time = "P"+str(int(d))+"DT"+str(int(h))+"H"+str(int(m))+"M"+str(int(s))+"S"
		else:
			mo, d = divmod(d, 30)
			Time = "P"+str(int(mo))+"M"+str(int(d))+"DT"+str(int(h))+"H"+str(int(m))+"M"+str(int(s))+"S"	

	return Time

def classtype(NodeType):
	if(NodeType == "thin"):
		return 0
	elif(NodeType == "haswell_128"):
		return 1
	elif(NodeType == "haswell_64"):
		return 2
	elif(NodeType == "fat"):
		return 3
	elif(NodeType == "haswell"):
		return 4
	elif(NodeType == "haswell_256"):
		return 5
	else:
		print "undefined node type"
	
def classtype2(NodeType):
	if(NodeType == "thin"):
		return 0
        elif(NodeType == "fat"):
		return 0
        elif(NodeType == "haswell"):
		return 0
	elif(NodeType == "haswell_128"):
		return 1
	elif(NodeType == "haswell_64"):
		return 1

def QCG_script_RC2(output_filename, multiscaleDoc, args, kernelNames, helpers, kernel_helpers, Plans):

	appId, project = getAppProjectId(multiscaleDoc)
	task_IDs, task_persistent,task_extension = getTasksAttributes(multiscaleDoc)



	args = []

	name = []
	exec_ = []
	Allcores = [] ## take inro account min and max (in plans later!!!!)
	Start = []
	End = []
	stdouts = []
	stderrs = []

	
	for i in tasks:
		task_IDs.append(i.attributes["taskId"].value)
	 
		try:
			task_persistent.append(i.attributes["persistent"].value)
		    
		except KeyError:
			task_persistent.append(None)
		
		try:
			task_extension.append(i.attributes["extension"].value)
		    
		except KeyError:
			task_extension.append(None)



	for tid in range(len(task_IDs)):
		cores = []

		kname = kernelNames[tid]+"_${it}"

		for i in range(0,len(Plans)):
			cores.append(Plans[i].getPlanScenario().getCores()[tid]);	
		
		## middleware
		tasks_temp = multiscaleDoc.getElementsByTagName("middleware")[0]
		executions = tasks_temp.getElementsByTagName("execution")
		workflows = tasks_temp.getElementsByTagName("workflow")
		


		execution_type   = executions[tid].attributes["type"].value
		application_name = executions[tid].getElementsByTagName("application")[0].attributes["name"].value
		arg = executions[tid].getElementsByTagName("arguments")[0]
		parametersSweeps = tasks_temp.getElementsByTagName("parametersSweep")[tid]
		
		application_args_tmp = []
		application_args = []
		for i in arg.getElementsByTagName("value"): 
	   		application_args_tmp.append( i )

		for i in range(0,len(application_args_tmp)):
	    		application_args.append(application_args_tmp[i].firstChild.nodeValue)

		start = parametersSweeps.getElementsByTagName("start")[0].firstChild.nodeValue
		end = parametersSweeps.getElementsByTagName("end")[0].firstChild.nodeValue

		
		stageInOutread   = executions[tid].getElementsByTagName("stageInOut")[0]
		for i in stageInOutread.getElementsByTagName("file"): 
	   		if i.attributes["name"].value == "stdout":
				stdout = i.getElementsByTagName("location")[0].firstChild.nodeValue
			elif i.attributes["name"].value == "stderr":
				stderr = i.getElementsByTagName("location")[0].firstChild.nodeValue
				

		name.append(kname)
		exec_.append(application_name)
		Allcores.append(cores)
		args.append(application_args)
		Start.append(start)
		End.append(end)
		stdouts.append(stdout)
		stderrs.append(stderr)
	
	
	jobs = []
	for i in range(0,len(name)):

		max_value = max(Allcores[i])
		min_value = min(Allcores[i])

		if (max_value == min_value):
			numcores  = OrderedDict({"exect" : max_value})
		else:
			numcores  = OrderedDict({"min" : min_value, "max" : max_value})


		resources = OrderedDict({"numCores" : numcores})
		execution = OrderedDict({"args" : args[i], "exec" : exec_[i], "stdout" : stdouts[i], "stderr" : stderrs[i]})

		
		t=OrderedDict({"execution" : execution, "name": name[i], "iterate": [Start[i],End[i]],  "resources" : resources})
		
		if(task_extension[i] is not None):
			dependency=OrderedDict({ "after" : [task_extension[i]] })
			t["dependencies"] = dependency
		
		jobs.append(t)
	
	dict1 = OrderedDict({"jobs" : jobs, "request" : "submit"})
	dict2 = OrderedDict({"command": "finishAfterAllTasksDone", "request": "control"})

	x = [dict1,dict2]

	with open(output_filename, 'w') as outfile:
		json.dump(x, outfile, sort_keys=False, indent=4)


def QCG_script_ES_mc(output_filename, multiscaleDoc, args, kernelNames, helpers, kernel_helpers, Plans):

	### Execution Parameters (get from multiscale.xml) #######

	app_id, project = getAppProjectId(multiscaleDoc)

	taskId, persistent, execution_type = getTaskAttributes(multiscaleDoc)
	application_name, application_args = getAppInfo(multiscaleDoc)


	stdout_url, stderr_url, stage_ins, stage_out = getInOut(multiscaleDoc)

	env_variables = getEnv(multiscaleDoc)

	#################################### Build QCG Script (Requirements) ############################################

	doc = minidom.Document()
	qcgJob = doc.createElement("qcgJob")

	qcgJob = setHeader(qcgJob, app_id, project)

	task = doc.createElement("task")
	task = setTask(task, persistent, taskId)


	if args.notifications:
		notifications = doc.createElement("notifications");
		consumer = doc.createElement("consumer");
		notifications, consumer = setNotification(notifications, consumer, args)

	requirements = doc.createElement("requirements")
	patternTopology = doc.createElement("multiCriteriaPatternTopology")
	kernels = doc.createElement("kernels")

	doc, kernels = addKernels(doc,kernels, kernelNames, kernel_helpers, helpers)

	plans = doc.createElement("plans");

	xx = len(Plans)
	for i in range(len(Plans)):
		plan = doc.createElement("plan");
		plan.setAttribute("id", Plans[i].getPlanName());

		costs = doc.createElement("costs");
		time = doc.createElement("time");
		energy = doc.createElement("energy");

		Time = timeConvert(Plans[i].getPlanScenario().getTotalTime())
		time.appendChild(doc.createTextNode(Time));
		energy.appendChild(doc.createTextNode( str(int(Plans[i].getPlanScenario().getTotalEnergy()) ) ));
		costs.appendChild(time);
		costs.appendChild(energy);

	
		group = doc.createElement("group");

		for j in range(0, len(kernelNames)):
			kernel = doc.createElement("kernel");
			kernel.setAttribute("refid", kernelNames[j]);

			node = doc.createElement("node");
			node.setAttribute("host", Plans[i].getPlanScenario().getHostName()[j]);
			node.appendChild(doc.createTextNode(str(Plans[i].getPlanScenario().getNodeType()[j])) );

			resources = doc.createElement("resources");
			cores = doc.createElement("cores");
			cores.appendChild(doc.createTextNode(str(Plans[i].getPlanScenario().getCores()[j])) );
			resources.appendChild(cores);

			kernel.appendChild(node);
			kernel.appendChild(resources);
			

			group.appendChild(kernel);
		

		plan.appendChild(costs);
		plan.appendChild(group)
		plans.appendChild(plan);

	patternTopology.appendChild(kernels);
	patternTopology.appendChild(plans);

	ter = [1,0,0] #array for time, energy and resources weight array
	max_t = 0
	max_e = 0
	max_E = 0

	total_t = []
	total_e = []
	total_E = []
	for j in xrange(0,len(Plans)):
		total_t.append( Plans[j].getPlanScenario().getTotalTime() )
		total_e.append( Plans[j].getPlanScenario().getTotalEnergy() )
		total_E.append( Plans[j].getPlanScenario().getNumberOfCores() * Plans[j].getPlanScenario().getTotalTime()/3600.)
		#print Plans[j].getPlanScenario().getNumberOfCores() , Plans[j].getPlanScenario().getTotalTime(), Plans[j].getPlanScenario().getNumberOfCores() * Plans[j].getPlanScenario().getTotalTime()

	if len(total_t) != 0 and len(total_e) != 0 and len(total_E):
		max_t = max(total_t)
		max_e = max(total_e)
		max_E = max(total_E)
	#print "max_E ", max_E
	
        if args.energy:
		ter[0] = 0
		ter[1] = 1

	if args.Resourceusage:
		ter[0] = 1
		ter[2] = 2
		
        decision = doc.createElement("decision");
	optimize = doc.createElement("optimize");
	
	deadline_t = doc.createElement("time");
	deadline_t.setAttribute("limit", timeConvert(max_t));
	deadline_t.appendChild(doc.createTextNode(str(ter[0])))

	if args.benchmark:
		deadline_t.setAttribute("predict", "false")

	deadline_e = doc.createElement("energy");
	deadline_e.setAttribute("limit", str(int(max_e)));
	deadline_e.appendChild(doc.createTextNode(str(ter[1])))

	deadline_r = doc.createElement("resources");
	deadline_r.setAttribute("limit", str(int(max_E)));
	deadline_r.appendChild(doc.createTextNode(str(ter[2])))
	
	optimize.appendChild(deadline_t);
	optimize.appendChild(deadline_e);
	optimize.appendChild(deadline_r);

	decision.appendChild(optimize);
	patternTopology.appendChild(decision)

	if args.reservation:
		patternTopology = setReservation(patternTopology, args)

	requirements.appendChild(patternTopology);

	#################################### Build QCG Script (Execution) ############################################

	execution = doc.createElement("execution");
	execution.setAttribute("type", execution_type);

	executable = doc.createElement("executable");
	application = doc.createElement("application");
	application.setAttribute("name", application_name);
	executable.appendChild(application);

	arguments = doc.createElement("arguments");
	value = doc.createElement("value");
	value.appendChild(doc.createTextNode(application_args));
	arguments.appendChild(value);

	stdout = doc.createElement("stdout");
	directory = doc.createElement("directory");
	location = doc.createElement("location");
	location.setAttribute("type", "URL");
        if args.benchmark or args.jobID:
		location.appendChild(doc.createTextNode(stdout_url+"/${JOB_ID}"));
	else:
		location.appendChild(doc.createTextNode(stdout_url));
	directory.appendChild(location);
	stdout.appendChild(directory);

	stderr = doc.createElement("stderr");
	directory = doc.createElement("directory");
	location = doc.createElement("location");
	location.setAttribute("type", "URL");
        if args.benchmark or args.jobID:
	        location.appendChild(doc.createTextNode(stderr_url+"/${JOB_ID}"));
	else:
		location.appendChild(doc.createTextNode(stderr_url));
	directory.appendChild(location);
	stderr.appendChild(directory);


	stageInOut = doc.createElement("stageInOut");

	for stageIn in stage_ins:
		file = doc.createElement("file");
		file.setAttribute("name", stageIn[0]);
		file.setAttribute("type", "in");
		location = doc.createElement("location");
		location.setAttribute("type", "URL");
		location.appendChild(doc.createTextNode(stageIn[1]));
		file.appendChild(location);
		stageInOut.appendChild(file);

	directory = doc.createElement("directory");
	directory.setAttribute("name", stage_out[0]);
	directory.setAttribute("type", "out");
	location = doc.createElement("location");
	location.setAttribute("type", "URL");
        if args.benchmark or args.jobID:
        	location.appendChild(doc.createTextNode(stage_out[1]+"/${JOB_ID}"));
	else:
		location.appendChild(doc.createTextNode(stage_out[1]));
	directory.appendChild(location);
	stageInOut.appendChild(directory);

	if args.benchmark or args.profile:
		directory = doc.createElement("directory");
		directory.setAttribute("name", "ArmResults");
		directory.setAttribute("type", "out");
		location = doc.createElement("location");
		location.setAttribute("type", "URL");
		location.appendChild(doc.createTextNode("gsiftp://qcg.man.poznan.pl//home/plgrid-groups/plggcompat/Common/ArmResults"));
		directory.appendChild(location);
		stageInOut.appendChild(directory);

	environment = doc.createElement("environment");

	for var in env_variables:
		env_var = doc.createElement("variable");
		env_var.setAttribute("name", var[0]);
		env_var.appendChild(doc.createTextNode(var[1]));
		environment.appendChild(env_var);

	execution.appendChild(executable);
	execution.appendChild(arguments);
	execution.appendChild(stdout);
	execution.appendChild(stderr);
	execution.appendChild(stageInOut);
	execution.appendChild(environment);

	#################################### last Build QCG Script ############################################

	if args.notifications:
		task.appendChild(notifications);

	task.appendChild(requirements);
	task.appendChild(execution);

	qcgJob.appendChild(task);

	doc.appendChild(qcgJob)


	writeXML(output_filename, doc)
	
	return

def getAppProjectId(multiscaleDoc):
	appId = multiscaleDoc.getElementsByTagName("job")[0].attributes["appID"].value
	project = multiscaleDoc.getElementsByTagName("job")[0].attributes["project"].value
	return appId, project

def getTaskAttributes(multiscaleDoc):
	task = multiscaleDoc.getElementsByTagName("task")[0];
	taskId = task.getAttribute("taskId")
	persistent = task.getAttribute("persistent")
	execution_type = multiscaleDoc.getElementsByTagName("execution")[0].attributes["type"].value;

	return taskId, persistent, execution_type

def getTasksAttributes(multiscaleDoc):
	multiscale_info = multiscaleDoc.getElementsByTagName('info')[0]
	tasks = multiscale_info.getElementsByTagName("task")

	task_IDs = []
	task_persistent = []
	task_extension  = []
	for i in tasks:
	    task_IDs.append(i.attributes["taskId"].value)
	    
	    try:
		task_persistent.append(i.attributes["persistent"].value) 
	    except KeyError:
		task_persistent.append(None)
		
	    try:
		task_extension.append(i.attributes["extension"].value)
	    except KeyError:
		task_extension.append(None)

	return task_IDs, task_persistent,task_extension

def getAppInfo(multiscaleDoc):
	application_name = multiscaleDoc.getElementsByTagName("application")[0].attributes["name"].value
	application_args = multiscaleDoc.getElementsByTagName("value")[0].firstChild.nodeValue
	return application_name, application_args

def getInOut(multiscaleDoc):
	stdout_node = minidom.parseString(multiscaleDoc.getElementsByTagName("stdout")[0].toxml());
	stderr_node = minidom.parseString(multiscaleDoc.getElementsByTagName("stderr")[0].toxml());

	stdout_url = stdout_node.getElementsByTagName("location")[0].firstChild.nodeValue;
	stderr_url = stderr_node.getElementsByTagName("location")[0].firstChild.nodeValue;

	stageIO_node = minidom.parseString(multiscaleDoc.getElementsByTagName("stageInOut")[0].toxml());

	stage_ins = [[i.attributes["name"].value, i.getElementsByTagName("location")[0].firstChild.nodeValue] for i in stageIO_node.getElementsByTagName("file")];
	stage_out = [[i.attributes["name"].value, i.getElementsByTagName("location")[0].firstChild.nodeValue] for i in stageIO_node.getElementsByTagName("directory")][0];

	return stdout_url, stderr_url, stage_ins, stage_out

def getEnv(multiscaleDoc):
	env_node = minidom.parseString(multiscaleDoc.getElementsByTagName("environment")[0].toxml());
	env_variables = [[i.attributes["name"].value, i.firstChild.nodeValue] for i in env_node.getElementsByTagName("variable")];
	return env_variables

def setHeader(qcgJob, app_id, project):
	qcgJob.setAttribute( "appId", app_id );
	qcgJob.setAttribute( "project", project );
	qcgJob.setAttribute( "xmlns:jxb", "http://java.sun.com/xml/ns/jaxb");
	qcgJob.setAttribute( "xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance");
	return qcgJob

def setTask(task, persistent, taskId):
	task.setAttribute("persistent", persistent)
	task.setAttribute("taskId", taskId)
	return task

def setNotification(notifications, consumer, args):
	noti = args.notifications
	noti = "mailto:"+noti
	consumer.appendChild(doc.createTextNode(noti))
	notifications.appendChild(consumer)
	return notifications, consumer


def addKernels(doc, kernels, kernelNames, kernel_helpers, helpers):
	for kname in kernelNames:
		kernel = doc.createElement("kernel");
		kernel.setAttribute("id", kname);
		kernels.appendChild(kernel);
	    
		if(kname in kernel_helpers):
			idx = kernel_helpers.index(kname)
			helpers = kernel_helpers[idx+1]
	    
		for h in helpers:
		    helper = doc.createElement("helper");
		    helper.setAttribute("id", h);
		    kernel.appendChild(helper)
	return doc, kernels

def setClasses(classes, doc):
	cc_host = ["supermuc","eagle","eagle","supermuc","supermuc-p2","eagle"]
	cc_type = ["thin","haswell_128","haswell_64","fat","haswell","haswell_256"] 

	for j in range(0,len(cc_host) ):
		Class = doc.createElement("class");
		Class.setAttribute("id", "c"+str(j));
		nnode = doc.createElement("node");
		nnode.setAttribute("host", cc_host[j] );
		nnode.appendChild(doc.createTextNode(cc_type[j]) );
		Class.appendChild(nnode);
		classes.appendChild(Class);

	return classes

def setReservation(patternTopology, args):
	hosts = doc.createElement("hosts");
	for z in range (0,len(args.reservation)):
		res = args.reservation[z]
		res = res.split(':')
		host = doc.createElement("host");
		reservation = doc.createElement("reservation");
		host.setAttribute("id", res[0]);
		reservation.appendChild(doc.createTextNode(res[2]) )
		host.appendChild(reservation)
		hosts.appendChild(host)
	patternTopology.appendChild(hosts);
	return patternTopology

def writeXML(output_filename, doc):
	f = open(output_filename, 'w');
	doc.writexml( f, indent="  ", addindent="  ", newl="\n")
	doc.unlink()
	return
