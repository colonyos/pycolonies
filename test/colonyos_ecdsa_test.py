import unittest
from colonyos_ecdsa import sign, get_id
import binascii

class TestInterop(unittest.TestCase):

    def test_interop(self):
        prv_key = "d6eb959e9aec2e6fdc44b5862b269e987b8a4d6f2baca542d8acaa97ee5e74f6"
        #prv_key = "fcc79953d8a751bf41db661592dc34d30004b1a651ffa0725b03ac227641499d"

        id = get_id(prv_key)
        print("ID:", id)

if __name__ == "__main__":
    unittest.main()
