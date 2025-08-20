import requests
import json
from typing import List, Optional, Any, TypeVar, Type
from pydantic import TypeAdapter, ValidationError
import base64
from websocket import create_connection
import os
import ctypes
import boto3
import hashlib
import uuid
from botocore.exceptions import ClientError

from crypto import Crypto
import rpc
from model import (
    Attribute, Empty, Process, FuncSpec, Workflow, ProcessGraph, S3Object, Reference, File, FileData, Cron, Log, Executor, Colony, 
    Statistics, Function, Snapshot, Allocations, Generator
)

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

T = TypeVar('T')

class ColoniesConnectionError(Exception):
    pass

class ColoniesError(Exception):
    pass

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

    def __rpc(
        self,
        request_payload: rpc.RequestPayload,
        prvkey: str,
        response_payload_type: Type[T]
    ) -> T:
        request_payload_json = request_payload.model_dump_json(by_alias=True)
        request_payload_b64 = str(base64.b64encode(request_payload_json.encode('utf-8')), "utf-8")
        crypto = Crypto(native=self.native_crypto)
        signature = crypto.sign(request_payload_b64, prvkey)

        request = rpc.Request(
            payloadtype=request_payload.msgtype,
            payload=request_payload_b64,
            signature=signature
        )

        request_json = request.model_dump_json()

        try:
            http_response = requests.post(url = self.url, data=request_json, verify=True)
            http_response.raise_for_status()
            response = rpc.Response.model_validate_json(http_response.content)
            response_payload_json = base64.b64decode(response.payload)
            if response.payloadtype == "error":
                error_payload = rpc.ErrorResponse.model_validate_json(response_payload_json)
                raise ColoniesConnectionError(error_payload.message)
            return TypeAdapter(response_payload_type).validate_json(response_payload_json)
        except requests.exceptions.RequestException as err:
            raise ColoniesConnectionError(f"Network request failed: {err}") from err
        except ValidationError as err:
            raise ColoniesError(f"API response validation failed: {err}") from err
        except UnicodeDecodeError as err:
            raise ColoniesError(f"Failed to decode response payload: {err}") from err

    def wait(self, process: Process, timeout: int, executor_prvkey: str) -> Process:
        state = Colonies.SUCCESSFUL
        if not process.spec.conditions:
            raise ValueError("Process must have conditions set")
        if not process.spec.conditions.colonyname:
            raise ValueError("Process must have a colony name set in its conditions")
        payload = rpc.SubscribeProcess(
            processid=process.processid,
            executortype=process.spec.conditions.executortype,
            state=state,
            timeout=timeout,
            colonyname=process.spec.conditions.colonyname,
        )

        payload_dict = payload.model_dump(by_alias=True)
        payload_b64 = str(base64.b64encode(json.dumps(payload_dict).encode('utf-8')), "utf-8")
        request = rpc.Request(payloadtype=payload.msgtype, payload=payload_b64, signature="")

        crypto = Crypto()
        request.signature = crypto.sign(request.payload, executor_prvkey)

        ws = create_connection(("wss://" if self.tls else "ws://") + self.host + ":" + str(self.port) + "/pubsub")
        ws.send(request.model_dump_json())
        ws.recv()
        ws.close()

        return self.get_process(process.processid, executor_prvkey)

    def add_colony(self, colony: Colony, server_prvkey: str) -> Colony:
        payload = rpc.AddColony(colony=colony)
        return self.__rpc(payload, server_prvkey, Colony)

    def del_colony(self, colonyname: str, server_prvkey: str) -> None:
        payload = rpc.RemoveColony(colonyname=colonyname)
        self.__rpc(payload, server_prvkey, Colony)

    def list_colonies(self, server_prvkey: str) -> List[Colony]:
        payload = rpc.GetColonies()
        return self.__rpc(payload, server_prvkey, List[Colony])

    def get_colony(self, colonyname: str, server_prvkey: str) -> Colony:
        payload = rpc.GetColony(colonyname=colonyname)
        return self.__rpc(payload, server_prvkey, Colony)

    def add_executor(
        self,
        executorid: str,
        executorname: str,
        executortype: str,
        colonyname: str,
        colony_prvkey: str,
        capabilities: Optional[rpc.Capabilities] = None
    ) -> Executor:
        payload = rpc.Executor(
            executorid=executorid,
            executortype=executortype,
            executorname=executorname,
            colonyname=colonyname,
            capabilities=capabilities
        )
        payload = rpc.AddExecutor(executor=payload)
        return self.__rpc(payload, colony_prvkey, Executor)

    def report_allocation(self, colonyname: str, executorname: str, allocations: Allocations, executor_prvkey: str) -> None:
        """
        Reports resource allocations for an executor.
        """
        payload = rpc.ReportAllocations(
            colonyname=colonyname,
            executorname=executorname,
            allocations=allocations
        )
        self.__rpc(payload, executor_prvkey, Empty)

    def list_executors(self, colonyname: str, executor_prvkey: str) -> List[Executor]:
        payload = rpc.GetExecutors(colonyname=colonyname)
        return self.__rpc(payload, executor_prvkey, List[Executor])

    def approve_executor(self, colonyname: str, executorname: str, colony_prvkey: str) -> None:
        payload = rpc.ApproveExecutor(colonyname=colonyname, executorname=executorname)
        self.__rpc(payload, colony_prvkey, Empty)

    def reject_executor(self, colonyname: str, executorname: str, colony_prvkey: str) -> None:
        payload = rpc.RejectExecutor(colonyname=colonyname, executorname=executorname)
        self.__rpc(payload, colony_prvkey, Empty)

    def remove_executor(self, colonyname: str, executorname: str, colony_prvkey: str) -> None:
        payload = rpc.RemoveExecutor(colonyname=colonyname, executorname=executorname)
        self.__rpc(payload, colony_prvkey, Empty)

    def get_executor(self, colonyname: str, executorname: str, executor_prvkey: str) -> Executor:
        payload = rpc.GetExecutor(colonyname=colonyname, executorname=executorname)
        return self.__rpc(payload, executor_prvkey, Executor)

    def submit_func_spec(self, spec: FuncSpec, executor_prvkey: str) -> Process:
        payload = rpc.SubmitFunctionSpec(spec=spec)
        return self.__rpc(payload, executor_prvkey, Process)

    def submit_workflow(self, workflow: Workflow, executor_prvkey: str) -> ProcessGraph:
        payload = rpc.SubmitWorkflowSpec(spec=workflow)
        return self.__rpc(payload, executor_prvkey, ProcessGraph)

    def assign(
        self,
        colonyname: str,
        timeout: int,
        executor_prvkey: str,
        available_cpu: str = "1000m",
        available_mem: str = "1000Mi"
    ) -> Process:
        payload = rpc.AssignProcess(
            colonyname=colonyname,
            timeout=timeout,
            availablecpu=available_cpu,
            availablemem=available_mem
        )
        return self.__rpc(payload, executor_prvkey, Process)

    def list_processes(self, colonyname: str, count: int, state: int, executor_prvkey: str) -> List[Process]:
        payload = rpc.GetProcesses(
            colonyname=colonyname,
            count=count,
            state=state
        )
        return self.__rpc(payload, executor_prvkey, List[Process])

    def get_process(self, processid: str, executor_prvkey: str) -> Process:
        payload = rpc.GetProcess(processid=processid)
        return self.__rpc(payload, executor_prvkey, Process)

    def remove_process(self, processid: str, executor_prvkey: str, all: bool = False) -> None:
        payload = rpc.RemoveProcess(processid=processid, all=all)
        self.__rpc(payload, executor_prvkey, Empty)

    def close(self, processid: str, output: List[Any], executor_prvkey: str) -> None:
        payload = rpc.CloseSuccessful(processid=processid, out=output)
        self.__rpc(payload, executor_prvkey, Empty)

    def fail(self, processid: str, errors: List[str], executor_prvkey: str) -> None:
        payload = rpc.CloseFailed(processid=processid, errors=errors)
        self.__rpc(payload, executor_prvkey, Empty)

    def set_output(self, processid: str, arr: List[Any], executor_prvkey: str) -> None:
        payload = rpc.SetOutput(processid=processid, out=arr)
        self.__rpc(payload, executor_prvkey, Empty)

    def stats(self, colonyname: str, executor_prvkey: str) -> Statistics:
        payload = rpc.GetColonyStatistics(colonyname=colonyname)
        return self.__rpc(payload, executor_prvkey, Statistics)

    def add_attribute(self, processid: str, key: str, value: str, executor_prvkey: str) -> Attribute:
        attribute = rpc.Attribute(
            key=key,
            value=value,
            targetid=processid,
            attributetype=1
        )
        payload = rpc.AddAttribute(attribute=attribute)
        return self.__rpc(payload, executor_prvkey, Attribute)

    def get_attribute(self, attributeid: str, executor_prvkey: str) -> Attribute:
        payload = rpc.GetAttribute(attributeid=attributeid)
        return self.__rpc(payload, executor_prvkey, Attribute)

    def get_processgraph(self, processgraphid: str, executor_prvkey: str) -> ProcessGraph:  # TODO: unittest
        payload = rpc.GetProcessGraph(processgraphid=processgraphid)
        return self.__rpc(payload, executor_prvkey, ProcessGraph)

    def add_function(self, colonyname: str, executorname: str, funcname: str, executor_prvkey: str) -> Function:
        func = rpc.Function(
            colonyname=colonyname,
            executorname=executorname,
            funcname=funcname,
        )
        payload = rpc.AddFunction(fun=func)
        return self.__rpc(payload, executor_prvkey, Function)

    def get_functions_by_executor(self, colonyname: str, executorname: str, executor_prvkey: str) -> List[Function]:
        payload = rpc.GetFunctions(
            colonyname=colonyname,
            executorname=executorname
        )
        return self.__rpc(payload, executor_prvkey, List[Function])

    def get_functions_by_colony(self, colonyname: str, executor_prvkey: str) -> List[Function]:
        payload = rpc.GetFunctions(colonyname=colonyname)
        return self.__rpc(payload, executor_prvkey, List[Function])

    def find_process(self, nodename: str, processids: List[str], executor_prvkey: str) -> Optional[Process]:
        for processid in processids:
            process = self.get_process(processid, executor_prvkey)
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
        executor_prvkey: str
    ) -> Process:
        funcspec.nodename = nodename
        payload = rpc.AddChild(
            processgraphid=processgraphid,
            parentprocessid=parentprocessid,
            childprocessid=childprocessid,
            insert=insert,
            spec=funcspec
        )
        return self.__rpc(payload, executor_prvkey, Process)

    def create_snapshot(self, colonyname: str, label: str, name: str, executor_prvkey: str) -> Snapshot:
        payload = rpc.CreateSnapshot(colonyname=colonyname, label=label, name=name)
        return self.__rpc(payload, executor_prvkey, Snapshot)

    def get_snapshots(self, colonyname: str, executor_prvkey: str) -> List[Snapshot]:
        payload = rpc.GetSnapshot(colonyname=colonyname)
        return self.__rpc(payload, executor_prvkey, List[Snapshot])

    def get_snapshot_by_name(self, colonyname: str, name: str, executor_prvkey: str) -> Snapshot:
        payload = rpc.GetSnapshot(colonyname=colonyname, name=name)
        return self.__rpc(payload, executor_prvkey, Snapshot)

    def get_snapshot_by_id(self, colonyname: str, snapshotid: str, executor_prvkey: str) -> Snapshot:
        payload = rpc.GetSnapshot(colonyname=colonyname, snapshotid=snapshotid,)
        return self.__rpc(payload, executor_prvkey, Snapshot)

    def add_log(self, processid: str, logmsg: str, executor_prvkey: str) -> None:
        payload = rpc.AddLog(processid=processid, message=logmsg)
        self.__rpc(payload, executor_prvkey, Empty)

    def get_process_log(self, colonyname: str, processid: str, count: int, since: int, executor_prvkey: str) -> List[Log]:
        payload = rpc.GetLogs(
            colonyname=colonyname,
            executorname="",
            processid=processid,
            count=count,
            since=since
        )
        return self.__rpc(payload, executor_prvkey, List[Log])

    def get_executor_log(self, colonyname: str, executorname: str, count: int, since: int, executor_prvkey: str) -> List[Log]:
        payload = rpc.GetLogs(
            colonyname=colonyname,
            executorname=executorname,
            processid="",
            count=count,
            since=since
        )
        return self.__rpc(payload, executor_prvkey, List[Log])

    def sync(self, dir: str, label: str, keeplocal: bool, colonyname: str, executor_prvkey: str) -> None:
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
        c_prvkey = ctypes.c_char_p(executor_prvkey.encode('utf-8'))

        res = c_lib.sync(c_host, c_port, c_insecure, c_skip_tls_verify, c_dir, c_label, c_keeplocal, c_colonyname, c_prvkey)
        if res != 0:
            raise Exception("failed to sync")

    def get_files(self, label: str, colonyname: str, executor_prvkey: str) -> List[FileData]:
        payload = rpc.GetFiles(colonyname=colonyname, label=label)
        return self.__rpc(payload, executor_prvkey, List[FileData])

    def add_cron(
        self,
        cronname: str,
        cronexpr: str,
        wait: bool,
        workflow: Workflow,
        colonyname: str,
        executor_prvkey: str,
        random:bool=False
    ) -> Cron:
        cron = rpc.Cron(
            name=cronname,
            colonyname=colonyname,
            interval=-1,  # -1 means cron expression is used
            waitforprevprocessgraph=wait,
            cronexpression=cronexpr,
            workflowspec=json.dumps(workflow.model_dump(by_alias=True)),
            random=random,
        )
        payload = rpc.AddCron(cron=cron)
        return self.__rpc(payload, executor_prvkey, Cron)

    def get_cron(self, cronid: str, executor_prvkey: str) -> Cron:
        payload = rpc.GetCron(cronid=cronid)
        return self.__rpc(payload, executor_prvkey, Cron)

    def get_crons(self, colonyname: str, count: int, executor_prvkey: str) -> List[Cron]:
        payload = rpc.GetCrons(colonyname=colonyname, count=count)
        return self.__rpc(payload, executor_prvkey, List[Cron])

    def del_cron(self, cronid: str, executor_prvkey: str, all: bool=False) -> None:
        payload = rpc.RemoveCron(all=all, cronid=cronid)
        self.__rpc(payload, executor_prvkey, Empty)

    def run_cron(self, cronid: str, executor_prvkey: str) -> Cron:
        payload = rpc.RunCron(cronid=cronid)
        return self.__rpc(payload, executor_prvkey, Cron)

    def resolve_generator_by_name(self, colonyname: str, generatorname: str, executor_prvkey: str) -> Generator:
        payload = rpc.ResolveGenerator(
            colonyname=colonyname,
            generatorname=generatorname
        )
        return self.__rpc(payload, executor_prvkey, Generator)

    def change_colony_id(self, colonyname: str, new_colony_id: str, server_prvkey: str) -> None:
        payload = rpc.ChangeColonyID(
            colonyname=colonyname,
            colonyid=new_colony_id
        )
        self.__rpc(payload, server_prvkey, Empty)

    def change_executor_id(self, colonyname: str, new_executor_id: str, colony_prvkey: str) -> None:
        payload = rpc.ChangeExecutorID(
            executorid=new_executor_id,
            colonyname=colonyname
        )
        self.__rpc(payload, colony_prvkey, Empty)

    def change_user_id(self, colonyname: str, new_user_id: str, colony_prvkey: str) -> None:
        payload = rpc.ChangeUserID(
            colonyname=colonyname,
            userid=new_user_id
        )
        self.__rpc(payload, colony_prvkey, Empty)

    def change_server_id(self, new_server_id: str, server_prvkey: str) -> None:
        payload = rpc.ChangeServerID(serverid=new_server_id)
        self.__rpc(payload, server_prvkey, Empty)

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
        executor_prvkey: str,
        filepath: str,
        label: str
    ) -> File:
        return self.__upload_file(filepath, label, colonyname, executor_prvkey)

    def upload_data(
        self,
        colonyname: str,
        executor_prvkey: str,
        filename: str,
        data: bytes,
        label: str
    ) -> File:
        return self.__upload_file(filename, label, colonyname, executor_prvkey, file_bytes=data)

    def __upload_file(
        self,
        filepath: str,
        label: str,
        colonyname: str,
        executor_prvkey: str,
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

        f = rpc.File(
            colonyname=colonyname,
            label=label,
            name=filename,
            size=filesize,
            checksum=checksum,
            checksumalg="SHA256",
            ref=ref
        )

        payload = rpc.AddFile(
            file=f
        )

        return self.__rpc(payload, executor_prvkey, File)

    def get_file(
        self,
        colonyname: str,
        executor_prvkey: str,
        label: Optional[str],
        filename: Optional[str] = None,
        fileid: Optional[str] = None,
        latest: bool = True
    ) -> List[File]:
        if (fileid and filename) or (not fileid and not filename) or (not filename and not label):
            raise ValueError("Please provide exactly one of: 'fileid' or ('filename' AND 'label')")
        payload = rpc.GetFile(
            colonyname=colonyname,
            fileid=fileid,
            label=label,
            name=filename,
            latest=latest
        )
        return self.__rpc(payload, executor_prvkey, List[File])

    def __remove_file(
        self,
        label: Optional[str],
        fileid: Optional[str],
        filename: Optional[str],
        colonyname: str,
        executor_prvkey: str
    ) -> None:
        if (fileid and filename) or (not fileid and not filename) or (not filename and not label):
            raise ValueError("Please provide exactly one of: 'fileid' or ('filename' AND 'label')")

        payload = rpc.RemoveFile(
            colonyname=colonyname,
            fileid=fileid,
            label=label,
            name=filename
        )
        self.__rpc(payload, executor_prvkey, Empty)

    def download_file(
        self,
        colonyname: str,
        executor_prvkey: str,
        dst: str,
        filename: str,
        label: Optional[str] = None,
        fileid: Optional[str] = None,
        latest: bool = True
    ) -> str:
        access_key = os.getenv("AWS_S3_ACCESSKEY")
        secret_key = os.getenv("AWS_S3_SECRETKEY")
        skip_verify_str = os.getenv("AWS_S3_SKIPVERIFY")

        dst = os.path.abspath(dst)

        try:
            os.makedirs(dst, exist_ok=True)
        except Exception as e:
            raise e

        file = self.get_file(colonyname, executor_prvkey, label=label, fileid=fileid, filename=filename, latest=latest)

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
        executor_prvkey: str,
        label: Optional[str] = None,
        filename: Optional[str] = None,
        fileid: Optional[str] = None,
        latest: bool = True
    ) -> bytes:
        access_key = os.getenv("AWS_S3_ACCESSKEY")
        secret_key = os.getenv("AWS_S3_SECRETKEY")
        skip_verify_str = os.getenv("AWS_S3_SKIPVERIFY")

        file = self.get_file(colonyname, executor_prvkey, label=label, fileid=fileid, filename=filename, latest=latest)

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
        executor_prvkey: str,
        filename: Optional[str] = None,
        label: Optional[str] = None,
        fileid: Optional[str] = None
    ) -> None:
        access_key = os.getenv("AWS_S3_ACCESSKEY")
        secret_key = os.getenv("AWS_S3_SECRETKEY")
        skip_verify_str = os.getenv("AWS_S3_SKIPVERIFY")

        file = self.get_file(colonyname, executor_prvkey, label=label, fileid=fileid, filename=filename)

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

        self.__remove_file(label, fileid, filename, colonyname, executor_prvkey)
