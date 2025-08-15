import requests
import json
from typing import List, Dict, Optional, Callable, Any
from model import Attribute, Process, FuncSpec, Workflow, ProcessGraph, Conditions, S3Object, Reference, File, Fs, FileData, Cron, Log, Executor, Colony, Statistics, Function, Snapshot, Allocations, Generator
import base64
from websocket import create_connection
import inspect
import os
import ctypes
from crypto import Crypto
import boto3
import hashlib
import uuid
from botocore.exceptions import ClientError

def colonies_client(native_crypto=False) -> tuple['Colonies', str, str, str, str]:
    colonies_server = os.getenv("COLONIES_SERVER_HOST")
    colonies_port = os.getenv("COLONIES_SERVER_PORT")
    colonies_tls = os.getenv("COLONIES_SERVER_TLS")
    colonyname = os.getenv("COLONIES_COLONY_NAME")
    colony_prvkey = os.getenv("COLONIES_COLONY_PRVKEY")
    executorname = os.getenv("COLONIES_EXECUTOR_NAME")
    prvkey = os.getenv("COLONIES_PRVKEY")

    if (
        colonies_server is None or
        colonies_port is None or
        colonyname is None or
        colony_prvkey is None or
        executorname is None or
        prvkey is None
    ):
        raise ValueError("Environment variables COLONIES_SERVER_HOST, COLONIES_SERVER_PORT, COLONIES_COLONY_NAME, and COLONIES_COLONY_PRVKEY must be set.")

    client = Colonies(colonies_server, int(colonies_port), colonies_tls == "true", native_crypto=native_crypto)

    return client, colonyname, colony_prvkey, executorname, prvkey

class ColoniesConnectionError(Exception):
    pass

class ColoniesError(Exception):
    pass

def func_spec(
    func: str | Callable,
    args: List[str | int],
    colonyname: str,
    executortype: str,
    executorname: str | None = None,
    priority: int = 1,
    maxexectime: int = -1,
    maxretries: int = -1,
    maxwaittime: int = -1,
    code: Optional[str] = None,
    kwargs: Optional[Dict] = None,
    fs: Optional[Fs] = None
) -> FuncSpec:
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
    url: str
    host: str
    port: int
    tls: bool
    native_crypto: bool

    WAITING = 0
    RUNNING = 1
    SUCCESSFUL = 2
    FAILED = 3

    def __init__(self, host: str, port: int, tls: bool = False, native_crypto: bool = False) -> None:
        self.host = host
        self.port = port
        self.native_crypto = native_crypto
        self.tls = tls
        self.url = ("https://" if self.tls else "http://") + self.host + ":" + str(self.port) + "/api"

    def __rpc(self, msg: Dict[str, Any], prvkey: str) -> Dict[str, Any] | List[Any]:
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
            if reply_msg_json.get("error", False):
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

    def add_colony(self, colony: Dict[str, str], prvkey: str) -> Colony:
        msg = {
            "msgtype": "addcolonymsg",
            "colony": colony
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return Colony(**response)

    def del_colony(self, colonyname: str, prvkey: str) -> None:
        msg = {
            "msgtype": "removecolonymsg",
            "colonyname": colonyname
        }
        self.__rpc(msg, prvkey)

    def list_colonies(self, prvkey: str) -> List[Colony]:
        msg = {
            "msgtype": "getcoloniesmsg",
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, list):
            raise ColoniesError("Expected response to be a list")
        return [Colony(**item) for item in response]

    def get_colony(self, colonyname: str, prvkey: str) -> Colony:
        msg = {
            "msgtype": "getcolonymsg",
            "colonyname": colonyname
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return Colony(**response)

    def add_executor(self, executor: Dict[str, str], prvkey: str) -> Executor:
        msg = {
            "msgtype": "addexecutormsg",
            "executor": executor
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return Executor(**response)

    def report_allocation(self, colonyname: str, executorname: str, allocations: Allocations, prvkey: str) -> None:
        """
        Reports resource allocations for an executor.
        """
        msg = {
            "msgtype": "reportallocationmsg",
            "colonyname": colonyname,
            "executorname": executorname,
            "allocations": allocations.model_dump(by_alias=True)
        }
        self.__rpc(msg, prvkey)

    def list_executors(self, colonyname: str, prvkey: str) -> List[Executor]:
        msg = {
            "msgtype": "getexecutorsmsg",
            "colonyname": colonyname
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, list):
            raise ColoniesError("Expected response to be a list")
        return [Executor(**item) for item in response]

    def approve_executor(self, colonyname: str, executorname: str, prvkey: str) -> None:
        msg = {
            "msgtype": "approveexecutormsg",
            "colonyname": colonyname,
            "executorname": executorname
        }
        self.__rpc(msg, prvkey)

    def reject_executor(self, colonyname: str, executorname: str, prvkey: str) -> None:
        msg = {
            "msgtype": "rejectexecutormsg",
            "colonyname": colonyname,
            "executorname": executorname
        }
        self.__rpc(msg, prvkey)

    def remove_executor(self, colonyname: str, executorname: str, prvkey: str) -> None:
        msg = {
            "msgtype": "removeexecutormsg",
            "colonyname": colonyname,
            "executorname": executorname
        }
        self.__rpc(msg, prvkey)

    def get_executor(self, colonyname: str, executorname: str, prvkey: str) -> Executor:
        msg = {
            "msgtype": "getexecutormsg",
            "colonyname": colonyname,
            "executorname": executorname
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return Executor(**response)

    def submit_func_spec(self, spec: FuncSpec, prvkey) -> Process:
        msg = {
            "msgtype": "submitfuncspecmsg",
            "spec": spec.model_dump(by_alias=True)
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return Process(**response)

    def submit_workflow(self, workflow: Workflow, prvkey) -> ProcessGraph:
        msg = {
            "msgtype": "submitworkflowspecmsg",
            "spec": workflow.model_dump(by_alias=True)
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return ProcessGraph(**response)

    def assign(
        self,
        colonyname: str,
        timeout: int,
        prvkey: str,
        available_cpu: str = "1000m",
        available_mem: str = "1000Mi"
    ) -> Process:
        msg = {
            "msgtype": "assignprocessmsg",
            "colonyname": colonyname,
            "timeout": timeout,
            "availablecpu": available_cpu,
            "availablemem": available_mem
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return Process(**response)

    def list_processes(self, colonyname: str, count: int, state: int, prvkey: str) -> List[Process]:
        msg = {
            "msgtype": "getprocessesmsg",
            "colonyname": colonyname,
            "count": count,
            "state": state
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, list):
            raise ColoniesError("Expected response to be a list")
        return [Process(**item) for item in response]

    def get_process(self, processid: str, prvkey: str) -> Process:
        msg = {
            "msgtype": "getprocessmsg",
            "processid": processid
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return Process(**response)

    def remove_process(self, processid: str, prvkey: str) -> None:
        msg = {
            "msgtype": "removeprocessmsg",
            "processid": processid
        }
        self.__rpc(msg, prvkey)

    def close(self, processid: str, output: List[Any], prvkey: str) -> None:
        msg = {
            "msgtype": "closesuccessfulmsg",
            "processid": processid,
            "out": output
        }
        self.__rpc(msg, prvkey)

    def fail(self, processid: str, errors: List[str], prvkey: str) -> None:
        msg = {
            "msgtype": "closefailedmsg",
            "processid": processid,
            "errors": errors
        }
        self.__rpc(msg, prvkey)

    def set_output(self, processid: str, arr: List[Any], prvkey: str) -> None:
        msg = {
            "msgtype": "setoutputmsg",
            "processid": processid,
            "out": arr
        }
        self.__rpc(msg, prvkey)

    def stats(self, colonyname: str, prvkey: str) -> Statistics:
        msg = {
            "msgtype": "getcolonystatsmsg",
            "colonyname": colonyname
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return Statistics(**response)

    def add_attribute(self, processid: str, key: str, value: str, prvkey: str) -> Attribute:
        attribute = {
            "key": key,
            "value": value,
            "targetid": processid,
            "attributetype": 1
        }
        msg = {
            "msgtype": "addattributemsg",
            "attribute": attribute
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return Attribute(**response)

    def get_attribute(self, attributeid: str, prvkey: str) -> Attribute:
        msg = {
            "msgtype": "getattributemsg",
            "attributeid": attributeid
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return Attribute(**response)

    def get_processgraph(self, processgraphid: str, prvkey: str) -> ProcessGraph:  # TODO: unittest
        msg = {
            "msgtype": "getprocessgraphmsg",
            "processgraphid": processgraphid
        }
        graph = self.__rpc(msg, prvkey)
        if not isinstance(graph, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return ProcessGraph(**graph)

    def add_function(self, colonyname: str, executorname: str, funcname: str, prvkey: str) -> Function:
        func = {
            "colonyname": colonyname,
            "executorname": executorname,
            "funcname": funcname,
        }
        msg = {
            "msgtype": "addfunctionmsg",
            "fun": func
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return Function(**response)

    def get_functions_by_executor(self, colonyname: str, executorname: str, prvkey: str) -> List[Function]:
        msg = {
            "msgtype": "getfunctionsmsg",
            "colonyname": colonyname,
            "executorname": executorname
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, list):
            raise ColoniesError("Expected response to be a list")
        return [Function(**item) for item in response]

    def get_functions_by_colony(self, colonyname: str, prvkey: str) -> List[Function]:
        msg = {
            "msgtype": "getfunctionsmsg",
            "colonyname": colonyname
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, list):
            raise ColoniesError("Expected response to be a list")
        return [Function(**item) for item in response]

    def find_process(self, nodename: str, processids: List[str], prvkey: str) -> Optional[Process]:
        for processid in processids:
            process = self.get_process(processid, prvkey)
            if process.spec.nodename == nodename:
                return process
        return None

    def add_child(
        self,
        processgraphid: str,
        parentprocessid: str,
        childprocessid: str,
        funcspec: FuncSpec,
        nodename: str,
        insert: bool,
        prvkey: str
    ) -> Process:
        funcspec.nodename = nodename
        msg = {
            "msgtype": "addchildmsg",
            "processgraphid": processgraphid,
            "parentprocessid": parentprocessid,
            "childprocessid": childprocessid,
            "insert": insert,
            "spec": funcspec.model_dump()
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return Process(**response)

    def create_snapshot(self, colonyname: str, label: str, name: str, prvkey: str) -> Snapshot:
        msg = {
            "msgtype": "createsnapshotmsg",
            "colonyname": colonyname,
            "label": label,
            "name": name
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return Snapshot(**response)

    def get_snapshots(self, colonyname: str, prvkey: str) -> List[Snapshot]:
        msg = {
            "msgtype": "getsnapshotsmsg",
            "colonyname": colonyname,
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, list):
            raise ColoniesError("Expected response to be a list")
        return [Snapshot(**item) for item in response]

    def get_snapshot_by_name(self, colonyname: str, name: str, prvkey: str) -> Snapshot:
        msg = {
            "msgtype": "getsnapshotmsg",
            "colonyname": colonyname,
            "snapshotid": "",
            "name": name
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return Snapshot(**response)

    def get_snapshot_by_id(self, colonyname: str, snapshotid: str, prvkey: str) -> Snapshot:
        msg = {
            "msgtype": "getsnapshotmsg",
            "colonyname": colonyname,
            "snapshotid": snapshotid,
            "name": ""
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return Snapshot(**response)

    def add_log(self, processid: str, logmsg: str, prvkey: str) -> None:
        msg = {
            "msgtype": "addlogmsg",
            "processid": processid,
            "message": logmsg
        }
        self.__rpc(msg, prvkey)

    def get_process_log(self, colonyname: str, processid: str, count: int, since: int, prvkey: str) -> List[Log]:
        msg = {
            "msgtype": "getlogsmsg",
            "colonyname": colonyname,
            "executorname": "",
            "processid": processid,
            "count": count,
            "since": since
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, list):
            raise ColoniesError("Expected response to be a list")
        return [Log(**item) for item in response]

    def get_executor_log(self, colonyname: str, executorname: str, count: int, since: int, prvkey: str) -> List[Log]:
        msg = {
            "msgtype": "getlogsmsg",
            "colonyname": colonyname,
            "executorname": executorname,
            "processid": "",
            "count": count,
            "since": since
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, list):
            raise ColoniesError("Expected response to be a list")
        return [Log(**item) for item in response]

    def sync(self, dir: str, label: str, keeplocal: bool, colonyname: str, prvkey: str) -> None:
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

    def get_files(self, label: str, colonyname: str, prvkey: str) -> List[FileData]:
        msg = {
            "msgtype": "getfilesmsg",
            "colonyname": colonyname,
            "label": label
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, list):
            raise ColoniesError("Expected response to be a list")
        return [FileData(**item) for item in response]

    def add_cron(
        self,
        cronname: str,
        cronexpr: str,
        wait: bool,
        workflow: Workflow,
        colonyname: str,
        prvkey: str
    ) -> Cron:
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
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return Cron(**response)

    def get_cron(self, cronid: str, prvkey: str) -> Cron:
        msg = {
            "msgtype": "getcronmsg",
            "cronid": cronid
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return Cron(**response)

    def run_cron(self, cronid, prvkey):
        msg = {
            "msgtype": "runcronmsg",
            "cronid": cronid
        }
        return self.__rpc(msg, prvkey)

    def resolve_generator_by_name(self, colonyname, generatorname, prvkey):
        msg = {
            "msgtype": "resolvegeneratormsg",
            "colonyname": colonyname,
            "generatorname": generatorname
        }
        return self.__rpc(msg, prvkey)

    def change_colony_id(self, colonyname, new_colony_id, prvkey):
        msg = {
            "msgtype": "changecolonyidmsg",
            "colonyname": colonyname,
            "colonyid": new_colony_id
        }
        self.__rpc(msg, prvkey)

    def change_executor_id(self, colonyname, new_executor_id, prvkey):
        msg = {
            "msgtype": "changeexecutoridmsg",
            "colonyname": colonyname,
            "executorid": new_executor_id
        }
        self.__rpc(msg, prvkey)

    def change_user_id(self, colonyname, new_user_id, prvkey):
        msg = {
            "msgtype": "changeuseridmsg",
            "colonyname": colonyname,
            "userid": new_user_id
        }
        self.__rpc(msg, prvkey)

    def change_server_id(self, new_server_id, prvkey):
        msg = {
            "msgtype": "changeserveridmsg",
            "serverid": new_server_id
        }
        self.__rpc(msg, prvkey)

    def get_crons(self, colonyname: str, count: int, prvkey: str) -> List[Cron]:
        msg = {
            "msgtype": "getcronsmsg",
            "colonyname": colonyname,
            "count": count
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, list):
            raise ColoniesError("Expected response to be a list")
        return [Cron(**item) for item in response]

    def del_cron(self, cronid: str, prvkey: str) -> None:
        msg = {
            "msgtype": "removecronmsg",
            "all": False,
            "cronid": cronid
        }
        self.__rpc(msg, prvkey)

    def __generate_random_id(self) -> str:
        random_uuid = uuid.uuid4()
        hasher = hashlib.sha256()
        hasher.update(random_uuid.bytes)
        return hasher.hexdigest()

    def __checksum_file(self, file_path: str) -> str:
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

    def __checksum_data(self, file_data: bytes) -> str:
        try:
            hasher = hashlib.sha256()
            hasher.update(file_data)
            return hasher.hexdigest()
        except Exception as e:
            raise e

    def __get_file_size(self, file_path: str) -> Optional[int]:
        try:
            size = os.path.getsize(file_path)
            return size
        except OSError as e:
            print(f"Error getting file size: {e}")
            return None

    def __check_bucket(self, s3_client: Any, bucket_name: str) -> None:
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

    def upload_file(
        self,
        colonyname: str,
        prvkey: str,
        filepath: str,
        label: str
    ) -> File:
        return self.__upload_file(filepath, label, colonyname, prvkey)

    def upload_data(
        self,
        colonyname: str,
        prvkey: str,
        filename: str,
        data: bytes,
        label: str
    ) -> File:
        return self.__upload_file(filename, label, colonyname, prvkey, file_bytes=data)

    def __upload_file(
        self,
        filepath: str,
        label: str,
        colonyname: str,
        prvkey: str,
        file_bytes: Optional[bytes] = None
    ) -> File:
        endpoint = os.getenv("AWS_S3_ENDPOINT")
        access_key = os.getenv("AWS_S3_ACCESSKEY")
        secret_key = os.getenv("AWS_S3_SECRETKEY")
        region = os.getenv("AWS_S3_REGION")
        use_tls_str = os.getenv("AWS_S3_TLS")
        bucket_name = os.getenv("AWS_S3_BUCKET")
        skip_verify_str = os.getenv("AWS_S3_SKIPVERIFY")

        if endpoint is None:
            raise ValueError("Environment variable AWS_S3_ENDPOINT is not set")
        if access_key is None:
            raise ValueError("Environment variable AWS_S3_ACCESSKEY is not set")
        if secret_key is None:
            raise ValueError("Environment variable AWS_S3_SECRETKEY is not set")
        if region is None:
            raise ValueError("Environment variable AWS_S3_REGION is not set")
        if use_tls_str is None:
            raise ValueError("Environment variable AWS_S3_TLS is not set")
        if bucket_name is None:
            raise ValueError("Environment variable AWS_S3_BUCKET is not set")
        if skip_verify_str is None:
            raise ValueError("Environment variable AWS_S3_SKIPVERIFY is not set")

        object_name = self.__generate_random_id()
        if file_bytes is None:
            filesize = self.__get_file_size(filepath)
            if filesize is None:
                raise ValueError(f"Could not get file size of {filepath}")
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

        response = self.__rpc(msg, prvkey)
        if not isinstance(response, dict):
            raise ColoniesError("Expected response to be a dictionary")
        return File(**response)

    def get_file(
        self,
        colonyname: str,
        prvkey: str,
        label: str,
        filename: str,
        fileid: Optional[str] = None,
        latest: bool = True
    ) -> List[File]:
        msg = {
            "msgtype": "getfilemsg",
            "colonyname": colonyname,
            "fileid": fileid,
            "label": label,
            "name": filename,
            "latest": latest
        }
        response = self.__rpc(msg, prvkey)
        if not isinstance(response, list):
            raise ColoniesError("Expected response to be a list")
        return [File(**item) for item in response]

    def __remove_file(
        self,
        label: Optional[str],
        fileid: Optional[str],
        name: Optional[str],
        colonyname: str,
        prvkey: str
    ) -> None:
        if fileid is not None and name is not None:
            raise ValueError("Both 'fileid' and 'name' cannot be set at the same time. Please provide only one.")

        msg = {
            "msgtype": "removefilemsg",
            "colonyname": colonyname,
            "fileid": fileid,
            "label": label,
            "name": name
        }
        self.__rpc(msg, prvkey)

    def download_file(
        self,
        colonyname: str,
        prvkey: str,
        dst: str,
        label: str,
        filename: str,
        fileid: Optional[str] = None,
        latest: bool = True
    ) -> str:
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

        object_name = file[0].ref.s3object.object
        region = file[0].ref.s3object.region
        endpoint = file[0].ref.s3object.server + ":" + str(file[0].ref.s3object.port)
        use_tls = file[0].ref.s3object.tls
        bucket_name = file[0].ref.s3object.bucket

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

    def download_data(
        self,
        colonyname: str,
        prvkey: str,
        label: str,
        filename: str,
        fileid: Optional[str] = None,
        latest: bool = True
    ) -> bytes:
        if fileid is not None and filename is not None:
            raise ValueError("Both 'fileid' and 'filename' cannot be set at the same time. Please provide only one.")

        access_key = os.getenv("AWS_S3_ACCESSKEY")
        secret_key = os.getenv("AWS_S3_SECRETKEY")
        skip_verify_str = os.getenv("AWS_S3_SKIPVERIFY")

        file = self.get_file(colonyname, prvkey, label=label, fileid=fileid, filename=filename, latest=latest)

        if len(file) == 0:
            raise Exception("invalid file")

        object_name = file[0].ref.s3object.object
        region = file[0].ref.s3object.region
        endpoint = file[0].ref.s3object.server + ":" + str(file[0].ref.s3object.port)
        use_tls = file[0].ref.s3object.tls
        bucket_name = file[0].ref.s3object.bucket

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

    def delete_file(
        self,
        colonyname: str,
        prvkey: str,
        filename: str,
        label: str,
        fileid: Optional[str] = None
    ) -> None:
        if fileid is not None and filename is not None:
            raise ValueError("Both 'fileid' and 'name' cannot be set at the same time. Please provide only one.")

        access_key = os.getenv("AWS_S3_ACCESSKEY")
        secret_key = os.getenv("AWS_S3_SECRETKEY")
        skip_verify_str = os.getenv("AWS_S3_SKIPVERIFY")

        file = self.get_file(colonyname, prvkey, label=label, fileid=fileid, filename=filename)

        if len(file) == 0:
            raise Exception("invalid file")

        object_name = file[0].ref.s3object.object
        region = file[0].ref.s3object.region
        endpoint = file[0].ref.s3object.server + ":" + str(file[0].ref.s3object.port)
        use_tls = file[0].ref.s3object.tls
        bucket_name = file[0].ref.s3object.bucket

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
