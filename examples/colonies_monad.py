import sys
sys.path.append(".")
from colonies import Colonies
from colonies import Workflow

class ColoniesMonad:
    def __init__(self, host, port, colonyid, executor_prvkey):
        self.wf = Workflow(colonyid)
        self.colonyid = colonyid
        self.executor_prvkey = executor_prvkey
        self.prev_func = None
        self.colonies = Colonies(host, port)

    def __rshift__(self, func):  # bind function
        func_spec = self.colonies.create_func_spec(func=func, 
                                                   args=[], 
                                                   colonyid=self.colonyid, 
                                                   executortype="python_executor",
                                                   priority=200,
                                                   maxexectime=100,
                                                   maxretries=3,
                                                   maxwaittime=100)
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
