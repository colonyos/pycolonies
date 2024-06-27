import hashlib
from ecdsa import ecdsa_raw_sign

from eth_utils.encoding import int_to_big_endian
from eth_keys.utils.numeric import (
    int_to_byte,
)

message = "hello"
prv_hex = "d6eb959e9aec2e6fdc44b5862b269e987b8a4d6f2baca542d8acaa97ee5e74f6"
prv_bytes = bytes.fromhex(prv_hex)
hash = hashlib.sha3_256()
hash.update(message.encode('utf-8'))
hash_bytes = hash.digest()


s = ecdsa_raw_sign(hash_bytes, prv_bytes)
print(s[0].to_bytes(32, 'big').hex())
print(s[1].to_bytes(32, 'big').hex())
print(s[2].to_bytes(32, 'big').hex())

def pad32(value: bytes) -> bytes:
    return value.rjust(32, b"\x00")

vb = int_to_byte(s[0])
rb = pad32(int_to_big_endian(s[1]))
sb = pad32(int_to_big_endian(s[2]))
sig = b"".join((rb, sb, vb))
print(sig.hex())



