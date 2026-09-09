# D4-T4-004: A TMR triple modular redundancy voter

## Problem statement

In fault protection, TMR (Triple Modular Redundancy) is the strongest hardware redundancy scheme: three independent circuits run the same operation in parallel and a 2-of-3 majority vote decides the final output. Even if one path outputs an error through fault injection or hardware damage, the other two still guarantee the correct result.

Implement the function `tmr_voter`, taking a byte-wise 2-of-3 majority vote over three byte strings of equal length.

## Function signature

```python
def tmr_voter(a: bytes, b: bytes, c: bytes) -> bytes:
    """
    A TMR (triple modular redundancy) voter: for three byte strings of equal
    length, take the majority value byte by byte (the value occurring >=2 times).

    Security requirement (constant time):
    - the voting logic must not use an if/else branch (avoiding secret-dependent
      control flow)
    - realize "take the majority" with bit operations:
      majority = (a & b) | (a & c) | (b & c)
    - the input bytes vote position by position in correspondence

    Args:
        a: a byte string (the output of circuit 1)
        b: a byte string (the output of circuit 2)
        c: a byte string (the output of circuit 3)

    Returns:
        the byte-wise 2-of-3 vote result, the same length as the inputs

    Raise ValueError if any input differs in length.
    """
```

## Constraints

1. The three inputs must be the same length, or raise `ValueError`
2. Take the byte-wise 2-of-3 majority value, **realized bitwise**: `majority = (a & b) | (a & c) | (b & c)`.
   Note that the two formulations agree exactly when "at least two of the three bytes are equal";   when all three bytes differ pairwise, "the value occurring ≥2 times" is undefined and   this problem is governed throughout by the bitwise majority formula above (which then gives a composite byte equal to none of the inputs,   this being exactly TMR's established behaviour when all three paths disagree).
3. **A constant-time implementation**: no `if`/`else` selection; use the bit operations `(a & b) | (a & c) | (b & c)`
4. No external cryptographic library is called
