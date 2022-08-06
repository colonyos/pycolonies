import ctypes
import pathlib
import os

class Crypto:
    def __init__(self):
        libname = os.environ.get("CRYPTOLIB")
        if libname == None:
            libname = "/usr/local/lib/libcryptolib.so"
        self.c_lib = ctypes.CDLL(libname)
        self.c_lib.prvkey.restype = ctypes.c_char_p
        self.c_lib.id.restype = ctypes.c_char_p
        self.c_lib.sign.restype = ctypes.c_char_p
        self.c_lib.hash.restype = ctypes.c_char_p
        self.c_lib.recoverid.restype = ctypes.c_char_p
    
    def prvkey(self):
        k = self.c_lib.prvkey()
        return k.decode("utf-8")
    
    def id(self, id):
        h = self.c_lib.id(id.encode('utf-8'))
        return h.decode("utf-8")

    def hash(self, data):
        h = self.c_lib.hash(data.encode('utf-8'))
        return h.decode("utf-8")
    
    def sign(self, data, prvkey):
        s = self.c_lib.sign(data.encode('utf-8'), prvkey.encode('utf-8'))
        return s.decode("utf-8")
    
    def recoverid(self, data, prvkey):
        id = self.c_lib.recoverid(data.encode('utf-8'), prvkey.encode('utf-8'))
        return id.decode("utf-8")
