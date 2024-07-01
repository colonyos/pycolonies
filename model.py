from datetime import datetime

from typing import List, Dict, Optional
from pydantic import BaseModel, Field, validator

class Gpu(BaseModel):
    name: str = ""
    mem: str = ""
    count: int = 0
    nodecount: int = 0


class Conditions(BaseModel):
    colonyname: str = ""
    executornames: List[str] | None = None
    executortype: str
    dependencies: List[str] = []
    nodes: int = 0
    cpu: str = ""
    processes: int = 0
    processes_per_node: int = Field(alias="processes-per-node", default=0)
    mem: str = ""
    storage: str = ""
    gpu: Gpu | None = Gpu()
    walltime: int = 0

    def __init__(self, **data):
        if 'processes_per_node' in data:
            data['processes-per-node'] = data.pop('processes_per_node')
        super().__init__(**data)


class Fs(BaseModel):
    mount: str
    snapshots: List[str] | None
    dirs: List[str] | None


class FuncSpec(BaseModel):
    nodename: str = ""
    funcname: str = ""
    args: List[str | int] = []
    kwargs: Dict[str, str] | None = {}
    priority: int = 0
    maxwaittime: int = 0
    maxexectime: int = 0
    maxretries: int = 0
    conditions: Conditions
    label: str = ""
    fs: Fs | None = Fs(mount="", snapshots=None, dirs=None)
    env: Dict[str, str] = {}


class Attribute(BaseModel):
    key: str
    value: str
    targetid: str
    attributetype: int


class Process(BaseModel):
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
    attributes: List[Attribute] | None
    spec: FuncSpec
    waitforparents: bool = False
    parents: List[str]
    children: List[str]
    processgraphid: str
    input: List[str | int | float] | None = Field(alias="in")
    output: List[str | int | float] | None = Field(alias="out")
    errors: List[str]
    
    def __init__(self, **data):
        if 'input' in data:
            data['in'] = data.pop('input')
        if 'output' in data:
            data['out'] = data.pop('output')
        super().__init__(**data)


class Workflow(BaseModel):
    colonyname: str
    functionspecs: List[FuncSpec] = []


class Position(BaseModel):
    x: int
    y: int


class ProcessNode(BaseModel):
    id: str
    data: Dict[str, str] = {}
    position: Position
    type: str
    style: Dict[str, str] = {}


class ProcessEdge(BaseModel):
    id: str
    source: str
    target: str
    animated: bool


class ProcessGraph(BaseModel):
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


class S3Object(BaseModel):
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

class Reference(BaseModel):
    protocol: str
    s3object: S3Object = Field(..., alias="s3object")

class File(BaseModel):
    fileid: str = Field(..., alias="fileid")
    colonyname: str = Field(..., alias="colonyname")
    label: str = Field(..., alias="label")
    name: str = Field(..., alias="name")
    size: int = Field(..., alias="size")
    sequencenr: int = Field(..., alias="sequencenr")
    checksum: str = Field(..., alias="checksum")
    checksumalg: str = Field(..., alias="checksumalg")
    ref: Reference = Field(..., alias="ref")
    added: Optional[datetime] = Field(None, alias="added")

    @validator('label')
    def ensure_single_slash(cls, v):
        if not v.startswith('/'):
            v = '/' + v
        v = '/' + v.strip('/')
        return v
