# -*- coding: utf-8 -*-
"""
D6-T4-001 solution: Shamir (t, n) threshold secret sharing.

The secret S is the constant term of a polynomial: f(x) = S + a1*x + ... + a_{t-1}*x^{t-1} (mod p).
Distribute n shares (i, f(i)) for i=1..n; x=0 is the secret itself and is not distributed.
Any t shares recover f(0)=S by Lagrange interpolation; fewer than t give no information at all.

Source: Shamir, How to Share a Secret, CACM 1979.
"""


def _inv(a, p):
    """Modular inverse (p prime, by Fermat's little theorem)."""
    return pow(a % p, p - 2, p)


def shamir_split(secret, t, n, prime, coeffs=None):
    """
    Split the secret into n shares under a (t, n) threshold.

    Args:
        secret: int, 0 <= secret < prime
        t: int, the recovery threshold (1 <= t <= n)
        n: int, the total number of shares
        prime: int, the prime modulus (must exceed both secret and n)
        coeffs: list[int], optional, the t-1 higher-order coefficients (for deterministic testing);
                this implementation requires them to be passed explicitly, to avoid irreproducible randomness

    Returns:
        list[(x, y)], n shares with x = 1..n

    Raises:
        ValueError: invalid t/n, secret out of range, wrong coeffs length, prime too small
    """
    if not (1 <= t <= n):
        raise ValueError("1 <= t <= n is required")
    if not (0 <= secret < prime):
        raise ValueError("secret must lie in [0, prime)")
    if prime <= n:
        raise ValueError("prime must exceed n so that x=1..n are pairwise incongruent")
    if coeffs is None:
        raise ValueError("this implementation needs coeffs (of length t-1) passed explicitly to stay deterministic")
    if len(coeffs) != t - 1:
        raise ValueError(f"coeffs must have length t-1={t - 1}")

    poly = [secret] + list(coeffs) # [a0=S, a1, ..., a_{t-1}]
    shares = []
    for i in range(1, n + 1):
        y = 0
        for power, c in enumerate(poly):
            y = (y + c * pow(i, power, prime)) % prime
        shares.append((i, y))
    return shares


def shamir_reconstruct(shares, prime):
    """
    Recover the secret f(0) from shares by Lagrange interpolation.

    Args:
        shares: list[(x, y)], at least one; the x values must be pairwise distinct
        prime: int, the prime modulus

    Returns:
        int, the recovered secret (= f(0) mod prime)

    Raises:
        ValueError: shares empty / duplicate x values
    """
    if not shares:
        raise ValueError("shares must not be empty")
    xs = [x for x, _ in shares]
    if len(set(xs)) != len(xs):
        raise ValueError("the x coordinates of the shares must be pairwise distinct")

    secret = 0
    for j, (xj, yj) in enumerate(shares):
        num = 1
        den = 1
        for m, (xm, _ym) in enumerate(shares):
            if m == j:
                continue
            num = (num * (-xm)) % prime
            den = (den * (xj - xm)) % prime
        lj = (num * _inv(den, prime)) % prime
        secret = (secret + yj * lj) % prime
    return secret % prime
