from xml.dom import minidom
import random, sys, getopt, heapq, os.path
import numpy as np

#Greedy algo and sweet spot calculation
#numberOfNodes for resource usage calculations
def getBestClassAndCores(submodels, classNames):
    numSubModels = len(submodels);
    best_resources = [];
    for i in range(numSubModels): # here to do mathematical calculation for the whole multiscale model
        sm = submodels[i];
        resources = minidom.parseString(sm.toxml()).getElementsByTagName('resources');
        
        minWallClockTimes = [];
        cores = [];
        names=[]; #temporarly here, to be modified
        nodetypes=[]; # the same
        for j in range(len(resources)):
            resource = resources[j];
            for k in range(0,len(resource.getElementsByTagName('nodeType'))):
                numCores = [x.firstChild.nodeValue.split(';') for x in resource.getElementsByTagName('numberOfCores')];
                numCores = [int(x) for x in numCores[k]];
                
                wallClockTime = [x.firstChild.nodeValue.split(';') for x in resource.getElementsByTagName('wallClockTime')];
                wallClockTime = [float(x) for x in wallClockTime[k]];
                
                numberOfNodes= [x.firstChild.nodeValue.split(';') for x in resource.getElementsByTagName('numberOfNodes')];
                numberOfNodes= [int(x) for x in numberOfNodes[k]];
                
                minWallClockTime = min(wallClockTime);
                idx = wallClockTime.index(minWallClockTime);
                
                minWallClockTimes.append(minWallClockTime);
                cores.append(numCores[idx]);
                names.append(resource.attributes["name"].value)
                nodetypes.append(resource.getElementsByTagName('nodeType')[k].firstChild.nodeValue);
            
        #Get the node with minimum wall clock time per all node types
        
        minWallClockTime = min(minWallClockTimes);
        idx = minWallClockTimes.index(minWallClockTime);
        
        
        best_node_name = names[idx];
        best_node_type = nodetypes[idx];
        print best_node_name, best_node_type, cores[idx]
        #class names are not static, so think of this :'(
        
        best_resource = [[findClassName(best_node_name, best_node_type, classNames), best_node_name, best_node_type], str(cores[idx])];
        best_resources.append(best_resource);
        #best_resources = [[classNames[0],1024], [classNames[0],2048], [classNames[0],512] ] #best now is per plan and static for fusion
    return best_resources;

# <codecell>

def findClassName(best_node_name, best_node_type, classNames):

	for i in classNames:
		print "in func", best_node_name, best_node_type
		print "in func", i[1], i[2]
		if (i[1] == best_node_name.strip()) and (i[2] == best_node_type.strip()):
			return i[0];
	raise Exception("No matching class found");

# <codecell>


############################################################################ Start Here #########################################

output_filename = "out.xml";
multiscaleDoc = minidom.parse("multiscale.xml");
matrixDoc = minidom.parse("matrix.xml");


# no min max
#multiscale_min_cores = int(multiscaleDoc.getElementsByTagName('min')[0].firstChild.nodeValue);
#multiscale_max_cores = int(multiscaleDoc.getElementsByTagName('max')[0].firstChild.nodeValue);


#output_filename = "qcg_bac.xml";


#################################### Requirements (get from matrix.xml) ############################################

# becasue now we have <performance>

multiscale_topology = multiscaleDoc.getElementsByTagName("topology")[0]

kernelNames = []

# no helpers
#helpers = []
#kernel_helpers= [] # to be generilised

for i in multiscale_topology.getElementsByTagName('instance'):
    if (i.attributes.values()[1].name == 'submodel'):
        kernelNames.append(i.attributes.values()[0].value)


print kernelNames

submodels_all = matrixDoc.getElementsByTagName('submodels')[0]

submodels = []
for i in submodels_all.getElementsByTagName("submodel"):
    instances = i.getElementsByTagName("instance")
    for instance in instances:
        if (instance.attributes["name"].value in kernelNames):
            submodels.append(i)
            
            

kernel_minCores = [int(i.firstChild.nodeValue) for i in matrixDoc.getElementsByTagName('min_cores')];
kernel_maxCores = [int(i.firstChild.nodeValue) for i in matrixDoc.getElementsByTagName('max_cores')];


print " ============ Pattern Service Demo v0.1 ========"
print "** In this submodel the kernels are", kernelNames, "**"
print "** In this multiscle run min number of cores per submodel is", kernel_minCores, "**"
print "** In this multiscle run max number of cores per submodel is", kernel_maxCores, "**"



resources = [i for i in submodels_all.getElementsByTagName('available_resources')];

resource_pairs = []
for resource_list in resources:
    for i in resource_list.getElementsByTagName('resource'):
        resource_pairs.append([i.attributes["name"].value, i.attributes["nodeType"].value])
        
unique_resources = list(set(map(tuple, resource_pairs)));
unique_resources = [list(i) for i in unique_resources];


classNames = []
for i in range(0,1): # static (for now) number of classes
    Class = []
    if (i == 0):
        Class = ["c"+str(i+1), unique_resources[1][0], unique_resources[1][1]]
    #elif (i == 1):
        #Class = ["c"+str(i+1), unique_resources[0][0], unique_resources[0][1]]
    
    classNames.append(Class);
print classNames

submodels_all = matrixDoc.getElementsByTagName('performance')[0]
#submodels_performance = [i for i in submodels_all.getElementsByTagName("submodel")]

submodels_performance = []
for i in submodels_all.getElementsByTagName("submodel"):
    instances = i.getElementsByTagName("instance")
    for instance in instances:
        if (instance.attributes["name"].value in kernelNames):
            submodels_performance.append(i)


# <codecell>

best = getBestClassAndCores(submodels_performance, classNames);
print best

# <codecell>



# fabricated plan (for now, for fusion)
planNames = [ 
				["plan1", "PT3H0M"],
			];

#print(best);
#

# in replica here the plan gruops per kernel (not like ES)
planGroups = [ 
				[ [ kernelNames[0], str(best[0][0][0]), str(best[0][1])] ],

				[ [ kernelNames[1], str(best[0][0][0]), str(best[1][1])] ]
			 ]

# <codecell>

#################################### Execution Parameters (get from multiscale.xml) ############################################

appId = multiscaleDoc.getElementsByTagName("job")[0].attributes["appID"].value;
#appId = "bac-compat";

project = multiscaleDoc.getElementsByTagName("job")[0].attributes["project"].value;

#execution_type = multiscaleDoc.getElementsByTagName("execution")[0].attributes["type"].value;

#application_name = multiscaleDoc.getElementsByTagName("application")[0].attributes["name"].value;

#application_version = multiscaleDoc.getElementsByTagName("application")[0].attributes["version"].value;

#application_args = multiscaleDoc.getElementsByTagName("value")[0].firstChild.nodeValue;

multiscale_info = multiscaleDoc.getElementsByTagName('info')[0]

tasks = multiscale_info.getElementsByTagName("task")

task_IDs = []
task_persistent = []
task_extension  = []
for i in tasks:
    task_IDs.append(i.attributes["taskId"].value)
    
    #if ( i.attributes["persistent"].value != None):
    try:
        task_persistent.append(i.attributes["persistent"].value)
    
    except KeyError:
        task_persistent.append(None)
        
    try:
        task_extension.append(i.attributes["extension"].value)
    
    except KeyError:
        task_extension.append(None)
        

#task_IDs = ["RC-task-1", "amber"];
#task_persistent = ["true", None];
#task_extension = [None, "namd_${PS_rep}"];

# <codecell>

doc = minidom.Document()
qcgJob = doc.createElement("qcgJob");
qcgJob.setAttribute( "appId", appId );
qcgJob.setAttribute( "project", project );
qcgJob.setAttribute( "xmlns:jxb", "http://java.sun.com/xml/ns/jaxb");
qcgJob.setAttribute( "xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance");
qcgJob.setAttribute( "xsi:noNamespaceSchemaLocation", ".");

t = -1
#Iterate over number of tasks
for tid in range(len(task_IDs)):
	t += 1

	task = doc.createElement("task");
	task.setAttribute("taskId", task_IDs[tid]);

	if(task_persistent[tid] is not None):
		task.setAttribute("persistent", task_persistent[tid]);

	if(task_extension[tid] is not None):
		task.setAttribute("extension", task_extension[tid]);		
	
	requirements = doc.createElement("requirements");

	patternTopology = doc.createElement("patternTopology");

	kernels = doc.createElement("kernels");

	kname = kernelNames[tid]
	kernel = doc.createElement("kernel");
	kernel.setAttribute("id", kname);
	kernels.appendChild(kernel);

	
	classes = doc.createElement("classes");

	for cname in classNames:
		c = doc.createElement("class");
		c.setAttribute("id", cname[0]);
		n = doc.createElement("node");
		n.setAttribute("host", cname[1]);
		n.appendChild(doc.createTextNode(cname[2]));
		c.appendChild(n);
		classes.appendChild(c);

	
	plans = doc.createElement("plans");

	#Plans in a task
	plan_group = planGroups[tid];

	#Iterate over number of plans in a task
	for i in range(len(plan_group)):
		plan = doc.createElement("plan");
		plan.setAttribute("id", planNames[0][0]);

		criteria = doc.createElement("criteria");
		time = doc.createElement("time");
		time.appendChild(doc.createTextNode(planNames[0][1]));
		criteria.appendChild(time);
		
		group = doc.createElement("group");

		#Iterate over number of 
		kernel = doc.createElement("kernel");
		kernel.setAttribute("refid", plan_group[i][0]);
		kernel.appendChild(doc.createTextNode(''));

		c = doc.createElement("class");
		c.setAttribute("refid", plan_group[i][1]);

		cores = doc.createElement("cores");
		cores.appendChild(doc.createTextNode(plan_group[i][2]));

		c.appendChild(cores);

		kernel.appendChild(c);
		group.appendChild(kernel);
		

		plan.appendChild(criteria);
		plan.appendChild(group)
		plans.appendChild(plan);

	patternTopology.appendChild(kernels); #Add kernels to task
	patternTopology.appendChild(classes); #Add classes to task
	patternTopology.appendChild(plans);

	requirements.appendChild(patternTopology);
	requirements.appendChild(doc.createTextNode(''));
	task.appendChild(requirements);
	qcgJob.appendChild(task);



	## middleware
	tasks = multiscaleDoc.getElementsByTagName("middleware")[0]
	executions = tasks.getElementsByTagName("execution")
	execution_type   = executions[t].attributes["type"].value

	application_name = executions[t].getElementsByTagName("application")[0].attributes["name"].value
	args = executions[t].getElementsByTagName("arguments")[0] # the second 0 no need in the main loop

	len_arg = 0
	application_args = []
	for i in args.getElementsByTagName("value"): 
   		application_args.append( i )
   		len_arg += 1


	execution = doc.createElement("execution");
	execution.setAttribute("type", execution_type);

	executable = doc.createElement("executable");
	application = doc.createElement("application");
	application.setAttribute("name", application_name);
	executable.appendChild(application);

	arguments = doc.createElement("arguments");
	value = doc.createElement("value");

	for i in range(0,len_arg):
    		value.appendChild(application_args[i]);
    		arguments.appendChild(value);

	stageInOutread = executions[t].getElementsByTagName("stageInOut")[0] # the second 0 no need in the main loop

	stageInOut = doc.createElement("stageInOut");
	stageInOut.appendChild(stageInOutread)

	execution.appendChild(executable);
	execution.appendChild(arguments);
	execution.appendChild(stageInOut);
	task.appendChild(requirements);
	task.appendChild(execution);

#################################### Build QCG Script (Execution Time) ############################################

#executionTime = doc.createElement("executionTime");
#executionDuration = doc.createElement("executionDuration");
#executionDuration.appendChild(doc.createTextNode(executionDuration_str));
#executionTime.appendChild(executionDuration);


#task.appendChild(requirements);
#task.appendChild(execution);
#task.appendChild(executionTime);
#task.appendChild(doc.createTextNode(''));

qcgJob.appendChild(task);
#qcgJob.appendChild(doc.createTextNode(''));

doc.appendChild(qcgJob)


f = open(output_filename, 'w');

doc.writexml( f, indent=" ", addindent=" ", newl="\n")

doc.unlink();

