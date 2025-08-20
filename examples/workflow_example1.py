from pycolonies import colonies_client
from pycolonies import FuncSpec
from pycolonies import Workflow
from typing import Dict, Tuple, Any

colonies, colonyname, colony_prvkey, executor_name, prvkey = colonies_client()

def gen_nums(ctx: Dict[str, Any] = {}) -> Tuple[int, int]:
    return 1, 2 

def sum_nums(n1: int, n2: int, ctx: Dict[str, Any] = {}) -> int:
    return n1 + n2 

wf = Workflow(colonyname=colonyname)
f = FuncSpec.create(func=gen_nums,
                    args=[], 
                    colonyname=colonyname, 
                    executortype="python-executor",
                    priority=200,
                    maxexectime=100,
                    maxretries=3,
                    maxwaittime=100)

wf.functionspecs.append(f)

f = FuncSpec.create(func=sum_nums, 
                    args=[], 
                    colonyname=colonyname, 
                    executortype="python-executor",
                    priority=200,
                    maxexectime=100,
                    maxretries=3,
                    maxwaittime=100)

assert f.conditions

f.conditions.dependencies.append("gen_nums")

wf.functionspecs.append(f)

processgraph = colonies.submit_workflow(wf, prvkey)
print("Workflow", processgraph.processgraphid, "submitted")

# wait for the sum_list process
process = colonies.find_process("sum_nums", processgraph.processids, prvkey)
if process:
    completed_process = colonies.wait(process, 100, prvkey)
    if completed_process and completed_process.output:
        print(completed_process.output[0])
