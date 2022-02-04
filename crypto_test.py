import unittest
import sys
sys.path.append(".")
from crypto import Crypto

class TestCrypto(unittest.TestCase):
    
    def test_prvkey(self):
        crypto = Crypto()
        prvkey = crypto.prvkey()
        self.assertEqual(len(prvkey), 64)
    
    def test_id(self):
        crypto = Crypto()
        i = crypto.id("6d2fb6f546bacfd98c68769e61e0b44a697a30596c018a50e28200aa59b01c0a")
        self.assertEqual(i, "4fef2b5a82d134d058c1883c72d6d9caf77cd59ca82d73105017590dea3dcb87")
    
    def test_sign(self):
        crypto = Crypto()
        prvkey = "d6eb959e9aec2e6fdc44b5862b269e987b8a4d6f2baca542d8acaa97ee5e74f6"
        data = "hello"
        digest = crypto.hash(data)
        sig = crypto.sign(digest, prvkey)
        self.assertEqual(len(sig), 130)
    
    def test_recoverid(self):
        crypto = Crypto()
        prvkey = "d6eb959e9aec2e6fdc44b5862b269e987b8a4d6f2baca542d8acaa97ee5e74f6"
        data = "hello"
        digest = crypto.hash(data)
        sig = crypto.sign(digest, prvkey)
        id = crypto.recoverid(digest, sig)
        self.assertEqual(id, "5d6568f883451ae2e407d1a0a7992e414f2a67b69d0e6e9176d353b98f06f696")
    
    def test_hash(self):
        crypto = Crypto()
        self.assertEqual(crypto.hash("hello world"), "644bcc7e564373040999aac89e7622f3ca71fba1d972fd94a31c3bfbf24e3938")
    

if __name__ == '__main__':
    unittest.main()
