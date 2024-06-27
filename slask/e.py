from eth_account.messages import encode_defunct
from web3 import Web3
from eth_account import Account
import hashlib

# Define the message
message = "hello"
private_key = "d6eb959e9aec2e6fdc44b5862b269e987b8a4d6f2baca542d8acaa97ee5e74f6"

account = Account.from_key(private_key)

address = account.address
print(f"Loaded Address: {address}")


# Encode the message
encoded_message = encode_defunct(text=message)

# Sign the message
signed_message = Account.sign_message(encoded_message, private_key)
print(signed_message)
hash = hashlib.sha3_256()
hash.update(message.encode('utf-8'))
hash_bytes = hash.digest()

print(f"Message: {message}")
print(f"Signature: {signed_message.signature.hex()}")
