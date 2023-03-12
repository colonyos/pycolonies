# Introduction
This repo contains a Python implementation of the [Colonies API](https://github.com/colonyos/colonies), making it possible to implement Colonies Executors and applications in Python.

The library assumes *libcryptolib.so* is installed in */usr/local/lib*. However, it is also possible to set the path the cryptolib.so using an environmental variable.
```bash
export CRYPTOLIB=".../colonies/lib/cryptolib.so"
```

## Getting started
### Starting a Colonies server
You need to have access to a Colonies server. On Linux, run the commands below to start a server. See the [Colonies release page](https://github.com/colonyos/colonies/releases) for Windows and Mac binaries.

```console
git clone https://github.com/colonyos/colonies
cd colonies
source devenv
./bin/colonies dev

...
INFO[0001] Successfully started Colonies development server
INFO[0001] Press ctrl+c to exit
```

### Submitting function specs
To execute a function, a function specification must be submitted to the Colonies server. The function is then executed by a so-called Executor that may reside anywhere on the Internet, for example in a Kubernetes Pod, an IoT device, a virtual machine on an edge server, or a smart phone. The Colonies server acts a mediator, matching function specification with suitable Executors.

![Simplified architecture](docs/images/colonies_arch_simple.png)

After a function specification has been submitted, a process is created on the Colonies server. A process in this case is not a operating system process or anything like that, but rather a database entry containing instructions how to execute the function. It also contains contextual information such as execution status, priority, submission time, and environmental variables, input and output values etc.

Below is an example of function specification.
```json
{
    "conditions": {
        "executortype": "echo_executor"
    },
    "func": "echo",
    "args": [
        "helloworld"
    ]
}
```

The function specification also contains requirements (conditions) that needs to be fulfilled for the function to be executed. In this case, only executors of the "echo-executor" type may execute the function.

A function specification can be submitted using the Colonies CLI.
```console
colonies function submit --spec echo_func_spec.json

INFO[0000] Process submitted                             ProcessID=ea398af346db85f45b118bb77ecda9ae25f4700dcafcccb4ba3e4d40eba5205a
```

We can also look up the process using the CLI,
```console
colonies process get -p ea398af346db85f45b118bb77ecda9ae25f4700dcafcccb4ba3e4d40eba5205a 

Process:
+--------------------+------------------------------------------------------------------+
| ID                 | ea398af346db85f45b118bb77ecda9ae25f4700dcafcccb4ba3e4d40eba5205a |
| IsAssigned         | False                                                            |
| AssignedExecutorID | None                                                             |
| State              | Waiting                                                          |
| Priority           | 0                                                                |
| SubmissionTime     | 2023-03-12 21:06:55                                              |
| StartTime          | 0001-01-01 01:12:12                                              |
| EndTime            | 0001-01-01 01:12:12                                              |
| WaitDeadline       | 0001-01-01 01:12:12                                              |
| ExecDeadline       | 0001-01-01 01:12:12                                              |
| WaitingTime        | 29.587933822s                                                    |
| ProcessingTime     | 0s                                                               |
| Retries            | 0                                                                |
| Errors             |                                                                  |
| Output             |                                                                  |
+--------------------+------------------------------------------------------------------+

FunctionSpec:
+-------------+-------------+
| Func        | echo        |
| Args        | helloworld  |
| MaxWaitTime | -1          |
| MaxExecTime | -1          |
| MaxRetries  | 0           |
| Priority    | 0           |
+-------------+-------------+

Conditions:
+--------------+------------------------------------------------------------------+
| ColonyID     | 4787a5071856a4acf702b2ffcea422e3237a679c681314113d86139461290cf4 |
| ExecutorIDs  | None                                                             |
| ExecutorType | echo_executor                                                    |
| Dependencies |                                                                  |
+--------------+------------------------------------------------------------------+

Attributes:
No attributes found
```

The command below shows all waiting processes. The process will be queued since we don't yet have an executor of the type "echo_executor". 
```console
colonies process psw
INFO[0000] Starting a Colonies client                    Insecure=true ServerHost=localhost ServerPort=50080
+------------------------------------------------------------------+------+------------+---------------------+---------------+
|                                ID                                | FUNC |    ARGS    |   SUBMISSION TIME   | EXECUTOR TYPE |
+------------------------------------------------------------------+------+------------+---------------------+---------------+
| 4787a5071856a4acf702b2ffcea422e3237a679c681314113d86139461290cf4 | echo | helloworld | 2023-03-12 21:09:09 | echo_executor |
+------------------------------------------------------------------+------+------------+---------------------+---------------+
```

We can of course also submit a function specification directly from Python.
```python
colonies = Colonies("localhost", 50080)
func_spec = colonies.create_func_spec(func="echo", 
                                      args=["helloworld"], 
                                      colonyid=colonyid, 
                                      executortype="echo_executor",
                                      priority=200,
                                      maxexectime=100,
                                      maxretries=3,
                                      maxwaittime=100)

process = colonies.submit(func_spec, executor_prvkey)
```

See [echo.py](https://github.com/colonyos/pycolonies/blob/main/examples/echo.py) for a full example.

### Implementing an Executor in Python
An executor is responsible for executing one or several functions. It connects to the Colonies server to get process assignments. 

The executor needs to be member of a colony in order to connect to the Colonies server and execute processes. A colony is like a project/namespace/tenant where one or several executors are members. Only the colony owner may add (register) executors to a colony and executors can only interact with other executors member of the same colony.

