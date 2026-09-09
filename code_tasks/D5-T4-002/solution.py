# -*- coding: utf-8 -*-
"""
D5-T4-002 solution: min-entropy estimation.

Min-entropy, not Shannon entropy, is the gold standard for assessing cryptographic
randomness -- it measures the worst case, namely how hard it is for an attacker to
guess the most likely sample value:

    H_min = -log2( max_i p_i )

where p_i is the empirical frequency of the i-th value in the sample. H_min <= H_shannon always holds.
A 160-bit entropy target needs ceil(160 / H_min) samples at H_min bits per sample.

Source: NIST SP 800-90B (Recommendation for the Entropy Sources Used for
Random Bit Generation); 《密码工程》(Cryptographic Engineering, in Chinese) Ch.12.
"""
import math
from collections import Counter


def min_entropy(samples):
    """
    Compute the empirical min-entropy of a sample sequence, in bits per sample.

    Args:
        samples: an iterable of discrete samples (elements must be hashable, e.g. int / str / bytes)

    Returns:
        float, H_min = -log2(max_i p_i), in bits per sample
        - all identical -> 0.0
        - k values uniformly distributed -> log2(k)

    Raises:
        ValueError: samples is empty
    """
    seq = list(samples)
    if len(seq) == 0:
        raise ValueError("samples must not be empty")
    n = len(seq)
    counts = Counter(seq)
    max_p = max(c / n for c in counts.values())
    return -math.log2(max_p)
