import requests
import json 
import sys
sys.path.append(".")
from crypto import Crypto
import base64
from websocket import create_connection
import inspect

class ColoniesConnectionError(Exception):
    pass

class ColoniesError(Exception):
    pass
    
def create_func_spec(func, args, colonyid, executortype, priority, maxexectime, maxretries, maxwaittime, code=None):
    if isinstance(func, str):
        func_spec = {
            "nodename": func,
            "funcname": func, 
            "args": args,
            "priority": priority,
            "maxwaittime": maxwaittime,
            "maxexectime": maxexectime,
            "maxretries": maxretries,
            "conditions": {
                "colonyid": colonyid,
                "executortype": executortype
            },
            "label": ""
        }
        if code is not None:
            code_bytes = code.encode("ascii")
            code_base64_bytes = base64.b64encode(code_bytes)
            code_base64 = code_base64_bytes.decode("ascii")
            func_spec["env"] = {}
            func_spec["env"]["code"] = code_base64

    else:
        code = inspect.getsource(func)
        code_bytes = code.encode("ascii")
        code_base64_bytes = base64.b64encode(code_bytes)
        code_base64 = code_base64_bytes.decode("ascii")

        funcname = func.__name__
        args_spec = inspect.getfullargspec(func)
        args_spec_str = ','.join(args_spec.args)

        func_spec = {
            "nodename": funcname,
            "funcname": funcname,
            "args": args,
            "priority": priority,
            "maxwaittime": maxwaittime,
            "maxexectime": maxexectime,
            "maxretries": maxretries,
            "conditions": {
                "colonyid": colonyid,
                "executortype": executortype
            },
            "env": {
                "args_spec": args_spec_str,
                "code": code_base64,
            },
        }

    return func_spec

class Workflow:
    def __init__(self, colonyid):
        self.colonyid = colonyid
        self.func_specs = []

    def add(self, func_spec, nodename, dependencies):
        func_spec["nodename"] = nodename
        func_spec["conditions"]["dependencies"] = dependencies
        self.func_specs.append(func_spec)

    def workflow_spec(self):
        return { 
                "colonyid" : self.colonyid,
                "functionspecs" : self.func_specs
                }

class Colonies:
    WAITING = 0
    RUNNING = 1
    SUCCESSFUL = 2
    FAILED = 3
    
    def __init__(self, host, port):
        self.url = "http://" + host + ":" + str(port) + "/api"
        self.host = host
        self.port = port
    
    def __rpc(self, msg, prvkey):
        payload = str(base64.b64encode(json.dumps(msg).encode('utf-8')), "utf-8")
        crypto = Crypto()
        signature = crypto.sign(payload, prvkey)

        rpc = {
            "payloadtype" : msg["msgtype"],
            "payload" : payload,
            "signature" : signature
        }

        rpc_json = json.dumps(rpc) 
        try:
            reply = requests.post(url = self.url, data=rpc_json, verify=False)
            reply_msg_json = json.loads(reply.content)
            base64_payload = reply_msg_json["payload"]
            payload_bytes = base64.b64decode(base64_payload)
            payload = json.loads(payload_bytes)
        except requests.exceptions.ConnectionError as err:
            raise ColoniesConnectionError(err)
        except Exception as err:
            raise ColoniesConnectionError(err)

        if reply.status_code == 200:
            return payload
        else:
            raise ColoniesError(payload["message"])
    
    def wait(self, process, timeout, prvkey):
        processid = process["processid"]
        executortype = process["spec"]["conditions"]["executortype"]
        state = 2
        msg = {
            "processid": processid,
            "executortype": executortype,
            "state": state,
            "timeout": timeout,
            "msgtype": "subscribeprocessmsg"
        }

        rpcmsg = {
            "payloadtype": msg["msgtype"],
            "payload": "",
            "signature": ""
        }

        rpcmsg["payload"] = str(base64.b64encode(json.dumps(msg).encode('utf-8')), "utf-8")
        crypto = Crypto()
        rpcmsg["signature"] = crypto.sign(rpcmsg["payload"], prvkey) 

        ws = create_connection("ws://" + self.host + ":" + str(self.port) + "/pubsub")
        ws.send(json.dumps(rpcmsg))
        ws.recv()
        ws.close()

        return self.get_process(process["processid"], prvkey)

    def add_colony(self, colony, prvkey):
        msg = {
            "msgtype": "addcolonymsg",
            "colony": colony
        }
        return self.__rpc(msg, prvkey)
    
    def del_colony(self, colonyid, prvkey):
        msg = {
            "msgtype": "deletecolonymsg",
            "colonyid": colonyid
        }
        return self.__rpc(msg, prvkey)
    
    def list_colonies(self, prvkey):
        msg = {
            "msgtype": "getcoloniesmsg",
        }
        return self.__rpc(msg, prvkey)
    
    def get_colony(self, colonyid, prvkey):
        msg = {
            "msgtype": "getcolonymsg",
            "colonyid": colonyid
        }
        return self.__rpc(msg, prvkey)
    
    def add_executor(self, executor, prvkey):
        msg = {
            "msgtype": "addexecutormsg",
            "executor": executor 
        }
        return self.__rpc(msg, prvkey)
    
    def list_executors(self, colonyid, prvkey):
        msg = {
            "msgtype": "getexecutorsmsg",
            "colonyid": colonyid
        }
        return self.__rpc(msg, prvkey)
    
    def approve_executor(self, executorid, prvkey):
        msg = {
            "msgtype": "approveexecutormsg",
            "executorid": executorid
        }
        return self.__rpc(msg, prvkey)
    
    def reject_executor(self, executorid, prvkey):
        msg = {
            "msgtype": "rejectexecutormsg",
            "executorid": executorid
        }
        return self.__rpc(msg, prvkey)
    
    def delete_executor(self, executorid, prvkey):
        msg = {
            "msgtype": "deleteexecutormsg",
            "executorid": executorid
        }
        return self.__rpc(msg, prvkey)
    
    def submit(self, spec, prvkey):
        if isinstance(spec, Workflow):
            msg = {
                "msgtype": "submitworkflowspecmsg",
                "spec": spec.workflow_spec()
            }
            return self.__rpc(msg, prvkey)
        else:
            msg = {
                "msgtype": "submitfuncspecmsg",
                "spec": spec
            }
            return self.__rpc(msg, prvkey)
    
    def assign(self, colonyid, timeout, prvkey):
        msg = {
            "msgtype": "assignprocessmsg",
            "timeout": timeout,
            "colonyid": colonyid
        }
        return self.__rpc(msg, prvkey)
  
    def list_processes(self, colonyid, count, state, prvkey):
        msg = {
            "msgtype": "getprocessesmsg",
            "colonyid": colonyid,
            "count": count,
            "state": state
        }
        return self.__rpc(msg, prvkey)
    
    def get_process(self, processid, prvkey):
        msg = {
            "msgtype": "getprocessmsg",
            "processid": processid
        }
        return self.__rpc(msg, prvkey)
    
    def delete_process(self, processid, prvkey):
        msg = {
            "msgtype": "deleteprocessmsg",
            "processid": processid
        }
        return self.__rpc(msg, prvkey)
    
    def close(self, processid, output, prvkey):
        msg = {
            "msgtype": "closesuccessfulmsg",
            "processid": processid,
            "out": output
        }

        return self.__rpc(msg, prvkey)
    
    def fail(self, processid, errors, prvkey):
        msg = {
            "msgtype": "closefailedmsg",
            "processid": processid,
            "errors": errors 
        }

        return self.__rpc(msg, prvkey)
    
    def stats(self, colonyid, prvkey):
        msg = {
            "msgtype": "getcolonystatsmsg",
            "colonyid": colonyid
        }
        return self.__rpc(msg, prvkey)
    
    def add_attribute(self, processid, key, value, prvkey):
        attribute = {}
        attribute["key"] = key 
        attribute["value"] = value
        attribute["targetid"] = processid
        attribute["attributetype"] = 1
       
        msg = {
            "msgtype": "addattributemsg",
            "attribute": attribute
        }
        return self.__rpc(msg, prvkey)
    
    def get_attribute(self, attributeid, prvkey):
        msg = {
            "msgtype": "getattributemsg",
            "attributeid": attributeid
        }
        return self.__rpc(msg, prvkey)
    
    def get_processgraph(self, processgraphid, prvkey):  # TODO: unittest
        msg = {
            "msgtype": "getprocessgraphmsg",
            "processgraphid": processgraphid
        }
        return self.__rpc(msg, prvkey)
    
    def add_function(self, executorid, colonyid, funcname, args, desc, prvkey):
        func = {}
        func["executorid"] = executorid
        func["colonyid"] = colonyid
        func["funcname"] = funcname
        func["args"] = args
        func["desc"] = desc
       
        msg = {
            "msgtype": "addfunctionmsg",
            "fun": func
        }
        return self.__rpc(msg, prvkey)
    
    def get_functions_by_executor(self, executorid, prvkey):
        msg = {
            "msgtype": "getfunctionsmsg",
            "executorid": executorid
        }
        return self.__rpc(msg, prvkey)
    
    def get_functions_by_colony(self, colonyid, prvkey):
        msg = {
            "msgtype": "getfunctionsmsg",
            "colonyid": colonyid
        }
        return self.__rpc(msg, prvkey)
   
    def find_process(self, nodename, processids, prvkey):
        for processid in processids:
            process = self.get_process(processid, prvkey)
            if process["spec"]["nodename"] == nodename:
                return process
        return None
    
    def add_child(self, processgraphid, parentprocessid, childprocessid, funcspec, nodename, insert, prvkey):
        funcspec["nodename"] = nodename
        msg = {
            "msgtype": "addchildmsg",
            "processgraphid": processgraphid,
            "parentprocessid": parentprocessid,
            "childprocessid": childprocessid,
            "insert": insert,
            "spec": funcspec
        }
        return self.__rpc(msg, prvkey)
