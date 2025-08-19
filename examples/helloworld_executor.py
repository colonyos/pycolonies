from pycolonies import Crypto
from pycolonies import colonies_client
import signal
import os
from typing import Any

class PythonExecutor:
    def __init__(self) -> None:
        colonies, colonyname, colony_prvkey, _, _ = colonies_client()
        self.colonies = colonies
        self.colonyname = colonyname
        self.colony_prvkey = colony_prvkey
        self.executorname = "helloworld-executor"
        self.executortype = "helloworld-executor"

        crypto = Crypto()
        self.executor_prvkey = crypto.prvkey()
        self.executorid = crypto.id(self.executor_prvkey)

        self.register()
        
    def register(self) -> None:
        try:
            self.colonies.add_executor(self.executorid, self.executorname, self.colonyname, self.colony_prvkey)
            self.colonies.approve_executor(self.colonyname, self.executorname, self.colony_prvkey)
            self.colonies.add_function(self.colonyname, self.executorname, "helloworld", self.executor_prvkey)
        except Exception as err:
            print(err)
            os._exit(0)
        
        print("Executor", self.executorname, "registered")
        
    def start(self) -> None:
        while (True):
            try:
                process = self.colonies.assign(self.colonyname, 10, self.executor_prvkey)
                print("Process", process.processid, "is assigned to executor")
                self.colonies.add_log(process.processid, "Hello from executor\n", self.executor_prvkey)
                if process.spec.funcname == "helloworld":
                    self.colonies.close(process.processid, ["helloworld"], self.executor_prvkey)
            except Exception as err:
                print(err)
                pass

    def unregister(self) -> None:
        self.colonies.remove_executor(self.colonyname, self.executorname, self.colony_prvkey)
        print("Executor", self.executorname, "unregistered")
        os._exit(0)

def sigint_handler(signum: int, frame: Any) -> None:
    del signum, frame
    executor.unregister()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint_handler)
    executor = PythonExecutor()
    executor.start()
