from pycolonies import Crypto
from pycolonies import colonies_client
import signal
import os
from typing import Any

def calc_ndvi(polygon, product, time):
    print("Calculation NDVI for polygon", polygon, "product", product, "time", time)
    return [0.1, 0.2, 0.3, 0.4, 0.5]

class PythonExecutor:
    def __init__(self) -> None:
        colonies, colonyname, colony_prvkey, _, _ = colonies_client()
        self.colonies = colonies
        self.colonyname = colonyname
        self.colony_prvkey = colony_prvkey
        self.executorname = "des-executor"
        self.executortype = "des-executor"

        crypto = Crypto()
        self.executor_prvkey = crypto.prvkey()
        self.executorid = crypto.id(self.executor_prvkey)

        self.register()
        
    def register(self) -> None:
        try:
            self.colonies.add_executor(
                executorname=self.executorname,
                executorid=self.executorid,
                colonyname=self.colonyname,
                executortype=self.executortype,
                colony_prvkey=self.colony_prvkey
            )
            self.colonies.approve_executor(self.colonyname, self.executorname, self.colony_prvkey)
            
            self.colonies.add_function(self.colonyname, 
                                       self.executorname, 
                                       "calc_ts",  
                                       self.executor_prvkey)
        except Exception as err:
            print(err)
            os._exit(0)
        
        print("Executor", self.executorname, "registered")
        
    def start(self) -> None:
        while (True):
            try:
                process = self.colonies.assign(self.colonyname, 3, self.executor_prvkey)
                print("Process", process.processid, "is assigned to executor")
                
                self.colonies.add_log(process.processid, "Calculating NDVI\n", self.executor_prvkey)

                if process.spec is None or process.spec.kwargs is None or len(process.spec.kwargs) == 0:
                    print("invalid process")
                    continue

                polygon = process.spec.kwargs["polygon"]
                product = process.spec.kwargs["product"]
                time = process.spec.kwargs["time"]

                ndvi_serie = calc_ndvi(polygon, product, time)

                if process.spec.funcname == "calc_ts":
                    self.colonies.close(process.processid, ndvi_serie, self.executor_prvkey)
            except Exception:
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
