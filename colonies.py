import requests
import json 
import sys
sys.path.append(".")
from crypto import Crypto
import base64

class Colonies:

    def __init__(self, url):
        self.url = "https://10.0.0.240:8080/api"
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
        add_colony_msg = {
            "msgtype": "addcolonymsg",
            "colony": colony
        }
        return self.__rpc(add_colony_msg, prvkey)
    
    def del_colony(self, colonyid, prvkey):
        add_colony_msg = {
            "msgtype": "deletecolonymsg",
            "colonyid": colonyid
        }
        return self.__rpc(add_colony_msg, prvkey)
