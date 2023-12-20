from pycolonies import func_spec
from pycolonies import colonies_client

colonies, colonyname, colony_prvkey, executor_name, prvkey = colonies_client()

func_spec = func_spec(func="helloworld", 
                      args=[], 
                      colonyname=colonyname, 
                      executortype="helloworld-executor",
                      priority=200,
                      maxexectime=10,
                      maxretries=3,
                      maxwaittime=100)

# submit the function spec to the colonies server
process = colonies.submit(func_spec, prvkey)
print("Process", process["processid"], "submitted")

# wait for the process to be executed
process = colonies.wait(process, 10, prvkey)
print(process["out"][0])
