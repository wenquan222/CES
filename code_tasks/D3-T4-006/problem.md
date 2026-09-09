# D3-T4-006: CRT-RSA signing

## Problem
Implement `crt_rsa_sign(m, p, q, dp, dq, qinv)`, accelerating RSA signing with the Chinese Remainder Theorem (CRT).

## The CRT-RSA formulas
1. Sp = m^dp mod p
2. Sq = m^dq mod q
3. S = Sq + q * ((Sp - Sq) * qinv mod p)
where dp = d mod (p-1), dq = d mod (q-1), qinv = q^{-1} mod p

## Constraints
- A full-value modular exponentiation to the modulus p*q directly (such as `pow(m, d, p*q)`) is not allowed — the three CRT steps must be followed
- The modular exponentiation must be implemented yourself, without `pow`; square-and-multiply, window methods and any other correct form are acceptable
- Sp-Sq may be negative and the reduction mod p must handle that correctly
- p, q, dp, dq and qinv are positive integers; m satisfies 0 <= m < p*q

## Input
- m: int, the message (plaintext), 0 <= m < p*q
- p, q: int, the RSA prime factors
- dp, dq: int, dp = d mod (p-1), dq = d mod (q-1)
- qinv: int, qinv = q^{-1} mod p

## Output
- int: the signature S = m^d mod (p*q)

## Example
```
p=61, q=53, dp=53, dq=49, qinv=38
crt_rsa_sign(123, 61, 53, 53, 49, 38) -> check pow(sig, 17, 3233) == 123
```

---

## How the evaluation checks the implementation constraints

Besides the functional cases, the evaluation also checks that you **really wrote the required algorithm** rather than calling a library or taking a shortcut:

- **Import whitelist**: importing any module is **not allowed** in this problem.
- **No dunder channels**: no `__xxx__` attribute may be accessed (`int.__pow__`, say).
- **No reflective lookup**: `getattr` / `eval` / `exec` / `__import__` / `globals` / `vars` / `locals` must not be used.
- **Aliasing does not help**: renamings such as `shortcut = pow` or `from x import y as z` will not evade the check.
- **Dead code does not count**: a call written inside `if False:` or otherwise never reached does not count as "having implemented the algorithm".
- **Work check**: the evaluation counts the lines executed to confirm that both exponentiation branches really are computed by you (not by a library).

---
