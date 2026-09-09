import pytest
from solution import parity_check

def test_even_parity():
    """Byte-XOR LSB = 0 -> even parity."""
    assert parity_check(b'\x00', 0) == True       # XOR=0, LSB=0
    assert parity_check(b'\x00\x00', 0) == True   # XOR=0, LSB=0
    assert parity_check(b'\x03', 1) == True       # XOR=0x03, LSB=1 -> odd
    assert parity_check(b'\x03', 0) == False

def test_odd_parity():
    """Byte-XOR LSB = 1 -> odd parity."""
    assert parity_check(b'\x01', 1) == True       # XOR=0x01, LSB=1
    assert parity_check(b'\x01', 0) == False

def test_parity_mismatch():
    assert parity_check(b'\x01', 0) == False

def test_empty():
    assert parity_check(b'', 0) == True
    assert parity_check(b'', 1) == False

def test_multi_byte():
    # 0x01 ^ 0x02 ^ 0x03 = 0x00 → LSB=0 → even
    assert parity_check(b'\x01\x02\x03', 0) == True
    assert parity_check(b'\x01\x02\x03', 1) == False

def test_invalid_expected():
    with pytest.raises(ValueError):
        parity_check(b'\x00', 2)
    with pytest.raises(ValueError):
        parity_check(b'\x00', -1)

def test_no_branch_in_compare():
    """Static check that the comparison uses no if/else."""
    import inspect
    src = inspect.getsource(parity_check)
    code_after_raise = src.split("raise ValueError")[1] if "raise ValueError" in src else src
    if_lines = [l for l in code_after_raise.split('\n') if ' if ' in l and 'actual' in l.lower() and 'expected' in l.lower()]
    assert len(if_lines) == 0, f"Found secret-dependent if: {if_lines}"


def test_lsb_semantics_not_nonzero():
    # The LSB of 0x02 is 0 (the byte is non-zero but parity looks at the LSB)
    assert parity_check(bytes([0x02]), 0) == True
    assert parity_check(bytes([0x02]), 1) == False


def test_even_count_ff():
    assert parity_check(bytes([0xFF, 0xFF]), 0) == True
    assert parity_check(bytes([0xFF, 0xFF, 0xFF]), 1) == True


def test_large_data_consistency():
    data = bytes(range(256))   # XOR of 0..255 is 0 -> LSB=0
    assert parity_check(data, 0) == True
    assert parity_check(data, 1) == False
