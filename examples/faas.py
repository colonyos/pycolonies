import sys
sys.path.append(".")
from crypto import Crypto
from colonies import Colonies
from utils import create_func_spec 

colonyid = "4787a5071856a4acf702b2ffcea422e3237a679c681314113d86139461290cf4"
executorid = "3fc05cf3df4b494e95d6a3d297a34f19938f7daa7422ab0d4f794454133341ac" 
executor_prvkey = "ddf7f7791208083b6a9ed975a72684f6406a269cfa36f1b1c32045c0a71fff05"

def foo(arg1, arg2):         
    a = arg1 + arg2         
    return a  

func_spec = create_func_spec(foo, ["1", "2"], colonyid)
print("Submitting function spec:", func_spec)

url = "http://localhost:50080/api"
client = Colonies(url)
client.submit(func_spec, executor_prvkey)
