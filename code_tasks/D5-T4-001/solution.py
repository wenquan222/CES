# -*- coding: utf-8 -*-
"""
D5-T4-001 solution: TVLA first-order Welch's t-test leakage detection.

TVLA (Test Vector Leakage Assessment) runs an unpaired, unequal-variance Welch
t-test between the fixed group and the random group at each time point:

    t = (μ_f - μ_r) / sqrt( s_f²/n_f + s_r²/n_r )

|t| >= 4.5 declares first-order side-channel leakage at that point (two-sided p < 1e-5).

Source: Goodwill-Jun-Jaffe-Rohatgi, A Testing Methodology for Side-Channel
Resistance Validation, NIST NIAP 2011; Schneider-Moradi, Leakage Assessment
Methodology, CHES 2015; ISO/IEC 17825:2024.
"""
import math

THRESHOLD = 4.5 # the standard TVLA threshold (large-sample normal approximation of two-sided p < 1e-5)


def compute_tvla(fixed_traces, random_traces):
    """
    Run a point-wise first-order Welch t-test between the two trace groups.

    Args:
        fixed_traces: list[list[float]], the fixed group, n_f traces x L sample points
        random_traces: list[list[float]], the random group, n_r traces x L sample points
                       Both groups must have the same L, and every trace within a group must be the same length

    Returns:
        (t_values, leak_points)
        t_values: list[float] of length L, the Welch t value at each time point
        leak_points: list[int], the indices where |t| >= 4.5, in ascending order

    Raises:
        ValueError: either group empty / zero sample points / inconsistent lengths within a group /
                    either group with fewer than 2 traces (variance cannot be estimated) / the two groups differing in L
    """
    if not fixed_traces or not random_traces:
        raise ValueError("fixed_traces and random_traces must not be empty")

    n_f = len(fixed_traces)
    n_r = len(random_traces)
    if n_f < 2 or n_r < 2:
        raise ValueError("each group needs at least 2 traces to estimate the variance")

    L = len(fixed_traces[0])
    if L == 0:
        raise ValueError("a trace must have at least 1 sample point")
    for tr in fixed_traces:
        if len(tr) != L:
            raise ValueError("all traces in the fixed group must have the same length")
    for tr in random_traces:
        if len(tr) != L:
            raise ValueError("the random group must have the same length as the fixed group")

    t_values = []
    leak_points = []
    for j in range(L):
        fcol = [fixed_traces[i][j] for i in range(n_f)]
        rcol = [random_traces[i][j] for i in range(n_r)]
        mf = sum(fcol) / n_f
        mr = sum(rcol) / n_r
        # Unbiased sample variance (ddof = 1)
        vf = sum((x - mf) ** 2 for x in fcol) / (n_f - 1)
        vr = sum((x - mr) ** 2 for x in rcol) / (n_r - 1)
        denom = math.sqrt(vf / n_f + vr / n_r)
        if denom == 0.0:
            t = 0.0
        else:
            t = (mf - mr) / denom
        t_values.append(t)
        if abs(t) >= THRESHOLD:
            leak_points.append(j)
    return t_values, leak_points
