# -*- coding: utf-8 -*-
"""
D6-T4-004 solution: PBKDF2-HMAC-SHA256, password-based key derivation (RFC 8018).

PBKDF2 derives a key from a low-entropy password, raising the cost of brute force and rainbow tables through salting and a high iteration count:

    DK = T_1 || T_2 || ... || T_l (truncated to the first dklen bytes)
    T_i = U_1 XOR U_2 XOR … XOR U_c
    U_1 = HMAC(password, salt ‖ INT32BE(i))
    U_j = HMAC(password, U_{j-1}) (j = 2..c, c = iterations)

This task requires the iteration and XOR to be implemented here (hashlib.pbkdf2_hmac is banned); the standard library
hmac + hashlib.sha256.

Source: RFC 8018 (PKCS #5 v2.1); NIST SP 800-132.
"""
import hmac
import hashlib
import struct

_HLEN = 32 # the SHA-256 output size in bytes


def pbkdf2_hmac_sha256(password, salt, iterations, dklen):
    """
    PBKDF2-HMAC-SHA256.

    Args:
        password: bytes, the password
        salt: bytes, the salt
        iterations: int, the iteration count (>= 1)
        dklen: int, the derived key length in bytes (>= 1)

    Returns:
        bytes, the derived key of length dklen

    Raises:
        ValueError: password/salt not bytes / iterations<1 / dklen<1 / dklen too large
    """
    if not isinstance(password, (bytes, bytearray)) or not isinstance(salt, (bytes, bytearray)):
        raise ValueError("password and salt must be bytes")
    if not isinstance(iterations, int) or iterations < 1:
        raise ValueError("iterations must be an integer >= 1")
    if not isinstance(dklen, int) or dklen < 1:
        raise ValueError("dklen must be an integer >= 1")
    if dklen > (2 ** 32 - 1) * _HLEN:
        raise ValueError("dklen is too large")

    password = bytes(password)
    salt = bytes(salt)
    blocks = (dklen + _HLEN - 1) // _HLEN
    dk = bytearray()
    for i in range(1, blocks + 1):
        u = hmac.new(password, salt + struct.pack(">I", i), hashlib.sha256).digest()
        t = bytearray(u)
        for _ in range(iterations - 1):
            u = hmac.new(password, u, hashlib.sha256).digest()
            for k in range(_HLEN):
                t[k] ^= u[k]
        dk += t
    return bytes(dk[:dklen])
