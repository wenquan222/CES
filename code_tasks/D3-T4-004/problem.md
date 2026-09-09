# D3-T4-004: Karatsuba big-number multiplication

## Problem
Implement `karatsuba_mul(x: int, y: int) -> int`, computing the product of two non-negative big integers with the Karatsuba divide-and-conquer algorithm and returning x*y.

## Constraints
- x and y are both non-negative integers (Python int); **raise `ValueError` if x or y is negative**
- Computing with `x * y` directly is not allowed (only in the base case n < the threshold)
- The Karatsuba divide-and-conquer formulas must be used:
  - z2 = karatsuba_mul(x1, y1)
  - z0 = karatsuba_mul(x0, y0)
  - z1 = karatsuba_mul(x1+x0, y1+y0) - z2 - z0
  - result = z2 * 2^(2k) + z1 * 2^k + z0
- At each level of recursion n = max(x.bit_length(), y.bit_length()), k = n//2
- Base case: fall back to direct computation when x or y < n_threshold (1000, say)

## Input
- x: int, non-negative
- y: int, non-negative

## Output
- int: x*y

## Examples
```python
>>> karatsuba_mul(123456789, 987654321)
121932631112635269
>>> karatsuba_mul(0, 999)
0
>>> karatsuba_mul(1, 10**100) == 10**100
True
```

---

## How the evaluation checks the implementation constraints

Besides the functional cases, the evaluation also checks that you **really wrote the required algorithm** rather than calling a library or taking a shortcut:

- **Import whitelist**: importing any module is **not allowed** in this problem.
- **No dunder channels**: no `__xxx__` attribute may be accessed (`int.__pow__`, say).
- **No reflective lookup**: `getattr` / `eval` / `exec` / `__import__` / `globals` / `vars` / `locals` must not be used.
- **Aliasing does not help**: renamings such as `shortcut = pow` or `from x import y as z` will not evade the check.
- **Dead code does not count**: a call written inside `if False:` or otherwise never reached does not count as "having implemented the algorithm".
- **Work check**: the evaluation counts the lines executed and compares the ratio between a large and a small input:
  the work of divide-and-conquer must grow with the input size, whereas `return x * y` is constant.

---
