import requests
import json 
import sys
sys.path.append(".")
from crypto import Crypto
import base64


class Colonies:
    WAITING = 0
    RUNNING = 1
    SUCCESSFUL = 2
    FAILED = 3
    
    def __init__(self, url):
        self.url = url
        pass
    
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
        reply = requests.post(url = self.url, data=rpc_json, verify=False)
        reply_msg_json = json.loads(reply.content)
        base64_payload = reply_msg_json["payload"]
        payload_bytes = base64.b64decode(base64_payload)
        payload = json.loads(payload_bytes)
       
        if reply.status_code == 200:
            return payload
        else:
            raise Exception(payload["message"])

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
    
    def get_colony(self, colonyid, prvkey):
        msg = {
            "msgtype": "getcolonymsg",
            "colonyid": colonyid
        }
        return self.__rpc(msg, prvkey)
    
    def add_runtime(self, runtime, prvkey):
        msg = {
            "msgtype": "addruntimemsg",
            "runtime": runtime
        }
        return self.__rpc(msg, prvkey)
    
    def list_runtimes(self, colonyid, prvkey):
        msg = {
            "msgtype": "getruntimesmsg",
            "colonyid": colonyid
        }
        return self.__rpc(msg, prvkey)
    
    def approve_runtime(self, runtimeid, prvkey):
        msg = {
            "msgtype": "approveruntimemsg",
            "runtimeid": runtimeid
        }
        return self.__rpc(msg, prvkey)
    
    def reject_runtime(self, runtimeid, prvkey):
        msg = {
            "msgtype": "rejectruntimemsg",
            "runtimeid": runtimeid
        }
        return self.__rpc(msg, prvkey)
    
    def delete_runtime(self, runtimeid, prvkey):
        msg = {
            "msgtype": "deleteruntimemsg",
            "runtimeid": runtimeid
        }
        return self.__rpc(msg, prvkey)
    
    def submit_process_spec(self, process_spec, prvkey):
        msg = {
            "msgtype": "submitprocessespecmsg",
            "spec": process_spec
        }
        return self.__rpc(msg, prvkey)
    
    def assign_process(self, colonyid, timeout, prvkey):
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
    
    def close(self, processid, successful, prvkey):
        if successful:
            msg = {
                "msgtype": "closesuccessfulmsg",
                "processid": processid
            }
        else: 
            msg = {
                "msgtype": "closefailedmsg",
                "processid": processid
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
