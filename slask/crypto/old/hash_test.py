import unittest
from hash import generate_hash, generate_hash_from_string, create_hash_from_string

class TestCrypto(unittest.TestCase):

    def test_generate_hash(self):
        hash = generate_hash(b"hello world")
        self.assertEqual(str(hash), "644bcc7e564373040999aac89e7622f3ca71fba1d972fd94a31c3bfbf24e3938")

        hash = generate_hash_from_string("hello world")
        self.assertEqual(str(hash), "644bcc7e564373040999aac89e7622f3ca71fba1d972fd94a31c3bfbf24e3938")

        byte_array = bytes([100, 75, 204, 126, 86, 67, 115, 4, 9, 153, 170, 200, 158, 118, 34, 243, 202, 113, 251, 161, 217, 114, 253, 148, 163, 28, 59, 251, 242, 78, 57, 56])
        self.assertEqual(hash.bytes, byte_array)

    def test_create_hash_from_string(self):
        hash, err = create_hash_from_string("644bcc7e564373040999aac89e7622f3ca71fba1d972fd94a31c3bfbf24e3938")
        self.assertIsNone(err)
        self.assertEqual(str(hash), "644bcc7e564373040999aac89e7622f3ca71fba1d972fd94a31c3bfbf24e3938")

        byte_array = bytes([100, 75, 204, 126, 86, 67, 115, 4, 9, 153, 170, 200, 158, 118, 34, 243, 202, 113, 251, 161, 217, 114, 253, 148, 163, 28, 59, 251, 242, 78, 57, 56])
        self.assertEqual(hash.bytes, byte_array)

if __name__ == "__main__":
    unittest.main()
