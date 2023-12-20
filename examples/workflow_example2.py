from pycolonies import colonies_client
from pycolonies import func_spec
from pycolonies import Workflow

colonies, colonyname, colony_prvkey, executor_name, prvkey = colonies_client()

def gen_nums(ctx={}):
    return 1, 2 

def reduce(*nums, ctx={}):
    total = 0
    for n in nums:
        total += n
    return total 

wf = Workflow(colonyname)
f = func_spec(func=gen_nums, 
              args=[], 
              colonyname=colonyname, 
              executortype="python-executor",
              priority=200,
              maxexectime=100,
              maxretries=3,
              maxwaittime=100)
wf.add(f, nodename="gen_nums1", dependencies=[])

f = func_spec(func=gen_nums, 
              args=[], 
              colonyname=colonyname, 
              executortype="python-executor",
              priority=200,
              maxexectime=100,
              maxretries=3,
              maxwaittime=100)
wf.add(f, nodename="gen_nums2", dependencies=[])

func_spec = func_spec(func=reduce, 
                             args=[], 
                             colonyname=colonyname, 
                             executortype="python-executor",
                             priority=200,
                             maxexectime=100,
                             maxretries=3,
                             maxwaittime=100) 
wf.add(func_spec, nodename="reduce", dependencies=["gen_nums1", "gen_nums2"])

processgraph = colonies.submit(wf, prvkey)
print("Workflow", processgraph["processgraphid"], "submitted")

# wait for the sum_list process
process = colonies.find_process("reduce", processgraph["processids"], prvkey)
process = colonies.wait(process, 100, prvkey)
print(process["out"][0])
