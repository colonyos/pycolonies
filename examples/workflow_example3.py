import sys
sys.path.append(".")
from colonies import Colonies
from colonies import create_func_spec
from colonies import Workflow
colonies = Colonies("localhost", 50080)

colonyid = "4787a5071856a4acf702b2ffcea422e3237a679c681314113d86139461290cf4"
executorid = "3fc05cf3df4b494e95d6a3d297a34f19938f7daa7422ab0d4f794454133341ac" 
executor_prvkey = "ddf7f7791208083b6a9ed975a72684f6406a269cfa36f1b1c32045c0a71fff05"

def map(ctx={}):
    code = """def gen_nums(ctx={}):
                return 1, 2""" 
  
    processgraphid = ctx["process"]["processgraphid"]
    map_processid = ctx["process"]["processid"]
    executor_prvkey = ctx["executor_prvkey"]
  
    processgraph = colonies.get_processgraph(processgraphid, executor_prvkey)
    reduce_process = colonies.find_process("reduce", processgraph["processids"], executor_prvkey)
    reduce_processid = reduce_process["processid"]

    insert = True
    for i in range(5):
        func_spec = create_func_spec(func="gen_nums", 
                                     args=[], 
                                     colonyid=ctx["colonyid"], 
                                     executortype="python_executor",
                                     priority=200,
                                     maxexectime=100,
                                     maxretries=3,
                                     maxwaittime=100,
                                     code=code)


        colonies.add_child(processgraphid, map_processid, reduce_processid, func_spec, "gen_nums_" + str(i), insert, executor_prvkey)
        insert = False

def reduce(*nums, ctx={}):
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

processgraph = colonies.submit(wf, executor_prvkey)
print("Workflow", processgraph["processgraphid"], "submitted")

# wait for the sum_list process
process = colonies.find_process("reduce", processgraph["processids"], executor_prvkey)
process = colonies.wait(process, 100, executor_prvkey)
print(process["out"][0])
