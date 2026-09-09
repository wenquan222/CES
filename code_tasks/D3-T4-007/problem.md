# D3-T4-007: Sliding window modular exponentiation

## Problem
Implement `sliding_window_modexp(base, exponent, modulus, window_size)`, computing base^exponent mod modulus by the sliding window method.

## The sliding window algorithm
1. Precompute: base^1, base^3, ..., base^(2^k-1) mod modulus (odd powers only)
2. Scan the binary representation of exponent from the high bits down
3. On a 0: result = result^2 mod modulus, and the window slides 1 bit onward
4. On a 1: find the longest window starting at the current position (at most k bits, the window ending in a 1)
   - result = result^(2^window_len) mod modulus
   - result = result * precomputed[window_val] mod modulus
   - skip the whole window's worth of bits

## Module-level names that must be exported (the evaluation imports them directly, so name them exactly as below)

Besides `sliding_window_modexp`, **the precomputation step must be a separate function defined at module top level under the following name**:

```python
def _precompute_odd_powers(base: int, modulus: int, window_size: int) -> dict:
    """Return {e: base^e mod modulus} for e ranging over 1, 3, 5, ..., 2^window_size - 1"""
```

The evaluation code runs `from solution import sliding_window_modexp, _precompute_odd_powers`,
and verifies that the result of `sliding_window_modexp` **really depends on the contents of that table**
— calling the precomputation function once without using the table it returns, or actually running an ordinary binary square-and-multiply,
does not count as completing this problem — what this problem examines is exactly the
"precompute the odd powers + scan by windows" approach, and simply writing an ordinary binary square-and-multiply does not count as completing it.

## Constraints
- Using `pow(base, exponent, modulus)` directly is not allowed
- k = window_size
- When precomputing the odd powers, use base^(odd) = base^(odd-2) * base^2 mod modulus

## Input
- base: int
- exponent: int (>=0)
- modulus: int (>0)
- window_size: int (>=1)

## Output
- int: base^exponent mod modulus

## Examples
```
sliding_window_modexp(3, 5, 100, 3) = 43
sliding_window_modexp(7, 12, 1000, 4) = 201
```

---

## How the evaluation checks the implementation constraints

Besides the functional cases, the evaluation also checks that you **really wrote the required algorithm** rather than calling a library or taking a shortcut:

- **Import whitelist**: importing any module is **not allowed** in this problem.
- **No dunder channels**: no `__xxx__` attribute may be accessed (`int.__pow__`, say).
- **No reflective lookup**: `getattr` / `eval` / `exec` / `__import__` / `globals` / `vars` / `locals` must not be used.
- **Aliasing does not help**: renamings such as `shortcut = pow` or `from x import y as z` will not evade the check.
- **Dead code does not count**: a call written inside `if False:` or otherwise never reached does not count as "having implemented the algorithm".
- **Work check**: the evaluation counts the lines executed: both the odd-power precomputation and the window scan must really happen.

---
