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
    
    def add_test_runtime(self, colonyid, colony_prvkey):
        runtime_prvkey = self.crypto.prvkey()
        runtimeid = self.crypto.id(runtime_prvkey)

        ran = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 10))

        runtime = {
            "name": "test_runtime_" + ran,
            "runtimeid": runtimeid,
            "colonyid": colonyid,
            "runtimetype": "test_runtime_type",
            "cpu": "AMD Ryzen 9 5950X (32) @ 3.400GHz",
            "cores": 32,
            "mem": 80326,
            "gpu": "NVIDIA GeForce RTX 2080 Ti Rev. A",
            "gpus": 1
        }

        return self.client.add_runtime(runtime, colony_prvkey), runtimeid, runtime_prvkey
    
    def submit_test_process(self, colonyid, runtime_prvkey):
        process_spec = {
            "conditions": {
                "colonyid": colonyid,
                "runtimeids": [],
                "runtimetype": "test_runtime_type",
            },
            "env": {
                "test_key": "test_value2"
            },
            "maxexectime": -1,
            "maxretries": 3
        }
    
        return self.client.submit_process_spec(process_spec, runtime_prvkey)
    
    def test_add_colony(self):
        added_colony, colonyid, _ = self.add_test_colony()
        self.assertEqual(added_colony["colonyid"], colonyid)

        self.client.del_colony(colonyid, self.server_prv)

        server_prv = "09545df1812e252a2a853cca29d7eace4a3fe2baad334e3b7141a98d43c31e7c"  # note last c, incorrect key
        with self.assertRaises(Exception): 
            client.add_colony(colony, server_prv)
   
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
    
    def test_add_runtime(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_runtime, runtimeid, runtime_prvkey = self.add_test_runtime(colonyid, colony_prvkey)

        self.assertEqual(runtimeid, added_runtime["runtimeid"])
        self.client.del_colony(colonyid, self.server_prv)
    
    def test_list_runtimes(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_runtime, runtimeid, runtime_prvkey = self.add_test_runtime(colonyid, colony_prvkey)

        runtimes_from_server = self.client.list_runtimes(colonyid, colony_prvkey)
        self.assertEqual(runtimes_from_server[0]["runtimeid"], runtimeid)

        self.client.del_colony(colonyid, self.server_prv)
    
    def test_approve_runtime(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_runtime, runtimeid, runtime_prvkey = self.add_test_runtime(colonyid, colony_prvkey)

        runtimes_from_server = self.client.list_runtimes(colonyid, colony_prvkey)
        self.assertEqual(runtimes_from_server[0]["state"], 0)
    
        self.client.approve_runtime(runtimeid, colony_prvkey)
        runtimes_from_server = self.client.list_runtimes(colonyid, colony_prvkey)
        self.assertEqual(runtimes_from_server[0]["state"], 1)

        self.client.del_colony(colonyid, self.server_prv)
    
    def test_reject_runtime(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_runtime, runtimeid, runtime_prvkey = self.add_test_runtime(colonyid, colony_prvkey)

        runtimes_from_server = self.client.list_runtimes(colonyid, colony_prvkey)
        self.assertEqual(runtimes_from_server[0]["state"], 0)
    
        self.client.reject_runtime(runtimeid, colony_prvkey)
        runtimes_from_server = self.client.list_runtimes(colonyid, colony_prvkey)
        self.assertEqual(runtimes_from_server[0]["state"], 2)

        self.client.del_colony(colonyid, self.server_prv)
    
    def test_delete_runtime(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_runtime, runtimeid, runtime_prvkey = self.add_test_runtime(colonyid, colony_prvkey)

        self.client.delete_runtime(runtimeid, colony_prvkey)
        runtimes_from_server = self.client.list_runtimes(colonyid, colony_prvkey)
        self.assertEqual(runtimes_from_server, None)  # XXX: Shouldn't list_runtimes return an empty list rather than None?

        self.client.del_colony(colonyid, self.server_prv)
    
    def test_submit_process(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_runtime, runtimeid, runtime_prvkey = self.add_test_runtime(colonyid, colony_prvkey)
        self.client.approve_runtime(runtimeid, colony_prvkey)
        process = self.submit_test_process(colonyid, runtime_prvkey)
        self.assertEqual(process["state"], 0)
        
        self.client.del_colony(colonyid, self.server_prv)
    
    def test_assign_process(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_runtime, runtimeid, runtime_prvkey = self.add_test_runtime(colonyid, colony_prvkey)
        self.client.approve_runtime(runtimeid, colony_prvkey)
        process = self.submit_test_process(colonyid, runtime_prvkey)
       
        assigned_process = self.client.assign_process(colonyid, 10, runtime_prvkey)
        self.assertEqual(assigned_process["processid"], process["processid"])

        self.client.del_colony(colonyid, self.server_prv)
    
    def test_list_process(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_runtime, runtimeid, runtime_prvkey = self.add_test_runtime(colonyid, colony_prvkey)
        self.client.approve_runtime(runtimeid, colony_prvkey)
 
        self.submit_test_process(colonyid, runtime_prvkey)
        self.submit_test_process(colonyid, runtime_prvkey)

        waiting_processes = self.client.list_processes(colonyid, 2, Colonies.WAITING, runtime_prvkey)
        self.assertEqual(len(waiting_processes), 2)

        self.client.del_colony(colonyid, self.server_prv)
    
    def test_get_process(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_runtime, runtimeid, runtime_prvkey = self.add_test_runtime(colonyid, colony_prvkey)
        self.client.approve_runtime(runtimeid, colony_prvkey)
 
        submitted_process = self.submit_test_process(colonyid, runtime_prvkey)

        process = self.client.get_process(submitted_process["processid"], runtime_prvkey)
        self.assertEqual(process["processid"], submitted_process["processid"])

        self.client.del_colony(colonyid, self.server_prv)
    
    def test_delete_process(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_runtime, runtimeid, runtime_prvkey = self.add_test_runtime(colonyid, colony_prvkey)
        self.client.approve_runtime(runtimeid, colony_prvkey)
 
        submitted_process = self.submit_test_process(colonyid, runtime_prvkey)
        
        self.client.delete_process(submitted_process["processid"], runtime_prvkey)

        with self.assertRaises(Exception): 
            self.client.get_process(submitted_process["processid"], runtime_prvkey)

        self.client.del_colony(colonyid, self.server_prv)
    
    def test_close_process(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_runtime, runtimeid, runtime_prvkey = self.add_test_runtime(colonyid, colony_prvkey)
        self.client.approve_runtime(runtimeid, colony_prvkey)
 
        submitted_process1 = self.submit_test_process(colonyid, runtime_prvkey)
        submitted_process2 = self.submit_test_process(colonyid, runtime_prvkey)
        submitted_process3 = self.submit_test_process(colonyid, runtime_prvkey)
        submitted_process4 = self.submit_test_process(colonyid, runtime_prvkey)

        self.client.assign_process(colonyid, 10, runtime_prvkey)
        self.client.assign_process(colonyid, 10, runtime_prvkey)
        self.client.assign_process(colonyid, 10, runtime_prvkey)

        self.client.close(submitted_process1["processid"], True, runtime_prvkey)
        self.client.close(submitted_process2["processid"], False, runtime_prvkey)

        waiting_processes = self.client.list_processes(colonyid, 2, Colonies.WAITING, runtime_prvkey)
        running_processes = self.client.list_processes(colonyid, 2, Colonies.RUNNING, runtime_prvkey)
        successful_processes = self.client.list_processes(colonyid, 2, Colonies.SUCCESSFUL, runtime_prvkey)
        failed_processes = self.client.list_processes(colonyid, 2, Colonies.FAILED, runtime_prvkey)

        self.assertEqual(len(waiting_processes), 1)
        self.assertEqual(len(running_processes), 1)
        self.assertEqual(len(successful_processes), 1)
        self.assertEqual(len(failed_processes), 1)

        self.client.del_colony(colonyid, self.server_prv)
    
    def test_stats(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_runtime, runtimeid, runtime_prvkey = self.add_test_runtime(colonyid, colony_prvkey)
        self.client.approve_runtime(runtimeid, colony_prvkey)
 
        submitted_process1 = self.submit_test_process(colonyid, runtime_prvkey)
        submitted_process2 = self.submit_test_process(colonyid, runtime_prvkey)
        submitted_process3 = self.submit_test_process(colonyid, runtime_prvkey)
        submitted_process4 = self.submit_test_process(colonyid, runtime_prvkey)

        self.client.assign_process(colonyid, 10, runtime_prvkey)
        self.client.assign_process(colonyid, 10, runtime_prvkey)
        self.client.assign_process(colonyid, 10, runtime_prvkey)
        
        self.client.close(submitted_process1["processid"], True, runtime_prvkey)
        self.client.close(submitted_process2["processid"], False, runtime_prvkey)
        
        waiting_processes = self.client.list_processes(colonyid, 2, 0, runtime_prvkey)
        running_processes = self.client.list_processes(colonyid, 2, 1, runtime_prvkey)
        successful_processes = self.client.list_processes(colonyid, 2, 2, runtime_prvkey)
        failed_processes = self.client.list_processes(colonyid, 2, 3, runtime_prvkey)

        stats = self.client.stats(colonyid, runtime_prvkey)

        self.assertEqual(len(waiting_processes), stats["waitingprocesses"])
        self.assertEqual(len(running_processes), stats["runningprocesses"])
        self.assertEqual(len(successful_processes), stats["successfulprocesses"])
        self.assertEqual(len(failed_processes), stats["failedprocesses"])

        self.client.del_colony(colonyid, self.server_prv)
    
    def test_add_attribute(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_runtime, runtimeid, runtime_prvkey = self.add_test_runtime(colonyid, colony_prvkey)
        self.client.approve_runtime(runtimeid, colony_prvkey)
 
        submitted_process = self.submit_test_process(colonyid, runtime_prvkey)
        self.client.assign_process(colonyid, 10, runtime_prvkey)

        self.client.add_attribute(submitted_process["processid"], "py_test_key", "py_test_value", runtime_prvkey)
        
        process = self.client.get_process(submitted_process["processid"], runtime_prvkey)
        found = False
        for attr in process["attributes"]:
            if attr["key"] == "py_test_key" and attr["value"] == "py_test_value":
                found = True
        self.assertTrue(found)

        self.client.del_colony(colonyid, self.server_prv)
    
    def test_get_attribute(self):
        added_colony, colonyid, colony_prvkey = self.add_test_colony()
        added_runtime, runtimeid, runtime_prvkey = self.add_test_runtime(colonyid, colony_prvkey)
        self.client.approve_runtime(runtimeid, colony_prvkey)
 
        submitted_process = self.submit_test_process(colonyid, runtime_prvkey)
        self.client.assign_process(colonyid, 10, runtime_prvkey)

        attribute = self.client.add_attribute(submitted_process["processid"], "py_test_key", "py_test_value", runtime_prvkey)
        attribute_from_server = self.client.get_attribute(attribute["attributeid"], runtime_prvkey)
        self.assertEqual(attribute_from_server["attributeid"], attribute["attributeid"])

        self.client.del_colony(colonyid, self.server_prv)
    
if __name__ == '__main__':
    unittest.main()
