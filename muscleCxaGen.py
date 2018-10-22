from xml.dom import minidom
from xml.dom.minidom import Node

def generateCxaTemplate(dir_name, multiscaleDoc, submodels):
	application_name = multiscaleDoc.getElementsByTagName("application")[0].attributes["name"].value;
	if (application_name != "muscle2"):
		return

	multiscaleInstances = []
	kernel = []
	kernelClasses = []
	fromTo = []
	fromToTimes = []# how many connections between each models

	multiscale_topology = multiscaleDoc.getElementsByTagName("topology")[0]
	
	for i in multiscale_topology.getElementsByTagName("instance"):
		multiscaleInstances.append(i.attributes["id"].value)

	for i in submodels.getElementsByTagName("instance"):
		if (i.attributes["id"].value in multiscaleInstances):
			kernel.append(i.attributes["id"].value)
			kernelClasses.append(i.attributes["class"].value)

	for i in submodels.getElementsByTagName("mapper"):
		if (i.attributes["id"].value in multiscaleInstances):
		    	kernel.append(i.attributes["id"].value)
			kernelClasses.append("DuplicationMapper")

	##### for coupling

	for i in multiscale_topology.getElementsByTagName("coupling"):
		FromTo = []
		From=i.attributes["from"].value
		To=i.attributes["to"].value
		FromTo.append(From)
		FromTo.append(To)

		if(FromTo not in fromTo):
			fromTo.append(FromTo)
			fromToTimes.append(1)
		else:
			idx = fromTo.index(FromTo)
			fromToTimes[idx]= fromToTimes[idx]+1


	Template  = open(dir_name+"/Template.cxa.rb", "w")
	Template.write("\n")
	Template.write("# Check Muscle environment is loaded\n")
	Template.write("abort \"Run 'source [MUSCLE_HOME]/etc/muscle.profile' before this script\" if not ENV.has_key?('MUSCLE_HOME')\n")
	Template.write("\n \n")
	Template.write("# Define steps, input files, cxa properties, commands and parameters \n# You can do this using cxa.env['property']=value")
	Template.write("\ncxa = Cxa.LAST")
	Template.write("\n \n")
	Template.write("# Declare kernels\n")
	for i in range(0,len(kernel)):
		if(kernelClasses[i] != "DuplicationMapper"):
			Template.write("cxa.add_kernel('"+kernel[i]+"', 'muscle.core.standalone."+kernelClasses[i]+"')\n")
		else:
			Template.write("cxa.add_kernel('"+kernel[i]+"', 'muscle.core.kernel."+kernelClasses[i]+"')\n")

	Template.write("\n\n# Configure connection schema\n#In tie fill with the appropriate connection ports\n")
	Template.write("# Notice that if a submodel connects with mapper, then one tie argument is needed only!!!\n")
	Template.write("cs = cxa.cs\n")
	n = 0
	id_mappers = [i for i, x in enumerate(kernelClasses) if x == "DuplicationMapper"]

	for i in fromTo:
		Template.write("cs.attach('"+i[0]+"' => '"+i[1]+"') {\n")
		for j in range(0,fromToTimes[n]):
			if (n in id_mappers):
				Template.write("tie('   ')\n")
			else:
				Template.write("tie('   ', '   ')\n")

		Template.write("}\n")
		n = n + 1

	Template.write("\n")
	Template.write("\n")

	Template.close() 
