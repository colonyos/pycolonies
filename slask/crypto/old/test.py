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
    # Extract the y-coordinate integer value
    kG_y_value = kG_y.value if isinstance(kG_y, FieldVal) else kG_y
    pub_key_recovery_code = (overflow << 1) | (kG_y_value & 1)
    return pub_key_recovery_code

# Example usage
class SECP256k1:
    order = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141  # Example order of SECP256k1

# Assuming kG is a Point with x and y coordinates
kG = Point(1234567890123456789012345678901234567890, 987654321098765432109876543210987654321)

# Convert kG.x to scalar and get overflow
kG_x_scalar, overflow = field_to_mod_n_scalar(kG.x)

# Get pub key recovery code
pub_key_recovery_code = get_pub_key_recovery_code(overflow, kG.y)
print("pub_key_recovery_code:", pub_key_recovery_code)

