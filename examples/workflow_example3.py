import sys
sys.path.append(".")
from colonies import Colonies
from colonies import Workflow
from utils import create_func_spec
from utils import formatargs

client = Colonies("localhost", 50080)

colonyid = "4787a5071856a4acf702b2ffcea422e3237a679c681314113d86139461290cf4"
executorid = "3fc05cf3df4b494e95d6a3d297a34f19938f7daa7422ab0d4f794454133341ac" 
executor_prvkey = "ddf7f7791208083b6a9ed975a72684f6406a269cfa36f1b1c32045c0a71fff05"

def map():
    print(client)
    return 1, 2 

def reduce(*nums):
    total = 0
    for n in nums:
        total += n
    return total 

wf = Workflow(colonyid)
func_spec = create_func_spec(func=map, 
                             args=[], 
                             colonyid=colonyid, 
                             executortype="python_executor",
                             priority=200,
                             maxexectime=100,
                             maxretries=3,
                             maxwaittime=100)
wf.add(func_spec, nodename="map", dependencies=[])

func_spec = create_func_spec(func=reduce, 
                             args=[], 
                             colonyid=colonyid, 
                             executortype="python_executor",
                             priority=200,
                             maxexectime=100,
                             maxretries=3,
                             maxwaittime=100) 
wf.add(func_spec, nodename="reduce", dependencies=["map"])

processgraph = client.submit(wf, executor_prvkey)

# wait for the sum_list process
process = client.find_process("reduce", processgraph["processids"], executor_prvkey)
process = client.wait(process, 100, executor_prvkey)
print(process["out"][0])
