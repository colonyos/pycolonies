import unittest
import string
import random
import sys
from typing import Tuple
sys.path.append(".")
from crypto import Crypto
from pycolonies import Colonies
from model import Executor, FuncSpec, Conditions, Workflow, Process, Colony
import os

test_colony_host = os.environ.get('TEST_COLONY_HOST', 'localhost')
test_colony_prvkey = os.environ.get('TEST_COLONY_PRVKEY', 'fcc79953d8a751bf41db661592dc34d30004b1a651ffa0725b03ac227641499d')

class TestColonies(unittest.TestCase):
    def setUp(self) -> None:
        self.colonies = Colonies(test_colony_host, 50080, tls=False, native_crypto=False)
        self.crypto = Crypto(native=False)
        self.server_prv = test_colony_prvkey

    def ran_prefix(self) -> str:
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=10))

    def add_test_colony(self) -> Tuple[Colony, str, str, str]:
        colony_prvkey = self.crypto.prvkey()
        colonyid = self.crypto.id(colony_prvkey)
        colony = {"colonyid": colonyid, "name": "python-test-" + self.ran_prefix()}

        return (
            self.colonies.add_colony(colony, self.server_prv),
            colonyid,
            colony["name"],
            colony_prvkey,
        )

    def add_test_executor(self, colonyname: str, colony_prvkey: str) -> Tuple[Executor, str, str, str]:
        executor_prvkey = self.crypto.prvkey()
        executorid = self.crypto.id(executor_prvkey)

        executor = {
            "executorname": "test-executor-" + self.ran_prefix(),
            "executorid": executorid,
            "colonyname": colonyname,
            "executortype": "test-executor-type",
        }

        return (
            self.colonies.add_executor(executor, colony_prvkey),
            executor["executorid"],
            executor["executorname"],
            executor_prvkey,
        )

    def submit_test_funcspec(self, colonyname: str, executor_prvkey: str) -> Process:
        spec = FuncSpec(
            conditions=Conditions(
                colonyname=colonyname, executortype="test-executor-type"
            ),
            env={"test_key": "test_value2"},
            maxexectime=-1,
            maxretries=3,
        )

        return self.colonies.submit_func_spec(spec, executor_prvkey)

    def test_add_colony(self) -> None:
        added_colony, _, colonyname, _ = self.add_test_colony()
        self.assertEqual(added_colony.name, colonyname)
        self.colonies.del_colony(colonyname, self.server_prv)

    def test_del_colony(self) -> None:
        _, _, colonyname, _ = self.add_test_colony()
        colonies_from_server = self.colonies.list_colonies(self.server_prv)

        found_colony = False
        for colony in colonies_from_server:
            if colony.name == colonyname:
                found_colony = True
        self.assertTrue(found_colony)

        self.colonies.del_colony(colonyname, self.server_prv)
        colonies_from_server = self.colonies.list_colonies(self.server_prv)

        found_colony = False
        for colony in colonies_from_server:
            if colony.name == colonyname:
                found_colony = True
        self.assertFalse(found_colony)

    def test_add_executor(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        added_executor, executorid, _, _ = self.add_test_executor(
            colonyname, colony_prvkey
        )

        self.assertEqual(executorid, added_executor.executorid)
        self.colonies.del_colony(colonyname, self.server_prv)

    def test_approve_executor(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )

        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)
        executors_from_server = self.colonies.list_executors(
            colonyname, executor_prvkey
        )
        self.assertEqual(executors_from_server[0].state, 1)

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_reject_executor(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, _ = self.add_test_executor(colonyname, colony_prvkey)
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)
        self.colonies.reject_executor(colonyname, executorname, colony_prvkey)

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_list_executors(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)
        executors_from_server = self.colonies.list_executors(
            colonyname, executor_prvkey
        )
        self.assertEqual(executors_from_server[0].state, 1)

        executors_from_server = self.colonies.list_executors(
            colonyname, executor_prvkey
        )
        self.assertEqual(executors_from_server[0].name, executorname)

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_remove_executor(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, _ = self.add_test_executor(colonyname, colony_prvkey)

        self.colonies.remove_executor(colonyname, executorname, colony_prvkey)

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_submit(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)
        process = self.submit_test_funcspec(colonyname, executor_prvkey)
        self.assertEqual(process.state, 0)

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_submit_workflow(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)
        workflow = Workflow(
            colonyname=colonyname,
            functionspecs=[
                FuncSpec(
                    nodename="node1",
                    conditions=Conditions(
                        colonyname=colonyname, executortype="test-executor-type"
                    ),
                    env={"test_key": "test_value2"},
                    maxexectime=-1,
                    maxretries=3,
                ),
                FuncSpec(
                    nodename="node2",
                    conditions=Conditions(
                        colonyname=colonyname,
                        executortype="test-executor-type",
                        dependencies=["node1"],
                    ),
                    env={"test_key": "test_value2"},
                    maxexectime=-1,
                    maxretries=3,
                ),
            ],
        )
        process = self.colonies.submit_workflow(workflow, executor_prvkey)
        self.assertEqual(process.state, 0)

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_assign(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)
        process = self.submit_test_funcspec(colonyname, executor_prvkey)

        assigned_process = self.colonies.assign(colonyname, 10, executor_prvkey)
        self.assertEqual(assigned_process.processid, process.processid)

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_list_process(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)

        self.submit_test_funcspec(colonyname, executor_prvkey)
        self.submit_test_funcspec(colonyname, executor_prvkey)

        waiting_processes = self.colonies.list_processes(
            colonyname, 2, Colonies.WAITING, executor_prvkey
        )
        self.assertEqual(len(waiting_processes), 2)

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_get_process(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)

        submitted_process = self.submit_test_funcspec(colonyname, executor_prvkey)

        process = self.colonies.get_process(
            submitted_process.processid, executor_prvkey
        )
        self.assertEqual(process.processid, submitted_process.processid)

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_remove_process(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)

        submitted_process = self.submit_test_funcspec(colonyname, executor_prvkey)

        self.colonies.remove_process(submitted_process.processid, executor_prvkey)

        with self.assertRaises(Exception):
            self.colonies.get_process(submitted_process.processid, executor_prvkey)

        self.colonies.del_colony(colonyname, self.server_prv)

    #
    def test_close_process(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)

        submitted_process1 = self.submit_test_funcspec(colonyname, executor_prvkey)
        submitted_process2 = self.submit_test_funcspec(colonyname, executor_prvkey)
        self.submit_test_funcspec(colonyname, executor_prvkey)
        self.submit_test_funcspec(colonyname, executor_prvkey)

        self.colonies.assign(colonyname, 10, executor_prvkey)
        self.colonies.assign(colonyname, 10, executor_prvkey)
        self.colonies.assign(colonyname, 10, executor_prvkey)

        self.colonies.close(submitted_process1.processid, [], executor_prvkey)
        self.colonies.fail(submitted_process2.processid, [], executor_prvkey)

        waiting_processes = self.colonies.list_processes(
            colonyname, 2, Colonies.WAITING, executor_prvkey
        )
        running_processes = self.colonies.list_processes(
            colonyname, 2, Colonies.RUNNING, executor_prvkey
        )
        successful_processes = self.colonies.list_processes(
            colonyname, 2, Colonies.SUCCESSFUL, executor_prvkey
        )
        failed_processes = self.colonies.list_processes(
            colonyname, 2, Colonies.FAILED, executor_prvkey
        )

        self.assertEqual(len(waiting_processes), 1)
        self.assertEqual(len(running_processes), 1)
        self.assertEqual(len(successful_processes), 1)
        self.assertEqual(len(failed_processes), 1)

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_stats(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)

        submitted_process1 = self.submit_test_funcspec(colonyname, executor_prvkey)
        submitted_process2 = self.submit_test_funcspec(colonyname, executor_prvkey)
        self.submit_test_funcspec(colonyname, executor_prvkey)
        self.submit_test_funcspec(colonyname, executor_prvkey)

        self.colonies.assign(colonyname, 10, executor_prvkey)
        self.colonies.assign(colonyname, 10, executor_prvkey)
        self.colonies.assign(colonyname, 10, executor_prvkey)

        self.colonies.close(submitted_process1.processid, [], executor_prvkey)
        self.colonies.fail(submitted_process2.processid, [], executor_prvkey)

        waiting_processes = self.colonies.list_processes(
            colonyname, 2, 0, executor_prvkey
        )
        running_processes = self.colonies.list_processes(
            colonyname, 2, 1, executor_prvkey
        )
        successful_processes = self.colonies.list_processes(
            colonyname, 2, 2, executor_prvkey
        )
        failed_processes = self.colonies.list_processes(
            colonyname, 2, 3, executor_prvkey
        )

        stats = self.colonies.stats(colonyname, executor_prvkey)

        self.assertEqual(len(waiting_processes), stats.waitingprocesses)
        self.assertEqual(len(running_processes), stats.runningprocesses)
        self.assertEqual(len(successful_processes), stats.successfulprocesses)
        self.assertEqual(len(failed_processes), stats.failedprocesses)

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_set_output(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)

        self.submit_test_funcspec(colonyname, executor_prvkey)
        assigned_process = self.colonies.assign(colonyname, 10, executor_prvkey)
        self.colonies.set_output(
            assigned_process.processid, ["output1", "output2"], executor_prvkey
        )

        process_from_server = self.colonies.get_process(
            assigned_process.processid, executor_prvkey
        )
        self.assertIsNotNone(process_from_server.output)
        if process_from_server.output is not None:
            self.assertTrue(len(process_from_server.output) == 2)
            self.assertTrue(process_from_server.output[0] == "output1")
            self.assertTrue(process_from_server.output[1] == "output2")

    def test_add_attribute(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, executorname, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)

        submitted_process = self.submit_test_funcspec(colonyname, executor_prvkey)
        self.colonies.assign(colonyname, 10, executor_prvkey)

        self.colonies.add_attribute(
            submitted_process.processid, "py_test_key", "py_test_value", executor_prvkey
        )

        process = self.colonies.get_process(
            submitted_process.processid, executor_prvkey
        )
        self.assertIsNotNone(process.attributes)
        found = False
        if process.attributes is not None:
            for attr in process.attributes:
                if attr.key == "py_test_key" and attr.value == "py_test_value":
                    found = True
        self.assertTrue(found)

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_get_attribute(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)

        submitted_process = self.submit_test_funcspec(colonyname, executor_prvkey)
        self.colonies.assign(colonyname, 10, executor_prvkey)

        attribute = self.colonies.add_attribute(
            submitted_process.processid, "py_test_key", "py_test_value", executor_prvkey
        )
        attribute_from_server = self.colonies.get_attribute(attribute.id, executor_prvkey)
        self.assertEqual(attribute_from_server.id, attribute.id)

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_add_function(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)

        self.colonies.add_function(
            colonyname, executorname, "funcname", executor_prvkey
        )

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_get_functions_by_colony(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)

        self.colonies.add_function(
            colonyname, executorname, "funcname", executor_prvkey
        )
        functions = self.colonies.get_functions_by_colony(colonyname, executor_prvkey)
        self.assertTrue(len(functions) == 1)
        self.assertEqual(functions[0].funcname, "funcname")

    def test_get_functions_by_executor(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)

        self.colonies.add_function(
            colonyname, executorname, "funcname", executor_prvkey
        )
        functions = self.colonies.get_functions_by_executor(
            colonyname, executorname, executor_prvkey
        )
        self.assertTrue(len(functions) == 1)
        self.assertEqual(functions[0].funcname, "funcname")

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_create_snapshot(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)

        self.colonies.create_snapshot(
            colonyname, "test_label", "test_name", executor_prvkey
        )
        snapshots = self.colonies.get_snapshots(colonyname, executor_prvkey)
        self.assertTrue(len(snapshots) == 1)
        snapshot = self.colonies.get_snapshot_by_name(
            colonyname, "test_name", executor_prvkey
        )
        self.assertEqual(snapshot.name, "test_name")
        snapshot2 = self.colonies.get_snapshot_by_id(
            colonyname, snapshot.snapshotid, executor_prvkey
        )
        self.assertEqual(snapshot2.name, "test_name")

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_get_add_logs(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)

        func_spec = FuncSpec(
            conditions=Conditions(
                colonyname=colonyname, executortype="test-executor-type"
            ),
            env={"test_key": "test_value2"},
            maxexectime=-1,
            maxretries=3,
        )

        self.colonies.submit_func_spec(func_spec, executor_prvkey)
        assigned_process = self.colonies.assign(colonyname, 10, executor_prvkey)

        self.colonies.add_log(
            assigned_process.processid, "test_log_msg", executor_prvkey
        )
        logs = self.colonies.get_process_log(
            colonyname, assigned_process.processid, 100, -1, executor_prvkey
        )
        self.assertTrue(len(logs) == 1)
        self.assertEqual(logs[0].message, "test_log_msg")

        logs = self.colonies.get_executor_log(
            colonyname, executorname, 100, -1, executor_prvkey
        )
        self.assertTrue(len(logs) == 1)
        self.assertEqual(logs[0].message, "test_log_msg")

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_sync(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)

        testdir = "/tmp/testdir" + str(random.randint(0, 1000000))
        os.system("mkdir -p " + testdir)
        os.system("echo hello > " + testdir + "/hello.txt")

        self.colonies.sync(testdir, "/test", False, colonyname, executor_prvkey)

        testdir2 = "/tmp/testdir" + str(random.randint(0, 1000000))
        os.system("mkdir -p " + testdir2)
        self.colonies.sync(testdir2, "/test", False, colonyname, executor_prvkey)

        # check if the files are the same
        f = open(testdir + "/hello.txt", "r")
        hello = f.read()
        f.close()
        self.assertEqual(hello, "hello\n")

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_get_files(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)

        testdir = "/tmp/testdir" + str(random.randint(0, 1000000))
        os.system("mkdir -p " + testdir)
        os.system("echo hello > " + testdir + "/hello.txt")

        self.colonies.sync(testdir, "/test", False, colonyname, executor_prvkey)

        testdir2 = "/tmp/testdir" + str(random.randint(0, 1000000))
        os.system("mkdir -p " + testdir2)
        self.colonies.sync(testdir2, "/test", False, colonyname, executor_prvkey)

        files = self.colonies.get_files("/test", colonyname, executor_prvkey)
        assert len(files) == 1

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_upload_file(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)

        srcdir = "/tmp/srcdir" + str(random.randint(0, 1000000))
        os.system("mkdir -p " + srcdir)
        os.system("echo hello > " + srcdir + "/hello.txt")
        
        dstdir = "/tmp/dstdir" + str(random.randint(0, 1000000))
        os.system("mkdir -p " + dstdir)

        filepath = srcdir + "/hello.txt"
        self.colonies.upload_file(colonyname, executor_prvkey, filepath=filepath, label="/test")

        dst = self.colonies.download_file(colonyname, executor_prvkey, dst=dstdir, label="/test", filename="hello.txt")
        assert dst == dstdir + "/hello.txt"

        f = open(dstdir + "/hello.txt", "r")
        hello = f.read()
        f.close()
        self.assertEqual(hello, "hello\n")

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_upload_data(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)

        data = b"testdata"
        self.colonies.upload_data(colonyname, executor_prvkey, filename="data", label="/testdata", data=data)

        data = self.colonies.download_data(colonyname, executor_prvkey, label="/testdata", filename="data")
        data_str = data.decode('utf-8')
        assert data_str == "testdata"

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_get_file(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)

        data = b"testdata"
        self.colonies.upload_data(colonyname, executor_prvkey, filename="data", label="/testdata", data=data)

        file = self.colonies.get_file(colonyname, executor_prvkey, label="/testdata", filename="data") 
        assert len(file) == 1
        assert file[0].name == "data"

        self.colonies.del_colony(colonyname, self.server_prv)
    
    def test_add_cron(self) -> None:
        _, _, colonyname, colony_prvkey = self.add_test_colony()
        _, _, executorname, executor_prvkey = self.add_test_executor(
            colonyname, colony_prvkey
        )
        self.colonies.approve_executor(colonyname, executorname, colony_prvkey)
        workflow = Workflow(
            colonyname=colonyname,
            functionspecs=[
                FuncSpec(
                    nodename="node1",
                    conditions=Conditions(
                        colonyname=colonyname, executortype="test-executor-type"
                    ),
                    env={"test_key": "test_value2"},
                    maxexectime=-1,
                    maxretries=3,
                ),
                FuncSpec(
                    nodename="node2",
                    conditions=Conditions(
                        colonyname=colonyname,
                        executortype="test-executor-type",
                        dependencies=["node1"],
                    ),
                    env={"test_key": "test_value2"},
                    maxexectime=-1,
                    maxretries=3,
                ),
            ],
        )
        name = "test_cron" + self.ran_prefix()
        cron = self.colonies.add_cron(name, "0/1 * * * * *", True, workflow, colonyname, executor_prvkey)

        assert cron.name == name 

        cron2 = self.colonies.get_cron(cron.cronid, executor_prvkey)
        assert cron2.name == name 
        
        name = "test_cron" + self.ran_prefix()
        cron = self.colonies.add_cron(name, "0/1 * * * * *", False, workflow, colonyname, executor_prvkey)

        crons = self.colonies.get_crons(colonyname, 10, executor_prvkey)
        assert len(crons) == 2

        self.colonies.del_cron(cron.cronid, executor_prvkey)
        
        crons = self.colonies.get_crons(colonyname, 10, executor_prvkey)
        assert len(crons) == 1 

        self.colonies.del_colony(colonyname, self.server_prv)

    def test_download_file_raise_value_error_for_conflicting_parameters(self) -> None:
        with self.assertRaises(ValueError) as err:
            self.colonies.download_file("test", "prvkey", fileid="123", filename="filename", dst="/tmp", label="/test")
        
        self.assertEqual("Both 'fileid' and 'filename' cannot be set at the same time. Please provide only one.", str(err.exception))

    def test_download_data_raise_value_error_for_conflicting_parameters(self) -> None:
        with self.assertRaises(ValueError) as err:
            self.colonies.download_data("test", "prvkey", fileid="123", filename="filename", label="/test")
        
        self.assertEqual("Both 'fileid' and 'filename' cannot be set at the same time. Please provide only one.", str(err.exception))

if __name__ == "__main__":
    unittest.main()
