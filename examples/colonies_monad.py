from pycolonies import Colonies
from pycolonies import Workflow
from pycolonies import func_spec 
from typing import Union, Callable, Any

import copy

class Function:
    def __init__(self,
                 func: Union[Callable, str],
                 colonyname: str, 
                 executortype: str, 
                 priority: int = 0, 
                 maxexectime: int = 200, 
                 maxretries: int = 3,
                 maxwaittime: int = -1) -> None:
        self.func_spec = func_spec(func=func, 
                                   args=[], 
                                   colonyname=colonyname, 
                                   executortype=executortype,
                                   priority=priority,
                                   maxexectime=maxexectime,
                                   maxretries=maxretries,
                                   maxwaittime=maxwaittime)
        if isinstance(func, str):
            self.name = func 
        else:
            self.name = func.__name__ 


class ColoniesMonad:
    def __init__(self, 
                 colonies: Colonies, 
                 colonyname: str, 
                 executor_prvkey: str) -> None: 
        self.wf = Workflow(colonyname=colonyname)
        self.colonyname = colonyname
        self.executor_prvkey = executor_prvkey
        self.prev_func = None
        self.colonies = colonies 

    def __ror__(self, other: 'ColoniesMonad') -> None:
        del other
        pass

    def __rshift__(self, f: Function) -> 'ColoniesMonad':  # bind function
        if self.prev_func is None:
            self.wf.functionspecs.append(f.func_spec)
            self.prev_func = f.name
        else:
            fs = copy.deepcopy(f.func_spec)
            assert fs.conditions, "FunctionSpec must have conditions defined."
            fs.conditions.dependencies = [self.prev_func]
            self.wf.functionspecs.append(fs)
            self.prev_func = f.name
        
        return self

    def unwrap(self) -> Any:
        if self.prev_func is None:
            raise RuntimeError("Monad has no functions to execute.")
        
        processgraph = self.colonies.submit_workflow(self.wf, self.executor_prvkey)
        last_process = self.colonies.find_process(self.prev_func, processgraph.processids, self.executor_prvkey)

        if last_process is None:
            raise ValueError(f"Process {self.prev_func} not found in the process graph.")

        process = self.colonies.wait(last_process, 100, self.executor_prvkey)

        return process.output[0] if process.output else None
