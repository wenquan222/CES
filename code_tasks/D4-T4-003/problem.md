# D4-T4-003: A share-wise implementation of XOR

## Problem statement

In Boolean masking schemes, the linear operations (XOR, ShiftRows, MixColumns) are naturally mask-friendly — it suffices to operate on each share independently.
Implement the function `xor_sharewise`, performing a byte-wise XOR of two byte strings of equal length. This is one of the most basic components of a masked AES implementation — used for linear operations on masked data.

## Function signature

```python
def xor_sharewise(a: bytes, b: bytes) -> bytes:
    """
    Take the byte-wise XOR (bitwise exclusive or) of two byte strings of equal length.

    In the context of a masking scheme:
    - if a and b are two shares respectively (share_a = x ⊕ m_x, share_b = y ⊕ m_y)
    - then xor_sharewise(share_a, share_b) = (x ⊕ y) ⊕ (m_x ⊕ m_y)
    - that is, the resulting share is consistent with the XOR of the original secrets

    Args:
        a: a byte string
        b: a byte string (which must be the same length as a)

    Returns:
        the byte-wise XOR result, the same length as the inputs

    Raise ValueError if a and b differ in length.
    """
```

## Constraints

1. The inputs must be the same length, or raise `ValueError`
2. Byte-wise XOR, without using an external cryptographic library
3. A deterministic function (the same input always giving the same output)

Python standard-library modules are allowed; no external cryptographic library may be used.
