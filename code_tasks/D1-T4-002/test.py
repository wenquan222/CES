# -*- coding: utf-8 -*-
"""
D1-T4-002 tests: compute_snr. 13 test cases.
Scoring: main metric = passed cases / total cases (continuous); secondary metric pass@1.
"""
import numpy as np
import pytest
import time


# Import path of the submitted implementation (replace with the module name)
from solution import compute_snr


# ── Numeric oracle ────────────────────────────────────────────────────
# Review round 8 pointed out that 8 of the original 10 cases only checked
# shape/dtype/no-NaN/runtime, so a wrong implementation returning all zeros of the
# right length passed 8/10 -- exactly the 0.8 line in the statement. The three
#
# cases below are independent numeric oracles aimed at "right shape, wrong numbers".
# The statement does NOT fix ddof=0 vs ddof=1 (the reference implementation says
# either is fine), so the oracle accepts all four combinations (signal/noise each
# ddof 0 or 1). Matching any one of them counts as correct -- a differing convention
# must not fail a correct implementation.
def _snr_reference(traces, iv, ddof_signal, ddof_noise):
    """An independent pure-Python loop implementation, sharing no code path with the vectorized one under test."""
    traces = np.asarray(traces, dtype=np.float64)
    iv = np.asarray(iv).astype(np.int64)
    N, T = traces.shape
    means, variances = [], []
    for v in np.unique(iv):
        rows = [i for i in range(N) if iv[i] == v]
        if len(rows) < 2:
            continue
        m, s = [0.0] * T, [0.0] * T
        for t in range(T):
            col = [float(traces[i][t]) for i in rows]
            mu = sum(col) / len(col)
            m[t] = mu
            s[t] = sum((c - mu) ** 2 for c in col) / (len(col) - ddof_noise)
        means.append(m)
        variances.append(s)
    out = np.zeros(T, dtype=np.float64)
    if len(means) < 2:
        return out
    K = len(means)
    for t in range(T):
        mu_t = sum(m[t] for m in means) / K
        sig = sum((m[t] - mu_t) ** 2 for m in means) / (K - ddof_signal)
        noi = sum(s[t] for s in variances) / K
        out[t] = sig / noi if noi > 1e-300 else 0.0
    return out


def _matches_any_convention(got, traces, iv, rtol=1e-7, atol=1e-10):
    got = np.asarray(got, dtype=np.float64)
    variants = []
    for ds in (0, 1):
        for dn in (0, 1):
            want = _snr_reference(traces, iv, ds, dn)
            variants.append(((ds, dn), want))
            if np.allclose(got, want, rtol=rtol, atol=atol):
                return True, None
    detail = "; ".join(
        f"ddof(signal={ds},noise={dn}) expects the first 4 points to be {np.round(w[:4], 6).tolist()}"
        for (ds, dn), w in variants)
    return False, f"actual first 4 points {np.round(got[:4], 6).tolist()}; under the four conventions {detail}"


@pytest.fixture
def synthetic_dataset():
    """
    Synthesize an N=5000, T=1000 trace set with HW leakage at the true leakage point t*=500.
    The intermediate value V is in {0..15} (the low 4 bits), so HW ranges over 0..4.
    """
    rng = np.random.RandomState(42)
    N, T = 5000, 1000
    iv = rng.randint(0, 16, size=N)
    hw = np.array([bin(i).count('1') for i in range(16)])[iv]  # (N,)
    traces = rng.randn(N, T) * 1.0           # noise sigma=1
    traces[:, 500] += hw.astype(float)       # inject HW leakage at t=500
    return traces, iv


# ============== 1. Shape ==============
def test_shape(synthetic_dataset):
    traces, iv = synthetic_dataset
    snr = compute_snr(traces, iv)
    assert snr.shape == (traces.shape[1],), f"wrong shape: {snr.shape}"
    assert snr.dtype == np.float64


# ============== 2. Correctness (peak at the true leakage point) ==============
def test_peak_at_leakage(synthetic_dataset):
    traces, iv = synthetic_dataset
    snr = compute_snr(traces, iv)
    peak = int(np.argmax(snr))
    assert abs(peak - 500) <= 2, f"the peak should be near t=500, actual t={peak}"


# ============== 3. Peak SNR of the right magnitude ==============
def test_peak_snr_magnitude(synthetic_dataset):
    """
    HW({0..15}) ranges over 0..4 with variance about 1.0; noise sigma^2=1. Theoretical SNR is about 1.
    """
    traces, iv = synthetic_dataset
    snr = compute_snr(traces, iv)
    peak_snr = snr.max()
    assert 0.3 < peak_snr < 5.0, f"peak SNR={peak_snr:.3f} is out of the plausible range"


# ============== 4. Classes with fewer than 2 samples are skipped ==============
def test_skip_small_class():
    rng = np.random.RandomState(0)
    N, T = 200, 50
    iv = rng.randint(0, 4, size=N)
    iv[0] = 99   # a single-sample class (must be skipped)
    traces = rng.randn(N, T)
    snr = compute_snr(traces, iv)
    assert snr.shape == (T,)
    assert not np.any(np.isnan(snr))
    assert not np.any(np.isinf(snr))


# ============== 5. A single class -> all zeros ==============
def test_single_class_zero():
    rng = np.random.RandomState(0)
    N, T = 100, 20
    iv = np.zeros(N, dtype=np.int64)
    traces = rng.randn(N, T)
    snr = compute_snr(traces, iv)
    assert np.allclose(snr, 0.0), "a single class must give an all-zero output"


# ============== 6. No error at time points with zero variance ==============
def test_zero_variance_point():
    rng = np.random.RandomState(0)
    N, T = 200, 30
    iv = rng.randint(0, 4, size=N)
    traces = rng.randn(N, T)
    traces[:, 10] = 0.0  # every trace is 0 at t=10
    snr = compute_snr(traces, iv)
    assert not np.any(np.isnan(snr))
    assert snr[10] == 0.0 or np.isfinite(snr[10])


# ============== 7. dtype compatibility ==============
def test_dtype_compat():
    rng = np.random.RandomState(0)
    traces = rng.randn(100, 20).astype(np.float32)
    iv_int8 = rng.randint(0, 8, size=100).astype(np.int8)
    traces[:, 4] += iv_int8.astype(np.float32)      # give t=4 genuine class-dependent leakage
    iv_uint8 = iv_int8.astype(np.uint8)

    snr1 = compute_snr(traces, iv_int8)
    snr2 = compute_snr(traces, iv_uint8)
    assert snr1.shape == snr2.shape
    assert np.allclose(snr1, snr2, atol=1e-6)
    # Two identical results do not prove correctness (all zeros are identical too), so also require the leakage point to be found
    assert int(np.argmax(snr1)) == 4, f"t=4 leaks clearly, yet the peak is at t={int(np.argmax(snr1))}"


# ============== 8. Performance with a large trace count ==============
def test_large_trace_count():
    rng = np.random.RandomState(0)
    N, T = 50000, 500
    iv = rng.randint(0, 256, size=N)
    traces = rng.randn(N, T)
    start = time.time()
    snr = compute_snr(traces, iv)
    elapsed = time.time() - start
    assert elapsed < 10.0, f"5e4 x 500 should take < 10s, actual {elapsed:.2f}s"
    assert snr.shape == (T,)


# ============== 9. Performance with 256 classes ==============
def test_256_classes_performance():
    rng = np.random.RandomState(0)
    N, T = 5000, 1000
    iv = rng.randint(0, 256, size=N)
    traces = rng.randn(N, T)
    start = time.time()
    snr = compute_snr(traces, iv)
    elapsed = time.time() - start
    assert elapsed < 5.0
    assert snr.shape == (T,)


# ============== 10. The extreme noise-free case ==============
def test_noiseless_case():
    """
    The traces within each class are identical (noise variance 0). SNR should be +Inf or a large value, but never NaN.
    """
    N, T = 100, 10
    iv = np.array([0]*50 + [1]*50)
    traces = np.zeros((N, T))
    traces[50:, 5] = 1.0   # class 1 has 1 at t=5
    snr = compute_snr(traces, iv)
    assert not np.any(np.isnan(snr))
    # t=5 should have a large SNR (infinite in theory)
    assert snr[5] > 100 or snr[5] == 0.0  # 0 means the implementation took the "guard hard when noise-free" path


# ============== 11. Numeric oracle: exact values on a hand-computed small matrix ==============
def test_exact_small_matrix():
    """A 6x2 hand-computed example. At t=0 the two class means are 2 and 8 with equal
    within-class variance; at t=1 everything is constant. Under the four ddof conventions
    the exact value at t=0 is 18 / 13.5 / 9 / 27 respectively, and t=1 is 0 in all cases."""
    traces = np.array([[1.0, 5.0], [2.0, 5.0], [3.0, 5.0],
                       [7.0, 5.0], [8.0, 5.0], [9.0, 5.0]])
    iv = np.array([0, 0, 0, 1, 1, 1])
    snr = compute_snr(traces, iv)
    assert snr.shape == (2,)
    ok, detail = _matches_any_convention(snr, traces, iv)
    assert ok, "the SNR on the hand-computed small matrix is wrong. " + (detail or "")
    assert snr[1] == pytest.approx(0.0, abs=1e-12), \
        f"every trace is constant 5 at t=1 so the within-class variance is 0; constraint 4 requires 0, actual {snr[1]}"


# ============== 12. Numeric oracle: point-wise comparison with an independent implementation ==============
def test_matches_independent_reference():
    """A random matrix whose noise level differs per class -- so the noise variance is
    not constant, and an implementation that computes only the numerator Var(class means)
    and hard-codes the denominator to 1 shows up here."""
    rng = np.random.RandomState(7)
    N, T = 240, 40
    iv = rng.randint(0, 6, size=N)
    traces = np.empty((N, T), dtype=np.float64)
    for i in range(N):
        traces[i] = rng.randn(T) * (0.5 + 0.3 * iv[i])
    traces[:, 7] += iv * 1.5          # only t=7 has class-dependent means
    snr = compute_snr(traces, iv)
    ok, detail = _matches_any_convention(snr, traces, iv)
    assert ok, "point-wise comparison with the independent implementation disagrees. " + (detail or "")


# ============== 13. Numeric oracle: leaking and non-leaking points must separate ==============
def test_leaking_vs_nonleaking_point():
    """t=0 has strongly class-dependent means and t=1 is pure noise. The SNR must
    separate the two clearly -- this does not depend on the ddof convention and passes
    for any genuine SNR computation."""
    rng = np.random.RandomState(11)
    N = 600
    iv = rng.randint(0, 4, size=N)
    traces = rng.randn(N, 2) * 0.2
    traces[:, 0] += iv * 2.0          # strong leakage
    snr = compute_snr(traces, iv)
    assert snr[0] > 5.0, f"t=0 leaks strongly (class spacing 2.0, noise sigma=0.2) yet the SNR is only {snr[0]:.4f}"
    assert snr[1] < 0.5, f"t=1 is pure noise so the SNR should be near 0, actual {snr[1]:.4f}"
    assert snr[0] > 20 * max(snr[1], 1e-12), "the leaking and non-leaking points are not clearly separated"
