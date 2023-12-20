from pycolonies import colonies_client
from colonies_monad import ColoniesMonad
from colonies_monad import Function

colonies, colonyname, colony_prvkey, executor_name, prvkey = colonies_client()

def gen_data(ctx={}):
    return 1, 2 

def process_data(*nums, ctx={}):
    total = 0
    for n in nums:
        total += n
    return total 

gen_data = Function(gen_data, colonyname, executortype="python-executor")
process_data = Function(process_data, colonyname, executortype="python-executor")
echo = Function("echo", colonyname, executortype="echo-executor")

m = ColoniesMonad(colonies, colonyname, prvkey)
result = (m >> gen_data >> process_data >> echo).unwrap()
print(result)  # prints 3 
