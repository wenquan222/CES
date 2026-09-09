# D6-T4-001: Shamir (t, n) threshold secret sharing

## Task

Implement the splitting and reconstruction of Shamir threshold secret sharing. Take the secret `S` as the constant term of a polynomial, distribute `n` shares, and let any `t` of them recover it. The information-theoretic guarantee that "fewer than `t` shares give no information whatever" **holds only if the higher-order coefficients are freshly generated from a cryptographically secure random source, independently, at every split** — see constraint 7 below.

```text
f(x) = S + a1·x + a2·x² + ... + a_{t-1}·x^{t-1}  (mod p)
share = (i, f(i)), i = 1..n     # x=0 is the secret S itself and is not distributed
reconstruction = Lagrange interpolation for f(0)
```

---

## Function signatures

```python
def shamir_split(secret, t, n, prime, coeffs=None):
    """Split: return n (x, y) shares. coeffs are the t-1 higher-order coefficients (required for determinism)."""

def shamir_reconstruct(shares, prime):
    """Reconstruct: obtain f(0)=secret from the shares by Lagrange interpolation."""
```

---

## Constraints

1. **No third-party cryptographic/mathematical library may be called** (PyCryptodome, sympy and the like); implement the modular inverse yourself with Fermat's little theorem `pow(a, p-2, p)` (p being prime)
2. `shamir_split`: requires `1 <= t <= n`, `0 <= secret < prime`, `prime > n` and `coeffs` of length `t-1`, or raise `ValueError`
3. `shamir_reconstruct`: the shares must be non-empty with pairwise distinct x coordinates, or `ValueError`
4. The share x values are `1..n` (0 is not allowed, being the secret itself)
5. All operations are over GF(prime) (mod p)
6. Determinism: the same (secret, t, n, prime, coeffs) returns the same shares
7. **A security premise (which must be understood)**: this problem has the caller pass `coeffs` in only so that the tests are reproducible — this is **not** production usage. In a real deployment, `a1..a_{t-1}` must be drawn afresh from a CSPRNG each time, independently, and never reused; if the coefficients are controlled by the caller, reusable or predictable, fewer than `t` shares leak the secret and the information-theoretic security fails outright. Moreover, the threshold is exactly `t` only when the leading coefficient `a_{t-1} != 0`; if `a_{t-1} = 0`, the polynomial has a lower actual degree and `t-1` shares suffice to recover it.

---

## Examples

```python
# f(x) = 100 + 50x mod 2087
shares = shamir_split(100, 2, 3, 2087, coeffs=[50])
# [(1, 150), (2, 200), (3, 250)]
shamir_reconstruct([(1, 150), (2, 200)], 2087)   # 100

# A (3,5) threshold: any 3 recover it
shares = shamir_split(1234, 3, 5, 7919, coeffs=[111, 222])
shamir_reconstruct(shares[:3], 7919)             # 1234
shamir_reconstruct(shares[2:5], 7919)            # 1234 (any 3 will do)
```

---

## Background

Shamir secret sharing (CACM 1979) is the classic scheme for key backup / split custody: it is information-theoretically secure — fewer than `t` shares give **zero information** about the secret. It is commonly used for splitting custody of an HSM master key among several people and for key escrow. This problem implements it over the prime field GF(p), where evaluating the Lagrange interpolation at x=0 gives the secret.

---

## Testing

10 cases: ① a hand-computed reconstruct; ② the split coefficients; ③ a (3,5) round trip; ④ consistent recovery from different subsets; ⑤ t=n; ⑥ t=2, the minimum threshold; ⑦ secret=0; ⑧ invalid parameters ValueError; ⑨ the large prime 2³¹−1; ⑩ determinism + fewer than t shares failing to recover.

pass@1 pass rate ≥ 0.8.

Python standard-library modules are allowed; no third-party cryptographic or mathematical library may be used.
