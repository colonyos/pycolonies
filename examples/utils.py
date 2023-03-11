import sys
sys.path.append(".")
import base64
import inspect

def create_func_spec(func, args, colonyid, executortype, priority, maxexectime, maxretries, maxwaittime):
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
                "executortype": executortype,
            },
            "label": ""
        }
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
                "executortype": executortype,
            },
            "env": {
                "args_spec": args_spec_str,
                "code": code_base64,
            },
        }

    return func_spec
