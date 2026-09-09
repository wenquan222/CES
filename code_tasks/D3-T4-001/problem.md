# D3-T4-001: Constant-time conditional selection ct_select

## Task

Implement the Python function `ct_select`, requiring **no secret-dependent control flow or memory access** (that is: no branching on the value of `cond`, and no indexing a sequence with `cond`).

> Note: at the CPython level no true constant-time guarantee is possible (interpreter scheduling, object caching and the big-integer implementation all introduce value-dependent time differences), so what this problem examines is the **branch-free property at the algorithmic level** rather than measurable constant time. The evaluation judges by the statically checkable rules below.


```python
def ct_select(cond: int, a: int, b: int) -> int:
    """
    Constant-time conditional selection: return a when cond=1, b when cond=0.

    Args:
        cond: int, must be 0 or 1
        a:    int, a 32-bit unsigned integer (0 ≤ a < 2^32)
        b:    int, a 32-bit unsigned integer (0 ≤ b < 2^32)

    Returns:
        a 32-bit unsigned integer (cond=1 → a; cond=0 → b)
    """
```

## Constraints

1. **No conditional control**: no `if`, no ternary `?:`, no `while`/`for` with secret-dependent loops
2. **No indexing with cond**: no `[cond]` access, no `[a, b][cond]`
3. Allowed only: arithmetic (`+`, `-`, `*`), bitwise operations (`&`, `|`, `^`, `~`, `<<`, `>>`), assignment
4. Input validation: raise `ValueError` if cond is neither 0 nor 1 (this validation `if` does not count as violating constraint 1)

## Hint

Use **bitmask arithmetic** — turn cond ∈ {0, 1} into a mask ∈ {0x00000000, 0xFFFFFFFF},
then use `(a & mask) | (b & ~mask)`. A hint, not the complete solution.

---

## How the evaluation checks the implementation constraints

Besides the functional cases, the evaluation also checks that you **really wrote the required algorithm** rather than calling a library or taking a shortcut:

- **Import whitelist**: importing any module is **not allowed** in this problem.
- **No dunder channels**: no `__xxx__` attribute may be accessed (`int.__pow__`, say).
- **No reflective lookup**: `getattr` / `eval` / `exec` / `__import__` / `globals` / `vars` / `locals` must not be used.
- **Aliasing does not help**: renamings such as `shortcut = pow` or `from x import y as z` will not evade the check.
- **Dead code does not count**: a call written inside `if False:` or otherwise never reached does not count as "having implemented the algorithm".
- The ban on branching applies to the **whole submitted file**, including helper functions and lambdas you define yourself; `match`/`case` counts as a branch too.
  The only exemption is input validation of the form `if <invalid input>: raise ...`.
- Indexing a sequence with the conditional value (`(b, a)[cond]`, say) is likewise **not allowed** — that is a memory access whose address is decided by a secret, and it fails just as writing a branch does.
