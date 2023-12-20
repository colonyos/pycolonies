from pycolonies import colonies_client
from pycolonies import func_spec
from pycolonies import Workflow
import copy

colonies, colonyname, colony_prvkey, executorid, executor_prvkey = colonies_client()

func_spec = func_spec(func="helloworld", 
                      args=[], 
                      colonyname=colonyname, 
                      executortype="helloworld-executor",
                      maxexectime=10,
                      maxretries=3,
                      maxwaittime=100)

wf = Workflow(colonyname)
wf.add(func_spec, nodename="hello1", dependencies=[])
wf.add(copy.deepcopy(func_spec), nodename="hello2", dependencies=["hello1"])
wf.add(copy.deepcopy(func_spec), nodename="hello3", dependencies=["hello1"])

colonies.submit(wf, executor_prvkey)
