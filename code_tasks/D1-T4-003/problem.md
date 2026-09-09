# D1-T4-003 · The matching stage of a template attack

## Task

Implement the **matching stage** of a template attack: given one test trace and the profiled multivariate Gaussian templates of 256 intermediate value classes, return the log-likelihood under each hypothesis k.

```python
from typing import Dict, Tuple
import numpy as np

def template_attack_match(
    test_trace: np.ndarray,
    templates: Dict[int, Tuple[np.ndarray, np.ndarray]]
) -> np.ndarray:
    """
    The matching stage of a template attack. Match one test trace against the
    templates in a D-dimensional feature space.

    Args:
        test_trace: feature vector of shape (D,) (D points of interest already
            selected)
        templates: dict with key = intermediate value i (int, 0..255) and
            value = (mean_i, cov_i)
            - mean_i: mean vector of class i, shape (D,)
            - cov_i: covariance matrix of class i, shape (D, D)
            Note: cov_i may be ill-conditioned and must be regularized

    Returns:
        float64 array of shape (256,), the log-likelihood of each k
        log P(test_trace | template_k) ∝
            -0.5 * [ (test - μ_k)^T Σ_k^{-1} (test - μ_k) + log det Σ_k ]
        If k ∉ templates, that position returns -inf (or a very large negative
        number).
    """
```

## Application setting

The template attack is the **strongest** form of attack in SCA (where a profiling device is available). The original paper, Chari-Rao-Rohatgi CHES 2002, gives the two-stage modelling + matching flow:

- **Profiling stage**: on device 1 (with the key known), build a multivariate Gaussian N(μ_i, Σ_i) for each intermediate value class
- **Matching stage** (this problem): on device 2 (with the key unknown), compute the log-likelihood for each trace and return the argmax



## Numerical challenge

**The covariance matrix Σ_i is readily singular** (when the number of PoIs exceeds the number of samples in a single class). A common approach is to accumulate probabilities by Bayes' rule. Choudary-Kuhn CARDIS 2013 give the standard practice of "efficient template attacks":

1. **Tikhonov regularization**: Σ_i ← Σ_i + λI (λ ≈ 1e-6 × trace(Σ_i))
2. **Cholesky decomposition** + a numerically stable computation of the quadratic form (not calling `np.linalg.inv` directly)
3. **log-det** via `np.linalg.slogdet` rather than `log(det)` (avoiding overflow)

## Constraints

1. Either Tikhonov regularization or pooled covariance **must** be used to handle an ill-conditioned Σ
2. The log-det **must** be computed with `np.linalg.slogdet` or Cholesky (`log(np.linalg.det(...))` is not allowed)
3. Numerical stability: the log-likelihood must cope with a high-dimensional setting of D=100
4. Performance: with D=50 and 256 templates, matching 1 test trace should take < 1 second (the graded test uses 1 s to absorb machine-to-machine variation)
5. A missing class (k ∉ templates) returns `-np.inf` (or a large negative number such as `-1e18`)
6. `scipy.stats.multivariate_normal.logpdf` must not be called (you must implement it yourself)

## Test cases

10 tests cover:

1. **Shape**: the output shape == `(256,)`
2. **Correctness**: on synthetic data (with the true k=0x42 known), the argmax should equal 0x42
3. **A missing class**: k=200 is not in templates, and the output [200] should be -inf or a large negative number
4. **Tolerance of a singular covariance**: no error when Σ_i is rank-deficient
5. **No numerical overflow**: at the large dimension D=100 the log-det does not return NaN/Inf
6. **Few classes (only K=2)**: works normally
7. **dtype compatibility**: accepts float32 / float64 templates
8. **Performance**: D=50, K=256, matching a single trace < 1s
9. **Determinism**: two calls on the same input give exactly the same result
10. **Monotonicity of the log-likelihood**: making the test trace more similar to the correct template should raise the log-likelihood

## Scoring

- Main metric: task_success (0 or 1 for the whole task) — 1 only if no blocking failure occurs and every functional case passes; process and performance cases are excluded from the functional set but block on failure, and the pass-rate threshold above is a diagnostic reference only
- Secondary metric: pass@1 (all cases passed = 1, otherwise = 0)
- Automatic scoring: from the recorded per-case outcomes; the pass rate is diagnostic