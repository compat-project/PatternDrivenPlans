class plan:
    def __init__(self, planName, planScenario):
        self.planName = planName
        self.planScenario = planScenario

    def getPlanName(self):
        return self.planName
        
    def getPlanScenario(self):
        return self.planScenario
	
def getBestPlans(scenarios, numberOfPlans):

	if(numberOfPlans == -1):
		numberOfPlans = len(scenarios)

	numberOfPlans = min(numberOfPlans, len(scenarios))
	plans = []
	x = 0
	for i in range(0,numberOfPlans):
		s = scenarios[i]
		p = plan("plan"+str(x), s)
		plans.append(p)
		x=x+1

	return plans

def getBestPlansB(scenarios, numberOfPlans, timeLimit):

	if(numberOfPlans == -1):
		numberOfPlans = len(scenarios)

	numberOfPlans = min(numberOfPlans, len(scenarios))
	plans = []
	x = 0
	for i in range(0,numberOfPlans):
		s = scenarios[i]
		s.setTotalTime(s.getTotalTime() + timeLimit)
		p = plan("plan"+str(x), s)
		plans.append(p)
		x=x+1

	return plans
		

def printPlans(Plans):
	print "name \t time \t cores per submodel \t Energy \t Time per submodel \t Node type \t\t Resource Usage"
	for i in range(0,len(Plans)):
		l = [round(x,2) for x in Plans[i].getPlanScenario().getSubmodelsTimes()]
		print Plans[i].getPlanName(), "\t", round(float(Plans[i].getPlanScenario().getTotalTime()),2) ,"\t", Plans[i].getPlanScenario().getCores(),"\t", round(float(Plans[i].getPlanScenario().getTotalEnergy()),2), "\t", l, "\t", Plans[i].getPlanScenario().getNodeType(),"\t", round(float(Plans[i].getPlanScenario().getResourceUsage())/3600.,2)
