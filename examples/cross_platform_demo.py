import os
import random
import pickle
import matplotlib.pyplot as plt
import random
import json

from termcolor import cprint 

from pycolonies import Colonies
from pycolonies import colonies_client
from pycolonies import func_spec
from pycolonies import Workflow

colonies, colonyname, colony_prvkey, executorid, executor_prvkey = colonies_client()

def gen_sleep(executortype):
    return {
    "conditions": {
        "executortype": executortype,
        "nodes": 1,
        "processes-per-node": 1,
        "mem": "500Mi",
        "cpu": "1000m",
        "gpu": {
            "count": 0
        },
        "walltime": 60
    },
    "funcname": "execute",
    "kwargs": {
        "cmd": "sleep 8",
        "docker-image": "ubuntu:20.04"
    },
    "maxexectime": 55,
    "maxretries": 3
}


wf = Workflow(colonyname)
wf.add(gen_sleep("ice-kubeexecutor"), nodename="ice-0", dependencies=[])
wf.add(gen_sleep("lumi-small-hpcexecutor"), nodename="lumi-0", dependencies=["ice-0"])
wf.add(gen_sleep("lumi-small-hpcexecutor"), nodename="lumi-1", dependencies=["ice-0"])
wf.add(gen_sleep("lumi-small-hpcexecutor"), nodename="lumi-2", dependencies=["ice-0"])
wf.add(gen_sleep("lumi-small-hpcexecutor"), nodename="lumi-3", dependencies=["ice-0"])
wf.add(gen_sleep("lumi-small-hpcexecutor"), nodename="lumi-4", dependencies=["ice-0"])
wf.add(gen_sleep("lumi-small-hpcexecutor"), nodename="lumi-5", dependencies=["ice-0"])
wf.add(gen_sleep("lumi-small-hpcexecutor"), nodename="lumi-6", dependencies=["ice-0"])
wf.add(gen_sleep("lumi-small-hpcexecutor"), nodename="lumi-7", dependencies=["ice-0"])
wf.add(gen_sleep("lumi-small-hpcexecutor"), nodename="leonardo-0", dependencies=["lumi-0", "lumi-1", "lumi-2", "lumi-3", "lumi-4", "lumi-5", "lumi-6", "lumi-7"])

wf.add(gen_sleep("ice-kubeexecutor"), nodename="ice-1", dependencies=["leonardo-0"])
colonies.submit(wf, executor_prvkey)
