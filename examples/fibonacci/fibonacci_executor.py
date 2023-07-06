from pycolonies import Crypto
from pycolonies import Colonies
import signal
import os
import uuid 

def fib(n):
    if n == 0 or n == 1:
        return n
    return fib(n - 1) + fib(n - 2)

class Executor:
    def __init__(self):
        host = os.getenv("COLONIES_SERVER_HOST")
        port = os.getenv("COLONIES_SERVER_PORT")
        self.colonies = Colonies(host, port)
        crypto = Crypto()
        self.colonyid = os.getenv("COLONIES_COLONY_ID")
        self.colony_prvkey = os.getenv("COLONIES_COLONY_PRVKEY")
        self.executor_prvkey = crypto.prvkey()
        self.executorid = crypto.id(self.executor_prvkey)

        self.register()
        
    def register(self):
        executor = {
            "executorname": "fibonacci_executor_" + str(uuid.uuid4()),
            "executorid": self.executorid,
            "colonyid": self.colonyid,
            "executortype": "fibonacci_executor"
        }
        
        try:
            self.colonies.add_executor(executor, self.colony_prvkey)
            self.colonies.approve_executor(self.executorid, self.colony_prvkey)
        except Exception as err:
            print(err)
        print("Executor", self.executorid, "registered")
        
        try:
            self.colonies.add_function(self.executorid, 
                                       self.colonyid, 
                                       "fib",  
                                       self.executor_prvkey)
            
        except Exception as err:
            print(err)
            os._exit(0)
   
    def start(self):
        while (True):
            try:
                process = self.colonies.assign(self.colonyid, 10, self.executor_prvkey)
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
        self.colonies.delete_executor(self.executorid, self.colony_prvkey)
        print("Executor", self.executorid, "unregistered")
        os._exit(0)

def sigint_handler(signum, frame):
    executor.unregister()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint_handler)
    executor = Executor()
    executor.start()
