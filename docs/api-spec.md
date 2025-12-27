# PyColonies API Reference

Complete API reference for the PyColonies SDK.

## Client Initialization

```python
from pycolonies import Colonies

client = Colonies(host, port, tls=False, native_crypto=True)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| host | str | Server hostname |
| port | int | Server port |
| tls | bool | Enable TLS (default: False) |
| native_crypto | bool | Use native crypto library (default: True) |

---

## Colony Management

### list_colonies
List all colonies on the server.

```python
colonies = client.list_colonies(server_prvkey)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| server_prvkey | str | Server private key |

**Returns:** List of colonies

---

### add_colony
Create a new colony.

```python
colony = client.add_colony(colonyid, colonyname, server_prvkey)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| colonyid | str | Colony ID (derived from colony private key) |
| colonyname | str | Colony name |
| server_prvkey | str | Server private key |

---

### get_colony
Get colony details.

```python
colony = client.get_colony(colonyname, prvkey)
```

---

### del_colony
Delete a colony.

```python
client.del_colony(colonyname, server_prvkey)
```

---

### stats
Get colony statistics.

```python
stats = client.stats(colonyname, prvkey)
```

**Returns:** Colony statistics (process counts, etc.)

---

## Executor Management

### add_executor
Register a new executor.

```python
executor = {
    "executorname": "my-executor",
    "executorid": executorid,
    "colonyname": colonyname,
    "executortype": "python-executor"
}
client.add_executor(executor, colony_prvkey)
```

---

### approve_executor
Approve a registered executor.

```python
client.approve_executor(colonyname, executorname, colony_prvkey)
```

---

### reject_executor
Reject a registered executor.

```python
client.reject_executor(colonyname, executorname, colony_prvkey)
```

---

### remove_executor
Remove an executor.

```python
client.remove_executor(colonyname, executorname, colony_prvkey)
```

---

### list_executors
List all executors in a colony.

```python
executors = client.list_executors(colonyname, prvkey)
```

**Returns:** List of executor objects

---

### get_executor
Get details about a specific executor.

```python
executor = client.get_executor(colonyname, executorname, prvkey)
```

---

## Process Management

### submit_func_spec
Submit a function specification for execution.

```python
from pycolonies import func_spec

spec = func_spec(
    func="my_function",
    args=["arg1", "arg2"],
    colonyname="my_colony",
    executortype="python-executor",
    maxexectime=60,
    maxwaittime=60,
    maxretries=3
)

process = client.submit_func_spec(spec, prvkey)
```

**Returns:** Process object with `processid`

---

### assign
Assign a waiting process to an executor.

```python
process = client.assign(colonyname, timeout, executor_prvkey)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| colonyname | str | Colony name |
| timeout | int | Timeout in seconds (blocks until process available) |
| executor_prvkey | str | Executor private key |

**Returns:** Process object or None if timeout

---

### get_process
Get process details by ID.

```python
process = client.get_process(processid, prvkey)
```

---

### list_processes
List processes by state.

```python
processes = client.list_processes(colonyname, count, state, prvkey)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| state | int | 0=waiting, 1=running, 2=success, 3=failed |

---

### close
Close a process as successful.

```python
client.close(processid, output, prvkey)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| output | list | Output values |

---

### fail
Close a process as failed.

```python
client.fail(processid, errors, prvkey)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| errors | list | Error messages |

---

### set_output
Set process output without closing.

```python
client.set_output(processid, output, prvkey)
```

---

### wait
Wait for a process to complete.

```python
completed_process = client.wait(process, timeout, prvkey)
```

---

### remove_process
Remove a process.

```python
client.remove_process(processid, prvkey)
```

---

### remove_all_processes
Remove all processes in a colony.

```python
client.remove_all_processes(colonyname, prvkey, state=-1)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| state | int | -1=all, 0=waiting, 1=running, 2=success, 3=failed |

---

## Workflow Management

### submit_workflow
Submit a workflow (process graph).

```python
from pycolonies import Workflow, func_spec

wf = Workflow(colonyname="my_colony")

f1 = func_spec(func="step1", args=[], colonyname="my_colony",
               executortype="python-executor", maxexectime=60, maxwaittime=60)
wf.functionspecs.append(f1)

f2 = func_spec(func="step2", args=[], colonyname="my_colony",
               executortype="python-executor", maxexectime=60, maxwaittime=60)
f2.conditions.dependencies.append("step1")
wf.functionspecs.append(f2)

processgraph = client.submit_workflow(wf, prvkey)
```

---

### get_processgraph
Get a process graph by ID.

```python
graph = client.get_processgraph(processgraphid, prvkey)
```

---

### get_processgraphs
List process graphs in a colony.

```python
graphs = client.get_processgraphs(colonyname, count, prvkey, state=None)
```

---

### get_processes_for_workflow
Get all processes in a workflow.

```python
processes = client.get_processes_for_workflow(processgraphid, colonyname, prvkey, count=100)
```

---

### remove_processgraph
Remove a process graph.

```python
client.remove_processgraph(processgraphid, prvkey)
```

---

### remove_all_processgraphs
Remove all process graphs.

```python
client.remove_all_processgraphs(colonyname, prvkey, state=None)
```

---

### add_child
Dynamically add a child process to a workflow.

```python
client.add_child(processgraphid, parentprocessid, childprocessid, funcspec, nodename, insert, prvkey)
```

---

### find_process
Find a process by node name in a workflow.

```python
process = client.find_process(nodename, processids, prvkey)
```

---

## Channel Operations

### channel_append
Append a message to a channel.

```python
client.channel_append(
    processid,
    channel_name,
    sequence,
    payload,
    prvkey,
    in_reply_to=0,
    payload_type=""
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| sequence | int | Client-assigned sequence number |
| payload | str/bytes | Message content |
| in_reply_to | int | Optional sequence being replied to |
| payload_type | str | "", "data", "end", or "error" |

---

### channel_read
Read messages from a channel.

```python
entries = client.channel_read(processid, channel_name, after_seq, limit, prvkey)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| after_seq | int | Read messages after this sequence (0 for all) |
| limit | int | Max messages to return |

**Returns:** List of message entries with `sequence`, `payload`, `type`, `inreplyto`

---

### subscribe_channel
Subscribe to channel messages via WebSocket.

```python
# Blocking mode - returns all messages
messages = client.subscribe_channel(processid, channel_name, prvkey, timeout=30)

# Callback mode - streaming
def on_message(entries):
    for entry in entries:
        print(entry['payload'].decode())
    return True  # False to stop

client.subscribe_channel(processid, channel_name, prvkey, timeout=30, callback=on_message)
```

---

## Blueprint Management

### add_blueprint_definition
Add a blueprint definition (requires colony owner key).

```python
definition = {
    "kind": "MyResource",
    "metadata": {
        "name": "my-resource-def",
        "colonyname": colonyname
    },
    "spec": {
        "names": {"kind": "MyResource"}
    }
}
client.add_blueprint_definition(definition, colony_prvkey)
```

---

### get_blueprint_definition
Get a blueprint definition by name.

```python
definition = client.get_blueprint_definition(colonyname, name, prvkey)
```

---

### get_blueprint_definitions
List all blueprint definitions.

```python
definitions = client.get_blueprint_definitions(colonyname, prvkey)
```

---

### remove_blueprint_definition
Remove a blueprint definition.

```python
client.remove_blueprint_definition(colonyname, name, colony_prvkey)
```

---

### add_blueprint
Add a blueprint instance.

```python
blueprint = {
    "kind": "MyResource",
    "metadata": {
        "name": "my-instance",
        "colonyname": colonyname
    },
    "handler": {
        "executortype": "my-reconciler"
    },
    "spec": {
        "replicas": 3,
        "image": "nginx:latest"
    }
}
client.add_blueprint(blueprint, prvkey)
```

---

### get_blueprint
Get a blueprint by name.

```python
blueprint = client.get_blueprint(colonyname, name, prvkey)
```

---

### get_blueprints
List blueprints, optionally filtered.

```python
blueprints = client.get_blueprints(colonyname, prvkey, kind=None, location=None)
```

---

### update_blueprint
Update a blueprint's spec.

```python
blueprint['spec']['replicas'] = 5
client.update_blueprint(blueprint, prvkey, force_generation=False)
```

---

### update_blueprint_status
Update a blueprint's status (called by reconciler).

```python
status = {
    "replicas": 5,
    "ready": True,
    "lastSeen": "2024-01-01T12:00:00Z"
}
client.update_blueprint_status(colonyname, name, status, prvkey)
```

---

### reconcile_blueprint
Trigger reconciliation for a blueprint.

```python
process = client.reconcile_blueprint(colonyname, name, prvkey, force=False)
```

---

### get_blueprint_history
Get change history for a blueprint.

```python
history = client.get_blueprint_history(blueprintid, prvkey, limit=None)
```

---

### remove_blueprint
Remove a blueprint.

```python
client.remove_blueprint(colonyname, name, prvkey)
```

---

## Cron Management

### add_cron
Add a cron job.

```python
from pycolonies import Workflow

wf = Workflow(colonyname=colonyname)
# ... add function specs to workflow

client.add_cron(cronname, cronexpr, wait, wf, colonyname, prvkey)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| cronexpr | str | Cron expression (e.g., "0 * * * *") |
| wait | bool | Wait for previous run to complete |

---

### get_cron
Get a cron job by ID.

```python
cron = client.get_cron(cronid, prvkey)
```

---

### get_crons
List cron jobs.

```python
crons = client.get_crons(colonyname, count, prvkey)
```

---

### run_cron
Manually trigger a cron job.

```python
process = client.run_cron(cronid, prvkey)
```

---

### del_cron
Delete a cron job.

```python
client.del_cron(cronid, prvkey)
```

---

## Generator Management

### add_generator
Add a generator.

```python
client.add_generator(generator, prvkey)
```

---

### get_generator
Get a generator by ID.

```python
generator = client.get_generator(generatorid, prvkey)
```

---

### get_generators
List generators.

```python
generators = client.get_generators(colonyname, prvkey, count=100)
```

---

### remove_generator
Remove a generator.

```python
client.remove_generator(generatorid, prvkey)
```

---

## User Management

### add_user
Add a user to a colony.

```python
user = {
    "colonyname": colonyname,
    "userid": userid,
    "name": "username",
    "email": "user@example.com",
    "phone": ""
}
client.add_user(user, server_prvkey)
```

---

### get_users
List users in a colony.

```python
users = client.get_users(colonyname, server_prvkey)
```

---

### remove_user
Remove a user.

```python
client.remove_user(colonyname, name, server_prvkey)
```

---

## Function Registry

### add_function
Register a function for an executor.

```python
client.add_function(colonyname, executorname, funcname, prvkey)
```

---

### get_functions_by_colony
List all functions in a colony.

```python
functions = client.get_functions_by_colony(colonyname, prvkey)
```

---

### get_functions_by_executor
List functions for a specific executor.

```python
functions = client.get_functions_by_executor(colonyname, executorname, prvkey)
```

---

## Attribute Management

### add_attribute
Add an attribute to a running process.

```python
attr = client.add_attribute(processid, key, value, prvkey)
```

---

### get_attribute
Get an attribute by ID.

```python
attr = client.get_attribute(attributeid, prvkey)
```

---

## Logging

### add_log
Add a log message to a process.

```python
client.add_log(processid, message, prvkey)
```

---

### get_process_log
Get logs for a process.

```python
logs = client.get_process_log(colonyname, processid, count, since, prvkey)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| count | int | Max log entries to return |
| since | int | Timestamp to start from |

---

### get_executor_log
Get logs for an executor.

```python
logs = client.get_executor_log(colonyname, executorid, count, since, prvkey)
```

---

## File Storage

### upload_file
Upload a file to storage.

```python
client.upload_file(colonyname, filepath, label, keeplocal, prvkey)
```

---

### upload_data
Upload data directly to storage.

```python
client.upload_data(colonyname, data, filename, label, prvkey)
```

---

### download_file
Download a file from storage.

```python
client.download_file(colonyname, fileid, localpath, prvkey)
```

---

### download_data
Download data from storage.

```python
data = client.download_data(colonyname, fileid, prvkey)
```

---

### get_file
Get file metadata.

```python
file = client.get_file(colonyname, fileid, prvkey)
```

---

### get_files
List files by label.

```python
files = client.get_files(colonyname, label, prvkey)
```

---

### get_file_labels
List file labels.

```python
labels = client.get_file_labels(colonyname, prvkey, name="", exact=False)
```

---

### delete_file
Delete a file from storage.

```python
client.delete_file(colonyname, fileid, prvkey)
```

---

### sync
Sync files between local and remote storage.

```python
client.sync(colonyname, label, dir, keeplocal, prvkey)
```

---

## Snapshots

### create_snapshot
Create a snapshot of files.

```python
client.create_snapshot(colonyname, label, name, prvkey)
```

---

### get_snapshots
List snapshots.

```python
snapshots = client.get_snapshots(colonyname, prvkey)
```

---

### get_snapshot_by_name
Get a snapshot by name.

```python
snapshot = client.get_snapshot_by_name(colonyname, name, prvkey)
```

---

### get_snapshot_by_id
Get a snapshot by ID.

```python
snapshot = client.get_snapshot_by_id(colonyname, snapshotid, prvkey)
```

---

## Process States

| State | Value | Description |
|-------|-------|-------------|
| WAITING | 0 | Process waiting for executor assignment |
| RUNNING | 1 | Process assigned and executing |
| SUCCESS | 2 | Process completed successfully |
| FAILED | 3 | Process failed |

---

## Error Handling

```python
from pycolonies import ColoniesError, ColoniesConnectionError

try:
    process = client.assign(colonyname, 10, prvkey)
except ColoniesConnectionError as e:
    print(f"Connection error: {e}")
except ColoniesError as e:
    print(f"API error: {e}")
```
