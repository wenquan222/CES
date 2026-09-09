# D6-T4-004: PBKDF2-HMAC-SHA256 (password-based key derivation)

## Task

Implement PBKDF2-HMAC-SHA256 (RFC 8018 / PKCS #5 v2.1) yourself, deriving a key from a low-entropy password. **`hashlib.pbkdf2_hmac` must not be called**; write the iteration and the XOR yourself; the standard library `hmac` + `hashlib.sha256` may be used.

```text
DK  = T_1 ‖ T_2 ‖ … ‖ T_l        (truncated to the first dklen bytes)
T_i = U_1 XOR U_2 XOR … XOR U_c
U_1 = HMAC(password, salt ‖ INT32BE(i))
U_j = HMAC(password, U_{j-1})     (j = 2..c, c = iterations)
```

---

## Function signature

```python
def pbkdf2_hmac_sha256(password, salt, iterations, dklen):
    """
    Args:
        password: bytes
        salt:     bytes
        iterations: int (>=1)
        dklen:    int (>=1), the number of derived key bytes
    Returns:
        bytes of length dklen
    """
```

---

## Constraints

1. **`hashlib.pbkdf2_hmac` must not be called**; implement the block iteration and the XOR yourself. `hmac.new(..., hashlib.sha256)` may be used.
2. The block counter `INT32BE(i)` is 4 bytes big-endian.
3. Exceptions (`ValueError`): `password`/`salt` not bytes, `iterations < 1`, `dklen < 1`, `dklen` too large (> (2³²−1)·32).
4. Return exactly `dklen` `bytes`.
5. Determinism.

---

## Example

```python
# Agreeing with the standard library (which is only a reference; the implementation must compute it itself)
pbkdf2_hmac_sha256(b"password", b"salt", 1000, 32)
# == hashlib.pbkdf2_hmac("sha256", b"password", b"salt", 1000, 32)
```

---

## Background

PBKDF2 is the classic password-based key derivation function and contrasts with HKDF (RFC 5869) — both are based on HMAC, but their **goals differ**:

- **PBKDF2** (RFC 8018 / SP 800-132): the input is a **low-entropy password**, and it relies on a **high iteration count** (tens to hundreds of thousands) to amplify the computational cost of each guess linearly and on a **salt** to defeat rainbow tables/precomputation, being aimed specifically at **resisting brute force**.
- **HKDF** (RFC 5869): the input is **high-entropy but non-uniformly distributed** keying material (a DH shared secret, say), which extract-then-expand **extracts** into a uniform key and then expands; the goal is **key extraction and expansion**, not brute-force resistance.

Misusing PBKDF2 on high-entropy material (wasting the iterations) or HKDF on a password (lacking the iteration cost that resists brute force) are both common engineering errors.

Note: modern password hashing favours scrypt / Argon2 (adding memory hardness against GPUs/ASICs), while PBKDF2 remains widely used in compliance settings thanks to FIPS approval.

---


## How the evaluation checks the implementation constraints

Besides the functional cases, the evaluation also checks that you **really wrote the required algorithm** rather than calling a library or taking a shortcut:

- **Import whitelist**: only `hmac`, `hashlib` and `struct` may be imported in this problem; importing anything else (including `operator` and any third-party cryptographic library) counts as a failure.
- **No dunder channels**: no `__xxx__` attribute may be accessed (`int.__pow__`, say).
- **No reflective lookup**: `getattr` / `eval` / `exec` / `__import__` / `globals` / `vars` / `locals` must not be used.
- **Aliasing does not help**: renamings such as `shortcut = pow` or `from x import y as z` will not evade the check.
- **Dead code does not count**: a call written inside `if False:` or otherwise never reached does not count as "having implemented the algorithm".
- **Work check**: the evaluation counts the lines executed: `iterations` rounds of block iteration and XOR run tens of thousands of lines of Python, whereas calling any ready-made PBKDF2 implementation runs only single digits.

---

## Testing

16 cases: ① comparison against the standard library (several iterations×dklen combinations); ② dklen>32 spanning blocks; ③ 1 iteration; ④ dklen ∈ {1,7,33,64,65} at block boundaries; ⑤ different salts giving different output; ⑥ returning dklen bytes; ⑦ iterations<1 ValueError; ⑧ dklen<1 ValueError; ⑨ password/salt not bytes ValueError; ⑩ determinism.

pass@1 pass rate ≥ 0.8.
