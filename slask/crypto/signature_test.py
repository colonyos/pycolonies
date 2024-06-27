import unittest
from signature import sign
from hash import generate_hash_from_string
from identity import Identity
import binascii

class TestInterop(unittest.TestCase):

    def test_interop(self):
        # prv_key = "d6eb959e9aec2e6fdc44b5862b269e987b8a4d6f2baca542d8acaa97ee5e74f6"
        prv_key = "fcc79953d8a751bf41db661592dc34d30004b1a651ffa0725b03ac227641499d"

        payload = "eyJtc2d0eXBlIjogImFkZGNvbG9ueW1zZyIsICJjb2xvbnkiOiB7ImNvbG9ueWlkIjogIjA4MjA2NTY1OWU4M2Q0ODE0M2FiNzQ4ZjUyYjk2M2ZkNWU0NDQ5NTA0YWYzMjgzYjE2ZGZmZGI3NjY2M2NlM2EiLCAibmFtZSI6ICJweXRob24tdGVzdC1EN1lPQzFHNzRCIn19"

        # Sign the hash
        signature = sign(payload, prv_key)
        print("Signature:", signature)
        #

if __name__ == "__main__":
    unittest.main()
