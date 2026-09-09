# D3-T4-003: Montgomery modular multiplication

## Task

Implement the Montgomery modular multiplication `MontMul(x, y) = x · y · R⁻¹ mod N`.



---

## Function signature

```python
def montgomery_modmul(x: int, y: int, N: int, N_prime: int, R: int) -> int:
    """
    Montgomery modular multiplication: return x · y · R^{-1} mod N

    Args:
        x, y: int, the operands in the Montgomery domain (0 ≤ x, y < N)
        N:    int, the modulus (must be odd, gcd(R, N) = 1)
        N_prime: int, the precomputed -N^{-1} mod R
        R:    int, must be a power of 2 with R > N

    Returns:
        x · y · R^{-1} mod N
    """
```

---

## The algorithm (the key formulas)

```text
Fact 1: gcd(N, R) = 1, N' = -N^{-1} mod R
       if U = T · N' mod R, then (T + U·N) / R ≡ T · R^{-1} mod N

The algorithm:
T = x · y         # ordinary multi-precision multiplication
U = (T · N') mod R = (T · N') & (R - 1)   # R is a power of 2, so mod is a mask
result = (T + U · N) // R                  # a right shift of log2(R) bits

# The final reduction: result may lie in [0, 2N)
if result >= N:
    result -= N

return result
```

---

## Module-level names that must be exported (the evaluation imports them directly, so name them exactly as below)

The Montgomery reduction step **must be a separate function defined at module top level under the following name**:

```python
def _redc(T: int, N: int, N_prime: int, R: int) -> int:
    """Perform one Montgomery reduction on T. Requires 0 <= T < N·R (the input
       domain of classic REDC, automatically satisfied in the main function
       where T = (x mod N)·(y mod N)):
       U = (T * N_prime) mod R
       t = (T + U * N) / R          (which divides exactly here)
       subtract one N if t >= N
       return t, satisfying t ≡ T * R^{-1} (mod N) and 0 <= t < N
    """
```

The evaluation code runs `from solution import montgomery_modmul, _redc`, verifies with random T that `_redc` satisfies the formula above, and verifies that the return value of `montgomery_modmul`
**really comes from the return value of `_redc`** — calling `_redc` once without using its result,
or computing `R^{-1}` separately and multiplying, does not count as completing this problem.
What this problem examines is exactly the REDC reduction procedure; computing `R^{-1} mod N` first and then multiplying gives the same result
but is not the algorithm this problem asks for.

## Constraints

1. `N` must be odd (gcd(R, N) = 1 is required, which an odd N satisfies automatically) — validate, raising `ValueError` if not
2. `R` must be a power of 2 with R > N — validate
3. Using Python's built-in `pow` as a shortcut is not allowed
4. `(x * y) % N` directly is not allowed (that is traditional reduction, not Montgomery)
5. The two Montgomery reduction steps must actually be executed: first U = T · N' mod R, then result = (T + U·N) // R
6. Determinism

---

## Verification: the relation between Montgomery and traditional modmul

For any x, y < N:

```text
MontMul(x, y) ≡ x · y · R^{-1} mod N
```

In particular:

```text
MontMul(MontMul(x · R, y · R), 1) = x · y · R · R · R^{-1} · R^{-1} mod N
                                  = x · y mod N
```

That is, Montgomery modular multiplication can "equivalently implement" traditional modular multiplication, with no trial division in between.

---

## Example

```python
N = 17          # the modulus (odd)
R = 32          # a power of 2, R > N
# N' = -N^{-1} mod R = -17^{-1} mod 32
# 17 · 17 = 289 = 9·32 + 1 → 17^{-1} mod 32 = 17
# N' = -17 mod 32 = 15
N_prime = 15

# Check: MontMul(3, 5) = 3 · 5 · 32^{-1} mod 17
# 32 mod 17 = 15; 32^{-1} mod 17 = 8 (since 15·8 = 120 = 7·17+1)
# 3 · 5 · 8 mod 17 = 120 mod 17 = 120 - 7·17 = 120-119 = 1
montgomery_modmul(3, 5, 17, 15, 32)  # → 1 ✓
```

---


## How the evaluation checks the implementation constraints

Besides the functional cases, the evaluation also checks that you **really wrote the required algorithm** rather than calling a library or taking a shortcut:

- **Import whitelist**: importing any module is **not allowed** in this problem.
- **No dunder channels**: no `__xxx__` attribute may be accessed (`int.__pow__`, say).
- **No reflective lookup**: `getattr` / `eval` / `exec` / `__import__` / `globals` / `vars` / `locals` must not be used.
- **Aliasing does not help**: renamings such as `shortcut = pow` or `from x import y as z` will not evade the check.
- **Dead code does not count**: a call written inside `if False:` or otherwise never reached does not count as "having implemented the algorithm".
- **Work check**: the evaluation counts an **upper bound** on the lines executed: one Montgomery reduction is only a few multiply-add-shift steps.
  If you bypass `N_prime` and compute `R^{-1} mod N`, that needs an extended Euclidean algorithm and the line count far exceeds the bound.
  The evaluation also recomputes with a wrong `N_prime`, and the result must change accordingly.

---

## Testing

17 cases cover: ① small integers N=17, R=32; ② a medium N (32-bit) consistency test; ③ large integers (512-bit RSA-style); ④ an even N raising an exception; ⑤ an R that is not a power of 2 raising an exception; ⑥ R ≤ N raising an exception; ⑦ the x=0/y=0 boundaries; ⑧ x=y (squaring); ⑨ verification of the "equivalent modular multiplication" composed from MontMul; ⑩ determinism.

pass@1 pass rate ≥ 0.8.
