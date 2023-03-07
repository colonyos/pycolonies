import unittest
import sys
import string
import random
sys.path.append(".")
from crypto import Crypto
from colonies import Colonies

class TestColonies(unittest.TestCase):
    def setUp(self):
        url = "http://localhost:50080/api"
        self.client = Colonies(url)
        self.crypto = Crypto()
        self.server_prv = "fcc79953d8a751bf41db661592dc34d30004b1a651ffa0725b03ac227641499d"

    def add_test_colony(self):
        colony_prvkey = self.crypto.prvkey()
        colonyid = self.crypto.id(colony_prvkey)
        colony = {
            "colonyid" : colonyid,
            "name" : "python_test"
        }

        return self.client.add_colony(colony, self.server_prv), colonyid, colony_prvkey
    
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

        return self.client.add_executor(executor, colony_prvkey), executorid, executor_prvkey
     
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
    
        return self.client.submit(func_spec, executor_prvkey)
    
    def test_add_colony(self):
        added_colony, colonyid, _ = self.add_test_colony()
        self.assertEqual(added_colony["colonyid"], colonyid)
        self.client.del_colony(colonyid, self.server_prv)

    def test_del_colony(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        colonies_from_server = self.client.list_colonies(self.server_prv)
      
        found_colony = False
        for colony in colonies_from_server:
            if colony["colonyid"] == colonyid:
                found_colony = True
        self.assertTrue(found_colony)

        self.client.del_colony(colonyid, self.server_prv)
        colonies_from_server = self.client.list_colonies(self.server_prv)
        
        found_colony = False
        for colony in colonies_from_server:
            if colony["colonyid"] == colonyid:
                found_colony = True
        self.assertFalse(found_colony)
     
    def test_add_executor(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)

        self.assertEqual(executorid, added_executor["executorid"])
        self.client.del_colony(colonyid, self.server_prv)
     
    def test_list_executors(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)

        executors_from_server = self.client.list_executors(colonyid, colony_prvkey)
        self.assertEqual(executors_from_server[0]["executorid"], executorid)

        self.client.del_colony(colonyid, self.server_prv)
     
    def test_approve_executor(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)

        executors_from_server = self.client.list_executors(colonyid, colony_prvkey)
        self.assertEqual(executors_from_server[0]["state"], 0)
    
        self.client.approve_executor(executorid, colony_prvkey)
        executors_from_server = self.client.list_executors(colonyid, colony_prvkey)
        self.assertEqual(executors_from_server[0]["state"], 1)

        self.client.del_colony(colonyid, self.server_prv)
     
    def test_reject_executor(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)

        executors_from_server = self.client.list_executors(colonyid, colony_prvkey)
        self.assertEqual(executors_from_server[0]["state"], 0)
    
        self.client.reject_executor(executorid, colony_prvkey)
        executors_from_server = self.client.list_executors(colonyid, colony_prvkey)
        self.assertEqual(executors_from_server[0]["state"], 2)

        self.client.del_colony(colonyid, self.server_prv)
     
    def test_delete_executor(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)

        self.client.delete_executor(executorid, colony_prvkey)
        executors_from_server = self.client.list_executors(colonyid, colony_prvkey)
        
        # XXX: Shouldn't list_executors return an empty list rather than None?
        self.assertEqual(executors_from_server, None)  

        self.client.del_colony(colonyid, self.server_prv)
     
    def test_submit(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.client.approve_executor(executorid, colony_prvkey)
        process = self.submit_test_funcspec(colonyid, executor_prvkey)
        self.assertEqual(process["state"], 0)
        
        self.client.del_colony(colonyid, self.server_prv)
     
    def test_assign(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.client.approve_executor(executorid, colony_prvkey)
        process = self.submit_test_funcspec(colonyid, executor_prvkey)
       
        assigned_process = self.client.assign(colonyid, 10, executor_prvkey)
        self.assertEqual(assigned_process["processid"], process["processid"])

        self.client.del_colony(colonyid, self.server_prv)
     
    def test_list_process(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.client.approve_executor(executorid, colony_prvkey)

        self.submit_test_funcspec(colonyid, executor_prvkey)
        self.submit_test_funcspec(colonyid, executor_prvkey)

        waiting_processes = self.client.list_processes(colonyid, 2, Colonies.WAITING, executor_prvkey)
        self.assertEqual(len(waiting_processes), 2)

        self.client.del_colony(colonyid, self.server_prv)
     
    def test_get_process(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.client.approve_executor(executorid, colony_prvkey)

        submitted_process = self.submit_test_funcspec(colonyid, executor_prvkey)

        process = self.client.get_process(submitted_process["processid"], executor_prvkey)
        self.assertEqual(process["processid"], submitted_process["processid"])

        self.client.del_colony(colonyid, self.server_prv)
     
    def test_delete_process(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.client.approve_executor(executorid, colony_prvkey)

        submitted_process = self.submit_test_funcspec(colonyid, executor_prvkey)
        
        self.client.delete_process(submitted_process["processid"], executor_prvkey)

        with self.assertRaises(Exception): 
            self.client.get_process(submitted_process["processid"], executor_prvkey)

        self.client.del_colony(colonyid, self.server_prv)
    
    def test_close_process(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.client.approve_executor(executorid, colony_prvkey)

        submitted_process1 = self.submit_test_funcspec(colonyid, executor_prvkey)
        submitted_process2 = self.submit_test_funcspec(colonyid, executor_prvkey)
        submitted_process3 = self.submit_test_funcspec(colonyid, executor_prvkey)
        submitted_process4 = self.submit_test_funcspec(colonyid, executor_prvkey)

        self.client.assign(colonyid, 10, executor_prvkey)
        self.client.assign(colonyid, 10, executor_prvkey)
        self.client.assign(colonyid, 10, executor_prvkey)

        self.client.close(submitted_process1["processid"], True, executor_prvkey)
        self.client.close(submitted_process2["processid"], False, executor_prvkey)

        waiting_processes = self.client.list_processes(colonyid, 2, Colonies.WAITING, executor_prvkey)
        running_processes = self.client.list_processes(colonyid, 2, Colonies.RUNNING, executor_prvkey)
        successful_processes = self.client.list_processes(colonyid, 2, Colonies.SUCCESSFUL, executor_prvkey)
        failed_processes = self.client.list_processes(colonyid, 2, Colonies.FAILED, executor_prvkey)

        self.assertEqual(len(waiting_processes), 1)
        self.assertEqual(len(running_processes), 1)
        self.assertEqual(len(successful_processes), 1)
        self.assertEqual(len(failed_processes), 1)

        self.client.del_colony(colonyid, self.server_prv)
 #    
    def test_stats(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.client.approve_executor(executorid, colony_prvkey)

        submitted_process1 = self.submit_test_funcspec(colonyid, executor_prvkey)
        submitted_process2 = self.submit_test_funcspec(colonyid, executor_prvkey)
        submitted_process3 = self.submit_test_funcspec(colonyid, executor_prvkey)
        submitted_process4 = self.submit_test_funcspec(colonyid, executor_prvkey)

        self.client.assign(colonyid, 10, executor_prvkey)
        self.client.assign(colonyid, 10, executor_prvkey)
        self.client.assign(colonyid, 10, executor_prvkey)
        
        self.client.close(submitted_process1["processid"], True, executor_prvkey)
        self.client.close(submitted_process2["processid"], False, executor_prvkey)
        
        waiting_processes = self.client.list_processes(colonyid, 2, 0, executor_prvkey)
        running_processes = self.client.list_processes(colonyid, 2, 1, executor_prvkey)
        successful_processes = self.client.list_processes(colonyid, 2, 2, executor_prvkey)
        failed_processes = self.client.list_processes(colonyid, 2, 3, executor_prvkey)

        stats = self.client.stats(colonyid, executor_prvkey)

        self.assertEqual(len(waiting_processes), stats["waitingprocesses"])
        self.assertEqual(len(running_processes), stats["runningprocesses"])
        self.assertEqual(len(successful_processes), stats["successfulprocesses"])
        self.assertEqual(len(failed_processes), stats["failedprocesses"])

        self.client.del_colony(colonyid, self.server_prv)
    
    def test_add_attribute(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.client.approve_executor(executorid, colony_prvkey)

        submitted_process = self.submit_test_funcspec(colonyid, executor_prvkey)
        self.client.assign(colonyid, 10, executor_prvkey)

        self.client.add_attribute(submitted_process["processid"], "py_test_key", "py_test_value", executor_prvkey)
        
        process = self.client.get_process(submitted_process["processid"], executor_prvkey)
        found = False
        for attr in process["attributes"]:
            if attr["key"] == "py_test_key" and attr["value"] == "py_test_value":
                found = True
        self.assertTrue(found)

        self.client.del_colony(colonyid, self.server_prv)
    
    def test_get_attribute(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_executor, executorid, executor_prvkey = self.add_test_executor(colonyid, colony_prvkey)
        self.client.approve_executor(executorid, colony_prvkey)

        submitted_process = self.submit_test_funcspec(colonyid, executor_prvkey)
        self.client.assign(colonyid, 10, executor_prvkey)

        attribute = self.client.add_attribute(submitted_process["processid"], "py_test_key", "py_test_value", executor_prvkey)
        attribute_from_server = self.client.get_attribute(attribute["attributeid"], executor_prvkey)
        self.assertEqual(attribute_from_server["attributeid"], attribute["attributeid"])

        self.client.del_colony(colonyid, self.server_prv)
    
if __name__ == '__main__':
    unittest.main()
