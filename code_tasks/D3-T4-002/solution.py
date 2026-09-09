# -*- coding: utf-8 -*-
"""
D3-T4-002 solution: RSA modular exponentiation, implemented by hand (square-and-multiply, left to right).
《密码工程》(Cryptographic Engineering, in Chinese) Ch.4 §3.
"""


def modexp_square_multiply(x: int, d: int, N: int) -> int:
    """Modular exponentiation implemented by hand, computing x^d mod N (this reference uses square-and-multiply, left to right)."""
    if not isinstance(N, int) or N < 2:
        raise ValueError(f"N must be int >= 2, got {N}")
    if not isinstance(d, int) or d < 0:
        raise ValueError(f"d must be int >= 0, got {d}")

    # Boundary cases
    if d == 0:
        return 1
    x = x % N  # reduce first
    if x == 0:
        return 0

    A = 1
    # Walk d from the most significant bit down to the least
    for j in range(d.bit_length() - 1, -1, -1):
        A = (A * A) % N
        if (d >> j) & 1:
            A = (A * x) % N
    return A
