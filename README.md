# Introduction
This repo contains [Colonies](https://github.com/colonyos/colonies) Python SDK, making it possible to implement Colonies Executors in Python. 

# Installation 
Note that the SDK has only be tested on Linux and MacOS. 

```bash
pip3 install pycolonies
```

The library assumes *libcryptolib.so* is installed in */usr/local/lib*. However, it is also possible to set the path to the cryptolib.so using an environmental variable.
```bash
export CRYPTOLIB=".../colonies/lib/cryptolib.so"
```

To install the Colonies cryptolib, type:
```bash
git clone git@github.com:colonyos/colonies.git
cd colonies
sudo make install
```

## Starting a Colonies server
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

## Calling a function 
To execute a function, a function specification must be submitted to the Colonies server. Colonies will then wrap the function specification in a process and assign the process to an Executor.

Below is an example of function specification.
```json
{
    "conditions": {
        "executortype": "echo_executor"
    },
    "func": "echo",
    "args": [
        "helloworld"
    ],
    "priority": 0,
    "maxexectime": 10,
    "maxretries": 3,
    "maxwaittime": 100,

}
```

A function specification can be submitted using the Colonies CLI.
```console
colonies function submit --spec echo_func_spec.json

INFO[0000] Process submitted                             ProcessID=ea398af346db85f45b118bb77ecda9ae25f4700dcafcccb4ba3e4d40eba5205a
```

Or using the Python SDK.
```python
func_spec = create_func_spec(func=sum_nums, 
                             args=["helloworld"], 
                             colonyid=colonyid, 
                             executortype="echo_executor",
                             priority=0,
                             maxexectime=10,
                             maxretries=3,
                             maxwaittime=100)

process = colonies.submit(func_spec, executor_prvkey)
```
See [echo.py](https://github.com/colonyos/pycolonies/blob/main/examples/echo.py) for a full example. 

Now it possible to look up the process using the Colonies CLI.
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

The command below shows all waiting processes. Note that the process is just enqueued since we don't yet have an Executor of the type *echo_executor*. 
```console
colonies process psw
INFO[0000] Starting a Colonies client                    Insecure=true ServerHost=localhost ServerPort=50080
+------------------------------------------------------------------+------+------------+---------------------+---------------+
|                                ID                                | FUNC |    ARGS    |   SUBMISSION TIME   | EXECUTOR TYPE |
+------------------------------------------------------------------+------+------------+---------------------+---------------+
| 4787a5071856a4acf702b2ffcea422e3237a679c681314113d86139461290cf4 | echo | helloworld | 2023-03-12 21:09:09 | echo_executor |
+------------------------------------------------------------------+------+------------+---------------------+---------------+
```

```console
python3 examples/echo.py
```

## Implementing an Executor in Python
Executors are responsible for executing processes. They connect to the Colonies server and get process assignments. To be able to submit function specifications or get process assignments, an Executor must be a member of a Colony. Only the Colony owner has the authority to add an Executor to a Colony. In order to interact with the Colonies server and other Executors, Executors must authenticate and prove their membership. This security mechanism is implemented through the utilization of public key encryption.

Since we have access to the Colony private key (see devenv file), we can implement a self-registering Executor. 
```python
colonies = Colonies("localhost", 50080)
crypto = Crypto()
colonyid = "4787a5071856a4acf702b2ffcea422e3237a679c681314113d86139461290cf4"
colony_prvkey="ba949fa134981372d6da62b6a56f336ab4d843b22c02a4257dcf7d0d73097514"
executor_prvkey = crypto.prvkey()
executorid = crypto.id(executor_prvkey)

executor = {
    "executorname": "echo_executor",
    "executorid": executorid,
    "colonyid": colonyid,
    "executortype": "echo_executor"
}

colonies.add_executor(executor, colony_prvkey)
colonies.approve_executor(executorid, colony_prvkey)
```

We also need to register the `echo` function, telling the Colonies server that this executor is capable of executing a function called `echo`. 

```python
colonies.add_function(executorid, 
                      colonyid, 
                      "echo",  
                      ["arg"], 
                      "Python function that returns its input as output", 
                      executor_prvkey)
```

The next step is to connect the Colonies server and get process assignments. Note that the Colonies server never establish connections to the Executors, but rather it the responsibility of the Executors to connects to the Colonies server. In this way, Executors may run behind firewalls without problems. The `assign` function below will block for 10 seconds if there are no suitable process to assign.

```python
process = colonies.assign(colonyid, 10, executor_prvkey)
if process["spec"]["funcname"] == "echo":
    assigned_args = process["spec"]["args"]
    colonies.close(process["processid"], [arg], executor_prvkey)
```

The *close* method sets the output (same the args in this case) and the process state to *successful*. Only the Executor assigned to a process may alter process information stored on the Colonies server. By setting the *maxexectime* attribute on the function spec, it is possible to specify how long an executor may run a process before it is released back the waiting queue at the Colonies server. This is a very useful feature to implement robust processing pipelines.

See [echo_executor.py](https://github.com/colonyos/pycolonies/blob/main/examples/echo_executor.py) for a full example. Type the command below to start the *echo Executor*. 

```console
python3 examples/echo_executor.py
```

# Workflows
Colonies supports creation of computational DAGs (Directed Acyclic Graphs). This makes it possible to create dependencies between several functions, i.e. control the order which functions are called and pass values between function calls, even if they run on different Executors. Since Executors may reside *anywhere* on the Internet, we can create workflows that are executed across platforms and infrastructures, **creating compute continuums**. 

The example below calculates `sum_nums(gen_nums())`. The `gen_nums()` function simply return a tuple containing 1 and 2. The `sum_nums()` function takes two arguments and calculates the sum of them.

```python
def gen_nums(ctx={}):
    return 1, 2 

def sum_nums(n1, n2, ctx={}):
    return n1 + n2 

wf = Workflow(colonyid)
func_spec = create_func_spec(func=gen_nums, 
                             args=[], 
                             colonyid=colonyid, 
                             executortype="python_executor")
wf.add(func_spec, nodename="gen_nums", dependencies=[])

func_spec = create_func_spec(func=sum_nums, 
                             args=[], 
                             colonyid=colonyid, 
                             executortype="python_executor")
wf.add(func_spec, nodename="sum_nums", dependencies=["gen_nums"])

processgraph = colonies.submit(wf, executor_prvkey)
```

## Dynamic processgraphs
 It also possible to dynamically modify a processgraph while it is still active, e.g. a function may submit more function specifications to a workflow while executing. This makes it possible to implement patterns like [MapReduce](https://en.wikipedia.org/wiki/MapReduce).

The `map()` function below dynamically adds 5 `gen_nums()` functions to the processgraph.

```python
def map(ctx={}):
    code = """def gen_nums(ctx={}):
                return 1, 2""" 
  
    processgraphid = ctx["process"]["processgraphid"]
    map_processid = ctx["process"]["processid"]
    executor_prvkey = ctx["executor_prvkey"]
  
    processgraph = colonies.get_processgraph(processgraphid, executor_prvkey)
    print(processgraph)
    reduce_process = colonies.find_process("reduce", processgraph["processids"], executor_prvkey)
    reduce_processid = reduce_process["processid"]

    insert = True
    for i in range(5):
        func_spec = create_func_spec(func="gen_nums", 
                                     args=[], 
                                     colonyid=ctx["colonyid"], 
                                     executortype="python_executor",
                                     priority=200,
                                     maxexectime=100,
                                     maxretries=3,
                                     maxwaittime=100,
                                     code=code)


        colonies.add_child(processgraphid, map_processid, reduce_processid, func_spec, "gen_nums_" + str(i), insert, executor_prvkey)
        insert = False
```

The `reduce()` function takes arbitrary integer arguments and returns the sum of them. 

```python
def reduce(*nums, ctx={}):
    total = 0
    for n in nums:
        total += n
    return total 
```

We can now create a workflow to calculate: `reduce(gen_nums(), gen_nums(), gen_nums(), gen_nums(), gen_nums())`. The result should be (1+2)*5=15.

```python
wf = Workflow(colonyid)
func_spec = create_func_spec(func=map, 
                             args=[], 
                             colonyid=colonyid, 
                             executortype="python_executor")
wf.add(func_spec, nodename="map", dependencies=[])

func_spec = create_func_spec(func=reduce, 
                             args=[], 
                             colonyid=colonyid, 
                             executortype="python_executor")
wf.add(func_spec, nodename="reduce", dependencies=["map"])

processgraph = colonies.submit(wf, executor_prvkey)
```

![MapReduce example](docs/images/mapreduce.png)

# Monadic workflows
The workflow code can be significantly simplified by expressing it as a monad. A good introduction to monads can be found [here](https://brian-candler.medium.com/function-composition-with-bind-4f6e3fdc0e7). The example below is not a complete monad, but illustrated how the Colonies *plumbing* can be removed and create elegant functional expressions. The `>>` operator is usually call the `bind` functions and makes it possible to chain function calls.   

```python
def gen_data(ctx={}):
    return 1, 2 

def process_data(*nums, ctx={}):
    total = 0
    for n in nums:
        total += n
    return total 

gen_data = Function(gen_data, colonyid, executortype="python_executor")
process_data = Function(process_data, colonyid, executortype="python_executor")
echo = Function("echo", colonyid, executortype="echo_executor")

m = ColoniesMonad("localhost", 50080, colonyid, executor_prvkey)
result = (m >> gen_data >> process_data >> echo).unwrap()
print(result)  # prints 3 
```

See [colonies_monad.py](https://github.com/colonyos/pycolonies/blob/main/examples/colonies_monad.py) and [monad_example2.py](https://github.com/colonyos/pycolonies/blob/main/examples/monad_example2.py) for a full example.
