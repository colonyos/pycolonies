import sys
sys.path.append(".")
from crypto import Crypto
from colonies import Colonies

def main():
    url = "https://10.0.0.240:8080/api"
    client = Colonies(url)
    colonyid = "bdebcd2a6069cab6d1cee1e081780e02ec16d9e9f15bbb84906731a5ca541592"
    runtimeid = "71d5da957ae22ec47c8a3d458ab91a596089a8a043fcd646228c03c7a892fe34"
    runtime_prvkey = "869e3a565bf7ac36b716073398eec8e7563f7800fcf555ce1a3922b6c01d115c"

    turn_on_lamp = {
        "conditions": {
            "colonyid": colonyid,
            "runtimeids": ["6af2c7593d2760b6c81f145828158dae2a9648cbb29061d95fe54f55f69c2e24"],
            "runtimetype": "lamp",
            "mem": 1000,
            "cores": 10,
            "gpus": 1
        },
        "env": {
            "lamp_state": sys.argv[1]
        }
    }
   
    client.submit_process_spec(turn_on_lamp, runtime_prvkey)

if __name__ == '__main__':
    main()
