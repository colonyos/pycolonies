from pycolonies import colonies_client
from pycolonies import func_spec

colonies, colonyname, colony_prvkey, executor_name, prvkey = colonies_client()

def sum_nums(n1, n2, ctx={}):
    return n1 + n2

func_spec = func_spec(func=sum_nums, 
                      args=[1, 2], 
                      colonyname=colonyname, 
                      executortype="python-executor",
                      priority=200,
                      maxexectime=10,
                      maxretries=3,
                      maxwaittime=100)

# submit the function spec to the colonies server
process = colonies.submit_func_spec(func_spec, prvkey)
print("Process", process.processid, "submitted")

# wait for the process to be executed
process = colonies.wait(process, 100, prvkey)
print(process.output[0])
