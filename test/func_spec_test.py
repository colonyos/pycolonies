import unittest

from pycolonies import FuncSpec


class TestFuncSpec(unittest.TestCase):
    def test_func_spec_sets_simple_properties(self) -> None:

        kwargs = {
            "one": "1",
            "two": "2",
            "three": ["3", "4"]
        }

        spec = FuncSpec.create(
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

        self.assertEqual(spec.nodename, "sum_nums")
        self.assertEqual(spec.funcname, "sum_nums")
        self.assertEqual(spec.args, ["helloworld"])

        assert spec.conditions is not None
        self.assertEqual(spec.conditions.colonyname, "colonyname")
        self.assertEqual(spec.conditions.executortype, "echo_executor")
        if spec.conditions.executornames is not None:
            self.assertEqual(spec.conditions.executornames[0], "exec_name")

        self.assertEqual(spec.priority, 0)
        self.assertEqual(spec.maxexectime, 10)
        self.assertEqual(spec.maxretries, 3)
        self.assertEqual(spec.maxwaittime, 100)

        self.assertEqual(spec.kwargs, kwargs)
