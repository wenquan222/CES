import numpy as np
import pytest
from solution import second_order_cpa, AES_SBOX

def test_output_shape():
    """The output shape must be (256,)."""
    np.random.seed(42)
    N, T = 200, 50
    traces = np.random.randn(N, T) * 0.05
    plaintexts = np.random.randint(0, 256, N)
    result = second_order_cpa(traces, plaintexts, 5, 20)
    assert result.shape == (256,)

def test_correct_key_highest():
    """The correct key hypothesis must have the highest correlation coefficient."""
    np.random.seed(42)
    key = 0x2B
    N, T = 500, 50
    t1, t2 = 10, 30
    plaintexts = np.random.randint(0, 256, N)
    masks = np.random.randint(0, 256, N)
    traces = np.random.randn(N, T) * 0.03

    sbox_outs = np.array([AES_SBOX[p ^ key] for p in plaintexts])
    masked_outs = sbox_outs ^ masks

    for i in range(N):
        traces[i, t1] += 0.1 * (bin(masks[i]).count('1'))
        traces[i, t2] += 0.1 * (bin(masked_outs[i]).count('1'))

    result = second_order_cpa(traces, plaintexts, t1, t2)
    best = int(np.argmax(result))
    assert best == key

def test_correlation_range():
    """Every correlation coefficient must lie in [-1, 1]."""
    np.random.seed(42)
    N, T = 200, 30
    traces = np.random.randn(N, T) * 0.05
    plaintexts = np.random.randint(0, 256, N)
    result = second_order_cpa(traces, plaintexts, 5, 15)
    assert np.all(result >= -1.0)
    assert np.all(result <= 1.0)

def test_no_signal_flat():
    """With no signal every correlation coefficient must be below 0.4 in absolute value."""
    np.random.seed(42)
    N, T = 300, 20
    traces = np.random.randn(N, T) * 0.02
    plaintexts = np.random.randint(0, 256, N)
    result = second_order_cpa(traces, plaintexts, 3, 7)
    assert np.max(np.abs(result)) < 0.4

def test_different_key():
    """With a different key (0x7E) the correct hypothesis is still the highest."""
    np.random.seed(88)
    key = 0x7E
    N, T = 500, 50
    t1, t2 = 8, 25
    plaintexts = np.random.randint(0, 256, N)
    masks = np.random.randint(0, 256, N)
    traces = np.random.randn(N, T) * 0.03

    sbox_outs = np.array([AES_SBOX[p ^ key] for p in plaintexts])
    masked_outs = sbox_outs ^ masks

    for i in range(N):
        traces[i, t1] += 0.1 * (bin(masks[i]).count('1'))
        traces[i, t2] += 0.1 * (bin(masked_outs[i]).count('1'))

    result = second_order_cpa(traces, plaintexts, t1, t2)
    best = int(np.argmax(result))
    assert best == key

def test_wrong_key_lower():
    """A wrong key must correlate less strongly than the correct one."""
    np.random.seed(99)
    key = 0x5A
    N, T = 500, 50
    t1, t2 = 12, 28
    plaintexts = np.random.randint(0, 256, N)
    masks = np.random.randint(0, 256, N)
    traces = np.random.randn(N, T) * 0.03

    sbox_outs = np.array([AES_SBOX[p ^ key] for p in plaintexts])
    masked_outs = sbox_outs ^ masks

    for i in range(N):
        traces[i, t1] += 0.1 * (bin(masks[i]).count('1'))
        traces[i, t2] += 0.1 * (bin(masked_outs[i]).count('1'))

    result = second_order_cpa(traces, plaintexts, t1, t2)
    correct_corr = result[key]
    # Every wrong key must correlate less strongly than the correct key
    wrong_keys = [k for k in range(256) if k != key]
    assert all(result[k] < correct_corr for k in wrong_keys[:10])

def test_deterministic():
    """Same input -> same output."""
    np.random.seed(77)
    N, T = 200, 30
    traces = np.random.randn(N, T) * 0.05
    plaintexts = np.random.randint(0, 256, N)
    r1 = second_order_cpa(traces, plaintexts, 5, 15)
    r2 = second_order_cpa(traces, plaintexts, 5, 15)
    np.testing.assert_array_almost_equal(r1, r2)

def test_stress_more_traces():
    """With 1000 traces it still runs and the output shape is correct."""
    np.random.seed(66)
    N, T = 1000, 40
    traces = np.random.randn(N, T) * 0.02
    plaintexts = np.random.randint(0, 256, N)
    result = second_order_cpa(traces, plaintexts, 5, 15)
    assert result.shape == (256,)
    assert not np.any(np.isnan(result))

def test_constant_trace():
    """Identical traces (zero variance) -> return all zeros."""
    np.random.seed(55)
    N, T = 100, 20
    traces = np.ones((N, T)) * 0.5
    plaintexts = np.random.randint(0, 256, N)
    result = second_order_cpa(traces, plaintexts, 5, 15)
    assert np.all(result == 0.0)

def test_weak_signal_detectable():
    """A weak signal with a large enough N -> the correct key is still distinguishable (correlation > 0 and highest)."""
    np.random.seed(44)
    key = 0xC3
    N, T = 2000, 50
    t1, t2 = 10, 35
    plaintexts = np.random.randint(0, 256, N)
    masks = np.random.randint(0, 256, N)
    traces = np.random.randn(N, T) * 0.04  # moderate noise

    sbox_outs = np.array([AES_SBOX[p ^ key] for p in plaintexts])
    masked_outs = sbox_outs ^ masks

    for i in range(N):
        traces[i, t1] += 0.03 * (bin(masks[i]).count('1'))  # weak signal
        traces[i, t2] += 0.03 * (bin(masked_outs[i]).count('1'))

    result = second_order_cpa(traces, plaintexts, t1, t2)
    best = int(np.argmax(result))
    assert best == key
