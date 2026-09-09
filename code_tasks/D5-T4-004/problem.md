# D5-T4-004: Leakage detection — NICV (normalized inter-class variance)

## Task

Implement NICV (Normalized Inter-Class Variance) leakage detection at each sample point. NICV is a side-channel leakage detection metric alongside TVLA that needs **neither the key nor a leakage model**, only a known class variable (a plaintext / ciphertext byte).

```text
For sample point j:
  NICV[j] = Var( E[L_j | X] ) / Var( L_j )
  numerator = the variance of the "conditional means" grouped by the class
              variable X (the between-group variance, weighted by group frequency)
  denominator = the total variance of all trace values at that point
The value lies in [0,1]; the larger it is, the stronger the leakage.
```

---

## Function signature

```python
def compute_nicv(traces, labels):
    """
    Args:
        traces: list[list[float]], N traces of M sample points each (equal length)
        labels: list[int] of length N, the class variable value of each trace
    Returns:
        list[float] of length M, each point's NICV ∈ [0,1]
    """
```

---

## Constraints

1. **numpy / scipy must not be used**; implement the grouping, means and variances yourself.
2. The between-group variance is weighted **by group frequency**: `Var(E[L|X]) = Σ_c (n_c/N)·(mean_c − mean_total)²`; the total variance is the population variance (dividing by N).
3. When the total variance at some sample point is 0, that point's NICV is recorded as `0.0` (avoiding division by zero).
4. Exceptions (`ValueError`): traces/labels empty / traces and labels having unequal lengths / traces of unequal length / traces with 0 points.
5. Return `list[float]` with each point ∈ `[0,1]`; deterministic.

---

## Examples

```python
# Perfect leakage: within-group variance 0, between-group = total variance
compute_nicv([[0.0],[0.0],[10.0],[10.0]], [0,0,1,1])   # [1.0]

# Independent of the label (equal group means) → no leakage
compute_nicv([[1.0],[5.0],[1.0],[5.0]], [0,0,1,1])     # [0.0]

# Partial leakage
compute_nicv([[1.0],[3.0],[7.0],[9.0]], [0,0,1,1])     # [0.9]
```

---

## Background

NICV was proposed by Bhasin et al. in 2014 and is a powerful tool for the D5 evaluator:

- **Lightweight**: whereas SNR requires "signal" and "noise" to be modelled separately, NICV needs only grouping by the known plaintext / ciphertext, with numerator and denominator each a single variance computation.
- **The upper bound property**: `NICV ≥ ρ²` (ρ being the correlation coefficient of any linear attack). So `NICV[j]=0` immediately implies that the point does not leak to a linear attack — which makes NICV an efficient tool for "screening leakage points (POIs) a priori".
- **Division of labour with TVLA**: TVLA's t-test answers "whether the two groups differ" (a binary test whose t value grows with sample size); NICV gives a normalized continuous strength in `[0,1]`, better suited to **quantifying** leakage and ranking POIs.

Note that NICV is essentially the proportion of between-group variance (statistics' η², the "between / total" idea of the F test) and shares its origin with ANOVA.

---

## Testing

10 cases: ① perfect leakage = 1.0; ② a constant point with total variance 0 → 0.0; ③ independent of the label → 0; ④ partial leakage hand-computed = 0.9; ⑤ every point ∈[0,1]; ⑥ with several sample points the return length = M; ⑦ more than two classes; ⑧ length mismatch ValueError; ⑨ traces of unequal length / empty / 0 points ValueError; ⑩ determinism.

pass@1 pass rate ≥ 0.8.
