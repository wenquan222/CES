# D6-T4-002: HKDF key derivation (RFC 5869)

## Task

Implement the complete **extract-then-expand** flow of HKDF (HMAC-based Key Derivation Function, RFC 5869), deriving a key of the specified length from input keying material.

```text
Extract:  PRK = HMAC-Hash(salt, IKM)              # extraction: non-uniform IKM → uniform PRK
Expand:   T(0) = the empty string
          T(i) = HMAC-Hash(PRK, T(i-1) ‖ info ‖ i)   # i being a single byte 1,2,3,...
          OKM  = T(1) ‖ T(2) ‖ ... truncated to the first length bytes
```

---

## Function signature

```python
def hkdf(ikm, salt, info, length, hash_name="sha256"):
    """
    Args:
        ikm:    bytes, the input keying material
        salt:   bytes, the salt (all zeros of length HashLen per the specification
                when b"" or None)
        info:   bytes, context binding information
        length: int, the desired number of output bytes (0 <= length <= 255*HashLen)
    Returns:
        bytes, the output keying material OKM of length = length
    """
```

---

## Constraints

1. **The standard library `hmac` + `hashlib` must be used**; third-party HKDF (the ready-made implementation of the cryptography library, say) must not be called
2. When salt is `None` or empty, use `HashLen` zero bytes per RFC 5869
3. The upper limit of `length` is `255 * HashLen` (255×32=8160 for SHA-256); exceeding it raises `ValueError`; a negative value raises `ValueError`
4. `length=0` returns `b""`
5. The counter `i` of Expand is a single byte (`bytes([i])`, starting from 1)
6. Determinism: the same input returns the same OKM; the return type is `bytes`

---

## Example (RFC 5869 Test Case 1)

```python
ikm  = bytes([0x0b] * 22)
salt = bytes(range(0x00, 0x0d))     # 00 01 ... 0c
info = bytes(range(0xf0, 0xfa))     # f0 f1 ... f9
okm  = hkdf(ikm, salt, info, 42)
# okm == 3cb25f25faacd57a90434f64d0362f2a2d2d0a90cf1a5a4c5db02d56ecc4c5bf34007208d5b887185865
```

---

## Background

HKDF (Krawczyk, CRYPTO 2010) is the de facto standard for modern key derivation, used widely in TLS 1.3, Signal, Noise and elsewhere. Its extract-then-expand design separates "key extraction" (extracting a uniform key from a high-entropy but non-uniform source) from "key expansion" (deriving several subkeys of arbitrary length). **RFC 5869 has been included among the key derivation methods approved for FIPS 140-3 (NIST SP 800-140D)**.

---

## Testing

10 cases: ① the official vector of RFC 5869 Test Case 1; ② Test Case 3 (empty salt/info); ③ salt=None equivalent to all zeros; ④ the exact output length; ⑤ length=0 empty; ⑥ different info giving different OKM; ⑦ different salt giving different OKM; ⑧ over-long ValueError; ⑨ negative length ValueError; ⑩ determinism + the bytes type.

pass@1 pass rate ≥ 0.8.
