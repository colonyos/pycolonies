# This code is based on the code from the following repository (MIT-licensed):
# https://github.com/ethereum/eth-utils
# https://github.com/ethereum/eth-keys 

import ctypes
import os
import hashlib
import hmac
import os
from typing import (
    Any,
    Callable,
    Tuple,
)

# SECPK1N
A: int = 0
N: int = (115792089237316195423570985008687907852837564279074904382605163141518161494337)
Gx: int = (55066263022277343669578718895168534326250603453777594175500187360389116729240)
Gy: int = (32670510020758816978083085130507043184471273380659243275938904335757337482424)
G: Tuple[int, int] = (Gx, Gy)
P: int = 2**256 - 2**32 - 977

class Crypto:
      def __init__(self, native=False):
          self.native = native
          if native:
            libname = os.environ.get("CRYPTOLIB")
            if libname == None:
                libname = "/usr/local/lib/libcryptolib.so"
            self.c_lib = ctypes.CDLL(libname)
            self.c_lib.prvkey.restype = ctypes.c_char_p
            self.c_lib.id.restype = ctypes.c_char_p
            self.c_lib.sign.restype = ctypes.c_char_p
            self.c_lib.hash.restype = ctypes.c_char_p
            self.c_lib.recoverid.restype = ctypes.c_char_p

      def prvkey(self):
          if self.native:
            k = self.c_lib.prvkey()
            return k.decode("utf-8")
          else:
            return genkey()

      def id(self, id):
          if self.native:
              h = self.c_lib.id(id.encode('utf-8'))
              return h.decode("utf-8")
          else:
              return get_id(id)

      def sign(self, data, prvkey):
          if self.native:
              s = self.c_lib.sign(data.encode('utf-8'), prvkey.encode('utf-8'))
              return s.decode("utf-8")
          else:
              return sign(data, prvkey)

def genkey():
    random_bytes = os.urandom(32)  # Generate 32 random bytes
    hash_obj = hashlib.sha3_256()  # Create a SHA-3 256 hash object
    hash_obj.update(random_bytes)  # Update the hash object with the random bytes
    hash_bytes = hash_obj.digest()  # Get the digest of the hash
    return hash_bytes.hex()  # Return the hexadecimal representation

def sign(msg, prv_hex):
    prv_bytes = bytes.fromhex(prv_hex)
    
    hash = hashlib.sha3_256()
    hash.update(msg.encode('utf-8'))
    hash_bytes = hash.digest()

    s = ecdsa_raw_sign(hash_bytes, prv_bytes)
    vb = int_to_byte(s[0])
    rb = pad32(int_to_big_endian(s[1]))
    sb = pad32(int_to_big_endian(s[2]))
    sig = b"".join((rb, sb, vb))

    sig_hex = sig.hex()
    return sig_hex

def get_id(prv_key):
    prv_key_bytes = bytes.fromhex(prv_key)
    pub = private_key_to_public_key(prv_key_bytes)
    pub_hex = "04"+pub.hex()  # the prefix "04" denotes that the public key is in uncompressed format
    hash = hashlib.sha3_256()
    hash.update(pub_hex.encode('utf-8'))
    
    return hash.hexdigest()

def pad32(value: bytes) -> bytes:
    return value.rjust(32, b"\x00")

def int_to_byte(value: int) -> bytes:
    return bytes([value])

def int_to_big_endian(value: int) -> bytes:
    return value.to_bytes((value.bit_length() + 7) // 8 or 1, "big")


def big_endian_to_int(value: bytes) -> int:
    return int.from_bytes(value, "big")

def encode_raw_public_key(raw_public_key: Tuple[int, int]) -> bytes:
    left, right = raw_public_key
    return b"".join(
        (
            pad32(int_to_big_endian(left)),
            pad32(int_to_big_endian(right)),
        )
    )

def private_key_to_public_key(private_key_bytes: bytes) -> bytes:
    private_key_as_num = big_endian_to_int(private_key_bytes)

    if private_key_as_num >= N:
        raise Exception("Invalid privkey")

    raw_public_key = fast_multiply(G, private_key_as_num)
    public_key_bytes = encode_raw_public_key(raw_public_key)
    return public_key_bytes

def deterministic_generate_k(
    msg_hash: bytes,
    private_key_bytes: bytes,
    digest_fn: Callable[[], Any] = hashlib.sha256,
) -> int:
    v_0 = b"\x01" * 32
    k_0 = b"\x00" * 32

    k_1 = hmac.new(
        k_0, v_0 + b"\x00" + private_key_bytes + msg_hash, digest_fn
    ).digest()
    v_1 = hmac.new(k_1, v_0, digest_fn).digest()
    k_2 = hmac.new(
        k_1, v_1 + b"\x01" + private_key_bytes + msg_hash, digest_fn
    ).digest()
    v_2 = hmac.new(k_2, v_1, digest_fn).digest()

    kb = hmac.new(k_2, v_2, digest_fn).digest()
    k = big_endian_to_int(kb)
    return k

def ecdsa_raw_sign(msg_hash: bytes, private_key_bytes: bytes) -> Tuple[int, int, int]:
    z = big_endian_to_int(msg_hash)
    k = deterministic_generate_k(msg_hash, private_key_bytes)

    r, y = fast_multiply(G, k)
    s_raw = inv(k, N) * (z + r * big_endian_to_int(private_key_bytes)) % N

    v = 27 + ((y % 2) ^ (0 if s_raw * 2 < N else 1))
    s = s_raw if s_raw * 2 < N else N - s_raw

    return v - 27, r, s

def fast_multiply(a: Tuple[int, int], n: int) -> Tuple[int, int]:
    return from_jacobian(jacobian_multiply(to_jacobian(a), n))

def from_jacobian(p: Tuple[int, int, int]) -> Tuple[int, int]:
    z = inv(p[2], P)
    return ((p[0] * z**2) % P, (p[1] * z**3) % P)

def to_jacobian(p: Tuple[int, int]) -> Tuple[int, int, int]:
    o = (p[0], p[1], 1)
    return o

def inv(a: int, n: int) -> int:
    if a == 0:
        return 0
    lm, hm = 1, 0
    low, high = a % n, n
    while low > 1:
        r = high // low
        nm, new = hm - lm * r, high - low * r
        lm, low, hm, high = nm, new, lm, low
    return lm % n

def jacobian_double(p: Tuple[int, int, int]) -> Tuple[int, int, int]:
    if not p[1]:
        return (0, 0, 0)
    ysq = (p[1] ** 2) % P
    S = (4 * p[0] * ysq) % P
    M = (3 * p[0] ** 2 + A * p[2] ** 4) % P
    nx = (M**2 - 2 * S) % P
    ny = (M * (S - nx) - 8 * ysq**2) % P
    nz = (2 * p[1] * p[2]) % P
    return (nx, ny, nz)

def jacobian_add(
    p: Tuple[int, int, int], q: Tuple[int, int, int]
) -> Tuple[int, int, int]:
    if not p[1]:
        return q
    if not q[1]:
        return p
    U1 = (p[0] * q[2] ** 2) % P
    U2 = (q[0] * p[2] ** 2) % P
    S1 = (p[1] * q[2] ** 3) % P
    S2 = (q[1] * p[2] ** 3) % P
    if U1 == U2:
        if S1 != S2:
            return (0, 0, 1)
        return jacobian_double(p)
    H = U2 - U1
    R = S2 - S1
    H2 = (H * H) % P
    H3 = (H * H2) % P
    U1H2 = (U1 * H2) % P
    nx = (R**2 - H3 - 2 * U1H2) % P
    ny = (R * (U1H2 - nx) - S1 * H3) % P
    nz = (H * p[2] * q[2]) % P
    return (nx, ny, nz)

def jacobian_multiply(a: Tuple[int, int, int], n: int) -> Tuple[int, int, int]:
    if a[1] == 0 or n == 0:
        return (0, 0, 1)
    if n == 1:
        return a
    if n < 0 or n >= N:
        return jacobian_multiply(a, n % N)
    if (n % 2) == 0:
        return jacobian_double(jacobian_multiply(a, n // 2))
    elif (n % 2) == 1:
        return jacobian_add(jacobian_double(jacobian_multiply(a, n // 2)), a)
    else:
        raise Exception("Invariant: Unreachable code path")
