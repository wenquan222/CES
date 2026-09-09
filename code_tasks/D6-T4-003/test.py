# -*- coding: utf-8 -*-
"""D6-T4-003 tests: pcr_extend (the TPM PCR measurement chain)."""
import hashlib
import pytest
from solution import pcr_extend


# 1. An empty measurement list leaves the PCR unchanged
def test_empty_measurements():
    init = b"\x00" * 32
    assert pcr_extend(init, []) == init


# 2. A single extension: PCR = SHA256(init || m)
def test_single():
    init = b"\x00" * 32
    m = b"hello"
    assert pcr_extend(init, [m]) == hashlib.sha256(init + m).digest()


# 3. Two extensions: the hash chain
def test_two_chain():
    init = b"\x00" * 32
    m1, m2 = b"aaa", b"bbb"
    expect = hashlib.sha256(hashlib.sha256(init + m1).digest() + m2).digest()
    assert pcr_extend(init, [m1, m2]) == expect


# 4. Order sensitivity: [m1,m2] != [m2,m1]
def test_order_sensitive():
    init = b"\x00" * 32
    a = pcr_extend(init, [b"m1", b"m2"])
    b = pcr_extend(init, [b"m2", b"m1"])
    assert a != b


# 5. A known vector: init = 0*32, extended with one 0*32
def test_known_vector():
    init = b"\x00" * 32
    out = pcr_extend(init, [b"\x00" * 32])
    assert out == hashlib.sha256(b"\x00" * 64).digest()


# 6. Returns 32 bytes
def test_returns_32():
    out = pcr_extend(b"\x11" * 32, [b"x", b"y", b"z"])
    assert isinstance(out, bytes) and len(out) == 32


# 7. Errors: initial_pcr not 32 bytes / not bytes
def test_bad_initial():
    with pytest.raises(ValueError):
        pcr_extend(b"\x00" * 31, [b"m"])
    with pytest.raises(ValueError):
        pcr_extend("notbytes", [b"m"])


# 8. Error: a measurement is not bytes
def test_bad_measurement():
    with pytest.raises(ValueError):
        pcr_extend(b"\x00" * 32, [b"ok", 123])


# 9. Determinism
def test_determinism():
    init = b"\x07" * 32
    ms = [b"boot", b"kernel", b"app"]
    assert pcr_extend(init, ms) == pcr_extend(init, ms)


# 10. No rollback: the extended value equals neither the initial nor any intermediate state
def test_no_rollback():
    init = b"\x00" * 32
    mid = pcr_extend(init, [b"m1"])
    final = pcr_extend(init, [b"m1", b"m2"])
    assert final != init and final != mid
