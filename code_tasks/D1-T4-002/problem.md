# D1-T4-002 · SNR computation (point-of-interest selection)

## Task

Implement a Python function that, given N power traces (T samples each) and the N corresponding intermediate values (discrete classes), computes the **Signal-to-Noise Ratio (SNR)** at each time point:

```python
def compute_snr(traces: np.ndarray, intermediate_values: np.ndarray) -> np.ndarray:
    """
    Compute the point-wise SNR using the standard definition in SCA.

    SNR(t) = Var( E[ L_t | V ] ) / E[ Var( L_t | V ) ]
    where:
      - numerator: group by V, take each group's mean at time t, and take the
        variance of those group means (the signal variance)
      - denominator: take each group's variance at time t and average over all
        groups (the mean noise variance)

    Args:
        traces: float array of shape (N, T): N traces of T samples each
        intermediate_values: integer array of shape (N,) (intermediate value
            classes such as 0..255)

    Returns:
        float array of shape (T,), the SNR at each time point;
        classes with fewer than 2 samples are to be skipped (they do not enter
        the variance estimate).
    """
```

## Application setting

SNR is the standard statistic for **point-of-interest selection** (PoI selection) in SCA. Mangard *Power Analysis Attacks* gives the formula:

$$
\text{SNR}(t) = \frac{\text{Var}_V \left( \mathbb{E}[L_t \mid V] \right)}{\mathbb{E}_V \left( \text{Var}[L_t \mid V] \right)}
$$

- The numerator characterizes "the difference in power consumption caused by different intermediate values", that is the **signal**
- The denominator characterizes "the fluctuation in power consumption for the same intermediate value", that is the **noise**
- A high-SNR time point = a point of strong leakage, to be taken as a PoI

A typical engineering practice: among 1000 candidate time points, take the top-10 by SNR for CPA or a template attack.

## Constraints

1. **No for-loop over the N traces** (numpy vectorization required); but a for-loop over the classes (about 256 of them) is allowed on the outside
2. The input `intermediate_values` has shape `(N,)` and is integer; there are at most 256 classes (as for an AES S-box output)
3. Classes with fewer than 2 samples must be **skipped** (they cannot contribute to the variance estimate, or the numerics become singular)
4. For a time point with an all-zero denominator (every class variance being 0): return `0` (not NaN or Inf)
5. Numeric type: return a `float64` array

## Test cases

13 tests cover:
1. **Shape**: the output shape == `(T,)`
2. **Correctness**: on a synthetic dataset (with known SNR) the output differs from the analytic value by < 1%
3. **Classes with fewer than 2 samples**: the result must contain no NaN/Inf
4. **A single class**: the numerator is identically 0 and the output is all 0
5. **256 classes (worst case)**: performance < 5 seconds (N=5000, T=1000)
6. **Locating the leakage point**: with the true leakage at t=500 in the synthetic data, the output argmax should be 500
7. **dtype compatibility**: accepts int8 / int32 / uint8 intermediate values
8. **A large trace count (N=50000)**: within 10 seconds (the graded test uses 10 s to absorb machine-to-machine variation)
9. **Zero-variance time points** (traces identically 0 at some time point): return 0 without error
10. **Numerical stability**: when the noise (within-group variance) is 0 at every time point, return `0` throughout per constraint 4, never NaN/Inf and never an error
11. **A hand-computed small matrix**: exact point-wise values on a 6×2 example
12. **Comparison with an independent implementation**: point-wise agreement on a random matrix with different noise levels per class
13. **Separation of leakage and non-leakage points**: the SNR at a strong leakage point is appreciably higher than at a pure noise point

> Whether the variance uses ddof=0 or ddof=1 is not prescribed; both conventions are accepted (the numeric cases allow all four combinations).

## Scoring

- Main metric: task_success (0 or 1 for the whole task) — 1 only if no blocking failure occurs and every functional case passes; process and performance cases are excluded from the functional set but block on failure, and the pass-rate threshold above is a diagnostic reference only
- Secondary metric: pass@1 (all cases passed = 1, otherwise = 0)
- Automatic scoring: from the recorded per-case outcomes; the pass rate is diagnostic