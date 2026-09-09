# -*- coding: utf-8 -*-
"""
D5-T4-004 solution: point-wise leakage detection by NICV (normalized inter-class variance).

NICV is a leakage-detection metric alongside TVLA (Bhasin et al. 2014):
    NICV[j] = Var( E[L_j | X] ) / Var( L_j )
where L_j is the value of every trace at sample point j and X is the known class
variable (a sensitive intermediate value such as a plaintext or ciphertext byte). The
numerator is the variance of the conditional means grouped by X, weighted by group
frequency (the between-group variance); the denominator is the total variance at that point.

Key properties:
    - NICV lies in [0, 1]; the larger it is the stronger the leakage;
    - it needs only the known plaintext/ciphertext (the class variable), no key and no leakage model;
    - NICV >= rho^2 (an upper bound on the squared correlation of any linear attack), so NICV=0 implies no linear attack works.

Source: Bhasin, Danger, Guilley, Najm, "NICV: Normalized Inter-Class Variance
for Detection of Side-Channel Leakage", 2014; 《密码工程》(Cryptographic Engineering, in Chinese), the side-channel assessment chapter.
"""


def compute_nicv(traces, labels):
    """
    Compute the NICV at each sample point.

    Args:
        traces: list[list[float]], N traces of M sample points each (all the same length)
        labels: list[int] of length N, the class-variable value for each trace

    Returns:
        list[float] of length M, the NICV in [0,1] at each sample point
        (where the total variance at a point is 0, its NICV is recorded as 0.0)

    Raises:
        ValueError: traces or labels empty / the two of unequal length / ragged traces / zero sample points
    """
    if not traces or not labels:
        raise ValueError("traces and labels must not be empty")
    if len(traces) != len(labels):
        raise ValueError("traces and labels must have the same length")
    n = len(traces)
    m = len(traces[0])
    if m == 0:
        raise ValueError("a trace must have a non-zero number of sample points")
    for t in traces:
        if len(t) != m:
            raise ValueError("all traces must have the same length")

    nicv = []
    for j in range(m):
        col = [traces[i][j] for i in range(n)]
        total_mean = sum(col) / n
        total_var = sum((x - total_mean) ** 2 for x in col) / n
        if total_var == 0.0:
            nicv.append(0.0)
            continue
        groups = {}
        for i in range(n):
            groups.setdefault(labels[i], []).append(col[i])
        between = 0.0
        for vals in groups.values():
            nc = len(vals)
            mc = sum(vals) / nc
            between += (nc / n) * (mc - total_mean) ** 2
        nicv.append(between / total_var)
    return nicv
