from pycolonies import Crypto
from pycolonies import colonies_client
import signal
import os
import uuid 

class PythonExecutor:
    def __init__(self):
        colonies, colonyname, colony_prvkey, _, _ = colonies_client()
        self.colonyname = colonyname
        self.colonies = colonies
        self.colony_prvkey = colony_prvkey

        crypto = Crypto()
        self.executor_prvkey = crypto.prvkey()
        self.executorid = crypto.id(self.executor_prvkey)

        self.register()
        
    def register(self):
        executor = {
            "executorname": "echo-executor",
            "executorid": self.executorid,
            "colonyname": self.colonyname,
            "executortype": "echo-executor"
        }
       
        self.executorname = executor["executorname"]

        try:
            self.colonies.add_executor(executor, self.colony_prvkey)
            self.colonies.approve_executor(self.colonyname, executor["executorname"], self.colony_prvkey)
        except Exception as err:
            print(err)
        print("Executor", self.executorname, "registered")
        
        try:
            self.colonies.add_function(self.colonyname,
                                       self.executorname, 
                                       "echo",  
                                       self.executor_prvkey)
            
        except Exception as err:
            print(err)
   
    def start(self):
        while (True):
            try:
                process = self.colonies.assign(self.colonyname, 10, self.executor_prvkey)
                print("Process", process.processid, "is assigned to executor")
                if process.spec.funcname == "echo":
                    # if "in" is defined, it is the output of the parent process,
                    # use the output from parent process instead of args
                    if len(process.input)>0:
                        args = process.input
                    else:
                        args = process.spec.args

                    # just set output to input value 
                    self.colonies.close(process.processid, [args[0]], self.executor_prvkey)
            except Exception as err:
                print(err)
                pass

    def unregister(self):
        self.colonies.remove_executor(self.colonyname, self.executorname, self.colony_prvkey)
        print("Executor", self.executorname, "unregistered")
        os._exit(0)

def sigint_handler(signum, frame):
    executor.unregister()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint_handler)
    executor = PythonExecutor()
    executor.start()
