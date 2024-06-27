import hashlib
import binascii
from ecdsa import SigningKey, SECP256k1
from hash import generate_hash_from_string

class Identity:
    def __init__(self, private_key=None):
        if private_key:
            self._private_key = private_key
        else:
            self._private_key = SigningKey.generate(curve=SECP256k1)
        self._public_key = self._private_key.get_verifying_key()
        self.id = generate_hash_from_string(self.public_key_as_hex())

    @staticmethod
    def from_hex(hex_encoded_prv):
        try:
            private_key_bytes = binascii.unhexlify(hex_encoded_prv)
            private_key = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
            return Identity(private_key), None
        except (TypeError, ValueError) as e:
            return None, e

    def private_key(self):
        return self._private_key

    def private_key_as_hex(self):
        return self._private_key.to_string().hex()

    def public_key_as_hex(self):
        return binascii.hexlify(self.public_key()).decode()

    def public_key(self):
        # Ethereum uses uncompressed public keys with a prefix of 0x04
        return b'\04' + self._public_key.to_string()

    def get_id(self):
        return self.id

# Example usage
if __name__ == "__main__":
    # Create a new identity
    identity = Identity()
    print("Private key:", identity.private_key_as_hex())
    print("Public key:", identity.public_key_as_hex())
    print("ID:", identity.get_id())

    # Create identity from a hex-encoded private key
    prv_key = "d6eb959e9aec2e6fdc44b5862b269e987b8a4d6f2baca542d8acaa97ee5e74f6"
    identity_from_hex, err = Identity.from_hex(prv_key)
    if err:
        print("Error:", err)
    else:
        print("Private key from hex:", identity_from_hex.private_key_as_hex())
        print("Public key from hex:", identity_from_hex.public_key_as_hex())
        print("ID from hex:", identity_from_hex.get_id())
