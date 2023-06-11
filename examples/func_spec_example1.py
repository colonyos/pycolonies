from pycolonies import Colonies
from pycolonies import func_spec

colonies = Colonies("localhost", 50080)

colonyid = "4787a5071856a4acf702b2ffcea422e3237a679c681314113d86139461290cf4"
executorid = "3fc05cf3df4b494e95d6a3d297a34f19938f7daa7422ab0d4f794454133341ac" 
executor_prvkey = "ddf7f7791208083b6a9ed975a72684f6406a269cfa36f1b1c32045c0a71fff05"

def sum_nums(n1, n2, ctx={}):
    import time
    time.sleep(20)
    return n1 + n2

func_spec = func_spec(func=sum_nums, 
                      args=[1, 2], 
                      colonyid=colonyid, 
                      executortype="python",
                      priority=200,
                      maxexectime=10,
                      maxretries=3,
                      maxwaittime=100)

# submit the function spec to the colonies server
process = colonies.submit(func_spec, executor_prvkey)
print("Process", process["processid"], "submitted")

# wait for the process to be executed
process = colonies.wait(process, 100, executor_prvkey)
print(process["out"][0])
