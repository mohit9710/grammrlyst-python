import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import random
import string


IV = "@@@@&&&&####$$$$"


def generate_salt(length=4):
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


def generate_checksum(params, merchant_key):
    data = "|".join(str(params[k]) for k in sorted(params.keys()))
    salt = generate_salt()
    final_string = data + "|" + salt
    hash_string = hashlib.sha256(final_string.encode()).hexdigest()
    checksum = hash_string + salt
    cipher = AES.new(merchant_key.encode(), AES.MODE_CBC, IV.encode())
    encrypted = cipher.encrypt(pad(checksum.encode(), AES.block_size))
    return base64.b64encode(encrypted).decode()


def verify_checksum(params, merchant_key, checksum):
    cipher = AES.new(merchant_key.encode(), AES.MODE_CBC, IV.encode())
    decrypted = unpad(cipher.decrypt(base64.b64decode(checksum)), AES.block_size)
    checksum_hash = decrypted.decode()
    salt = checksum_hash[-4:]
    data = "|".join(str(params[k]) for k in sorted(params.keys()))
    final_string = data + "|" + salt
    return hashlib.sha256(final_string.encode()).hexdigest() == checksum_hash[:-4]
