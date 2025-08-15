from pycolonies import colonies_client
from pycolonies import func_spec

colonies, colonyname, colony_prvkey, executor_name, prvkey = colonies_client()

f = func_spec(func="test",
              args=[],
              kwargs={
                  "arg_kw_1":"arg_1",
                  "arg_kw_2":"arg_2"
                  }, 
              colonyname=colonyname, 
              executortype="kwargs-executor",
              priority=200,
              maxexectime=100,
              maxretries=3,
              maxwaittime=100)

process = colonies.submit_func_spec(f, prvkey)
print("Process", process.processid, "submitted")
process = colonies.wait(process, 100, prvkey)
if process and process.output:
    print(process.output[0])
