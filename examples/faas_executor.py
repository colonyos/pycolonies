import sys
sys.path.append(".")
from crypto import Crypto
from colonies import Colonies
import signal
import base64 
import os

def print_to_string(*args, **kwargs):
    newstr = ""
    for a in args:
        newstr+=str(a)+' '
    return newstr

class PythonExecutor:
    def __init__(self):
        #url = "http://localhost:50080/api"
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
                print(assigned_process["processid"], "is assigned to executor")

                code_base64 = assigned_process["spec"]["env"]["code"]
                code_bytes2 = base64.b64decode(code_base64)
                code = code_bytes2.decode("ascii")
                exec(code)
                funcname = assigned_process["spec"]["funcname"]
                args = assigned_process["spec"]["args"]
                formatedArgsStr = print_to_string(args)
                formatedArgsStr = formatedArgsStr.replace('[', '')
                formatedArgsStr = formatedArgsStr.replace(']', '')
                res = eval(funcname+'(' + formatedArgsStr + ')') 
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
