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
        signature_hex = "e713a1bb015fecabb5a084b0fe6d6e7271fca6f79525a634183cfdb175fe69241f4da161779d8e6b761200e1cf93766010a19072fa778f9643363e2cfadd640900"
        data = "hello"
        sig = crypto.sign(data, prvkey)
        self.assertEqual(len(sig), 130)
        self.assertEqual(sig, signature_hex)
    
if __name__ == '__main__':
    unittest.main()
