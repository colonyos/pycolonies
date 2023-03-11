import sys
sys.path.append(".")
from crypto import Crypto
from colonies import Colonies
from colonies import ColoniesConnectionError
import signal
import base64 
import os
import uuid

def formatargs(args):
    s = ""
    for a in args:
        s+=str(a)+', '
               
    s = s.replace('[', '')
    s = s.replace(']', '')
    s = s.strip()
    
    if len(s)>0 and s[len(s)-1] == ",":
        s = s[:len(s)-1]
    
    return s

class PythonExecutor:
    def __init__(self):
        self.client = Colonies("localhost", 50080)
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
            "executortype": "faas_executor"
        }
        
        try:
            self.client.add_executor(executor, self.colony_prvkey)
            self.client.approve_executor(self.executorid, self.colony_prvkey)
        except Exception as err:
            print(err)
            sys.exit(-1)
        print("Executor", self.executorid, "registered")
   
    def start(self):
        while (True):
            try:
                # try to get a process from the colonies server, the call will block for max 10 seconds
                # an exception will be raised if no processes can be assigned, and we will restart start the while loop
                assigned_process = self.client.assign(self.colonyid, 10, self.executor_prvkey)
                print()
                print("Process", assigned_process["processid"], "is assigned to Executor")


                # ok, executor was assigned a process, extract the function code to run
                code_base64 = assigned_process["spec"]["env"]["code"]
                code_bytes2 = base64.b64decode(code_base64)
                code = code_bytes2.decode("ascii")

                # add the function to the global scope
                exec(code)

                # register the function to the colonies server
                print(assigned_process["spec"]["env"]["args_spec"])



                try:
                    self.client.add_function(self.executorid, 
                                             self.colonyid, 
                                             assigned_process["spec"]["funcname"],  
                                             assigned_process["spec"]["env"]["args_spec"].split(","), 
                                             "Python function", 
                                             self.executor_prvkey)
                except Exception as err:
                    # ignore, the function is already registered
                    pass

                # extract args and call the function code we just injected
                funcspec = assigned_process["spec"]
                funcname = funcspec["funcname"]
                args = funcspec["args"]
                formated_args = formatargs(args)
                print("Executing:", funcspec["funcname"] + "(" + formatargs(funcspec["args"]) + ")")

                # call the injected function
                try:
                    res = eval(funcname+'(' + formated_args + ')')
                except:
                    print("Failed to execute function:")
                    print(code)
                    self.client.fail(assigned_process["processid"], ["Failed to execute function"], self.executor_prvkey)
                    continue
                
                # close the process as successful
                self.client.close(assigned_process["processid"], [res], self.executor_prvkey)
            except ColoniesConnectionError as err:
                print(err)
                sys.exit(-1)
            except Exception as err:
                pass

    def unregister(self):
        self.client.delete_executor(self.executorid, self.colony_prvkey)
        print("Executor", self.executorid, "unregistered")
        os._exit(0)

def sigint_handler(signum, frame):
    executor.unregister()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint_handler)
    executor = PythonExecutor()
    executor.start()
