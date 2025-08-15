from typing import List

from pycolonies import colonies_client
from model import Workflow, FuncSpec, Conditions, Gpu

colonies, colonyname, colony_prvkey, executorid, executor_prvkey = colonies_client()

def gen_sleep(executorname: str, nodename: str, dependencies: List[str]) -> FuncSpec:
    return FuncSpec (
        conditions=Conditions(
            executortype="container-executor",
            executornames=[
                executorname
            ],
            nodes=1,
            processespernode=1,
            mem="500Mi",
            cpu="1000m",
            gpu=Gpu(
                count=0
            ),
            walltime=60,
            dependencies=dependencies
        ),
        funcname="execute",
        kwargs={
            "cmd": "sleep 8",
            "docker-image": "ubuntu:20.04"
        },
        maxexectime=55,
        maxretries=3,
        nodename=nodename
    )


wf = Workflow(colonyname=colonyname)
wf.functionspecs.append(gen_sleep("icekube", nodename="ice-0", dependencies=[]))
wf.functionspecs.append(gen_sleep("lumi-std", nodename="lumi-0", dependencies=["ice-0"]))
wf.functionspecs.append(gen_sleep("lumi-std", nodename="lumi-1", dependencies=["ice-0"]))
wf.functionspecs.append(gen_sleep("lumi-std", nodename="lumi-2", dependencies=["ice-0"]))
wf.functionspecs.append(gen_sleep("lumi-std", nodename="lumi-3", dependencies=["ice-0"]))
wf.functionspecs.append(gen_sleep("lumi-std", nodename="lumi-4", dependencies=["ice-0"]))
wf.functionspecs.append(gen_sleep("lumi-std", nodename="lumi-5", dependencies=["ice-0"]))
wf.functionspecs.append(gen_sleep("lumi-std", nodename="lumi-6", dependencies=["ice-0"]))
wf.functionspecs.append(gen_sleep("lumi-std ", nodename="lumi-7", dependencies=["ice-0"]))
wf.functionspecs.append(gen_sleep("leonardo-booster", nodename="leonardo-0", dependencies=["lumi-0", "lumi-1", "lumi-2", "lumi-3", "lumi-4", "lumi-5", "lumi-6", "lumi-7"]))

wf.functionspecs.append(gen_sleep("icekube", nodename="ice-1", dependencies=["leonardo-0"]))
colonies.submit_workflow(wf, executor_prvkey)
