import hashlib
from ecdsa import SigningKey, SECP256k1, VerifyingKey, BadSignatureError, util
from ecdsa.util import sigdecode_string, sigencode_string
import binascii
from hash import Hash, generate_hash_from_string  # Import from hash.py
import hashlib

SignatureLength = 128 
RecoveryIDOffset = 64

import hashlib
import binascii
from ecdsa import SigningKey, SECP256k1, util
from ecdsa.util import sigencode_string, sigdecode_string, number_to_string, randrange_from_seed__trytryagain
from ecdsa.ellipticcurve import Point

def sign(s, prv_hex_str):
    print("str:", s)
    print("prv_hex_str:", prv_hex_str)
    hash = hashlib.sha3_256()
    hash.update(s.encode('utf-8'))
    hash_bytes = hash.digest()
    is_compressed = False
    print(hash_bytes.hex())

    prv_hex_str_bytes = binascii.unhexlify(prv_hex_str)
    prv = SigningKey.from_string(prv_hex_str_bytes, curve=SECP256k1)
    if len(hash_bytes) != 32:
        raise ValueError(f"Hash is required to be exactly 32 bytes ({len(hash_bytes)})")
    if prv.curve != SECP256k1:
        raise ValueError("Private key curve is not secp256k1")

    sig = prv.sign_digest_deterministic(hash_bytes, hashfunc=hashlib.sha256, sigencode=util.sigencode_string)
    r, s = util.sigdecode_string(sig, prv.curve.order)

    print("----------------------------")
    iteration = 0
    while True:
        # Generate a deterministic nonce using RFC 6979
        k = util.rfc6979.generate_nonce(prv_hex_str_bytes, hash_bytes, SECP256k1.order, iteration)
        
        try:
            # Sign the hash deterministically
            sig = prv.sign_digest_deterministic(hash_bytes, hashfunc=hashlib.sha256, sigencode=util.sigencode_string, extra_entropy=number_to_string(k, prv.curve.order))
            r, s = util.sigdecode_string(sig, prv.curve.order)
            
            # Calculate Recovery ID
            R = prv.verifying_key.pubkey.point
            n = prv.curve.order
            recovery_id = (R.y() % 2) | (2 if r >= n else 0)
            
            # Adjust Recovery ID for s
            if s > n // 2:
                recovery_id ^= 1
            
            # Calculate v
            v = recovery_id + 27  # For Bitcoin, add 27 to recovery_id
           
            print("found soluation")
            print("r:", r)
            print("s:", s)
            print("Recovery ID:", recovery_id)
            print("v:", v)
            
            break
        
        except Exception as e:
            print(f"Iteration {iteration} failed with error: {e}")
            iteration += 1
            continue
    print("----------------------------")

    # Calculate Recovery ID
    R = prv.verifying_key.pubkey.point
    n = prv.curve.order
    recovery_id = (R.y() % 2) | (2 if r >= n else 0)

    # Adjust Recovery ID for s
    if s > n // 2:
        recovery_id ^= 1

    compact_sig_magic_offset = 27
    compact_sig_recovery_code = compact_sig_magic_offset + recovery_id
    print("compact_sig_recovery_code:", compact_sig_recovery_code)

    b = bytearray(65)
    b[0] = compact_sig_recovery_code
    b[1:33] = r.to_bytes(32, byteorder='big')
    b[33:65] = s.to_bytes(32, byteorder='big')

    v = b[0] - 27
    compact_sig = bytearray(64)
    compact_sig[0:32] = b[1:33]
    compact_sig[32:64] = b[33:65]
    compact_sig.append(v)

    return compact_sig.hex()
    # return b.hex()



def signOld(s, prv_hex_str):
    print("str:", s)
    print("prv_hex_str:", prv_hex_str)
    hash = hashlib.sha3_256()
    hash.update(s.encode('utf-8'))
    hash_bytes = hash.digest()
    is_compressed = False
    print(hash_bytes.hex())

    prv_hex_str_bytes = binascii.unhexlify(prv_hex_str)
    prv = SigningKey.from_string(prv_hex_str_bytes, curve=SECP256k1)
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

    # Calculate recovery id (recid)
    # recid = 0
    # for recid in range(2):
    #     compact_s = (recid << 255) | s  # "compact_s" is not accessed
    #     try:
    #         verifying_key = VerifyingKey.from_public_point(SECP256k1.generator * r, curve=SECP256k1)
    #         if verifying_key.verify_digest(sig, hash_bytes):
    #             break
    #     except BadSignatureError:
    #         continue
    #
    # if recid not in [0, 1]:
    #     raise ValueError("Failed to find valid recovery ID")

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
    #compact_sig_recovery_code = compact_sig_magic_offset
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


def signNotWorking(s, prv_hex_str):
    # Hash the input string using SHA-256
    hash = hashlib.sha256()
    hash.update(s.encode('utf-8'))
    hash_bytes = hash.digest()
    is_compressed = False

    # Convert the private key from hex string to bytes
    prv_hex_str_bytes = binascii.unhexlify(prv_hex_str)
    prv = SigningKey.from_string(prv_hex_str_bytes, curve=SECP256k1)

    # Ensure the hash is 32 bytes
    if len(hash_bytes) != 32:
        raise ValueError(f"Hash is required to be exactly 32 bytes ({len(hash_bytes)})")

    # Ensure the private key is using the SECP256k1 curve
    if prv.curve != SECP256k1:
        raise ValueError("Private key curve is not secp256k1")

    # Generate the deterministic signature
    sig = prv.sign_digest_deterministic(hash_bytes, hashfunc=hashlib.sha256, sigencode=util.sigencode_string)
    r, s = util.sigdecode_string(sig, SECP256k1.order)

    # Normalize s to be in the lower half of the curve order
    order_half = SECP256k1.order // 2
    if s > order_half:
        s = SECP256k1.order - s

    # Calculate recovery id (recid)
    recid = None
    for i in range(4):
        try:
            possible_keys = VerifyingKey.from_public_key_recovery_with_digest(
                sig,
                hash_bytes,
                curve=SECP256k1
            )
            for verifying_key in possible_keys:
                try:
                    if verifying_key.verify_digest(hash_bytes, sig, sigdecode=util.sigdecode_string):
                        recid = i
                        break
                except BadSignatureError:
                    continue
            if recid is not None:
                break
        except BadSignatureError:
            continue
        except Exception as e:
            print(f"Error with recovery ID {i}: {e}")
            continue

    if recid is None:
        raise ValueError("Failed to find valid recovery ID")

    print("recid:", recid)


    compact_sig_magic_offset = 27
    compact_sig_comp_pub_key = 4

    compact_sig_recovery_code = compact_sig_magic_offset + 1 
    if is_compressed:
        compact_sig_recovery_code += compact_sig_comp_pub_key

    # Create the compact signature
    b = bytearray(65)
    b[0] = compact_sig_recovery_code
    b[1:33] = r.to_bytes(32, byteorder='big')
    b[33:65] = s.to_bytes(32, byteorder='big')

    # Append the recovery ID correctly
    compact_sig = bytearray(64)
    compact_sig[0:32] = b[1:33]
    compact_sig[32:64] = b[33:65]
    compact_sig.append(recid)

    return compact_sig.hex()

# Example usage
# Assuming you have a private key in hex string form
# payload = "some data to sign"
# private_key_hex = "your_private_key_hex_string"
# signature = sign(payload, private_key_hex)
# print(signature)


def signAlmost(s, prv_hex_str):
    hash = hashlib.sha3_256()
    hash.update(s.encode('utf-8'))
    hash_bytes = hash.digest()
    is_compressed = False

    prv_hex_str_bytes = binascii.unhexlify(prv_hex_str)
    prv = SigningKey.from_string(prv_hex_str_bytes, curve=SECP256k1)
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
    #print("r:", hex(r))
    #print("s:", hex(s))

    # Calculate recovery id (recid)
    recid = 0
    for recid in range(2):
        compact_s = (recid << 255) | s  # "compact_s" is not accessed
        try:
            verifying_key = VerifyingKey.from_public_point(SECP256k1.generator * r, curve=SECP256k1)
            if verifying_key.verify_digest(sig, hash_bytes):
                break
        except BadSignatureError:
            continue

    if recid not in [0, 1]:
        raise ValueError("Failed to find valid recovery ID")

    compact_sig_magic_offset = 27
    compact_sig_comp_pub_key = 4

    #compact_sig_recovery_code = compact_sig_magic_offset + recid
    compact_sig_recovery_code = compact_sig_magic_offset
    if is_compressed:
        compact_sig_recovery_code += compact_sig_comp_pub_key

    #print("compact_sig_recovery_code:", compact_sig_recovery_code)

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

