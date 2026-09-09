# -*- coding: utf-8 -*-
"""
D5-T4-003 solution: the NIST SP 800-22 monobit (frequency) test.

The most basic randomness test in SP 800-22: it checks whether the counts of 0s and 1s across the sequence are close to balanced.
Principle (H0: the sequence is random):
    eps_i in {0,1}; let X_i = 2*eps_i - 1 in {-1,+1}
    Sn = Σ Xi, Sobs = |Sn| / sqrt(n)
    P-value = erfc( Sobs / sqrt(2) )
Decision: P-value >= alpha (=0.01) -> accept H0 (no departure from randomness found).

Note: this task requires erfc to be implemented by a numerical approximation
(math.erfc / scipy must not be called), to test command of the numerics underlying a
statistical test -- which is exactly what an RNG assessment tool rests on.

Source: NIST SP 800-22 Rev.1a §2.1 Frequency (Monobit) Test;
《密码工程》(Cryptographic Engineering, in Chinese) Ch.12, design and assessment of random number generators.
"""
from math import exp, sqrt


def _erfc(x):
    """A numerical approximation of the complementary error function erfc(x)
    (Numerical Recipes erfcc, fractional error < 1.2e-7). Uses only exp and basic
    arithmetic; does not rely on math.erfc or scipy."""
    z = abs(x)
    t = 1.0 / (1.0 + 0.5 * z)
    ans = t * exp(
        -z * z - 1.26551223
        + t * (1.00002368
        + t * (0.37409196
        + t * (0.09678418
        + t * (-0.18628806
        + t * (0.27886807
        + t * (-1.13520398
        + t * (1.48851587
        + t * (-0.82215223
        + t * 0.17087277)))))))))
    return ans if x >= 0.0 else 2.0 - ans


def monobit_frequency_test(bits):
    """
    The SP 800-22 monobit frequency test, returning a P-value.

    Args:
        bits: list[int], every element in {0, 1}
    Returns:
        float, P-value in [0, 1]; >= 0.01 means no departure from randomness was found

    Raises:
        ValueError: empty sequence / an element outside {0,1}
    """
    if not bits:
        raise ValueError("the bit sequence must not be empty")
    for b in bits:
        if b not in (0, 1):
            raise ValueError("the sequence may contain only 0 or 1")
    n = len(bits)
    s_n = sum(2 * b - 1 for b in bits)
    s_obs = abs(s_n) / sqrt(n)
    p_value = _erfc(s_obs / sqrt(2.0))
    # The numerical approximation may stray minutely out of range; clip to [0,1]
    if p_value < 0.0:
        p_value = 0.0
    elif p_value > 1.0:
        p_value = 1.0
    return p_value
