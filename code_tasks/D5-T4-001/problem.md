# D5-T4-001: TVLA first-order Welch t-test leakage detection

## Task

Implement the core computation of TVLA (Test Vector Leakage Assessment): for the two sets of power traces, the **fixed group** and the **random group**, run an **unpaired, unequal-variance Welch t-test** at each time point, output the t trace and mark the leakage points.

```text
For sample point j:
    t[j] = (μ_f - μ_r) / sqrt( s_f²/n_f + s_r²/n_r )

where μ_f, s_f², n_f are the mean, the unbiased sample variance and the trace
count of the fixed group at that point;
     μ_r, s_r², n_r are the corresponding quantities of the random group.
|t[j]| ≥ 4.5 → point j is judged to have first-order side-channel leakage
(corresponding to a two-sided p < 1e-5).
```

---

## Function signature

```python
def compute_tvla(fixed_traces, random_traces):
    """
    A first-order Welch t-test at each time point.

    Args:
        fixed_traces:  list[list[float]], n_f traces × L points
        random_traces: list[list[float]], n_r traces × L points

    Returns:
        (t_values, leak_points)
        t_values:    list[float] of length L, the Welch t value at each point
        leak_points: list[int], the indices of the time points with |t| ≥ 4.5
            (ascending)
    """
```

---

## Constraints

1. **The Welch formula must be implemented yourself**; ready-made statistics/array libraries such as `scipy.stats.ttest_ind` and `numpy` must not be called
2. The variance uses the **unbiased estimate** (dividing by n−1, that is ddof=1)
3. **Unequal variances**: the two groups' variances are computed separately (Welch, not the pooled-variance Student t-test)
4. Support **unequal trace counts in the two groups** (n_f ≠ n_r)
5. The threshold constant `THRESHOLD = 4.5`
6. Exceptions (raising `ValueError`): either group empty / 0 sample points / inconsistent trace lengths within a group / the sample point counts L of the two groups inconsistent / either group having fewer than 2 traces (the variance being inestimable)
7. When both groups' variances are 0 at some point (a zero denominator), record t as 0.0
8. Determinism: the same input returns the same result

---

## Examples

```python
# Two groups with the same distribution → no leakage
fixed  = [[0, 10], [1, 11]] * 25
random = [[0, 10], [1, 11]] * 25
t_values, leak = compute_tvla(fixed, random)
# leak == [], all |t| < 4.5

# A large difference of means → leakage detected
fixed  = [[0, 0], [1, 1]] * 50      # mean 0.5
random = [[100, 100], [101, 101]] * 50  # mean 100.5
t_values, leak = compute_tvla(fixed, random)
# leak == [0, 1], |t| ≥ 4.5 at both points
```

---

## Background

TVLA is the core metric of the DPA leakage detection step in ISO/IEC 17825:2024. The fixed-vs-random split has **the greatest statistical power** of all splits (the variance of the secret intermediate value being 0 in the fixed group and greatest in the random group). This problem tests only first-order TVLA — note that |t|<4.5 **cannot** prove an implementation secure (being independent at each point, it cannot detect joint multi-point leakage).

---

## Testing

10 cases cover: ① the threshold constant; ② the return length; ③ no leakage under the same distribution; ④ detection of strong leakage; ⑤ a hand-computed comparison against the Welch formula; ⑥ unequal sample counts in the two groups; ⑦ correct leak_points indices (mixed points); ⑧ empty input ValueError; ⑨ a single trace ValueError; ⑩ inconsistent lengths ValueError + determinism.

pass@1 pass rate ≥ 0.8.
