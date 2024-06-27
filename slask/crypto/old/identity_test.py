import unittest

from identity import Identity

class TestCrypto(unittest.TestCase):

    def test_create_identity(self):
        identity, err = Identity.from_hex("6d2fb6f546bacfd98c68769e61e0b44a697a30596c018a50e28200aa59b01c0a")
        self.assertIsNone(err)
        self.assertIsNotNone(identity)

        # self.assertEqual(identity.get_id(), "4fef2b5a82d134d058c1883c72d6d9caf77cd59ca82d73105017590dea3dcb87")
        self.assertEqual(identity.private_key_as_hex(), "6d2fb6f546bacfd98c68769e61e0b44a697a30596c018a50e28200aa59b01c0a")
        self.assertEqual(identity.public_key_as_hex(), "0408e903276ee7973666dceeefa5335e5c4b6b5989821906db98f8de8acf8f853824ca3234a8602200baa2d75f30cb2050cda18602824c3eb2da654a93a01a7ad4")


        # identity, err = Identity.from_hex("6d2fb6f546bacfd98c68769e61e0b44a697a30596c018a50e28200aa59b01c0a")
        # self.assertIsNone(err)
        #
        # #self.assertEqual(identity.id, "4fef2b5a82d134d058c1883c72d6d9caf77cd59ca82d73105017590dea3dcb87")
        # self.assertEqual(identity.private_key_as_hex(), "6d2fb6f546bacfd98c68769e61e0b44a697a30596c018a50e28200aa59b01c0a")
        # self.assertEqual(identity.public_key_as_hex(), "0408e903276ee7973666dceeefa5335e5c4b6b5989821906db98f8de8acf8f853824ca3234a8602200baa2d75f30cb2050cda18602824c3eb2da654a93a01a7ad4")

if __name__ == "__main__":
    unittest.main()

