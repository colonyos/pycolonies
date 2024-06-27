import hashlib
from ecdsa import SigningKey, SECP256k1, VerifyingKey, BadSignatureError, util
from ecdsa.util import sigdecode_string, sigencode_string
import binascii
from hash import Hash, generate_hash_from_string  # Import from hash.py
from identity import Identity

SignatureLength = 128 
RecoveryIDOffset = 64

class FieldVal:
    def __init__(self, value):
        self.value = value

    def to_bytes(self, length, byteorder):
        return self.value.to_bytes(length, byteorder)

class ModNScalar:
    def __init__(self):
        self.value = 0

    def set_bytes(self, buf):
        self.value = int.from_bytes(buf, byteorder='big')
        overflow = 1 if self.value >= SECP256k1.order else 0
        self.value %= SECP256k1.order
        return overflow

    def is_zero(self):
        return self.value == 0

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def y_is_odd(self):
        return self.y % 2 != 0

def field_to_mod_n_scalar(v):
    # Convert the field value to a mutable byte array
    buf = bytearray(v.to_bytes(32, byteorder='big'))

    # Create a scalar from the byte array
    s = ModNScalar()
    overflow = s.set_bytes(buf)

    # Zero the byte array for security
    for i in range(len(buf)):
        buf[i] = 0

    return s, overflow

def get_pub_key_recovery_code(overflow, kG_y):
    # Extract the integer value from the PointJacobi object
    kG_y_bytes = kG_y.to_bytes()  # Convert to bytes
    kG_y_int = int.from_bytes(kG_y_bytes, byteorder='big')  # Convert bytes to int
    pub_key_recovery_code = (overflow << 1) | (kG_y_int & 1)
    return pub_key_recovery_code


def sign_compact(hash, prv, is_compressed=False):
    print("hash:", hash.bytes.hex())
    hash_bytes = hash.bytes
    if len(hash_bytes) != 32:
        raise ValueError(f"Hash is required to be exactly 32 bytes ({len(hash_bytes)})")
    if prv.curve != SECP256k1:
        raise ValueError("Private key curve is not secp256k1")

    sig = prv.sign_digest_deterministic(hash_bytes, hashfunc=hashlib.sha256, sigencode=util.sigencode_string)
    r, s = util.sigdecode_string(sig, prv.curve.order)

    order_half = prv.curve.order // 2
    if s > order_half:
        s = prv.curve.order - s

    # hex and encode r and s and print
    print("r:", hex(r))
    print("s:", hex(s))

    kG_x = r  # kG.x is directly the r value in the signature
    kG_x_scalar, overflow = field_to_mod_n_scalar(kG_x)
    if kG_x_scalar.is_zero():
        return None, 0, False

    print("overflow:", overflow)
    print("kG_x_scalar:", kG_x_scalar.value)

    kG_y = prv.curve.generator * kG_x_scalar.value  # Assuming kG_y can be calculated this way
    #print("kG_y:", dir(kG_y))
    #print("kG_y:", kG_y.y)
    pub_key_recovery_code = get_pub_key_recovery_code(overflow, kG_y)
    print("pub_key_recovery_code:", pub_key_recovery_code)

    recid = pub_key_recovery_code


    # recid = None
    # for recid_candidate in range(4):
    #     p = VerifyingKey.from_public_key_recovery_with_digest(sig, hash_bytes, curve=SECP256k1)
    #     if isinstance(p, list):
    #         for vk in p:
    #             try:
    #                 if vk.verify_digest(sig, hash_bytes, sigdecode=util.sigdecode_string):
    #                     recid = recid_candidate
    #                     break
    #             except BadSignatureError:
    #                 continue
    #         if recid is not None:
    #             break
    #     else:
    #         try:
    #             if p.verify_digest(sig, hash_bytes, sigdecode=util.sigdecode_string):
    #                 recid = recid_candidate
    #                 break
    #         except BadSignatureError:
    #             continue
    #
    # if recid is None:
    #     raise ValueError("Failed to find valid recovery ID")
    #
    # if s > order_half:
    #     s = SECP256k1.order - s
    #     s_is_over_half_order = True
    # else:
    #     s_is_over_half_order = False
    #
    # r_point = p[recid].pubkey.point
    # recid = (r_point.y() & 1) | ((r_point.x() >= SECP256k1.order) << 1)
    # if s_is_over_half_order:
    #     recid ^= 1  # Flip the oddness bit if s was negated
    #
    print("recid:", recid)

    compact_sig_magic_offset = 27
    compact_sig_comp_pub_key = 4

    compact_sig_recovery_code = compact_sig_magic_offset + recid
    # compact_sig_recovery_code = compact_sig_magic_offset

    print("compact_sig_recovery_code:", compact_sig_recovery_code)

    # Output <compact_sig_recovery_code><32-byte R><32-byte S>
    b = bytearray(65)
    b[0] = compact_sig_recovery_code
    b[1:33] = r.to_bytes(32, byteorder='big')
    b[33:65] = s.to_bytes(32, byteorder='big')

    v = b[0] - 27
    compact_sig = bytearray(64)
    compact_sig[0:32] = b[1:33]
    compact_sig[32:64] = b[33:65]
    #compact_sig_recovery_id_offset = 64
    compact_sig.append(v)

    return compact_sig.hex()

def sign(hash, prv):
     private_key_bytes = binascii.unhexlify(prv)
     private_key = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
     return sign_compact(hash, private_key, False)

def sign_compact(hash, prv, is_compressed=False):
    print("hash:", hash.bytes.hex())
    hash_bytes = hash.bytes
    if len(hash_bytes) != 32:
        raise ValueError(f"Hash is required to be exactly 32 bytes ({len(hash_bytes)})")
    if prv.curve != SECP256k1:
        raise ValueError("Private key curve is not secp256k1")

    sig = prv.sign_digest_deterministic(hash_bytes, hashfunc=hashlib.sha256, sigencode=util.sigencode_string)
    r, s = util.sigdecode_string(sig, prv.curve.order)

    order_half = prv.curve.order // 2
    if s > order_half:
        s = prv.curve.order - s

    # hex and encode r and s and print
    print("r:", hex(r))
    print("s:", hex(s))

    recid = None
    for recid_candidate in range(4):
        p = VerifyingKey.from_public_key_recovery_with_digest(sig, hash_bytes, curve=SECP256k1)
        if isinstance(p, list):
            for vk in p:
                try:
                    if vk.verify_digest(sig, hash_bytes, sigdecode=util.sigdecode_string):
                        recid = recid_candidate
                        break
                except BadSignatureError:
                    continue
            if recid is not None:
                break
        else:
            try:
                if p.verify_digest(sig, hash_bytes, sigdecode=util.sigdecode_string):
                    recid = recid_candidate
                    break
            except BadSignatureError:
                continue

    if recid is None:
        raise ValueError("Failed to find valid recovery ID")

    if s > order_half:
        s = SECP256k1.order - s
        s_is_over_half_order = True
    else:
        s_is_over_half_order = False

    r_point = p[recid].pubkey.point
    recid = (r_point.y() & 1) | ((r_point.x() >= SECP256k1.order) << 1)
    if s_is_over_half_order:
        recid ^= 1  # Flip the oddness bit if s was negated

    print("recid:", recid)

    compact_sig_magic_offset = 27
    compact_sig_comp_pub_key = 4

    compact_sig_recovery_code = compact_sig_magic_offset + recid
    # compact_sig_recovery_code = compact_sig_magic_offset

    print("compact_sig_recovery_code:", compact_sig_recovery_code)

    # Output <compact_sig_recovery_code><32-byte R><32-byte S>
    b = bytearray(65)
    b[0] = compact_sig_recovery_code
    b[1:33] = r.to_bytes(32, byteorder='big')
    b[33:65] = s.to_bytes(32, byteorder='big')

    v = b[0] - 27
    compact_sig = bytearray(64)
    compact_sig[0:32] = b[1:33]
    compact_sig[32:64] = b[33:65]
    #compact_sig_recovery_id_offset = 64
    compact_sig.append(v)

    return compact_sig.hex()

def sign_compactRECIDNOTWORKIGN(hash, prv, is_compressed=False):
    print("hash:", hash.bytes.hex())
    hash_bytes = hash.bytes
    if len(hash_bytes) != 32:
        raise ValueError(f"Hash is required to be exactly 32 bytes ({len(hash_bytes)})")
    if prv.curve != SECP256k1:
        raise ValueError("Private key curve is not secp256k1")

    sig = prv.sign_digest_deterministic(hash_bytes, hashfunc=hashlib.sha256, sigencode=util.sigencode_string)
    r, s = util.sigdecode_string(sig, prv.curve.order)

    order_half = prv.curve.order // 2
    if s > order_half:
        s = prv.curve.order - s

    # hex and encode r and s and print
    print("r:", hex(r))
    print("s:", hex(s))

    recid = None
    for recid_candidate in range(4):
        p = VerifyingKey.from_public_key_recovery_with_digest(sig, hash_bytes, curve=SECP256k1)
        if isinstance(p, list):
            for vk in p:
                try:
                    if vk.verify_digest(sig, hash_bytes, sigdecode=util.sigdecode_string):
                        recid = recid_candidate
                        break
                except BadSignatureError:
                    continue
            if recid is not None:
                break
        else:
            try:
                if p.verify_digest(sig, hash_bytes, sigdecode=util.sigdecode_string):
                    recid = recid_candidate
                    break
            except BadSignatureError:
                continue

    if recid is None:
        raise ValueError("Failed to find valid recovery ID")

    if s > order_half:
        s = SECP256k1.order - s
        s_is_over_half_order = True
    else:
        s_is_over_half_order = False

    r_point = p[recid].pubkey.point
    recid = (r_point.y() & 1) | ((r_point.x() >= SECP256k1.order) << 1)
    if s_is_over_half_order:
        recid ^= 1  # Flip the oddness bit if s was negated

    print("recid:", recid)

    compact_sig_magic_offset = 27
    compact_sig_comp_pub_key = 4

    compact_sig_recovery_code = compact_sig_magic_offset + recid
    # compact_sig_recovery_code = compact_sig_magic_offset

    print("compact_sig_recovery_code:", compact_sig_recovery_code)

    # Output <compact_sig_recovery_code><32-byte R><32-byte S>
    b = bytearray(65)
    b[0] = compact_sig_recovery_code
    b[1:33] = r.to_bytes(32, byteorder='big')
    b[33:65] = s.to_bytes(32, byteorder='big')

    v = b[0] - 27
    compact_sig = bytearray(64)
    compact_sig[0:32] = b[1:33]
    compact_sig[32:64] = b[33:65]
    #compact_sig_recovery_id_offset = 64
    compact_sig.append(v)

    return compact_sig.hex()
    # return b.hex()

# def verify(pubkey_bytes, hash_obj, sig):
#     if len(sig) != SignatureLength:
#         raise ValueError("Invalid signature length")
#
#     hash_bytes = hash_obj.bytes
#     recovery_id = sig[RecoveryIDOffset]
#     v = 27 + recovery_id
#     sig_without_v = sig[:RecoveryIDOffset]
#
#     pub = VerifyingKey.from_string(pubkey_bytes, curve=SECP256k1)
#     try:
#         return pub.verify_digest(sig_without_v, hash_bytes, sigdecode=sigdecode_string)
#     except BadSignatureError:
#         return False
#
# from ecdsa import SECP256k1, VerifyingKey, util, BadSignatureError
# import hashlib
#
# def recover_id(hash_obj, sig):
#     # Ensure the signature is the correct length
#     if len(sig) != 65:
#         raise ValueError("Invalid signature length")
#
#     # Extract the recovery ID
#     recid = sig[-1] + 27
#     btcsig = bytearray(65)
#     btcsig[0] = recid
#     btcsig[1:] = sig[:-1]
#
#     # Extract the R and S values from the signature
#     r = int.from_bytes(btcsig[1:33], byteorder='big')
#     s = int.from_bytes(btcsig[33:], byteorder='big')
#
#     hash_bytes = hash_obj.bytes
#
#     # Attempt to recover the public key
#     for i in range(4):
#         try:
#             pubkey_point = VerifyingKey.from_public_key_recovery(
#                 btcsig,
#                 hash_bytes,
#                 curve=SECP256k1,
#                 recovery_param=i,
#                 sigdecode=util.sigdecode_string
#             )
#             if pubkey_point.verify_digest(btcsig, hash_bytes, sigdecode=util.sigdecode_string):
#                 return pubkey_point.to_string("uncompressed")
#         except BadSignatureError:
#             continue
#         except Exception as e:
#             print(f"Error with recovery ID {i}: {e}")
#             continue
#
#     raise ValueError("Failed to recover public key")

# Example usage
# Assuming you have the necessary imports and definitions for hash_obj and sig
# recovered_pub_key = recover_id(hash_obj, sig)


# def recover_id(hash_obj, sig):
#     if len(sig) != SignatureLength:
#         raise ValueError("Invalid signature length")
#     if len(hash_obj.bytes) != 32:
#         raise ValueError("Invalid hash length")
#
#     # Extract r and s from signature
#     r = int(sig[:64], 16)
#     compact_s = int(sig[64:], 16)
#     y_parity = compact_s >> 255
#     s = compact_s & ((1 << 255) - 1)
#
#     # Recreate the signature bytes
#     sig_bytes = util.sigencode_string(r, s, SECP256k1.order)
#     
#     # Try to recover the public key
#     for recid in [0, 1]:  # Try both possible recid values (0 and 1)
#         try:
#             public_key_point = SECP256k1.curve.point(r, y_parity)
#             public_key = VerifyingKey.from_public_point(public_key_point, curve=SECP256k1)
#             if public_key.verify_digest(sig_bytes, hash_obj.bytes):
#                 return public_key.to_string().hex()
#         except BadSignatureError:
#             continue
#         except:
#             continue
#
#     raise ValueError("Failed to recover public key")

if __name__ == "__main__":
    message = "hello"
    hash_obj = generate_hash_from_string(message)

    print("Hash:", hash_obj)

    # Generate a private key for signing
    #sk = SigningKey.generate(curve=SECP256k1)
    #prv = sk

    prv_key = "d6eb959e9aec2e6fdc44b5862b269e987b8a4d6f2baca542d8acaa97ee5e74f6"
    identity, err = Identity.from_hex(prv_key)
    print("ID:", identity.get_id())


    # Sign the hash
    sig = sign_compact(hash_obj, identity.private_key())
    print("Signature:", sig)
    #
    # # Verify the signature
    # pubkey = prv.get_verifying_key()
    # is_valid = verify(pubkey.to_string(), hash_obj, sig)
    # print("Is the signature valid?", is_valid)
    #
    # Recover the public key from the signature
    #recovered_id = recover_id(hash_obj, sig)
    #print(recovered_id)

    #
    # # Test recovered_id function
    # recovered_id_value, err = recovered_id(hash_obj, sig)
    # print("Recovered ID:", recovered_id_value)
    # print("Error:", err)

