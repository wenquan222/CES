# D3-T4-002: RSA modular exponentiation (implemented yourself)

## Task

Implement the RSA modular exponentiation `x^d mod N` **yourself**, without calling a library function.
Processing the bits of d one at a time suffices; both the left-to-right (high-to-low) and the right-to-left (low-to-high) square-and-multiply forms are accepted, as is any other correct self-written algorithm such as a window method.



---

## Function signature

```python
def modexp_square_multiply(x: int, d: int, N: int) -> int:
    """
    Implement modular exponentiation yourself, computing x^d mod N.

    Args:
        x: int, the base (0 ≤ x < N)
        d: int, the exponent (0 ≤ d)
        N: int, the modulus (N >= 2)

    Returns:
        x^d mod N
    """
```

---

## The algorithm (example: left-to-right square-and-multiply)

```text
A = 1
for j = bitlen(d) - 1 down to 0:
    A = A² mod N          # the square is always done
    if (bit j of d == 1):
        A = A · x mod N   # the multiply is conditional
return A
```

---

## Constraints

1. **Calling Python's built-in `pow(x, d, N)` directly is banned** (that is the shortcut)
2. **A loop over the bits of d must be used** (not `x**d % N` followed by a reduction — that computes an enormous intermediate value)
3. The bit scanning direction and the window organization are unrestricted (left-to-right, right-to-left and window methods are all accepted);
   the left-to-right form given below is only **one example** and is not a form you must follow
4. You must perform the modular squarings and modular multiplications tied to the exponent bits/windows yourself; a ready-made modular exponentiation must not be called, while the bit scanning direction and window organization remain unrestricted
5. Boundaries: `d = 0` returns 1; `x = 0` with `d > 0` returns 0
6. `N` must be >= 2, or raise `ValueError`
7. The function is deterministic

---

## Performance requirement

For RSA-2048 parameters (N ~ 2^2048, d ~ 2^2048), a single call should take < 10 seconds (the reference implementation takes about 1 second; the graded test uses 10 s to absorb machine-to-machine variation).
Small test cases (N < 2^32) should take < 0.01 seconds.

---

## Examples

```python
# The textbook example
modexp_square_multiply(2, 10, 1000)  # = 2^10 mod 1000 = 1024 mod 1000 = 24

# RSA-toy
N = 3233      # = 53 × 61
e = 17
d = 2753
m = 65
c = modexp_square_multiply(m, e, N)  # encryption
assert c == 2790
m_dec = modexp_square_multiply(c, d, N)  # decryption
assert m_dec == m
```

---


## How the evaluation checks the implementation constraints

Besides the functional cases, the evaluation also checks that you **really wrote the required algorithm** rather than calling a library or taking a shortcut:

- **Import whitelist**: importing any module is **not allowed** in this problem.
- **No dunder channels**: no `__xxx__` attribute may be accessed (`int.__pow__`, say).
- **No reflective lookup**: `getattr` / `eval` / `exec` / `__import__` / `globals` / `vars` / `locals` must not be used.
- **Aliasing does not help**: renamings such as `shortcut = pow` or `from x import y as z` will not evade the check.
- **Dead code does not count**: a call written inside `if False:` or otherwise never reached does not count as "having implemented the algorithm".
- **Work check**: the evaluation counts how many lines of Python one call executes: a self-written modular exponentiation with a 512-bit exponent runs on the order of a thousand lines, whereas calling the built-in `pow` (however it is reached) runs only single digits.

---

## Testing

16 cases cover: ① toy RSA encryption/decryption consistency; ② the d=0 / d=1 boundaries; ③ the x=0 / x=1 boundaries; ④ the modulus N=2; ⑤ large numbers (1024-bit); ⑥ performance (RSA-2048 < 5s); ⑦ the N<2 exception; ⑧ agreement with Python's `pow` (used for checking, not called); ⑨ determinism; ⑩ fixed vectors with known answers.

pass@1 pass rate ≥ 0.8.
