from pycolonies import colonies_client
from pycolonies import func_spec
from pycolonies import Workflow

colonies, colonyname, colony_prvkey, executorid, executor_prvkey = colonies_client()

fs1 = func_spec(func="hello1", 
                      args=[], 
                      colonyname=colonyname, 
                      executortype="helloworld-executor",
                      maxexectime=10,
                      maxretries=3,
                      maxwaittime=100)

fs2 = func_spec(func="hello2", 
                      args=[], 
                      colonyname=colonyname, 
                      executortype="helloworld-executor",
                      maxexectime=10,
                      maxretries=3,
                      maxwaittime=100)

fs3 = func_spec(func="hello3", 
                      args=[], 
                      colonyname=colonyname, 
                      executortype="helloworld-executor",
                      maxexectime=10,
                      maxretries=3,
                      maxwaittime=100)

assert fs2.conditions is not None
assert fs3.conditions is not None

fs2.conditions.dependencies.append("hello1")
fs3.conditions.dependencies.append("hello2")

wf = Workflow(colonyname=colonyname, functionspecs=[fs1, fs2, fs3])

colonies.submit_workflow(wf, executor_prvkey)
