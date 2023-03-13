import sys
sys.path.append(".")
from crypto import Crypto
from colonies import Colonies
from colonies import ColoniesConnectionError
from colonies import create_func_spec
import signal
import base64 
import os
import uuid
import inspect

class PythonExecutor:
    def __init__(self):
        self.colonies = Colonies("localhost", 50080)
        crypto = Crypto()
        self.colonyid = "4787a5071856a4acf702b2ffcea422e3237a679c681314113d86139461290cf4"
        self.colony_prvkey="ba949fa134981372d6da62b6a56f336ab4d843b22c02a4257dcf7d0d73097514"
        self.executor_prvkey = crypto.prvkey()
        self.executorid = crypto.id(self.executor_prvkey)

        global colonies
        colonies = self.colonies

        self.register()
        
    def register(self):
        executor = {
            "executorname": str(uuid.uuid4()),
            "executorid": self.executorid,
            "colonyid": self.colonyid,
            "executortype": "python_executor"
        }
        
        try:
            self.colonies.add_executor(executor, self.colony_prvkey)
            self.colonies.approve_executor(self.executorid, self.colony_prvkey)
        except Exception as err:
            print(err)
            sys.exit(-1)
        
        print("Executor", self.executorid, "registered")
   
    def start(self):
        while (True):
            try:
                # try to get a process from the colonies server, the call will block for max 10 seconds
                # an exception will be raised if no processes can be assigned, and we will restart start the while loop
                assigned_process = self.colonies.assign(self.colonyid, 10, self.executor_prvkey)
                print()
                print("Process", assigned_process["processid"], "is assigned to Executor")

                # ok, executor was assigned a process, extract the function code to run
                code_base64 = assigned_process["spec"]["env"]["code"]
                code_bytes2 = base64.b64decode(code_base64)
                code = code_bytes2.decode("ascii")

                # add the function to the global scope
                exec(code)

                # extract args and call the function code we just injected
                funcspec = assigned_process["spec"]
                funcname = funcspec["funcname"]
                try:
                    self.colonies.add_function(self.executorid, 
                                             self.colonyid, 
                                             funcname,  
                                             funcspec["env"]["args_spec"].split(","), 
                                             "Python function", 
                                             self.executor_prvkey)
                except Exception as err:
                    print(err)

                # if "in" is defined, it is the output of the parent process,
                # use the output from parent process instead of args
                if len(assigned_process["in"])>0:
                    args = []
                    for args_from_parent in assigned_process["in"]:
                        if args_from_parent is not None:
                            for a in args_from_parent:
                                args.append(a)
                else:
                    args = funcspec["args"]

                print("Executing:", funcspec["funcname"])

                # call the injected function
                try:
                    ctx = {"process": assigned_process,
                           "colonyid": self.colonyid,
                           "executorid": self.executorid,
                           "executor_prvkey": self.executor_prvkey}
                    res = eval(funcname)(*tuple(args), ctx=ctx)
                except Exception as err:
                    print("Failed to execute function:", err)
                    print(code)
                    self.colonies.fail(assigned_process["processid"], ["Failed to execute function"], self.executor_prvkey)
                    continue

                # close the process as successful
                self.colonies.close(assigned_process["processid"], [res], self.executor_prvkey)
            except ColoniesConnectionError as err:
                print(err)
                sys.exit(-1)
            except Exception as err:
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
