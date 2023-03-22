import sys
sys.path.append(".")
from colonies import Colonies
from colonies import Workflow
from colonies_monad import ColoniesMonad
from colonies_monad import Function

colonyid = "4787a5071856a4acf702b2ffcea422e3237a679c681314113d86139461290cf4"
executorid = "3fc05cf3df4b494e95d6a3d297a34f19938f7daa7422ab0d4f794454133341ac" 
executor_prvkey = "ddf7f7791208083b6a9ed975a72684f6406a269cfa36f1b1c32045c0a71fff05"

def gen_data(ctx={}):
    return 1, 2 

def process_data(*nums, ctx={}):
    total = 0
    for n in nums:
        total += n
    return total 

def print_result(total, ctx={}):
    print("total=", total)
    return total

gen_data_fn = Function(gen_data, colonyid, executortype="python_executor")
process_data_fn = Function(process_data, colonyid, executortype="python_executor")
print_fn = Function(print_result, colonyid, executortype="python_executor")

m = ColoniesMonad("localhost", 50080, colonyid, executor_prvkey)
(m >> gen_data_fn >>  process_data_fn >> print_fn).unwrap()
