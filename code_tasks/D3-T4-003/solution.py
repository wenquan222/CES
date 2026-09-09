# -*- coding: utf-8 -*-
"""
D3-T4-003 solution: Montgomery modular multiplication.
《密码工程》(Cryptographic Engineering, in Chinese) Ch.4 §4:
  Fact 1: gcd(N, R) = 1, N' = -N^{-1} mod R
  if U = T*N' mod R, then (T + U*N) / R = T*R^{-1} mod N
"""


def _redc(T: int, N: int, N_prime: int, R: int) -> int:
    """One Montgomery reduction (REDC).

    U = (T · N') mod R
    t = (T + U*N) / R          -- this division is always exact; that is what N' is for
    subtract one more N when t >= N
    returns t = T*R^{-1} (mod N) with 0 <= t < N
    """
    U = (T * N_prime) & (R - 1)          # R is a power of 2, so the modulus is a bit mask
    t = (T + U * N) >> (R.bit_length() - 1)
    if t >= N:
        t -= N
    return t


def montgomery_modmul(x: int, y: int, N: int, N_prime: int, R: int) -> int:
    """Montgomery modular multiplication: x * y * R^{-1} mod N."""
    if not isinstance(N, int) or N <= 0 or N % 2 == 0:
        raise ValueError(f"N must be positive odd integer, got {N}")
    if not isinstance(R, int) or R <= N:
        raise ValueError(f"R must be > N, got R={R}, N={N}")
    if R & (R - 1) != 0:
        raise ValueError(f"R must be a power of 2, got {R}")

    return _redc((x % N) * (y % N), N, N_prime, R)
