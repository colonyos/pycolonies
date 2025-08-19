from typing import List, Any, Optional
from pydantic import Field

from model import (
    Model, Colony, User, FuncSpec, Allocations, Gpu, Software, Workflow,
    Reference
)

# ==============================================================================
# Request and Response messages
# ==============================================================================

class RequestPayload(Model):
    msgtype: str

class Request(Model):
    payloadtype: str
    payload: str
    signature: str

class ErrorResponse(Model):
    status: str
    message: str

class Response(Model):
    payloadtype: str
    payload: str

# ==============================================================================
# Payloads for API Requests (excluding server-managed fields)
# ==============================================================================

class Hardware(Model):
    """Client-provided hardware capabilities."""
    model: Optional[str] = None
    nodes: int = 1
    cpu: Optional[str] = None
    mem: Optional[str] = None
    storage: Optional[str] = None
    gpu: Optional[Gpu] = None

class Capabilities(Model):
    """Client-provided executor capabilities."""
    hardware: Optional[Hardware] = None
    software: Optional[Software] = None

class Executor(Model):
    """Payload for adding a new executor. Excludes server-managed fields."""
    executorid: str
    executortype: str
    name: str = Field(..., alias="executorname")
    colonyname: str
    capabilities: Optional[Capabilities] = None

class Attribute(Model):
    """Payload for adding an attribute. Excludes server-generated fields."""
    targetid: str
    attributetype: int
    key: str
    value: str

class Function(Model):
    """Payload for adding a function. Excludes server-generated fields."""
    executorname: str
    colonyname: str
    funcname: str

class Generator(Model):
    """Payload for adding a generator. Excludes server-generated fields."""
    colonyname: str
    name: str
    workflowspec: str
    trigger: int
    timeout: int

class Cron(Model):
    """Payload for adding a cron job. Excludes server-generated fields."""
    colonyname: str
    name: str
    cronexpression: str
    interval: int
    random: bool
    workflowspec: str
    waitforprevprocessgraph: bool

class File(Model):
    """Payload for adding a file. Excludes server-generated fields."""
    colonyname: str
    label: str
    name: str
    size: int
    checksum: str
    checksumalg: str
    ref: Reference

# ==============================================================================
# Colony API Requests
# ==============================================================================

class AddColony(RequestPayload):
    colony: Colony
    msgtype: str = "addcolonymsg"

class RemoveColony(RequestPayload):
    colonyname: str
    msgtype: str = "removecolonymsg"

class GetColonies(RequestPayload):
    msgtype: str = "getcoloniesmsg"

class GetColony(RequestPayload):
    colonyname: str
    msgtype: str = "getcolonymsg"

# ==============================================================================
# Executor API Requests
# ==============================================================================

class AddExecutor(RequestPayload):
    executor: Executor
    msgtype: str = "addexecutormsg"

class GetExecutors(RequestPayload):
    colonyname: str
    msgtype: str = "getexecutorsmsg"

class GetExecutor(RequestPayload):
    colonyname: str
    executorname: str
    msgtype: str = "getexecutormsg"

class ApproveExecutor(RequestPayload):
    colonyname: str
    executorname: str
    msgtype: str = "approveexecutormsg"

class RejectExecutor(RequestPayload):
    colonyname: str
    executorname: str
    msgtype: str = "rejectexecutormsg"

class RemoveExecutor(RequestPayload):
    colonyname: str
    executorname: str
    msgtype: str = "removeexecutormsg"

class ReportAllocations(RequestPayload):
    colonyname: str
    executorname: str
    allocations: Allocations
    msgtype: str = "reportallocationmsg"

# ==============================================================================
# Process API Requests
# ==============================================================================

class SubmitFunctionSpec(RequestPayload):
    spec: FuncSpec
    msgtype: str = "submitfuncspecmsg"

class AssignProcess(RequestPayload):
    colonyname: str
    timeout: int
    availablecpu: str
    availablemem: str
    msgtype: str = "assignprocessmsg"

class GetProcesses(RequestPayload):
    colonyname: str
    count: int
    state: int
    executortype: Optional[str] = None
    label: Optional[str] = None
    initiator: Optional[str] = None
    msgtype: str = "getprocessesmsg"

class GetProcessHist(RequestPayload):
    colonyname: str
    executorid: str
    seconds: int
    state: int
    msgtype: str = "getprocesshistmsg"

class GetProcess(RequestPayload):
    processid: str
    msgtype: str = "getprocessmsg"

class RemoveProcess(RequestPayload):
    processid: str
    all: bool
    msgtype: str = "removeprocessmsg"

class RemoveAllProcesses(RequestPayload):
    colonyname: str
    state: int
    msgtype: str = "removeallprocessesmsg"

class CloseSuccessful(RequestPayload):
    processid: str
    out: List[Any]
    msgtype: str = "closesuccessfulmsg"

class CloseFailed(RequestPayload):
    processid: str
    errors: List[str]
    msgtype: str = "closefailedmsg"

class SetOutput(RequestPayload):
    processid: str
    out: List[Any]
    msgtype: str = "setoutputmsg"

class AddAttribute(RequestPayload):
    attribute: Attribute
    msgtype: str = "addattributemsg"

class GetAttribute(RequestPayload):
    attributeid: str
    msgtype: str = "getattributemsg"

class SubscribeProcesses(RequestPayload):
    colonyname: str
    executortype: str
    state: int
    timeout: int
    msgtype: str = "subscribeprocessesmsg"

class SubscribeProcess(RequestPayload):
    colonyname: str
    processid: str
    executortype: str
    state: int
    timeout: int
    msgtype: str = "subscribeprocessmsg"

# ==============================================================================
# Workflow & Process Graph API Requests
# ==============================================================================

class SubmitWorkflowSpec(RequestPayload):
    spec: Workflow
    msgtype: str = "submitworkflowspecmsg"

class AddChild(RequestPayload):
    processgraphid: str
    parentprocessid: str
    childprocessid: str
    spec: FuncSpec
    insert: bool
    msgtype: str = "addchildmsg"

class GetProcessGraph(RequestPayload):
    processgraphid: str
    msgtype: str = "getprocessgraphmsg"

class GetProcessGraphs(RequestPayload):
    colonyname: str
    count: int
    state: int
    msgtype: str = "getprocessgraphsmsg"

class RemoveProcessGraph(RequestPayload):
    processgraphid: str
    all: bool
    msgtype: str = "removeprocessgraphmsg"

class RemoveAllProcessGraphs(RequestPayload):
    colonyname: str
    state: int
    msgtype: str = "removeallprocessgraphsmsg"

# ==============================================================================
# Cron API Requests
# ==============================================================================

class AddCron(RequestPayload):
    cron: Cron
    msgtype: str = "addcronmsg"

class GetCron(RequestPayload):
    cronid: str
    msgtype: str = "getcronmsg"

class GetCrons(RequestPayload):
    colonyname: str
    count: int
    msgtype: str = "getcronsmsg"

class RunCron(RequestPayload):
    cronid: str
    msgtype: str = "runcronmsg"

class RemoveCron(RequestPayload):
    cronid: str
    all: bool
    msgtype: str = "removecronmsg"

# ==============================================================================
# Generator API Requests
# ==============================================================================

class AddGenerator(RequestPayload):
    generator: Generator
    msgtype: str = "addgeneratormsg"

class GetGenerator(RequestPayload):
    generatorid: str
    msgtype: str = "getgeneratormsg"

class ResolveGenerator(RequestPayload):
    colonyname: str
    generatorname: str
    msgtype: str = "resolvegeneratormsg"

class GetGenerators(RequestPayload):
    colonyname: str
    count: int
    msgtype: str = "getgeneratorsmsg"

class PackGenerator(RequestPayload):
    generatorid: str
    arg: str
    msgtype: str = "packgeneratormsg"

class RemoveGenerator(RequestPayload):
    generatorid: str
    all: bool
    msgtype: str = "removegeneratormsg"

# ==============================================================================
# File Management API Requests
# ==============================================================================

class AddFile(RequestPayload):
    file: File
    msgtype: str = "addfilemsg"

class GetFile(RequestPayload):
    """
    Get a file by its ID or (label and name).
    """
    colonyname: str
    fileid: Optional[str]
    label: Optional[str]
    name: Optional[str]
    latest: bool
    msgtype: str = "getfilemsg"

class GetFiles(RequestPayload):
    colonyname: str
    label: str
    msgtype: str = "getfilesmsg"

class GetFileLabels(RequestPayload):
    colonyname: str
    name: str
    exact: bool
    msgtype: str = "getfilelabelsmsg"

class RemoveFile(RequestPayload):
    """
    Remove a file by its ID or (label and name).
    """
    colonyname: str
    fileid: Optional[str]
    label: Optional[str]
    name: Optional[str]
    msgtype: str = "removefilemsg"

# ==============================================================================
# Logging API Requests
# ==============================================================================

class AddLog(RequestPayload):
    processid: str
    message: str
    msgtype: str = "addlogmsg"

class GetLogs(RequestPayload):
    colonyname: str
    processid: str
    executorname: str
    count: int
    since: int
    msgtype: str = "getlogsmsg"

class SearchLogs(RequestPayload):
    colonyname: str
    text: str
    days: int
    count: int
    msgtype: str = "searchlogsmsg"

# ==============================================================================
# User Management API Requests
# ==============================================================================

class AddUser(RequestPayload):
    user: User
    msgtype: str = "addusermsg"

class GetUser(RequestPayload):
    colonyname: str
    name: str
    msgtype: str = "getusermsg"

class GetUsers(RequestPayload):
    colonyname: str
    msgtype: str = "getusersmsg"

class RemoveUser(RequestPayload):
    colonyname: str
    name: str
    msgtype: str = "removeusermsg"

# ==============================================================================
# Snapshot API Requests
# ==============================================================================

class CreateSnapshot(RequestPayload):
    colonyname: str
    label: str
    name: str
    msgtype: str = "createsnapshotmsg"

class GetSnapshot(RequestPayload):
    """
    If `snapshotid` is provided, retrieves a specific snapshot.
    If `name` is provided, retrieves the latest snapshot with that name.
    If neither is provided, retrieves the latest snapshot.
    """
    colonyname: str
    snapshotid: Optional[str] = None
    name: Optional[str] = None
    msgtype: str = "getsnapshotmsg"

class GetSnapshots(RequestPayload):
    colonyname: str
    msgtype: str = "getsnapshotsmsg"

class RemoveSnapshot(RequestPayload):
    colonyname: str
    snapshotid: str
    name: str
    msgtype: str = "removesnapshotmsg"

class RemoveAllSnapshots(RequestPayload):
    colonyname: str
    msgtype: str = "removeallsnapshotsmsg"

# ==============================================================================
# Server & Miscellaneous API Requests
# ==============================================================================

class GetCluster(RequestPayload):
    msgtype: str = "getclustermsg"

class Version(RequestPayload):
    buildversion: str
    buildtime: str
    msgtype: str = "versionmsg"

class GetStatistics(RequestPayload):
    msgtype: str = "getstatisticsmsg"

class GetColonyStatistics(RequestPayload):
    colonyname: str
    msgtype: str = "getcolonystatsmsg"

class AddFunction(RequestPayload):
    fun: Function
    msgtype: str = "addfunctionmsg"

class GetFunctions(RequestPayload):
    colonyname: str
    executorname: Optional[str] = None
    msgtype: str = "getfunctionsmsg"

class RemoveFunction(RequestPayload):
    functionid: str
    msgtype: str = "removefunctionmsg"

# ==============================================================================
# ID Management Requests
# ==============================================================================

class ChangeColonyID(RequestPayload):
    colonyname: str
    colonyid: str
    msgtype: str = "changecolonyidmsg"

class ChangeExecutorID(RequestPayload):
    colonyname: str
    executorid: str
    msgtype: str = "changeexecutoridmsg"

class ChangeServerID(RequestPayload):
    serverid: str
    msgtype: str = "changeserveridmsg"

class ChangeUserID(RequestPayload):
    colonyname: str
    userid: str
    msgtype: str = "changeuseridmsg"
