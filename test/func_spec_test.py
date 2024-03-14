import unittest

from pycolonies import func_spec


class TestFuncSpec(unittest.TestCase):
    def test_func_spec_sets_simple_properties(self):

        kwargs = {
            "one": "1",
            "two": "2"
        }

        fs = func_spec(
            func="sum_nums",
            args=["helloworld"],
            colonyname="colonyname",
            executortype="echo_executor",
            executorname="exec_name",
            priority=0,
            maxexectime=10,
            maxretries=3,
            maxwaittime=100,
            kwargs=kwargs
        )

        self.assertEqual(fs["nodename"], "sum_nums")
        self.assertEqual(fs["funcname"], "sum_nums")
        self.assertEqual(fs["args"], ["helloworld"])

        self.assertEqual(fs["conditions"]["colonyname"], "colonyname")
        self.assertEqual(fs["conditions"]["executortype"], "echo_executor")
        self.assertEqual(fs["conditions"]["executorname"], "exec_name")

        self.assertEqual(fs["priority"], 0)
        self.assertEqual(fs["maxexectime"], 10)
        self.assertEqual(fs["maxretries"], 3)
        self.assertEqual(fs["maxwaittime"], 100)

        self.assertEqual(fs["kwargs"], kwargs)
