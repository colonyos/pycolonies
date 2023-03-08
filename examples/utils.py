import sys
sys.path.append(".")
import base64
import inspect

def create_func_spec(func, args, colonyid):
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
        "priority": 0,
        "maxwaittime": -1,
        "maxexectime": 10,
        "maxretries": 3,
        "conditions": {
            "colonyid": colonyid,
            "executorids": [],
            "executortype": "faas",
        },
        "label": "",
        "env": {
            "args_spec": args_spec_str,
            "code": code_base64,
        },
    }

    return func_spec
