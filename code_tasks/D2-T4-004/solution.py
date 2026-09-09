# -*- coding: utf-8 -*-
"""
D2-T4-005 solution: key recovery by fault sensitivity analysis (FSA).

The core observation of FSA (Li-Sakiyama-Gomisawa et al., CHES 2010):
the critical-path delay of a hardware S-box is roughly linear in the Hamming weight
of its input. The attacker narrows the clock glitch step by step; the critical glitch
width at which the error just appears is the critical-path delay (the fault
sensitivity). The round-1 S-box input is plaintext XOR key, so the key distinguisher is:

    for each key-byte guess k, compute the Pearson correlation between HW(plaintext XOR k)
    and the fault-sensitivity sequence; the k with the largest correlation (positive --
    the critical-path delay grows monotonically with input HW) is the correct key byte.
    Note: use the signed maximum, not |correlation|, or k and k XOR 0xFF become
    indistinguishable under the HW model (their HWs are complementary and the
    correlations exactly opposite).

Note: structurally similar to power CPA, but the data are critical fault glitch
widths / critical-path delays rather than power -- a hybrid of fault attack and
side-channel correlation analysis.

Source: Li, Sakiyama, Gomisawa, Fukunaga, Takahashi, Ohta,
Fault Sensitivity Analysis, CHES 2010.
"""


def _hw(x):
    """Hamming weight (the number of 1 bits in the byte)."""
    return bin(x & 0xFF).count("1")


def _pearson(xs, ys):
    """Pearson correlation coefficient; returns 0.0 when either variance is 0."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return 0.0
    return cov / ((vx ** 0.5) * (vy ** 0.5))


def fsa_recover(plaintexts, sensitivities):
    """
    Recover one key byte from fault sensitivities (the FSA key distinguisher).

    Args:
        plaintexts: list[int], the plaintext byte for each injection (0..255)
        sensitivities: list[float], the corresponding fault sensitivities (critical-path delay / critical glitch width)

    Returns:
        int in 0..255, the key byte maximizing corr(HW(p^k), sensitivities) (positive correlation)

    Raises:
        ValueError: the two sequences differ in length / fewer than 2 samples / a plaintext byte out of range
    """
    if len(plaintexts) != len(sensitivities):
        raise ValueError("plaintexts and sensitivities must have the same length")
    if len(plaintexts) < 2:
        raise ValueError("at least 2 samples are required")
    for p in plaintexts:
        if not isinstance(p, int) or not (0 <= p <= 255):
            raise ValueError("a plaintext byte must be an integer in [0,255]")

    best_k = 0
    best_corr = -2.0 # a correlation lies in [-1,1], so -2 guarantees the first update
    for k in range(256):
        hws = [_hw(p ^ k) for p in plaintexts]
        r = _pearson(hws, sensitivities) # signed: in FSA the delay grows monotonically with HW (positive correlation)
        if r > best_corr:
            best_corr = r
            best_k = k
    return best_k
