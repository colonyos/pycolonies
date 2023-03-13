import sys
sys.path.append(".")
from crypto import Crypto
from colonies import Colonies
import signal
import os
import uuid 

class PythonExecutor:
    def __init__(self):
        self.colonies = Colonies("localhost", 50080)
        crypto = Crypto()
        self.colonyid = "4787a5071856a4acf702b2ffcea422e3237a679c681314113d86139461290cf4"
        self.colony_prvkey="ba949fa134981372d6da62b6a56f336ab4d843b22c02a4257dcf7d0d73097514"
        self.executor_prvkey = crypto.prvkey()
        self.executorid = crypto.id(self.executor_prvkey)

        self.register()
        
    def register(self):
        executor = {
            "executorname": str(uuid.uuid4()),
            "executorid": self.executorid,
            "colonyid": self.colonyid,
            "executortype": "echo_executor"
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
                                       "echo",  
                                       ["arg"], 
                                       "Python function that returns it input as output", 
                                       self.executor_prvkey)
            
        except Exception as err:
            print(err)
   
    def start(self):
        while (True):
            try:
                process = self.colonies.assign(self.colonyid, 10, self.executor_prvkey)
                print("Process", process["processid"], "is assigned to executor")
                if process["spec"]["funcname"] == "echo":
                    # if "in" is defined, it is the output of the parent process,
                    # use the output from parent process instead of args
                    if len(process["in"])>0:
                        args = process["in"]
                    else:
                        args = process["spec"]["args"]
                

                    # just set output to input value 
                    self.colonies.close(process["processid"], [args[0]], self.executor_prvkey)
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
    executor = PythonExecutor()
    executor.start()
