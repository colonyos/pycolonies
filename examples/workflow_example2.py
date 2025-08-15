from pycolonies import colonies_client
from pycolonies import func_spec
from pycolonies import Workflow
from typing import Dict, Tuple, Any

colonies, colonyname, colony_prvkey, executor_name, prvkey = colonies_client()

def gen_nums(ctx: Dict[str, Any] = {}) -> Tuple[int, int]:
    return 1, 2 

def reduce(*nums: int, ctx: Dict[str, Any] = {}) -> int:
    total = 0
    for n in nums:
        total += n
    return total 

wf = Workflow(colonyname=colonyname)
f = func_spec(func=gen_nums, 
              args=[], 
              colonyname=colonyname, 
              executortype="python-executor",
              priority=200,
              maxexectime=100,
              maxretries=3,
              maxwaittime=100)

f.nodename = "gen_nums1"
wf.functionspecs.append(f)

f = func_spec(func=gen_nums, 
              args=[], 
              colonyname=colonyname, 
              executortype="python-executor",
              priority=200,
              maxexectime=100,
              maxretries=3,
              maxwaittime=100)

f.nodename = "gen_nums2"
wf.functionspecs.append(f)

func_spec = func_spec(func=reduce, 
                             args=[], 
                             colonyname=colonyname, 
                             executortype="python-executor",
                             priority=200,
                             maxexectime=100,
                             maxretries=3,
                             maxwaittime=100) 

func_spec.conditions.dependencies = ["gen_nums1", "gen_nums2"]
wf.functionspecs.append(func_spec)

processgraph = colonies.submit_workflow(wf, prvkey)
print("Workflow", processgraph.processgraphid, "submitted")

# wait for the sum_list process
process = colonies.find_process("reduce", processgraph.processids, prvkey)
if process:
    completed_process = colonies.wait(process, 100, prvkey)
    if completed_process and completed_process.output:
        print(completed_process.output[0])
