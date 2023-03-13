import sys
sys.path.append(".")
from colonies import Colonies
from colonies import Workflow
from colonies_monad import ColoniesMonad

colonyid = "4787a5071856a4acf702b2ffcea422e3237a679c681314113d86139461290cf4"
executorid = "3fc05cf3df4b494e95d6a3d297a34f19938f7daa7422ab0d4f794454133341ac" 
executor_prvkey = "ddf7f7791208083b6a9ed975a72684f6406a269cfa36f1b1c32045c0a71fff05"

def turn_camera(ctx={}):
    print("turn on camera")
    return "localhost", 8080 

def configure_inference(camera_host, camera_port, ctx={}):
    print("configure_inference server")
    print("camera_host", camera_host)
    print("camera_port", camera_port)
    return "nodeports", 8223

m = ColoniesMonad("localhost", 50080, colonyid, executor_prvkey)
result = (m >> turn_camera >> configure_inference).unwrap()
print(result)  # prints 3 
