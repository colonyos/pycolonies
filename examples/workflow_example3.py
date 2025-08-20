from pycolonies import colonies_client
from pycolonies import FuncSpec
from pycolonies import Workflow
from typing import Dict, Any

colonies, colonyname, colony_prvkey, executor_name, prvkey = colonies_client()

def map(ctx: Dict[str, Any] = {}) -> None:
    code = """def gen_nums(ctx={}):
                return 1, 2""" 
    processgraphid = ctx["process"].processgraphid
    map_processid = ctx["process"].processid
    executor_prvkey = ctx["executor_prvkey"]
  
    processgraph = colonies.get_processgraph(processgraphid, executor_prvkey)

    reduce_process = colonies.find_process("reduce", processgraph.processids, executor_prvkey)
    if reduce_process is None:
        raise RuntimeError("Could not find reduce process")
    reduce_processid = reduce_process.processid

    insert = True
    for i in range(1):
        f = FuncSpec.create(func="gen_nums", 
                            args=[], 
                            colonyname=ctx["colonyname"], 
                            executortype="python-executor",
                            priority=200,
                            maxexectime=100,
                            maxretries=3,
                            maxwaittime=100,
                            code=code)


        colonies.add_child(processgraphid, map_processid, reduce_processid, f, "gen_nums_" + str(i), insert, executor_prvkey)

        insert = False

def reduce(*nums: int, ctx: Dict[str, Any] = {}) -> int:
    del ctx
    print("REDUCED CALLED")
    total = 0
    for n in nums:
        total += n
    return total 

wf = Workflow(colonyname=colonyname)

f = FuncSpec.create(func=map, 
                    args=[], 
                    colonyname=colonyname, 
                    executortype="python-executor",
                    priority=200,
                    maxexectime=100,
                    maxretries=3,
                    maxwaittime=100)

wf.functionspecs.append(f)

f = FuncSpec.create(func=reduce, 
                    args=[], 
                    colonyname=colonyname, 
                    executortype="python-executor",
                    priority=200,
                    maxexectime=100,
                    maxretries=3,
                    maxwaittime=100)

assert f.conditions, "FunctionSpec must have conditions defined."

f.conditions.dependencies.append("map")
wf.functionspecs.append(f)

processgraph = colonies.submit_workflow(wf, prvkey)
print("Workflow", processgraph.processgraphid, "submitted")

# wait for the sum_list process
process = colonies.find_process("reduce", processgraph.processids, prvkey)
if process:
    completed_process = colonies.wait(process, 1000, prvkey)
    if completed_process and completed_process.output:
        print(completed_process.output[0])
