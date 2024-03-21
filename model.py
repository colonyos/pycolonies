from datetime import datetime

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


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
    input: List[str | int] | None = Field(alias="in")
    output: List[str | int] | None = Field(alias="out")
    errors: List[str]


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

