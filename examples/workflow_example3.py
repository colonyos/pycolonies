from pycolonies import colonies_client
from pycolonies import func_spec
from pycolonies import Workflow

colonies, colonyname, colony_prvkey, executor_name, prvkey = colonies_client()

def map(ctx={}):
    code = """def gen_nums(ctx={}):
                return 1, 2""" 
    processgraphid = ctx["process"].processgraphid
    map_processid = ctx["process"].processid
    executor_prvkey = ctx["executor_prvkey"]
  
    processgraph = colonies.get_processgraph(processgraphid, executor_prvkey)

    reduce_process = colonies.find_process("reduce", processgraph.processids, executor_prvkey)
    reduce_processid = reduce_process.processid

    insert = True
    for i in range(1):
        f = func_spec(func="gen_nums", 
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

def reduce(*nums, ctx={}):
    print("REDUCED CALLED")
    total = 0
    for n in nums:
        total += n
    return total 

wf = Workflow(colonyname=colonyname)

f = func_spec(func=map, 
              args=[], 
              colonyname=colonyname, 
              executortype="python-executor",
              priority=200,
              maxexectime=100,
              maxretries=3,
              maxwaittime=100)

wf.functionspecs.append(f)

f = func_spec(func=reduce, 
              args=[], 
              colonyname=colonyname, 
              executortype="python-executor",
              priority=200,
              maxexectime=100,
              maxretries=3,
              maxwaittime=100)

f.conditions.dependencies.append("map")
wf.functionspecs.append(f)

processgraph = colonies.submit_workflow(wf, prvkey)
print("Workflow", processgraph.processgraphid, "submitted")

# wait for the sum_list process
process = colonies.find_process("reduce", processgraph.processids, prvkey)
process = colonies.wait(process, 1000, prvkey)
print(process.output[0])
