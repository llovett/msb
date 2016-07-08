import binascii
import hashlib

PASSWORD_SALT = '7e3fca8b-8a86-4830-9eb0-a55a27de2f83'


def salted_hash(password):
    return binascii.hexlify(hashlib.pbkdf2_hmac(
        hash_name='sha256',
        password=password,
        salt=PASSWORD_SALT,
        iterations=100000
    ))
