from pycolonies import Colonies
from pycolonies import Workflow
from colonies_monad_v2 import ColoniesMonad
from colonies_monad_v2 import Function

colonyid = "4787a5071856a4acf702b2ffcea422e3237a679c681314113d86139461290cf4"
executorid = "3fc05cf3df4b494e95d6a3d297a34f19938f7daa7422ab0d4f794454133341ac" 
executor_prvkey = "ddf7f7791208083b6a9ed975a72684f6406a269cfa36f1b1c32045c0a71fff05"

def decide_lamp_state(ctx={}):
    return "off"

decide_lamp_state = Function(decide_lamp_state, colonyid, executortype="python_executor")
set_lamp_state = Function("set_lamp_state", colonyid, executortype="lamp_executor")

m = ColoniesMonad("localhost", 50080, colonyid, executor_prvkey)
result = (m >> decide_lamp_state >> set_lamp_state).unwrap()
