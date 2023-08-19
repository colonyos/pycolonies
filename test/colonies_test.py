import unittest
import sys
import string
import random
sys.path.append(".")
from crypto import Crypto
from pycolonies import Colonies

class TestColonies(unittest.TestCase):
    def setUp(self):
        self.colonies = Colonies("localhost", 50080)
        self.crypto = Crypto()
        self.server_prv = "fcc79953d8a751bf41db661592dc34d30004b1a651ffa0725b03ac227641499d"

    def add_test_colony(self):
        colony_prvkey = self.crypto.prvkey()
        colonyid = self.crypto.id(colony_prvkey)
        colony = {
            "colonyid" : colonyid,
            "name" : "python_test"
        }

        return self.colonies.add_colony(colony, self.server_prv), colonyid, colony_prvkey
    
    def add_test_executor(self, colonyid, colony_prvkey):
        executor_prvkey = self.crypto.prvkey()
        executorid = self.crypto.id(executor_prvkey)

        ran = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 10))

        executor = {
            "executorname": "test_executor_" + ran,
            "executorid": executorid,
            "colonyid": colonyid,
            "executortype": "test_executor_type"
        }

        return self.colonies.add_executor(executor, colony_prvkey), executorid, executor_prvkey
     
    def submit_test_funcspec(self, colonyid, executor_prvkey):
        func_spec = {
            "conditions": {
                "colonyid": colonyid,
                "executorids": [],
                "executortype": "test_executor_type",
            },
            "env": {
                "test_key": "test_value2"
            },
            "maxexectime": -1,
            "maxretries": 3
        }
    
        return self.colonies.submit(func_spec, executor_prvkey)
    
    def test_add_colony(self):
        added_colony, colonyid, _ = self.add_test_colony()
        self.assertEqual(added_colony["colonyid"], colonyid)
        self.colonies.del_colony(colonyid, self.server_prv)

    def test_del_colony(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        colonies_from_server = self.colonies.list_colonies(self.server_prv)
      
        found_colony = False
        for colony in colonies_from_server:
            if colony["colonyid"] == colonyid:
                found_colony = True
        self.assertTrue(found_colony)

        self.colonies.del_colony(colonyid, self.server_prv)
        colonies_from_server = self.colonies.list_colonies(self.server_prv)
        
        found_colony = False
        for colony in colonies_from_server:
            if colony["colonyid"] == colonyid:
                found_colony = True
        self.assertFalse(found_colony)
     
    def test_add_executor(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)

        self.assertEqual(executorid, added_executor["executorid"])
        self.colonies.del_colony(colonyid, self.server_prv)
     
    def test_list_executors(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)

        executors_from_server = self.colonies.list_executors(colonyid, colony_prvkey)
        self.assertEqual(executors_from_server[0]["executorid"], executorid)

        self.colonies.del_colony(colonyid, self.server_prv)
     
    def test_approve_executor(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)

        executors_from_server = self.colonies.list_executors(colonyid, colony_prvkey)
        self.assertEqual(executors_from_server[0]["state"], 0)
    
        self.colonies.approve_executor(executorid, colony_prvkey)
        executors_from_server = self.colonies.list_executors(colonyid, colony_prvkey)
        self.assertEqual(executors_from_server[0]["state"], 1)

        self.colonies.del_colony(colonyid, self.server_prv)
     
    def test_reject_executor(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)

        executors_from_server = self.colonies.list_executors(colonyid, colony_prvkey)
        self.assertEqual(executors_from_server[0]["state"], 0)
    
        self.colonies.reject_executor(executorid, colony_prvkey)
        executors_from_server = self.colonies.list_executors(colonyid, colony_prvkey)
        self.assertEqual(executors_from_server[0]["state"], 2)

        self.colonies.del_colony(colonyid, self.server_prv)
     
    def test_delete_executor(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)

        self.colonies.delete_executor(executorid, colony_prvkey)
        executors_from_server = self.colonies.list_executors(colonyid, colony_prvkey)
        
        # XXX: Shouldn't list_executors return an empty list rather than None?
        self.assertEqual(executors_from_server, None)  

        self.colonies.del_colony(colonyid, self.server_prv)
     
    def test_submit(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.colonies.approve_executor(executorid, colony_prvkey)
        process = self.submit_test_funcspec(colonyid, executor_prvkey)
        self.assertEqual(process["state"], 0)
        
        self.colonies.del_colony(colonyid, self.server_prv)
     
    def test_assign(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.colonies.approve_executor(executorid, colony_prvkey)
        process = self.submit_test_funcspec(colonyid, executor_prvkey)
       
        assigned_process = self.colonies.assign(colonyid, 10, executor_prvkey)
        self.assertEqual(assigned_process["processid"], process["processid"])

        self.colonies.del_colony(colonyid, self.server_prv)
     
    def test_list_process(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.colonies.approve_executor(executorid, colony_prvkey)

        self.submit_test_funcspec(colonyid, executor_prvkey)
        self.submit_test_funcspec(colonyid, executor_prvkey)

        waiting_processes = self.colonies.list_processes(colonyid, 2, Colonies.WAITING, executor_prvkey)
        self.assertEqual(len(waiting_processes), 2)

        self.colonies.del_colony(colonyid, self.server_prv)
     
    def test_get_process(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.colonies.approve_executor(executorid, colony_prvkey)

        submitted_process = self.submit_test_funcspec(colonyid, executor_prvkey)

        process = self.colonies.get_process(submitted_process["processid"], executor_prvkey)
        self.assertEqual(process["processid"], submitted_process["processid"])

        self.colonies.del_colony(colonyid, self.server_prv)
     
    def test_delete_process(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.colonies.approve_executor(executorid, colony_prvkey)

        submitted_process = self.submit_test_funcspec(colonyid, executor_prvkey)
        
        self.colonies.delete_process(submitted_process["processid"], executor_prvkey)

        with self.assertRaises(Exception): 
            self.colonies.get_process(submitted_process["processid"], executor_prvkey)

        self.colonies.del_colony(colonyid, self.server_prv)
    
    def test_close_process(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.colonies.approve_executor(executorid, colony_prvkey)

        submitted_process1 = self.submit_test_funcspec(colonyid, executor_prvkey)
        submitted_process2 = self.submit_test_funcspec(colonyid, executor_prvkey)
        submitted_process3 = self.submit_test_funcspec(colonyid, executor_prvkey)
        submitted_process4 = self.submit_test_funcspec(colonyid, executor_prvkey)

        self.colonies.assign(colonyid, 10, executor_prvkey)
        self.colonies.assign(colonyid, 10, executor_prvkey)
        self.colonies.assign(colonyid, 10, executor_prvkey)

        self.colonies.close(submitted_process1["processid"], [], executor_prvkey)
        self.colonies.fail(submitted_process2["processid"], [], executor_prvkey)

        waiting_processes = self.colonies.list_processes(colonyid, 2, Colonies.WAITING, executor_prvkey)
        running_processes = self.colonies.list_processes(colonyid, 2, Colonies.RUNNING, executor_prvkey)
        successful_processes = self.colonies.list_processes(colonyid, 2, Colonies.SUCCESSFUL, executor_prvkey)
        failed_processes = self.colonies.list_processes(colonyid, 2, Colonies.FAILED, executor_prvkey)

        self.assertEqual(len(waiting_processes), 1)
        self.assertEqual(len(running_processes), 1)
        self.assertEqual(len(successful_processes), 1)
        self.assertEqual(len(failed_processes), 1)

        self.colonies.del_colony(colonyid, self.server_prv)
 #    
    def test_stats(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.colonies.approve_executor(executorid, colony_prvkey)

        submitted_process1 = self.submit_test_funcspec(colonyid, executor_prvkey)
        submitted_process2 = self.submit_test_funcspec(colonyid, executor_prvkey)
        submitted_process3 = self.submit_test_funcspec(colonyid, executor_prvkey)
        submitted_process4 = self.submit_test_funcspec(colonyid, executor_prvkey)

        self.colonies.assign(colonyid, 10, executor_prvkey)
        self.colonies.assign(colonyid, 10, executor_prvkey)
        self.colonies.assign(colonyid, 10, executor_prvkey)
        
        self.colonies.close(submitted_process1["processid"], [], executor_prvkey)
        self.colonies.fail(submitted_process2["processid"], [], executor_prvkey)
        
        waiting_processes = self.colonies.list_processes(colonyid, 2, 0, executor_prvkey)
        running_processes = self.colonies.list_processes(colonyid, 2, 1, executor_prvkey)
        successful_processes = self.colonies.list_processes(colonyid, 2, 2, executor_prvkey)
        failed_processes = self.colonies.list_processes(colonyid, 2, 3, executor_prvkey)

        stats = self.colonies.stats(colonyid, executor_prvkey)

        self.assertEqual(len(waiting_processes), stats["waitingprocesses"])
        self.assertEqual(len(running_processes), stats["runningprocesses"])
        self.assertEqual(len(successful_processes), stats["successfulprocesses"])
        self.assertEqual(len(failed_processes), stats["failedprocesses"])

        self.colonies.del_colony(colonyid, self.server_prv)
    
    def test_add_attribute(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.colonies.approve_executor(executorid, colony_prvkey)

        submitted_process = self.submit_test_funcspec(colonyid, executor_prvkey)
        self.colonies.assign(colonyid, 10, executor_prvkey)

        self.colonies.add_attribute(submitted_process["processid"], "py_test_key", "py_test_value", executor_prvkey)
        
        process = self.colonies.get_process(submitted_process["processid"], executor_prvkey)
        found = False
        for attr in process["attributes"]:
            if attr["key"] == "py_test_key" and attr["value"] == "py_test_value":
                found = True
        self.assertTrue(found)

        self.colonies.del_colony(colonyid, self.server_prv)
    
    def test_get_attribute(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.colonies.approve_executor(executorid, colony_prvkey)

        submitted_process = self.submit_test_funcspec(colonyid, executor_prvkey)
        self.colonies.assign(colonyid, 10, executor_prvkey)

        attribute = self.colonies.add_attribute(submitted_process["processid"], "py_test_key", "py_test_value", executor_prvkey)
        attribute_from_server = self.colonies.get_attribute(attribute["attributeid"], executor_prvkey)
        self.assertEqual(attribute_from_server["attributeid"], attribute["attributeid"])

        self.colonies.del_colony(colonyid, self.server_prv)
    
    def test_add_function(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.colonies.approve_executor(executorid, colony_prvkey)
    
        self.colonies.add_function(executorid, colonyid, "funcname", executor_prvkey)

        self.colonies.del_colony(colonyid, self.server_prv)
    
    def test_get_functions_by_colony(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.colonies.approve_executor(executorid, colony_prvkey)
    
        self.colonies.add_function(executorid, colonyid, "funcname", executor_prvkey)
        functions = self.colonies.get_functions_by_colony(colonyid, executor_prvkey)
        self.assertTrue(len(functions)==1)
        self.assertEqual(functions[0]["funcname"], "funcname")
    
    def test_get_functions_by_executor(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.colonies.approve_executor(executorid, colony_prvkey)
    
        self.colonies.add_function(executorid, colonyid, "funcname", executor_prvkey)
        functions = self.colonies.get_functions_by_executor(executorid, executor_prvkey)
        self.assertTrue(len(functions)==1)
        self.assertEqual(functions[0]["funcname"], "funcname")

        self.colonies.del_colony(colonyid, self.server_prv)
    
    def test_create_snapshot(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.colonies.approve_executor(executorid, colony_prvkey)

        self.colonies.create_snapshot(colonyid, "test_label", "test_name", executor_prvkey)
        snapshots = self.colonies.get_snapshots(colonyid, executor_prvkey)
        self.assertTrue(len(snapshots)==1)
        snapshot = self.colonies.get_snapshot_by_name(colonyid, "test_name", executor_prvkey)
        self.assertEqual(snapshot["name"], "test_name")
        snapshot2 = self.colonies.get_snapshot_by_id(colonyid, snapshot["snapshotid"], executor_prvkey)
        self.assertEqual(snapshot2["name"], "test_name")

        self.colonies.del_colony(colonyid, self.server_prv)
    
    def test_get_add_logs(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.colonies.approve_executor(executorid, colony_prvkey)
        
        func_spec = {
            "conditions": {
                "colonyid": colonyid,
                "executorids": [],
                "executortype": "test_executor_type",
            },
            "env": {
                "test_key": "test_value2"
            },
            "maxexectime": -1,
            "maxretries": 3
        }
    
        self.colonies.submit(func_spec, executor_prvkey)
        assigned_process = self.colonies.assign(colonyid, 10, executor_prvkey)

        self.colonies.add_log(assigned_process["processid"], "test_log_msg", executor_prvkey)
        logs = self.colonies.get_process_log(assigned_process["processid"], 100, -1, executor_prvkey)
        self.assertTrue(len(logs)==1)
        self.assertEqual(logs[0]["message"], "test_log_msg")
        
        logs = self.colonies.get_executor_log(executorid, 100, -1, executor_prvkey)
        self.assertTrue(len(logs)==1)
        self.assertEqual(logs[0]["message"], "test_log_msg")
   
        self.colonies.del_colony(colonyid, self.server_prv)
    
if __name__ == '__main__':
    unittest.main()
