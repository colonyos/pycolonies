import hashlib
from eth_keys.utils.numeric import int_to_byte
import hashlib
import hmac
from typing import (
    Any,
    Callable,
    Tuple,
)

from eth_utils.encoding import (
    big_endian_to_int,
    int_to_big_endian,
)

from eth_keys.constants import (
    SECPK1_A as A,
    SECPK1_B as B,
    SECPK1_G as G,
    SECPK1_N as N,
    SECPK1_P as P,
    SECPK1_Gx as Gx,
    SECPK1_Gy as Gy,
)

from eth_keys.exceptions import (
    BadSignature,
)

from eth_keys.utils.padding import (
    pad32,
)

from jacobian import (
    fast_add,
    fast_multiply,
    from_jacobian,
    inv,
    is_identity,
    jacobian_add,
    jacobian_multiply,
)

from typing import (
    Tuple,
)

from eth_keys.constants import (
    IDENTITY_POINTS,
    SECPK1_A as A,
    SECPK1_N as N,
    SECPK1_P as P,
)

from eth_account import Account

def genkey():
    new_account = Account.create()
    return new_account.key.hex()[2:]

def pad32(value: bytes) -> bytes:
    return value.rjust(32, b"\x00")

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

def decode_public_key(public_key_bytes: bytes) -> Tuple[int, int]:
    left = big_endian_to_int(public_key_bytes[0:32])
    right = big_endian_to_int(public_key_bytes[32:64])
    return left, right

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

def compress_public_key(uncompressed_public_key_bytes: bytes) -> bytes:
    x, y = decode_public_key(uncompressed_public_key_bytes)
    if y % 2 == 0:
        prefix = b"\x02"
    else:
        prefix = b"\x03"
    return prefix + pad32(int_to_big_endian(x))

def decompress_public_key(compressed_public_key_bytes: bytes) -> bytes:
    if len(compressed_public_key_bytes) != 33:
        raise ValueError("Invalid compressed public key")

    prefix = compressed_public_key_bytes[0]
    if prefix not in (2, 3):
        raise ValueError("Invalid compressed public key")

    x = big_endian_to_int(compressed_public_key_bytes[1:])
    y_squared = (x**3 + A * x + B) % P
    y_abs = pow(y_squared, ((P + 1) // 4), P)

    if (prefix == 2 and y_abs & 1 == 1) or (prefix == 3 and y_abs & 1 == 0):
        y = (-y_abs) % P
    else:
        y = y_abs

    return encode_raw_public_key((x, y))

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

def ecdsa_raw_verify(
    msg_hash: bytes, rs: Tuple[int, int], public_key_bytes: bytes
) -> bool:
    raw_public_key = decode_public_key(public_key_bytes)

    r, s = rs

    w = inv(s, N)
    z = big_endian_to_int(msg_hash)

    u1, u2 = z * w % N, r * w % N
    x, y = fast_add(
        fast_multiply(G, u1),
        fast_multiply(raw_public_key, u2),
    )
    return bool(r == x and (r % N) and (s % N))

def ecdsa_raw_recover(msg_hash: bytes, vrs: Tuple[int, int, int]) -> bytes:
    v, r, s = vrs
    v += 27

    if not (27 <= v <= 34):
        raise BadSignature(f"{v} must in range 27-31")

    x = r

    xcubedaxb = (x * x * x + A * x + B) % P
    beta = pow(xcubedaxb, (P + 1) // 4, P)
    y = beta if v % 2 ^ beta % 2 else (P - beta)
    # If xcubedaxb is not a quadratic residue, then r cannot be the x coord
    # for a point on the curve, and so the sig is invalid
    if (xcubedaxb - y * y) % P != 0 or not (r % N) or not (s % N):
        raise BadSignature("Invalid signature")
    z = big_endian_to_int(msg_hash)
    Gz = jacobian_multiply((Gx, Gy, 1), (N - z) % N)
    XY = jacobian_multiply((x, y, 1), s)
    Qr = jacobian_add(Gz, XY)
    Q = jacobian_multiply(Qr, inv(r, N))

    if is_identity(Q):
        raise BadSignature("InvalidSignature")

    raw_public_key = from_jacobian(Q)

    return encode_raw_public_key(raw_public_key)

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

def to_jacobian(p: Tuple[int, int]) -> Tuple[int, int, int]:
    o = (p[0], p[1], 1)
    return o

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

def from_jacobian(p: Tuple[int, int, int]) -> Tuple[int, int]:
    z = inv(p[2], P)
    return ((p[0] * z**2) % P, (p[1] * z**3) % P)

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

def fast_multiply(a: Tuple[int, int], n: int) -> Tuple[int, int]:
    return from_jacobian(jacobian_multiply(to_jacobian(a), n))

def fast_add(a: Tuple[int, int], b: Tuple[int, int]) -> Tuple[int, int]:
    return from_jacobian(jacobian_add(to_jacobian(a), to_jacobian(b)))

def is_identity(p: Tuple[int, int, int]) -> bool:
    return p in IDENTITY_POINTS
