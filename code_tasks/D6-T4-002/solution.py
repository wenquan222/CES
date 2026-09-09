# -*- coding: utf-8 -*-
"""
D6-T4-002 solution: HKDF (HMAC-based Key Derivation Function, RFC 5869) .

The two-step extract-then-expand construction:
    Extract: PRK = HMAC-Hash(salt, IKM) # extract a uniform PRK from the non-uniform IKM
    Expand: T(0) = empty; T(i) = HMAC(PRK, T(i-1) || info || i); OKM = the first L bytes of T(1) || T(2) || ...

Source: Krawczyk, CRYPTO 2010; RFC 5869; NIST SP 800-56C.
HKDF (RFC 5869) is among the key derivation methods approved for FIPS 140-3 (SP 800-140D).
"""
import hashlib
import hmac


def hkdf(ikm, salt, info, length, hash_name="sha256"):
    """
    The full HKDF flow, returning length bytes of output keying material (OKM).

    Args:
        ikm: bytes, the input keying material
        salt: bytes, the salt (may be b"" or None; when empty the specification uses all zeros)
        info: bytes, context/application binding information (may be b"")
        length: int, the desired number of output bytes (0 <= length <= 255*HashLen)
        hash_name: str, the hash algorithm name (default sha256, HashLen=32)

    Returns:
        bytes, the OKM of length length

    Raises:
        ValueError: length negative / greater than 255*HashLen
    """
    hash_len = hashlib.new(hash_name).digest_size
    if length < 0:
        raise ValueError("length must not be negative")
    if length > 255 * hash_len:
        raise ValueError(f"length exceeds the limit 255*HashLen={255 * hash_len}")
    if salt is None or len(salt) == 0:
        salt = b"\x00" * hash_len

    # Extract
    prk = hmac.new(salt, ikm, hash_name).digest()

    # Expand
    okm = b""
    t = b""
    i = 1
    while len(okm) < length:
        t = hmac.new(prk, t + info + bytes([i]), hash_name).digest()
        okm += t
        i += 1
    return okm[:length]
