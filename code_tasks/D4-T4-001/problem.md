# D4-T4-001: Implementing an infection fault countermeasure

## Task

Implement the Python function `infect_or_pass`, realizing the **infection countermeasure** of AES fault protection:

```python
def infect_or_pass(state_a: bytes, state_b: bytes, mask: bytes) -> bytes:
    """
    The core operation of the infection fault countermeasure.

    Perform an "identity comparison + pollution" on two AES intermediate states
    (state_a, state_b) that ought to be equal:
    - if state_a == state_b (no fault injected), return state_a
    - if state_a != state_b (a fault detected), return (state_a XOR mask)
      -- mask being an externally supplied random byte string that makes the
      polluted output look no different from a normal one

    Args:
        state_a: a 16-byte AES state
        state_b: a 16-byte AES state (which should equal state_a)
        mask:    a 16-byte random pollution mask

    Returns:
        16 bytes
            - state_a, if state_a == state_b
            - state_a XOR mask, if state_a != state_b

    Raise ValueError if any input is not 16 bytes.
    """
```

## Security requirements

1. The comparison + pollution **must be constant time** — the execution time must not reveal whether a fault occurred
2. Secret-dependent control flow such as `if` / `else` / `==` is **not allowed** (input length validation excepted)
3. Realize "branch-free conditional selection" with bitmask + XOR

## Hint

The idea: compute (state_a XOR state_b) byte by byte → construct an "equal or not" bitmask arithmetically → use the mask to select whether to pollute.

---

## How the evaluation checks the implementation constraints

Besides the functional cases, the evaluation also checks that you **really wrote the required algorithm** rather than calling a library or taking a shortcut:

- **Import whitelist**: importing any module is **not allowed** in this problem.
- **No dunder channels**: no `__xxx__` attribute may be accessed (`int.__pow__`, say).
- **No reflective lookup**: `getattr` / `eval` / `exec` / `__import__` / `globals` / `vars` / `locals` must not be used.
- **Aliasing does not help**: renamings such as `shortcut = pow` or `from x import y as z` will not evade the check.
- **Dead code does not count**: a call written inside `if False:` or otherwise never reached does not count as "having implemented the algorithm".
- The ban on branches and equality comparisons (`==` / `!=`) applies to the **whole submitted file**, including helper functions and lambdas, and `match`/`case` counts as a branch too. The only exemption is input validation of the form `if <invalid input>: raise ...`.

---
