import ctypes
import pathlib
import os

class CFS:
    def __init__(self):
        libname = os.environ.get("CFSLIB")
        if libname == None:
            libname = "/usr/local/lib/libcfslib.so"
        self.c_lib = ctypes.CDLL(libname)
        # self.c_lib.prvkey.restype = ctypes.c_char_p
        # self.c_lib.id.restype = ctypes.c_char_p
        # self.c_lib.sign.restype = ctypes.c_char_p
        # self.c_lib.hash.restype = ctypes.c_char_p
        self.c_lib.sync.restype = ctypes.c_int
    
    def sync(self, host, port, insecure, skip_tls_verify, dir, label, keeplocal, colonyname, prvkey):
        c_host = ctypes.c_char_p(host.encode('utf-8'))
        c_port = ctypes.c_int(port)
        c_insecure = ctypes.c_int(insecure==False)
        c_skip_tls_verify = ctypes.c_int(skip_tls_verify)
        c_dir = ctypes.c_char_p(dir.encode('utf-8'))
        c_label = ctypes.c_char_p(label.encode('utf-8'))
        c_keeplocal = ctypes.c_int(keeplocal)
        c_colonyname = ctypes.c_char_p(colonyname.encode('utf-8'))
        c_prvkey = ctypes.c_char_p(prvkey.encode('utf-8'))

        res = self.c_lib.sync(c_host, c_port, c_insecure, c_skip_tls_verify, c_dir, c_label, c_keeplocal, c_colonyname, c_prvkey)
        if res != 0:
            raise Exception("failed to sync")
