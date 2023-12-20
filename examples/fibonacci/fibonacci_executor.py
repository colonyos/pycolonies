from pycolonies import Crypto
from pycolonies import colonies_client
import signal
import os
import uuid 

def fib(n):
    if n == 0 or n == 1:
        return n
    return fib(n - 1) + fib(n - 2)

class Executor:
    def __init__(self):
        colonies, colonyname, colony_prvkey, _, _ = colonies_client()
        self.colonies = colonies
        self.colonyname = colonyname
        self.colony_prvkey = colony_prvkey
        self.executorname = "fibonacci-executor"
        self.executortype = "fibonacci-executor"

        crypto = Crypto()
        self.executor_prvkey = crypto.prvkey()
        self.executorid = crypto.id(self.executor_prvkey)

        self.register()
        
    def register(self):
        executor = {
            "executorname": self.executorname + str(uuid.uuid4()),
            "executorid": self.executorid,
            "colonyname": self.colonyname,
            "executortype": self.executortype
        }
        
        try:
            self.colonies.add_executor(executor, self.colony_prvkey)
            self.colonies.approve_executor(self.colonyname, self.executorname, self.colony_prvkey)
        except Exception as err:
            print(err)
        print("Executor", self.executorname, "registered")
        
        try:
            self.colonies.add_function(self.executorid, 
                                       self.colonyname, 
                                       "fib",  
                                       self.executor_prvkey)
            
        except Exception as err:
            print(err)
            os._exit(0)
   
    def start(self):
        while (True):
            try:
                process = self.colonies.assign(self.colonyname, 10, self.executor_prvkey)
                print("Process", process["processid"], "is assigned to executor")
                if process["spec"]["funcname"] == "fib":
                    print("Calculating fib(" + str(process["spec"]["args"][0]) + ")")
                    n = fib(process["spec"]["args"][0])
                    print("Result is ", n)
                    self.colonies.close(process["processid"], [str(n)], self.executor_prvkey)
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
    executor = Executor()
    executor.start()
