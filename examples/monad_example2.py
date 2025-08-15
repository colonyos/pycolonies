from pycolonies import colonies_client
from colonies_monad import ColoniesMonad
from colonies_monad import Function
from typing import Dict, Tuple, Any

colonies, colonyname, colony_prvkey, executor_name, prvkey = colonies_client()

def gen_data(ctx: Dict[str, Any] = {}) -> Tuple[int, int]:
    return 1, 2 

def process_data(*nums: int, ctx: Dict[str, Any] = {}) -> int:
    total = 0
    for n in nums:
        total += n
    return total 

gen_data_fn = Function(gen_data, colonyname, executortype="python-executor")
process_data_fn = Function(process_data, colonyname, executortype="python-executor")
echo = Function("echo", colonyname, executortype="echo-executor")

m = ColoniesMonad(colonies, colonyname, prvkey)
result = (m >> gen_data_fn >> process_data_fn >> echo).unwrap()
print(result)  # prints 3 
