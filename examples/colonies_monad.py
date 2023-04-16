from pycolonies import Colonies
from pycolonies import Workflow
from pycolonies import create_func_spec 

class Function:
    def __init__(self,
                 func,
                 colonyid, 
                 executortype, 
                 priority=0, 
                 maxexectime=200, 
                 maxretries=3,
                 maxwaittime=-1):
        self.func_spec = create_func_spec(func=func, 
                                          args=[], 
                                          colonyid=colonyid, 
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
                 host, 
                 port, 
                 colonyid, 
                 executor_prvkey): 
        self.wf = Workflow(colonyid)
        self.colonyid = colonyid
        self.executor_prvkey = executor_prvkey
        self.prev_func = None
        self.colonies = Colonies(host, port)

    def __ror__(self, other):
        pass

    def __rshift__(self, f):  # bind function
        if self.prev_func is None:
            self.wf.add(f.func_spec, nodename=f.name, dependencies=[])
            self.prev_func = f.name
        else:
            self.wf.add(f.func_spec, nodename=f.name, dependencies=[self.prev_func])
            self.prev_func = f.name
        
        return self

    def unwrap(self):
        processgraph = self.colonies.submit(self.wf, self.executor_prvkey)
        last_process = self.colonies.find_process(self.prev_func, processgraph["processids"], self.executor_prvkey)
        process = self.colonies.wait(last_process, 100, self.executor_prvkey)

        if len(process["out"])>0:
            return process["out"][0]
        return ""
