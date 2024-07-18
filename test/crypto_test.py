import unittest
import sys
sys.path.append(".")
from crypto import Crypto
from crypto import jacobian_add, jacobian_double, fast_multiply

class TestCrypto(unittest.TestCase):
    def test_prvkey(self):
        crypto = Crypto()
        prvkey = crypto.prvkey()
        self.assertEqual(len(prvkey), 64)
     
    def test_id(self):
        crypto = Crypto()
        i = crypto.id("6d2fb6f546bacfd98c68769e61e0b44a697a30596c018a50e28200aa59b01c0a")
        self.assertEqual(i, "4fef2b5a82d134d058c1883c72d6d9caf77cd59ca82d73105017590dea3dcb87")
   
    def test_jacobian_add(self):
        p1 = 9145974245324100229099870468775465651310464820817378424695723232290407343942
        p2 = 5726454693002325744504615879224937090641195997533856518133185097441749801032
        p3 = 115714549703150523321131187169862203539915631312738481595605540015431713717331
        p = (p1, p2, p3)

        q1 = 3378859141843082240981311929530924778908494294056496383285600481501351521548 
        q2 = 27521306930728475164406447156615413460758360212583572363332152141481614403438 
        q3 = 49323301439068515073562494645799725679211443313890051705798536862743810731758
        q = (q1, q2, q3)
        
        r = jacobian_add(p, q)
        
        self.assertEqual(r, (3839523019051154503084769099381507415584753837414379863264960425500703565923, 20189644703747003499840421980750524561734367487063517298774288662171391490014, 60937054099961058364101483468792603644143119999146283853926532658309628838553))

    def test_jacobian_double(self):
        p1 = 9145974245324100229099870468775465651310464820817378424695723232290407343942
        p2 = 5726454693002325744504615879224937090641195997533856518133185097441749801032
        p3 = 115714549703150523321131187169862203539915631312738481595605540015431713717331
        p = (p1, p2, p3)

        r = jacobian_double(p)
        self.assertEqual(r, (47799865997534219673197337605336645889814818209350362461488238402445197905424, 60263407694755846743636806277114588321762727181244820843669538143699156517749, 98392693047863901823354926635876248059211737341107593029860323683906341241571))

    def test_fast_multiply(self):
        p1 = 9145974245324100229099870468775465651310464820817378424695723232290407343942
        p2 = 5726454693002325744504615879224937090641195997533856518133185097441749801032
        p = (p1, p2)
        n =  49323301439068515073562494645799725679211443313890051705798536862743810731758
        r = fast_multiply(p, n)
        self.assertEqual(r, (55168891259068323847970500732782990269643885682720201005538882429359294222592, 24653118739118393505255051840680624663656725984701285210882487021736401159116))

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
