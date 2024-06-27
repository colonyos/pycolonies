import hashlib
import binascii

class Hash:
    def __init__(self, bytes_data=None):
        self.bytes = bytes_data

    def bytes(self):
        return self.bytes

    def __str__(self):
        return self.bytes.hex()

def generate_hash(buf):
    d = hashlib.sha3_256()
    d.update(buf)
    return Hash(d.digest())

def generate_hash_from_string(string):
    return generate_hash(string.encode('utf-8'))

def create_hash_from_string(string):
    try:
        bytes_data = binascii.unhexlify(string)
        return Hash(bytes_data), None
    except binascii.Error as e:
        return None, e
