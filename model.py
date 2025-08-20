from datetime import datetime
import base64
import inspect

from typing import List, Dict, Optional, Any, Callable
from pydantic import BaseModel, Field, field_validator, ConfigDict

# Base model for all RPC request messages
class Model(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class Gpu(Model):
    name: Optional[str] = None
    mem: Optional[str] = None
    count: Optional[int] = None
    nodecount: Optional[int] = None


class Conditions(Model):
    colonyname: Optional[str] = None
    executornames: Optional[List[str]] = None
    executortype: str
    dependencies: List[str] = []
    nodes: int = 0
    cpu: Optional[str] = None
    processes: int = 0
    processespernode: int = 0
    mem: Optional[str] = None
    storage: Optional[str] = None
    gpu: Optional[Gpu] = None
    walltime: int = 0

class Fs(Model):
    mount: str
    snapshots: Optional[List[str]]
    dirs: Optional[List[str]]


class FuncSpec(Model):
    nodename: Optional[str] = None
    funcname: str
    args: List[str | int] = []
    kwargs: Dict[str, str | List[str]] = {}
    priority: int = 0
    maxwaittime: int = 0
    maxexectime: int = 0
    maxretries: int = 0
    conditions: Optional[Conditions] = None
    label: Optional[str] = None
    fs: Optional[Fs] = None
    env: Dict[str, str] = {}

    @staticmethod
    def create(
        func: str | Callable,
        args: List[str | int],
        colonyname: Optional[str] = None,
        executortype: Optional[str] = None,
        nodename: Optional[str] = None,
        executorname: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        priority: int = 1,
        maxexectime: int = -1,
        maxretries: int = -1,
        maxwaittime: int = -1,
        code: Optional[str] = None,
        kwargs: Dict[str, str | List[str]] = {},
        conditions: Optional[Conditions] = None,
        fs: Optional[Fs] = None,
        env: Dict[str, str] = {},
    ) -> 'FuncSpec':
        if conditions is None \
                and colonyname is not None \
                and executortype is not None:
            conditions = Conditions(
                colonyname=colonyname,
                executortype=executortype,
                dependencies=dependencies or []
            )
        else:
            raise ValueError("Either `conditions` or `colonyname` and `executortype` must be provided.")
        
        env = env.copy()
        if isinstance(func, str):
            nodename = nodename or func
            funcname = func
            if code is not None:
                code_bytes = code.encode("ascii")
                code_base64_bytes = base64.b64encode(code_bytes)
                code_base64 = code_base64_bytes.decode("ascii")
                env["code"] = code_base64
        else:
            code = inspect.getsource(func)
            code_bytes = code.encode("ascii")
            code_base64_bytes = base64.b64encode(code_bytes)
            code_base64 = code_base64_bytes.decode("ascii")

            funcname = func.__name__
            args_spec = inspect.getfullargspec(func)
            args_spec_str = ','.join(args_spec.args)

            nodename = nodename or funcname
            env["args_spec"] = args_spec_str
            env["code"] = code_base64

        if executorname is not None:
            conditions.executornames = [ executorname ]
        
        # Create instance with all the prepared data
        return FuncSpec(
            nodename=nodename,
            funcname=funcname,
            args=args,
            kwargs=kwargs,
            priority=priority,
            maxwaittime=maxwaittime,
            maxexectime=maxexectime,
            maxretries=maxretries,
            conditions=conditions,
            fs=fs,
            env=env,
        )



class Attribute(Model):
    id: str = Field(..., alias="attributeid")
    targetid: str
    targetcolonyname: str = Field(..., alias="targetcolonyname")
    targetprocessgraphid: str = Field(..., alias="targetprocessgraphid")
    state: int
    attributetype: int
    key: str
    value: str


class Process(Model):
    processid: str
    initiatorid: str
    initiatorname: str
    assignedexecutorid: str
    isassigned: bool
    state: int
    prioritytime: int
    submissiontime: datetime
    starttime: datetime
    endtime: datetime
    waitdeadline: datetime
    execdeadline: datetime
    retries: int
    attributes: Optional[List[Attribute]]
    spec: FuncSpec
    waitforparents: bool = False
    parents: List[str]
    children: List[str]
    processgraphid: str
    input: Optional[List[str | int | float]] = Field(alias="in")
    output: Optional[List[str | int | float]] = Field(alias="out")
    errors: List[str]
    
    def __init__(self, **data: Any) -> None:
        if 'input' in data:
            data['in'] = data.pop('input')
        if 'output' in data:
            data['out'] = data.pop('output')
        super().__init__(**data)


class Workflow(Model):
    colonyname: str
    functionspecs: List[FuncSpec] = []


class Position(Model):
    x: int
    y: int


class ProcessNode(Model):
    id: str
    data: Dict[str, str] = {}
    position: Position
    type: str
    style: Dict[str, str] = {}


class ProcessEdge(Model):
    id: str
    source: str
    target: str
    animated: bool


class ProcessGraph(Model):
    processgraphid: str
    initiatorid: str
    initiatorname: str
    colonyname: str
    rootprocessids: List[str]
    state: int
    submissiontime: datetime
    starttime: datetime
    endtime: datetime
    processids: List[str]
    nodes: List[ProcessNode]
    edges: List[ProcessEdge]


class S3Object(Model):
    server: str
    port: int
    tls: bool
    accesskey: str = Field(..., alias="accesskey")
    secretkey: str = Field(..., alias="secretkey")
    region: str = Field(..., alias="region")
    encryptionkey: str = Field(..., alias="encryptionkey")
    encryptionalg: str = Field(..., alias="encryptionalg")
    object: str = Field(..., alias="object")
    bucket: str = Field(..., alias="bucket")

class Reference(Model):
    protocol: str
    s3object: S3Object = Field(..., alias="s3object")

class File(Model):
    fileid: str = Field(..., alias="fileid")
    colonyname: str = Field(..., alias="colonyname")
    label: str = Field(..., alias="label")
    name: str = Field(..., alias="name")
    size: int = Field(..., alias="size")
    sequencenr: int = Field(..., alias="sequencenr")
    checksum: str = Field(..., alias="checksum")
    checksumalg: str = Field(..., alias="checksumalg")
    ref: Reference = Field(..., alias="ref")
    added: Optional[datetime] = Field(default=None, alias="added")

    @field_validator('label')
    def ensure_single_slash(cls, v):
        if not v.startswith('/'):
            v = '/' + v
        v = '/' + v.strip('/')
        return v


class FileData(Model):
    name: str
    checksum: str
    size: int
    s3filename: str


class Cron(Model):
    cronid: str
    initiatorid: str
    initiatorname: str
    colonyname: str
    name: str
    cronexpression: str
    interval: int
    random: bool
    nextrun: datetime
    lastrun: datetime
    workflowspec: str
    prevprocessgraphid: str
    waitforprevprocessgraph: bool
    checkerperiod: int


class Log(Model):
    processid: str
    colonyname: str
    executorname: str
    message: str
    timestamp: int


class Location(Model):
    long: float
    lat: float
    desc: str


class Hardware(Model):
    model: str
    nodes: int
    cpu: str
    mem: str
    storage: str
    gpu: Gpu


class Software(Model):
    name: str
    type: str
    version: str


class Capabilities(Model):
    hardware: Hardware
    software: Software


class Allocations(Model):
    projects: Optional[Dict[str, Any]] = None


class Executor(Model):
    executorid: str
    executortype: str
    name: str = Field(..., alias="executorname")
    colonyname: str
    state: int
    requirefuncreg: bool
    commissiontime: datetime
    lastheardfromtime: datetime
    location: Location
    capabilities: Capabilities
    allocations: Allocations


class Colony(Model):
    colonyid: str
    name: str


class Statistics(Model):
    colonies: int
    executors: int
    waitingprocesses: int
    runningprocesses: int
    successfulprocesses: int
    failedprocesses: int
    waitingworkflows: int
    runningworkflows: int
    successfulworkflows: int
    failedworkflows: int


class Function(Model):
    functionid: str
    executorname: str
    executortype: str
    colonyname: str
    funcname: str
    counter: int
    minwaittime: float
    maxwaittime: float
    minexectime: float
    maxexectime: float
    avgwaittime: float
    avgexectime: float


class Snapshot(Model):
    snapshotid: str
    colonyname: str
    label: str
    name: str
    fileids: List[str]
    added: datetime


class Generator(Model):
    generatorid: str
    initiatorid: str
    initiatorname: str
    colonyname: str
    name: str
    workflowspec: str
    trigger: int
    checksomeneeded: bool
    lastchecksum: str
    checkerperiod: int
    timeout: int
    added: datetime

class User(Model):
    colonyname: str
    id: str = Field(..., alias="userid")
    name: str
    email: str
    phone: str

class Empty(Model):
    """An empty class used to represent an empty response in RPC calls."""
    pass
