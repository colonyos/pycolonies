import sys
sys.path.append(".")
from crypto import Crypto
from colonies import Colonies
import signal
import os

class PythonExecutor:
    def __init__(self):
        url = "http://localhost:50080/api"
        self.client = Colonies(url)
        crypto = Crypto()
        self.client = Colonies(url)
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
                if assigned_process["spec"]["funcname"] == "say":
                    arg = ""
                    assigned_args = assigned_process["spec"]["args"]
                    if len(assigned_args)>0:
                        arg = assigned_args[0]

                    print(arg)
                    self.client.close(assigned_process["processid"], [arg], self.executor_prvkey)
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
