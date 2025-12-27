import requests
import json 
from model import Process, FuncSpec, Workflow, ProcessGraph, Conditions, Gpu, S3Object, Reference, File
import base64
from websocket import create_connection
import inspect
import os
import ctypes
from crypto import Crypto
import boto3
import hashlib
import uuid
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

def colonies_client(native_crypto=False):
    colonies_server = os.getenv("COLONIES_SERVER_HOST")
    colonies_port = os.getenv("COLONIES_SERVER_PORT")
    colonies_tls = os.getenv("COLONIES_SERVER_TLS")
    colonyname = os.getenv("COLONIES_COLONY_NAME")
    colony_prvkey = os.getenv("COLONIES_COLONY_PRVKEY")
    executorname = os.getenv("COLONIES_EXECUTOR_NAME")
    prvkey = os.getenv("COLONIES_PRVKEY")

    if colonies_tls == "true":
        client = Colonies(colonies_server, int(colonies_port), True, native_crypto=native_crypto)
    else:
        client = Colonies(colonies_server, int(colonies_port), False, native_crypto=native_crypto)

    return client, colonyname, colony_prvkey, executorname, prvkey

class ColoniesConnectionError(Exception):
    pass

class ColoniesError(Exception):
    pass
    
def func_spec(func, args, colonyname, executortype, executorname=None, priority=1, maxexectime=-1, maxretries=-1, maxwaittime=-1, code=None, kwargs=None, fs=None):
    if isinstance(func, str):
        func_spec = FuncSpec(
            nodename=func,
            funcname=func, 
            args=args,
            kwargs=kwargs,
            fs=fs,
            priority=priority,
            maxwaittime=maxwaittime,
            maxexectime=maxexectime,
            maxretries=maxretries,
            conditions= Conditions(
                colonyname=colonyname,
                executortype=executortype
            )
        )
        if code is not None:
            code_bytes = code.encode("ascii")
            code_base64_bytes = base64.b64encode(code_bytes)
            code_base64 = code_base64_bytes.decode("ascii")
            func_spec.env["code"] = code_base64

    else:
        code = inspect.getsource(func)
        code_bytes = code.encode("ascii")
        code_base64_bytes = base64.b64encode(code_bytes)
        code_base64 = code_base64_bytes.decode("ascii")

        funcname = func.__name__
        args_spec = inspect.getfullargspec(func)
        args_spec_str = ','.join(args_spec.args)

        func_spec = FuncSpec(
            nodename=funcname,
            funcname=funcname,
            args=args,
            kwargs=kwargs,
            priority=priority,
            maxwaittime=maxwaittime,
            maxexectime=maxexectime,
            maxretries=maxretries,
            conditions=Conditions(
                colonyname=colonyname,
                executortype=executortype
            ),
            env={
                "args_spec": args_spec_str,
                "code": code_base64,
            }
        )

    if executorname is not None:
            func_spec.conditions.executornames = [ executorname ]

    return func_spec

class Colonies:
    WAITING = 0
    RUNNING = 1
    SUCCESSFUL = 2
    FAILED = 3
    
    def __init__(self, host, port, tls=False, native_crypto=False):
        self.native_crypto = native_crypto
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
        crypto = Crypto(native=self.native_crypto)
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
            err_detected = False
            if reply_msg_json["error"] == True:
                err_detected = True 
            base64_payload = reply_msg_json["payload"]
            payload_bytes = base64.b64decode(base64_payload)
            payload = json.loads(payload_bytes)
            if err_detected:
                raise ColoniesConnectionError(payload["message"])
        except requests.exceptions.ConnectionError as err:
            raise ColoniesConnectionError(err)
        except Exception as err:
            raise ColoniesConnectionError(err)

        if reply.status_code == 200:
            return payload
        else:
            raise ColoniesError(payload["message"])
    
    def wait(self, process: Process, timeout, prvkey) -> Process:
        state = 2
        msg = {
            "processid": process.processid,
            "executortype": process.spec.conditions.executortype,
            "state": state,
            "timeout": timeout,
            "colonyname": process.spec.conditions.colonyname,
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

        return self.get_process(process.processid, prvkey)

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

    def get_executor(self, colonyname, executorname, prvkey):
        """Get details about a specific executor.

        Args:
            colonyname: Name of the colony
            executorname: Name of the executor
            prvkey: Private key for authentication

        Returns:
            Executor details
        """
        msg = {
            "msgtype": "getexecutormsg",
            "colonyname": colonyname,
            "executorname": executorname
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
                
    def submit_func_spec(self, spec: FuncSpec, prvkey) -> Process:
        msg = {
                "msgtype": "submitfuncspecmsg",
                "spec": spec.model_dump(by_alias=True)
            }
        response = self.__rpc(msg, prvkey)
        return Process(**response)
    
    def submit_workflow(self, workflow: Workflow, prvkey) -> ProcessGraph:
        msg = {
                "msgtype": "submitworkflowspecmsg",
                "spec": workflow.model_dump(by_alias=True)
            }
        response = self.__rpc(msg, prvkey)
        return ProcessGraph(**response)

    def assign(self, colonyname, timeout, prvkey) -> Process:
        msg = {
            "msgtype": "assignprocessmsg",
            "timeout": timeout,
            "colonyname": colonyname
        }
        response = self.__rpc(msg, prvkey)
        return Process(**response)
  
    def list_processes(self, colonyname, count, state, prvkey):
        msg = {
            "msgtype": "getprocessesmsg",
            "colonyname": colonyname,
            "count": count,
            "state": state
        }
        return self.__rpc(msg, prvkey)
    
    def get_process(self, processid, prvkey) -> Process:
        msg = {
            "msgtype": "getprocessmsg",
            "processid": processid
        }
        response = self.__rpc(msg, prvkey)
        return Process(**response)
    
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
        graph = self.__rpc(msg, prvkey)
        return ProcessGraph(**graph)

    def get_processgraphs(self, colonyname, count, prvkey, state=None):
        """Get process graphs (workflows) in a colony.

        Args:
            colonyname: Name of the colony
            count: Maximum number to return
            prvkey: Private key for authentication
            state: Optional state filter (0=waiting, 1=running, 2=success, 3=failed)

        Returns:
            List of process graphs
        """
        msg = {
            "msgtype": "getprocessgraphsmsg",
            "colonyname": colonyname,
            "count": count
        }
        if state is not None:
            msg["state"] = state
        return self.__rpc(msg, prvkey)

    def remove_processgraph(self, processgraphid, prvkey):
        """Remove a process graph (workflow).

        Args:
            processgraphid: ID of the process graph to remove
            prvkey: Private key for authentication
        """
        msg = {
            "msgtype": "removeprocessgraphmsg",
            "processgraphid": processgraphid
        }
        return self.__rpc(msg, prvkey)

    def remove_all_processgraphs(self, colonyname, prvkey, state=None):
        """Remove all process graphs in a colony.

        Args:
            colonyname: Name of the colony
            prvkey: Private key for authentication
            state: Optional state filter
        """
        msg = {
            "msgtype": "removeallprocessgraphsmsg",
            "colonyname": colonyname
        }
        if state is not None:
            msg["state"] = state
        return self.__rpc(msg, prvkey)

    def get_processes_for_workflow(self, processgraphid, colonyname, prvkey, count=100):
        """Get all processes belonging to a workflow.

        Args:
            processgraphid: ID of the process graph
            colonyname: Name of the colony
            prvkey: Private key for authentication
            count: Maximum number to return

        Returns:
            List of processes in the workflow
        """
        msg = {
            "msgtype": "getprocessesmsg",
            "processgraphid": processgraphid,
            "colonyname": colonyname,
            "count": count,
            "state": -1
        }
        return self.__rpc(msg, prvkey)

    def remove_all_processes(self, colonyname, prvkey, state=-1):
        """Remove all processes in a colony.

        Args:
            colonyname: Name of the colony
            prvkey: Private key for authentication
            state: Optional state filter (-1 for all)
        """
        msg = {
            "msgtype": "removeallprocessesmsg",
            "colonyname": colonyname,
            "state": state
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
            if process.spec.nodename == nodename:
                return process
        return None
    
    def add_child(self, processgraphid, parentprocessid, childprocessid, funcspec: FuncSpec, nodename, insert, prvkey):
        funcspec.nodename = nodename
        msg = {
            "msgtype": "addchildmsg",
            "processgraphid": processgraphid,
            "parentprocessid": parentprocessid,
            "childprocessid": childprocessid,
            "insert": insert,
            "spec": funcspec.model_dump()
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
    
    def add_cron(self, cronname, cronexpr, wait, workflow: Workflow, colonyname, prvkey):
        workflowspec_str = json.dumps(workflow.model_dump(by_alias=True))
        workflowspec_str = workflowspec_str.replace('"', '\"')
        cron = {
                "name": cronname,
                "colonyname": colonyname,
                "interval": -1,
                "waitforprevprocessgrap": wait,
                "cronexpression": cronexpr,
                "workflowspec": workflowspec_str
               }

        msg = {
                "msgtype": "addcronmsg",
                "cron": cron
            }
        return self.__rpc(msg, prvkey)
    
    def get_cron(self, cronid, prvkey):
        msg = {
                "msgtype": "getcronmsg",
                "cronid": cronid
            }
        return self.__rpc(msg, prvkey)
    
    def get_crons(self, colonyname, count, prvkey):
        msg = {
                "msgtype": "getcronsmsg",
                "colonyname": colonyname,
                "count": count
            }
        return self.__rpc(msg, prvkey)
    
    def del_cron(self, cronid, prvkey):
        msg = {
                "msgtype": "removecronmsg",
                "all": False,
                "cronid": cronid
            }
        return self.__rpc(msg, prvkey)

    def run_cron(self, cronid, prvkey):
        """Manually trigger a cron job.

        Args:
            cronid: The cron ID to run
            prvkey: Private key for authentication

        Returns:
            The triggered process
        """
        msg = {
            "msgtype": "runcronmsg",
            "cronid": cronid
        }
        return self.__rpc(msg, prvkey)

    # Generator methods
    def get_generators(self, colonyname, prvkey, count=100):
        """Get all generators in a colony.

        Args:
            colonyname: Name of the colony
            prvkey: Private key for authentication
            count: Maximum number to return

        Returns:
            List of generators
        """
        msg = {
            "msgtype": "getgeneratorsmsg",
            "colonyname": colonyname,
            "count": count
        }
        return self.__rpc(msg, prvkey)

    def get_generator(self, generatorid, prvkey):
        """Get a specific generator by ID.

        Args:
            generatorid: The generator ID
            prvkey: Private key for authentication

        Returns:
            Generator details
        """
        msg = {
            "msgtype": "getgeneratormsg",
            "generatorid": generatorid
        }
        return self.__rpc(msg, prvkey)

    def add_generator(self, generator, prvkey):
        """Add a new generator.

        Args:
            generator: Generator specification object
            prvkey: Private key for authentication

        Returns:
            The created generator
        """
        msg = {
            "msgtype": "addgeneratormsg",
            "generator": generator
        }
        return self.__rpc(msg, prvkey)

    def remove_generator(self, generatorid, prvkey):
        """Remove a generator.

        Args:
            generatorid: The generator ID to remove
            prvkey: Private key for authentication
        """
        msg = {
            "msgtype": "removegeneratormsg",
            "generatorid": generatorid
        }
        return self.__rpc(msg, prvkey)

    # User methods
    def get_users(self, colonyname, prvkey):
        """Get all users in a colony.

        Args:
            colonyname: Name of the colony
            prvkey: Private key for authentication

        Returns:
            List of users
        """
        msg = {
            "msgtype": "getusersmsg",
            "colonyname": colonyname
        }
        return self.__rpc(msg, prvkey)

    def add_user(self, user, prvkey):
        """Add a new user to a colony.

        Args:
            user: User object with colonyname, userid, name, email, phone
            prvkey: Private key for authentication (colony owner)

        Returns:
            The created user
        """
        msg = {
            "msgtype": "addusermsg",
            "user": user
        }
        return self.__rpc(msg, prvkey)

    def remove_user(self, colonyname, name, prvkey):
        """Remove a user from a colony.

        Args:
            colonyname: Name of the colony
            name: Name of the user to remove
            prvkey: Private key for authentication (colony owner)
        """
        msg = {
            "msgtype": "removeusermsg",
            "colonyname": colonyname,
            "name": name
        }
        return self.__rpc(msg, prvkey)

    # File label methods
    def get_file_labels(self, colonyname, prvkey, name="", exact=False):
        """Get file labels in a colony.

        Args:
            colonyname: Name of the colony
            prvkey: Private key for authentication
            name: Optional name filter
            exact: If True, match name exactly

        Returns:
            List of file labels
        """
        msg = {
            "msgtype": "getfilelabelsmsg",
            "colonyname": colonyname,
            "name": name,
            "exact": exact
        }
        return self.__rpc(msg, prvkey)

    def __generate_random_id(self):
        random_uuid = uuid.uuid4()
        hasher = hashlib.sha256()
        hasher.update(random_uuid.bytes)
        return hasher.hexdigest()
    
    def __checksum_file(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                buffer = bytearray(10000)
                hasher = hashlib.sha256()
                while True:
                    n = f.readinto(buffer)
                    if not n:
                        break
                    hasher.update(buffer[:n])
            return hasher.hexdigest()
        except Exception as e:
            raise e 

    def __checksum_data(self, file_data):
        try:
            hasher = hashlib.sha256()
            hasher.update(file_data)
            return hasher.hexdigest()
        except Exception as e:
            raise e

    def __get_file_size(self, file_path):
        try:
            size = os.path.getsize(file_path)
            return size
        except OSError as e:
            print(f"Error getting file size: {e}")
            return None

    def __check_bucket(self, s3_client, bucket_name):
        try:
            s3_client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    s3_client.create_bucket(Bucket=bucket_name)
                except ClientError as e:
                    raise Exception(f"Error creating bucket: {e}")
            else:
                raise Exception(f"Error checking bucket: {e}")

    def upload_file(self, colonyname, prvkey, filepath=None, label=None):
        return self.__upload_file(filepath, label, colonyname, prvkey)
    
    def upload_data(self, colonyname, prvkey, filename=None, data=None, label=None):
        return self.__upload_file(filename, label, colonyname, prvkey, file_bytes=data)

    def __upload_file(self, filepath, label, colonyname, prvkey, file_bytes=None):
        endpoint = os.getenv("AWS_S3_ENDPOINT")
        access_key = os.getenv("AWS_S3_ACCESSKEY")
        secret_key = os.getenv("AWS_S3_SECRETKEY")
        region = os.getenv("AWS_S3_REGION")
        use_tls_str = os.getenv("AWS_S3_TLS")
        bucket_name = os.getenv("AWS_S3_BUCKET")
        skip_verify_str = os.getenv("AWS_S3_SKIPVERIFY")

        object_name = self.__generate_random_id()
        if file_bytes is None:
            filesize = self.__get_file_size(filepath)
        else:
            filesize = len(file_bytes)

        endpoint_parts = endpoint.split(":")
        if len(endpoint_parts) == 2:
            server = endpoint_parts[0]
            port = int(endpoint_parts[1])
        else:
            raise Exception("invalid endpoint")

        use_tls = use_tls_str.lower() in ['true', '1', 'yes']

        if not endpoint.startswith('http://') and not endpoint.startswith('https://'):
            endpoint = f"http{'s' if use_tls else ''}://{endpoint}"


        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            use_ssl=use_tls,
            verify=skip_verify_str.lower() not in ['true', '1', 'yes']
        )

        self.__check_bucket(s3_client, bucket_name)

        filename = os.path.basename(filepath)
        
        try:
            if file_bytes is None:
                s3_client.upload_file(filepath, bucket_name, object_name)
            else:
                # Upload byte array
                s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=file_bytes)
        except Exception as e:
            raise e

        if region == None:
            region = ""

        if use_tls_str == "true":
            tls = True
        else:
            tls = False

        obj = S3Object(
            server=server,
            port=port,
            tls=tls,
            accesskey="",
            secretkey="",
            region=region,
            encryptionkey="",
            encryptionalg="",
            object=object_name,
            bucket=bucket_name
        )

        ref = Reference(
            protocol="s3",
            s3object=obj
        )

        if file_bytes is None:
            checksum = self.__checksum_file(filepath)
        else:
            checksum = self.__checksum_data(file_bytes)

        f = File(
            fileid="",
            colonyname=colonyname,
            label=label,
            name=filename,
            size=filesize,
            sequencenr=1,
            checksum=checksum,
            checksumalg="SHA256",
            ref=ref
        )

        msg = {
            "msgtype": "addfilemsg",
            "file": f.model_dump(by_alias=True)
        }
       
        return self.__rpc(msg, prvkey)
    
    def get_file(self, colonyname, prvkey, label=None, fileid=None, filename=None, latest=True):
        if fileid is not None and filename is not None:
            raise ValueError("Both 'fileid' and 'filename' cannot be set at the same time. Please provide only one.")
        
        msg = {
            "msgtype": "getfilemsg",
            "colonyname": colonyname,
            "fileid": fileid,
            "label": label,
            "name": filename,
            "latest": latest
        }
        return self.__rpc(msg, prvkey)
    
    def __remove_file(self, label, fileid, name, colonyname, prvkey):
        if fileid is not None and name is not None:
            raise ValueError("Both 'fileid' and 'name' cannot be set at the same time. Please provide only one.")

        msg = {
            "msgtype": "removefilemsg",
            "colonyname": colonyname,
            "fileid": fileid,
            "label": label,
            "name": name
        }
        return self.__rpc(msg, prvkey)
    
    def download_file(self, colonyname, prvkey,  dst=None, label=None, fileid=None, filename=None, latest=True):
        if fileid is not None and filename is not None:
            raise ValueError("Both 'fileid' and 'filename' cannot be set at the same time. Please provide only one.")
        
        access_key = os.getenv("AWS_S3_ACCESSKEY")
        secret_key = os.getenv("AWS_S3_SECRETKEY")
        skip_verify_str = os.getenv("AWS_S3_SKIPVERIFY")
        
        dst = os.path.abspath(dst)

        try:
            os.makedirs(dst, exist_ok=True)
        except Exception as e:
            raise e

        file = self.get_file(colonyname, prvkey, label=label, fileid=fileid, filename=filename, latest=latest)

        if len(file) == 0:
            raise Exception("invalid file")

        object_name = file[0]["ref"]["s3object"]["object"]
        region = file[0]["ref"]["s3object"]["region"]
        endpoint = file[0]["ref"]["s3object"]["server"] + ":" + str(file[0]["ref"]["s3object"]["port"])
        use_tls = file[0]["ref"]["s3object"]["tls"]
        bucket_name = file[0]["ref"]["s3object"]["bucket"]

        verify = True
        if skip_verify_str:
            verify = skip_verify_str.lower() not in ['true', '1', 'yes']

        if not endpoint.startswith('http://') and not endpoint.startswith('https://'):
            endpoint = f"http{'s' if use_tls else ''}://{endpoint}"

        if region == "":
            region = None

        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            use_ssl=use_tls,
            verify=verify
        )

        dst = os.path.join(dst, filename)

        try:
            s3_client.download_file(bucket_name, object_name, dst)
            return dst
        except Exception as e:
            raise e

    def download_data(self, colonyname, prvkey, label=None, fileid=None, filename=None, latest=True):
        if fileid is not None and filename is not None:
            raise ValueError("Both 'fileid' and 'filename' cannot be set at the same time. Please provide only one.")
        
        access_key = os.getenv("AWS_S3_ACCESSKEY")
        secret_key = os.getenv("AWS_S3_SECRETKEY")
        skip_verify_str = os.getenv("AWS_S3_SKIPVERIFY")
       
        file = self.get_file(colonyname, prvkey, label=label, fileid=fileid, filename=filename, latest=latest)

        if len(file) == 0:
            raise Exception("invalid file")

        object_name = file[0]["ref"]["s3object"]["object"]
        region = file[0]["ref"]["s3object"]["region"]
        endpoint = file[0]["ref"]["s3object"]["server"] + ":" + str(file[0]["ref"]["s3object"]["port"])
        use_tls = file[0]["ref"]["s3object"]["tls"]
        bucket_name = file[0]["ref"]["s3object"]["bucket"]

        verify = True
        if skip_verify_str:
            verify = skip_verify_str.lower() not in ['true', '1', 'yes']

        if not endpoint.startswith('http://') and not endpoint.startswith('https://'):
            endpoint = f"http{'s' if use_tls else ''}://{endpoint}"

        if region == "":
            region = None

        try:
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
                use_ssl=use_tls,
                verify=verify
            )
        except Exception as e:
            raise e

        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=object_name)
            data = response['Body'].read()
            return data
        except Exception as e:
            raise e

    def delete_file(self, colonyname, prvkey, label=None, fileid=None, filename=None):
        if fileid is not None and filename is not None:
            raise ValueError("Both 'fileid' and 'name' cannot be set at the same time. Please provide only one.")

        access_key = os.getenv("AWS_S3_ACCESSKEY")
        secret_key = os.getenv("AWS_S3_SECRETKEY")
        skip_verify_str = os.getenv("AWS_S3_SKIPVERIFY")

        file = self.get_file(colonyname, prvkey, label=label, fileid=fileid, filename=filename)

        if len(file) == 0:
            raise Exception("invalid file")

        object_name = file[0]["ref"]["s3object"]["object"]
        region = file[0]["ref"]["s3object"]["region"]
        endpoint = file[0]["ref"]["s3object"]["server"] + ":" + str(file[0]["ref"]["s3object"]["port"])
        use_tls = file[0]["ref"]["s3object"]["tls"]
        bucket_name = file[0]["ref"]["s3object"]["bucket"]

        verify = True
        if skip_verify_str:
            verify = skip_verify_str.lower() not in ['true', '1', 'yes']

        if not endpoint.startswith('http://') and not endpoint.startswith('https://'):
            endpoint = f"http{'s' if use_tls else ''}://{endpoint}"

        if region == "":
            region = None

        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            use_ssl=use_tls,
            verify=verify
        )

        try:
            s3_client.delete_object(Bucket=bucket_name, Key=object_name)
        except Exception as e:
            raise e

        self.__remove_file(label, fileid, filename, colonyname, prvkey)

    # Channel methods
    def channel_append(self, processid, channel_name, sequence, payload, prvkey, in_reply_to=0, payload_type=""):
        """Append a message to a channel.

        Args:
            processid: The process ID that owns the channel
            channel_name: Name of the channel
            sequence: Client-assigned sequence number
            payload: Message payload (bytes or string)
            prvkey: Private key for authentication
            in_reply_to: Optional sequence number this message replies to
            payload_type: Optional message type ("", "end", "error")
        """
        if isinstance(payload, str):
            payload = payload.encode('utf-8')

        # Convert payload to array of bytes (like colonies-ts does)
        payload_array = list(payload)

        msg = {
            "msgtype": "channelappendmsg",
            "processid": processid,
            "name": channel_name,
            "sequence": sequence,
            "inreplyto": in_reply_to,
            "payload": payload_array,
            "payloadtype": payload_type
        }
        return self.__rpc(msg, prvkey)

    def channel_read(self, processid, channel_name, after_seq, limit, prvkey):
        """Read messages from a channel.

        Args:
            processid: The process ID that owns the channel
            channel_name: Name of the channel
            after_seq: Read messages after this sequence number (0 for all)
            limit: Maximum number of messages to return (0 for no limit)
            prvkey: Private key for authentication

        Returns:
            List of message entries with payload as bytes
        """
        msg = {
            "msgtype": "channelreadmsg",
            "processid": processid,
            "name": channel_name,
            "afterseq": after_seq,
            "limit": limit
        }
        entries = self.__rpc(msg, prvkey)

        # Decode payloads - could be array of ints or base64 string
        if entries:
            for entry in entries:
                if 'payload' in entry and entry['payload']:
                    payload = entry['payload']
                    if isinstance(payload, list):
                        # Array of bytes
                        entry['payload'] = bytes(payload)
                    elif isinstance(payload, str):
                        # Base64 encoded string
                        entry['payload'] = base64.b64decode(payload)

        return entries

    def subscribe_channel(self, processid, channel_name, prvkey, after_seq=0, timeout=30, callback=None):
        """Subscribe to channel messages via WebSocket.

        Args:
            processid: The process ID that owns the channel
            channel_name: Name of the channel
            prvkey: Private key for authentication
            after_seq: Start reading after this sequence number
            timeout: Timeout in seconds
            callback: Optional callback function(entries) called for each batch of messages.
                     If callback returns False, subscription ends.
                     If None, blocks and returns all messages when timeout or stream ends.

        Returns:
            If callback is None, returns list of all received messages
        """
        msg = {
            "processid": processid,
            "name": channel_name,
            "afterseq": after_seq,
            "timeout": timeout,
            "msgtype": "subscribechannelmsg"
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

        all_entries = []
        try:
            while True:
                data = ws.recv()
                reply_msg = json.loads(data)

                if reply_msg.get("error"):
                    payload_bytes = base64.b64decode(reply_msg["payload"])
                    error_msg = json.loads(payload_bytes)
                    raise ColoniesError(error_msg.get("message", "Channel subscription error"))

                payload_bytes = base64.b64decode(reply_msg["payload"])
                entries = json.loads(payload_bytes)

                # Decode payloads in entries - could be array of ints or base64 string
                if entries:
                    for entry in entries:
                        if 'payload' in entry and entry['payload']:
                            payload = entry['payload']
                            if isinstance(payload, list):
                                entry['payload'] = bytes(payload)
                            elif isinstance(payload, str):
                                entry['payload'] = base64.b64decode(payload)

                    if callback:
                        if callback(entries) == False:
                            break
                    else:
                        all_entries.extend(entries)
                else:
                    # Empty response indicates timeout
                    break
        finally:
            ws.close()

        if callback is None:
            return all_entries

    # Blueprint Definition methods
    def add_blueprint_definition(self, definition, prvkey):
        """Add a blueprint definition.

        Args:
            definition: Blueprint definition object with kind, metadata, spec
            prvkey: Private key for authentication (colony owner key required)

        Returns:
            The created blueprint definition
        """
        msg = {
            "msgtype": "addblueprintdefinitionmsg",
            "blueprintdefinition": definition
        }
        return self.__rpc(msg, prvkey)

    def get_blueprint_definition(self, colony_name, name, prvkey):
        """Get a blueprint definition by name.

        Args:
            colony_name: Name of the colony
            name: Name of the blueprint definition
            prvkey: Private key for authentication

        Returns:
            The blueprint definition
        """
        msg = {
            "msgtype": "getblueprintdefinitionmsg",
            "colonyname": colony_name,
            "name": name
        }
        return self.__rpc(msg, prvkey)

    def get_blueprint_definitions(self, colony_name, prvkey):
        """Get all blueprint definitions in a colony.

        Args:
            colony_name: Name of the colony
            prvkey: Private key for authentication

        Returns:
            List of blueprint definitions
        """
        msg = {
            "msgtype": "getblueprintdefinitionsmsg",
            "colonyname": colony_name
        }
        return self.__rpc(msg, prvkey)

    def remove_blueprint_definition(self, colony_name, name, prvkey):
        """Remove a blueprint definition.

        Args:
            colony_name: Name of the colony (namespace)
            name: Name of the blueprint definition to remove
            prvkey: Private key for authentication (colony owner key required)
        """
        msg = {
            "msgtype": "removeblueprintdefinitionmsg",
            "namespace": colony_name,
            "name": name
        }
        return self.__rpc(msg, prvkey)

    # Blueprint methods
    def add_blueprint(self, blueprint, prvkey):
        """Add a blueprint instance.

        Args:
            blueprint: Blueprint object with kind, metadata, handler, spec
            prvkey: Private key for authentication

        Returns:
            The created blueprint
        """
        msg = {
            "msgtype": "addblueprintmsg",
            "blueprint": blueprint
        }
        return self.__rpc(msg, prvkey)

    def get_blueprint(self, colony_name, name, prvkey):
        """Get a blueprint by name.

        Args:
            colony_name: Name of the colony (namespace)
            name: Name of the blueprint
            prvkey: Private key for authentication

        Returns:
            The blueprint
        """
        msg = {
            "msgtype": "getblueprintmsg",
            "namespace": colony_name,
            "name": name
        }
        return self.__rpc(msg, prvkey)

    def get_blueprints(self, colony_name, prvkey, kind=None, location=None):
        """Get blueprints in a colony, optionally filtered.

        Args:
            colony_name: Name of the colony (namespace)
            prvkey: Private key for authentication
            kind: Optional kind filter
            location: Optional location filter

        Returns:
            List of blueprints
        """
        msg = {
            "msgtype": "getblueprintsmsg",
            "namespace": colony_name
        }
        if kind:
            msg["kind"] = kind
        if location:
            msg["locationname"] = location
        return self.__rpc(msg, prvkey)

    def update_blueprint(self, blueprint, prvkey, force_generation=False):
        """Update an existing blueprint.

        Args:
            blueprint: Updated blueprint object
            prvkey: Private key for authentication
            force_generation: Force generation bump even if spec unchanged

        Returns:
            The updated blueprint
        """
        msg = {
            "msgtype": "updateblueprintmsg",
            "blueprint": blueprint,
            "forcegeneration": force_generation
        }
        return self.__rpc(msg, prvkey)

    def remove_blueprint(self, colony_name, name, prvkey):
        """Remove a blueprint.

        Args:
            colony_name: Name of the colony (namespace)
            name: Name of the blueprint to remove
            prvkey: Private key for authentication
        """
        msg = {
            "msgtype": "removeblueprintmsg",
            "namespace": colony_name,
            "name": name
        }
        return self.__rpc(msg, prvkey)

    def update_blueprint_status(self, colony_name, name, status, prvkey):
        """Update blueprint status (current state).

        Args:
            colony_name: Name of the colony
            name: Name of the blueprint
            status: Status object representing current state
            prvkey: Private key for authentication
        """
        msg = {
            "msgtype": "updateblueprintstatusmsg",
            "colonyname": colony_name,
            "blueprintname": name,
            "status": status
        }
        return self.__rpc(msg, prvkey)

    def reconcile_blueprint(self, colony_name, name, prvkey, force=False):
        """Trigger reconciliation for a blueprint.

        Args:
            colony_name: Name of the colony (namespace)
            name: Name of the blueprint
            prvkey: Private key for authentication
            force: Force reconciliation even if no changes detected

        Returns:
            The reconciliation process
        """
        msg = {
            "msgtype": "reconcileblueprintmsg",
            "namespace": colony_name,
            "name": name,
            "force": force
        }
        return self.__rpc(msg, prvkey)

    def get_blueprint_history(self, blueprint_id, prvkey, limit=None):
        """Get the history of changes for a specific blueprint.

        Args:
            blueprint_id: ID of the blueprint
            prvkey: Private key for authentication
            limit: Optional limit on number of history entries

        Returns:
            List of blueprint history entries
        """
        msg = {
            "msgtype": "getblueprinthistorymsg",
            "blueprintid": blueprint_id
        }
        if limit is not None:
            msg["limit"] = limit
        return self.__rpc(msg, prvkey)
