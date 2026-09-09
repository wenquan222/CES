# -*- coding: utf-8 -*-
"""
D1-T4-002 solution: SNR (signal-to-noise ratio) point-of-interest selection.
Formula: SNR(t) = Var_V( E[L_t | V] ) / E_V( Var[L_t | V] )
"""
import numpy as np


def compute_snr(traces: np.ndarray, intermediate_values: np.ndarray) -> np.ndarray:
    """
    Compute the point-wise SNR using the standard definition in SCA.

    Args:
        traces: shape (N, T) float
        intermediate_values: shape (N,) int

    Returns:
        shape (T,) float64
    """
    traces = np.asarray(traces, dtype=np.float64)
    iv = np.asarray(intermediate_values).astype(np.int64)
    N, T = traces.shape

    unique_v = np.unique(iv)
    class_means = []         # per-class mean (T,)
    class_vars = []          # per-class variance (T,)

    for v in unique_v:
        mask = (iv == v)
        n_v = mask.sum()
        if n_v < 2:
            continue  # fewer than 2 samples, skip
        sub = traces[mask]                    # (n_v, T)
        class_means.append(sub.mean(axis=0))  # (T,)
        # Either ddof=1 (unbiased) or ddof=0 is acceptable; ddof=1 is the convention here
        class_vars.append(sub.var(axis=0, ddof=1))

    if len(class_means) < 2:
        # At least 2 classes are needed for the signal variance; otherwise SNR is undefined -> return all zeros
        return np.zeros(T, dtype=np.float64)

    cm = np.stack(class_means, axis=0)        # (K, T)
    cv = np.stack(class_vars, axis=0)         # (K, T)

    signal_var = cm.var(axis=0, ddof=1)       # (T,)  Var over classes of means
    noise_var = cv.mean(axis=0)               # (T,)  E over classes of vars

    # Numeric guard: return 0 when the denominator is 0
    snr = np.zeros(T, dtype=np.float64)
    valid = noise_var > 1e-300
    snr[valid] = signal_var[valid] / noise_var[valid]

    # Handle inf / nan
    snr = np.nan_to_num(snr, nan=0.0, posinf=np.finfo(np.float64).max, neginf=0.0)
    return snr
