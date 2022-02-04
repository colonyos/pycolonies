import unittest
import sys
sys.path.append(".")
from crypto import Crypto
from colonies import Colonies

class TestColonies(unittest.TestCase):

    def test_add_colony(self):
        url = "https://10.0.0.240:8080/api"
        client = Colonies(url)

        crypto = Crypto()
        prvkey = crypto.prvkey()
        colonyid = crypto.id(prvkey)

        colony = {
            "colonyid" : colonyid,
            "name" : "python_test"
        }

        server_prv = "09545df1812e252a2a853cca29d7eace4a3fe2baad334e3b7141a98d43c31e7b"
        added_colony = client.add_colony(colony, server_prv)
        self.assertEqual(added_colony["colonyid"], colonyid)

        client.del_colony(colonyid, server_prv)

        server_prv = "09545df1812e252a2a853cca29d7eace4a3fe2baad334e3b7141a98d43c31e7c"  # note last c, incorrect key
        with self.assertRaises(Exception): 
            client.add_colony(colony, server_prv)
    
    def test_del_colony(self):
        url = "https://10.0.0.240:8080/api"
        client = Colonies(url)
        server_prv = "09545df1812e252a2a853cca29d7eace4a3fe2baad334e3b7141a98d43c31e7b"
        colonyid = "09545df1812e252a2a853cca29d7eace4a3fe2baad334e3b7141a98d43c31e7b"
        client.del_colony(colonyid, server_prv)


if __name__ == '__main__':
    unittest.main()
