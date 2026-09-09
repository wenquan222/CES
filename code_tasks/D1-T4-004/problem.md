# D1-T4-004: NICV point-of-interest computation

## Task

Implement the function `compute_nicv(traces, intermediate_values, num_bins=100)`, which computes the NICV (Normalized Inter-Class Variance) at each time point.

## Background

NICV is a method of point-of-interest (PoI) selection, defined as NICV[t] = Var(E[L[t]|V]) / Var(L[t]), where L[t] is the observed trace value at time point t and V is the intermediate value (an S-box output, say).

## Parameters

- `traces`: np.ndarray of shape (N, T), N traces of T time points each
- `intermediate_values`: np.ndarray of shape (N,), the intermediate value (0-255) corresponding to each trace
- `num_bins`: int, default 100, **a reserved parameter that the current implementation does not use** (NICV groups naturally by the values of `intermediate_values` and needs no binning of the trace amplitudes); it is kept only for interface compatibility

## Returns

- np.ndarray of shape (T,), the NICV value at each time point, in the range [0, 1]

## Requirements

- Use numpy vectorized computation
- The NICV values should lie in the range [0, 1]

Python standard-library modules are allowed, as is NumPy; no other third-party package may be used.
