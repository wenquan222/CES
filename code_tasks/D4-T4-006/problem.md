# D4-T4-006: Parity check fault detection

## Problem statement

In fault protection, the parity check is one of the lightest error detection schemes: compute a 1-bit XOR checksum over the intermediate state and compare it with the expected parity. Implement the function `parity_check`, computing the parity bit of a byte string and comparing it in constant time.

## Function signature

```python
def parity_check(data: bytes, expected_parity: int) -> bool:
    """
    Compute the parity bit of the input byte string and compare it with the
    expected value.

    The parity algorithm:
    1. XOR-accumulate all the bytes → acc
    2. Take the least significant bit (LSB) of acc as the actual parity bit,
       actual_parity
    3. Compare actual_parity with expected_parity

    Security requirement (constant time):
    the comparison must not use an if/else branch to produce the return value --
    the result must be constructed with bit operations.
    Recommended: match = 1 - (actual ^ expected)  (an int of 0 or 1, cast to bool)

    Args:
        data: the byte string to check
        expected_parity: the expected parity value (0 or 1)

    Returns:
        True if the parity matches, False otherwise

    Raise ValueError if expected_parity is neither 0 nor 1.
    """
```

## Constraints

1. `expected_parity` may only be 0 or 1, or `ValueError`
2. A constant-time implementation — `if actual_parity == expected_parity: return True else: return False` is not allowed
3. No external cryptographic library is called
4. The parity bit of an empty byte string is 0
