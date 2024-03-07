import unittest
import sys
import os
sys.path.append(".")
from cfs import CFS
import random

class TestCFS(unittest.TestCase):
    def test_sycn(self):
        colonies_server = os.getenv("COLONIES_SERVER_HOST")
        colonies_port_str = os.getenv("COLONIES_SERVER_PORT")
        colonies_tls_str = os.getenv("COLONIES_SERVER_TLS")
        colonyname = os.getenv("COLONIES_COLONY_NAME")
        prvkey = os.getenv("COLONIES_PRVKEY")
        colonies_port = int(colonies_port_str)
        colonies_tls = colonies_tls_str == "true"

        # create a tmp dir in /tmp with a file containing a string hello
        # make the testdir a random name
        testdir = "/tmp/testdir" + str(random.randint(0, 1000000))
        os.system("mkdir -p " + testdir)
        os.system("echo hello > " + testdir + "/hello.txt")

        cfs = CFS()
        cfs.sync(colonies_server, colonies_port, colonies_tls, False, testdir, "/test", False, colonyname, prvkey)

        testdir2 = "/tmp/testdir" + str(random.randint(0, 1000000))
        os.system("mkdir -p " + testdir2)
        cfs.sync(colonies_server, colonies_port, colonies_tls, False, testdir2, "/test", False, colonyname, prvkey)

        # check if the files are the same
        # open hello.txt 
        f = open(testdir + "/hello.txt", "r")
        hello = f.read()
        f.close()
        self.assertEqual(hello, "hello\n")

        # clean up
        #os.rmdir(testdir)
        #os.rmdir(testdir2)

if __name__ == '__main__':
    unittest.main()
