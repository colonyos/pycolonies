import sys
sys.path.append(".")
from colonies import Colonies
from colonies import create_func_spec
from colonies import Workflow

class ColoniesMonad:
    def __init__(self, 
                 host, 
                 port, 
                 colonyid, 
                 executor_prvkey, 
                 executor="python_executor", 
                 priority=0, 
                 maxexectime=200, 
                 maxretries=3,
                 maxwaittime=-1):
        self.wf = Workflow(colonyid)
        self.colonyid = colonyid
        self.executor_prvkey = executor_prvkey
        self.executor=executor
        self.priority = priority
        self.maxexectime = maxexectime
        self.maxretries = maxretries
        self.maxwaittime = maxwaittime
        self.prev_func = None
        self.colonies = Colonies(host, port)

    def __rshift__(self, func):  # bind function
        func_spec =create_func_spec(func=func, 
                                    args=[], 
                                    colonyid=self.colonyid, 
                                    executortype=self.executor,
                                    priority=self.priority,
                                    maxexectime=self.maxexectime,
                                    maxretries=self.maxretries,
                                    maxwaittime=self.maxwaittime)
        if self.prev_func is None:
            self.wf.add(func_spec, nodename=func.__name__, dependencies=[])
            self.prev_func = func.__name__
        else:
            self.wf.add(func_spec, nodename=func.__name__, dependencies=[self.prev_func])
            self.prev_func = func.__name__
        
        return self

    def unwrap(self):
        processgraph = self.colonies.submit(self.wf, self.executor_prvkey)
        last_process = self.colonies.find_process(self.prev_func, processgraph["processids"], self.executor_prvkey)
        process = self.colonies.wait(last_process, 100, self.executor_prvkey)
        return process["out"][0]
