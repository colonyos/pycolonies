import unittest
from signature import sign_compact
from hash import generate_hash_from_string
from identity import Identity
import binascii

class TestInterop(unittest.TestCase):

    def test_interop(self):
        # prv_key = "d6eb959e9aec2e6fdc44b5862b269e987b8a4d6f2baca542d8acaa97ee5e74f6"
        prv_key = "fcc79953d8a751bf41db661592dc34d30004b1a651ffa0725b03ac227641499d"
        identity, err = Identity.from_hex(prv_key)
        
        print("ID:", identity.get_id())
        self.assertIsNone(err)
        self.assertIsNotNone(identity)

        hash_obj = generate_hash_from_string("eyJtc2d0eXBlIjogImFkZGNvbG9ueW1zZyIsICJjb2xvbnkiOiB7ImNvbG9ueWlkIjogIjA4MjA2NTY1OWU4M2Q0ODE0M2FiNzQ4ZjUyYjk2M2ZkNWU0NDQ5NTA0YWYzMjgzYjE2ZGZmZGI3NjY2M2NlM2EiLCAibmFtZSI6ICJweXRob24tdGVzdC1EN1lPQzFHNzRCIn19")

        # Sign the hash
        signature = sign_compact(hash_obj, identity.private_key())
        print("ID:", identity.get_id())
        print("Digest:", hash_obj)
        print("Signature:", signature)
        #
        # # Recover the ID from the signature
        recovered_id_value = recover_id(hash_obj, signature)
        print("Recovered ID:", recovered_id_value)
        #self.assertIsNone(err)
        # self.assertEqual(recovered_id_value, identity.get_id())

if __name__ == "__main__":
    unittest.main()
#
#
# import unittest
# import binascii
# from identity import Identity, generate_hash_from_string
# from signature import recovered_id
#
# class TestInterop(unittest.TestCase):
#
#     def test_interop(self):
#         prv_key = "d6eb959e9aec2e6fdc44b5862b269e987b8a4d6f2baca542d8acaa97ee5e74f6"
#         identity, err = Identity.from_hex(prv_key)
#         self.assertIsNone(err)
#         self.assertIsNotNone(identity)
#
#         hash_value = generate_hash_from_string("hello")
#
#         signature, err = Sign(hash_value, identity.private_key())
#         self.assertIsNone(err)
#         signature_str = binascii.hexlify(signature).decode()
#         print("prvkey: " + identity.private_key_as_hex())
#         print("pubkey: " + identity.public_key_as_hex())
#         print("id: " + identity.get_id())
#         print("digest: " + hash_value)
#         print("signature: " + signature_str)
#
#         signature_hex = "997eca36736d465e0e8d64e6d657ff4c939c8f5cad4272797ea0fe372bfd8d0953d21b3d06ded5dd80aee8cfa3a9be7ce615ce690eb64184fe15962943fe541300"
#         signature_bytes = binascii.unhexlify(signature_hex)
#         recovered_id_value, err = recovered_id(hash_value, signature_bytes)
#         self.assertIsNone(err)
#         self.assertEqual(recovered_id_value, identity.get_id())
#
# if __name__ == "__main__":
#     unittest.main()
#
