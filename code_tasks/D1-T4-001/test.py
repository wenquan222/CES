"""D1-T4-001 test cases."""
import numpy as np
import pytest
from solution import compute_cpa, SBOX, HW_TABLE


@pytest.fixture
def synthetic_dataset():
    """Generate 5000 traces with a known key, true_key[0] = 0x42."""
    np.random.seed(42)
    N, T = 5000, 1000
    plaintexts = np.random.randint(0, 256, (N, 16), dtype=np.uint8)
    true_key = np.zeros(16, dtype=np.uint8)
    true_key[0] = 0x42
    intermediate = SBOX[plaintexts[:, 0] ^ true_key[0]]
    leakage = HW_TABLE[intermediate].astype(np.float64)
    traces = np.random.randn(N, T) * 2.0
    traces[:, 500] += leakage  # SNR ≈ 0.5
    return traces, plaintexts, true_key


def test_shape(synthetic_dataset):
    traces, plaintexts, _ = synthetic_dataset
    r = compute_cpa(traces, plaintexts, 0)
    assert r.shape == (256, traces.shape[1])


def test_recover_correct_key(synthetic_dataset):
    """The attack must recover true_key[0]."""
    traces, plaintexts, true_key = synthetic_dataset
    r = compute_cpa(traces, plaintexts, 0)
    recovered = np.argmax(np.max(np.abs(r), axis=1))
    assert recovered == true_key[0]


def test_no_nan_on_zero_variance():
    """All-zero traces must not produce NaN."""
    traces = np.zeros((100, 50))
    plaintexts = np.random.randint(0, 256, (100, 16), dtype=np.uint8)
    r = compute_cpa(traces, plaintexts, 0)
    assert not np.any(np.isnan(r))


def test_small_sample():
    """No error on a very small sample, N=200."""
    np.random.seed(0)
    traces = np.random.randn(200, 100)
    plaintexts = np.random.randint(0, 256, (200, 16), dtype=np.uint8)
    r = compute_cpa(traces, plaintexts, 0)
    assert r.shape == (256, 100)


def test_performance():
    """5000 x 5000 within 5 seconds."""
    import time
    np.random.seed(1)
    traces = np.random.randn(5000, 5000)
    plaintexts = np.random.randint(0, 256, (5000, 16), dtype=np.uint8)
    start = time.time()
    _ = compute_cpa(traces, plaintexts, 0)
    elapsed = time.time() - start
    assert elapsed < 5.0, f"too slow: {elapsed:.2f}s"


def test_sbox_and_hw_table_correct():
    """The exported SBOX and HW_TABLE must hold the standard values -- the evaluation builds intermediate values directly from them."""
    assert len(SBOX) == 256 and len(HW_TABLE) == 256
    assert int(SBOX[0x00]) == 0x63
    assert int(SBOX[0x53]) == 0xED
    assert int(SBOX[0xFF]) == 0x16
    assert sorted(int(x) for x in SBOX) == list(range(256))   # the S-box is a bijection
    for v in (0x00, 0x01, 0x0F, 0xFF, 0xA5):
        assert int(HW_TABLE[v]) == bin(v).count("1")


def test_correlation_in_valid_range(synthetic_dataset):
    """A Pearson correlation coefficient must lie in [-1, 1]."""
    traces, plaintexts, _ = synthetic_dataset
    r = compute_cpa(traces, plaintexts, 0)
    assert np.all(np.isfinite(r))
    assert np.max(np.abs(r)) <= 1.0 + 1e-9


def test_peak_at_leaking_sample(synthetic_dataset):
    """The correlation peak for the correct key must land on the time point where the leakage was actually injected (sample 500)."""
    traces, plaintexts, true_key = synthetic_dataset
    r = compute_cpa(traces, plaintexts, 0)
    assert int(np.argmax(np.abs(r[true_key[0]]))) == 500


def test_key_byte_index_is_used():
    """With the leakage built on byte 3, attacking idx=3 recovers it and attacking
    idx=0 does not -- this catches implementations that ignore the key_byte_idx argument."""
    np.random.seed(7)
    N, T = 4000, 200
    plaintexts = np.random.randint(0, 256, (N, 16), dtype=np.uint8)
    k3 = 0x9C
    leakage = HW_TABLE[SBOX[plaintexts[:, 3] ^ k3]].astype(np.float64)
    traces = np.random.randn(N, T) * 2.0
    traces[:, 77] += leakage
    r3 = compute_cpa(traces, plaintexts, 3)
    assert int(np.argmax(np.max(np.abs(r3), axis=1))) == k3
    r0 = compute_cpa(traces, plaintexts, 0)
    assert int(np.argmax(np.max(np.abs(r0), axis=1))) != k3


def test_no_leak_gives_low_correlation():
    """No significant correlation peak may appear on pure-noise traces."""
    np.random.seed(11)
    traces = np.random.randn(3000, 100)
    plaintexts = np.random.randint(0, 256, (3000, 16), dtype=np.uint8)
    r = compute_cpa(traces, plaintexts, 0)
    assert np.max(np.abs(r)) < 0.20


def test_deterministic(synthetic_dataset):
    """Two calls on the same input must give identical results."""
    traces, plaintexts, _ = synthetic_dataset
    assert np.array_equal(compute_cpa(traces, plaintexts, 0),
                          compute_cpa(traces, plaintexts, 0))
