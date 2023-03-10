import sys
sys.path.append(".")
from crypto import Crypto
from colonies import Colonies
import signal
import base64 
import os

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
            "executorname": "python_executor",
            "executorid": self.executorid,
            "colonyid": self.colonyid,
            "executortype": "faas"
        }
        
        try:
            self.client.add_executor(executor, self.colony_prvkey)
            self.client.approve_executor(self.executorid, self.colony_prvkey)
        except Exception as err:
            print(err)
        print("Executor", self.executorid, "registered")
   
    def start(self):
        while (True):
            try:
                assigned_process = self.client.assign(self.colonyid, 10, self.executor_prvkey)
                print()
                print("Process", assigned_process["processid"], "is assigned to Executor")

                code_base64 = assigned_process["spec"]["env"]["code"]
                code_bytes2 = base64.b64decode(code_base64)
                code = code_bytes2.decode("ascii")
                exec(code)
                funcspec = assigned_process["spec"]
                funcname = funcspec["funcname"]
                args = funcspec["args"]
                formated_args = formatargs(args)
                print("Executing:", funcspec["funcname"] + "(" + formatargs(funcspec["args"]) + ")")
                res = eval(funcname+'(' + formated_args + ')')
                self.client.close(assigned_process["processid"], [res], self.executor_prvkey)
            except Exception as err:
                print(err)
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
