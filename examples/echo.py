import sys
sys.path.append(".")
from colonies import Colonies

colonies = Colonies("localhost", 50080)

colonyid = "4787a5071856a4acf702b2ffcea422e3237a679c681314113d86139461290cf4"
executorid = "3fc05cf3df4b494e95d6a3d297a34f19938f7daa7422ab0d4f794454133341ac" 
executor_prvkey = "ddf7f7791208083b6a9ed975a72684f6406a269cfa36f1b1c32045c0a71fff05"

def foo(arg1, arg2):         
    a = arg1 + arg2
    return a  

func_spec = colonies.create_func_spec(func="echo", 
                                      args=["helloworld"], 
                                      colonyid=colonyid, 
                                      executortype="echo_executor",
                                      priority=200,
                                      maxexectime=100,
                                      maxretries=3,
                                      maxwaittime=100)

process = colonies.submit(func_spec, executor_prvkey)
print("Process", process["processid"], "submitted")
process = colonies.wait(process, 100, executor_prvkey)
print(process["out"][0])