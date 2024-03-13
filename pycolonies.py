import requests
import json 
import sys
sys.path.append(".")
from crypto import Crypto
import base64
from websocket import create_connection
import inspect
import os
import ctypes

def colonies_client():
    colonies_server = os.getenv("COLONIES_SERVER_HOST")
    colonies_port = os.getenv("COLONIES_SERVER_PORT")
    colonies_tls = os.getenv("COLONIES_SERVER_TLS")
    colonyname = os.getenv("COLONIES_COLONY_NAME")
    colony_prvkey = os.getenv("COLONIES_COLONY_PRVKEY")
    executorname = os.getenv("COLONIES_EXECUTOR_NAME")
    prvkey = os.getenv("COLONIES_PRVKEY")

    if colonies_tls == "true":
        client = Colonies(colonies_server, int(colonies_port), True)
    else:
        client = Colonies(colonies_server, int(colonies_port), False)

    return client, colonyname, colony_prvkey, executorname, prvkey

class ColoniesConnectionError(Exception):
    pass

class ColoniesError(Exception):
    pass
    
def func_spec(func, args, colonyname, executortype, priority=1, maxexectime=-1, maxretries=-1, maxwaittime=-1, code=None, kwargs=None, fs=None):
    if isinstance(func, str):
        func_spec = {
            "nodename": func,
            "funcname": func, 
            "args": args,
            "kwargs": kwargs,
            "fs": fs,
            "priority": priority,
            "maxwaittime": maxwaittime,
            "maxexectime": maxexectime,
            "maxretries": maxretries,
            "conditions": {
                "colonyname": colonyname,
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
            "kwargs": kwargs,
            "priority": priority,
            "maxwaittime": maxwaittime,
            "maxexectime": maxexectime,
            "maxretries": maxretries,
            "conditions": {
                "colonyname": colonyname,
                "executortype": executortype
            },
            "env": {
                "args_spec": args_spec_str,
                "code": code_base64,
            },
        }

    return func_spec

class Workflow:
    def __init__(self, colonyname):
        self.colonyname = colonyname
        self.func_specs = []

    def add(self, func_spec, nodename, dependencies):
        func_spec["nodename"] = nodename
        func_spec["conditions"]["dependencies"] = dependencies
        self.func_specs.append(func_spec)

    def workflow_spec(self):
        return { 
                "colonyname" : self.colonyname,
                "functionspecs" : self.func_specs
                }

class Colonies:
    WAITING = 0
    RUNNING = 1
    SUCCESSFUL = 2
    FAILED = 3
    
    def __init__(self, host, port, tls=False):
        if tls:
            self.url = "https://" + host + ":" + str(port) + "/api"
            self.host = host
            self.port = port
            self.tls = True
        else:
            self.url = "http://" + host + ":" + str(port) + "/api"
            self.host = host
            self.port = port
            self.tls = False 
    
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
            reply = requests.post(url = self.url, data=rpc_json, verify=True)
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
            "colonyname": process["spec"]["conditions"]["colonyname"],
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

        if self.tls:
            ws = create_connection("wss://" + self.host + ":" + str(self.port) + "/pubsub")
        else:
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
    
    def del_colony(self, colonyname, prvkey):
        msg = {
            "msgtype": "removecolonymsg",
            "colonyname": colonyname
        }
        return self.__rpc(msg, prvkey)
    
    def list_colonies(self, prvkey):
        msg = {
            "msgtype": "getcoloniesmsg",
        }
        return self.__rpc(msg, prvkey)
    
    def get_colony(self, colonyname, prvkey):
        msg = {
            "msgtype": "getcolonymsg",
            "colonyname": colonyname
        }
        return self.__rpc(msg, prvkey)
    
    def add_executor(self, executor, prvkey):
        msg = {
            "msgtype": "addexecutormsg",
            "executor": executor 
        }
        return self.__rpc(msg, prvkey)
    
    def list_executors(self, colonyname, prvkey):
        msg = {
            "msgtype": "getexecutorsmsg",
            "colonyname": colonyname
        }
        return self.__rpc(msg, prvkey)
    
    def approve_executor(self, colonyname, executorname, prvkey):
        msg = {
            "msgtype": "approveexecutormsg",
            "colonyname": colonyname,
            "executorname": executorname
        }
        return self.__rpc(msg, prvkey)
    
    def reject_executor(self, colonyname, executorname, prvkey):
        msg = {
            "msgtype": "rejectexecutormsg",
            "colonyname": colonyname,
            "executorname": executorname
        }
        return self.__rpc(msg, prvkey)
    
    def remove_executor(self, colonyname, executorname, prvkey):
        msg = {
            "msgtype": "removeexecutormsg",
            "colonyname": colonyname,
            "executorname": executorname
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
    
    def assign(self, colonyname, timeout, prvkey):
        msg = {
            "msgtype": "assignprocessmsg",
            "timeout": timeout,
            "colonyname": colonyname
        }
        return self.__rpc(msg, prvkey)
  
    def list_processes(self, colonyname, count, state, prvkey):
        msg = {
            "msgtype": "getprocessesmsg",
            "colonyname": colonyname,
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
    
    def remove_process(self, processid, prvkey):
        msg = {
            "msgtype": "removeprocessmsg",
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
    
    def set_output(self, processid, arr, prvkey):
        msg = {
            "msgtype": "setoutputmsg",
            "processid": processid,
            "out": arr 
        }

        return self.__rpc(msg, prvkey)
    
    def stats(self, colonyname, prvkey):
        msg = {
            "msgtype": "getcolonystatsmsg",
            "colonyname": colonyname
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
    
    def add_function(self, colonyname, executorname, funcname, prvkey):
        func = {}
        func["executorname"] = executorname
        func["colonyname"] = colonyname
        func["funcname"] = funcname
       
        msg = {
            "msgtype": "addfunctionmsg",
            "fun": func
        }
        return self.__rpc(msg, prvkey)
    
    def get_functions_by_executor(self, colonyname, executorname, prvkey):
        msg = {
            "msgtype": "getfunctionsmsg",
            "colonyname": colonyname,
            "executorname": executorname
        }
        return self.__rpc(msg, prvkey)
    
    def get_functions_by_colony(self, colonyname, prvkey):
        msg = {
            "msgtype": "getfunctionsmsg",
            "colonyname": colonyname
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
    
    def create_snapshot(self, colonyname, label, name, prvkey):
        msg = {
            "msgtype": "createsnapshotmsg",
            "colonyname": colonyname,
            "label": label,
            "name": name
        }
        return self.__rpc(msg, prvkey)
    
    def get_snapshots(self, colonyname, prvkey):
        msg = {
            "msgtype": "getsnapshotsmsg",
            "colonyname": colonyname,
        }
        return self.__rpc(msg, prvkey)
    
    def get_snapshot_by_name(self, colonyname, name, prvkey):
        msg = {
            "msgtype": "getsnapshotmsg",
            "colonyname": colonyname,
            "snapshotid": "",
            "name": name
        }
        return self.__rpc(msg, prvkey)
    
    def get_snapshot_by_id(self, colonyname, snapshotid, prvkey):
        msg = {
            "msgtype": "getsnapshotmsg",
            "colonyname": colonyname,
            "snapshotid": snapshotid,
            "name": ""
        }
        return self.__rpc(msg, prvkey)
    
    def add_log(self, processid, logmsg, prvkey):
        msg = {
            "msgtype": "addlogmsg",
            "processid": processid,
            "message": logmsg
        }
        return self.__rpc(msg, prvkey)
    
    def get_process_log(self, colonyname, processid, count, since, prvkey):
        msg = {
            "msgtype": "getlogsmsg",
            "colonyname": colonyname,
            "executorid": "",
            "processid": processid,
            "count": count,
            "since": since
        }
        return self.__rpc(msg, prvkey)
    
    def get_executor_log(self, colonyname, executorname, count, since, prvkey):
        msg = {
            "msgtype": "getlogsmsg",
            "colonyname": colonyname,
            "executorname": executorname,
            "processid": "",
            "count": count,
            "since": since
        }
        return self.__rpc(msg, prvkey)

    def sync(self, dir, label, keeplocal, colonyname, prvkey):
        libname = os.environ.get("CFSLIB")
        if libname == None:
            libname = "/usr/local/lib/libcfslib.so"
        c_lib = ctypes.CDLL(libname)
        c_lib.sync.restype = ctypes.c_int
        
        c_host = ctypes.c_char_p(self.host.encode('utf-8'))
        c_port = ctypes.c_int(self.port)
        c_insecure = ctypes.c_int(self.tls==False)
        c_skip_tls_verify = ctypes.c_int(False)
        c_dir = ctypes.c_char_p(dir.encode('utf-8'))
        c_label = ctypes.c_char_p(label.encode('utf-8'))
        c_keeplocal = ctypes.c_int(keeplocal)
        c_colonyname = ctypes.c_char_p(colonyname.encode('utf-8'))
        c_prvkey = ctypes.c_char_p(prvkey.encode('utf-8'))

        res = c_lib.sync(c_host, c_port, c_insecure, c_skip_tls_verify, c_dir, c_label, c_keeplocal, c_colonyname, c_prvkey)
        if res != 0:
            raise Exception("failed to sync")

    def get_files(self, label, colonyname, prvkey):
        msg = {
            "msgtype": "getfilesmsg",
            "colonyname": colonyname,
            "label": label
        }
        return self.__rpc(msg, prvkey)
