import numpy as np
import pytest
from solution import recover_key_byte_from_cache

def test_recover_single_byte():
    """Recover a single key byte (byte_idx=0)."""
    np.random.seed(123)
    key = np.array([0x2B, 0x7E, 0x15, 0x16, 0x28, 0xAE, 0xD2, 0xA6,
                    0xAB, 0xF7, 0x15, 0x88, 0x09, 0xCF, 0x4F, 0x3C], dtype=np.uint8)
    M = 50
    plaintexts = np.random.randint(0, 256, (M, 16), dtype=np.uint8)
    timings = np.zeros((M, 256))
    for i in range(M):
        base = np.random.randn(256) * 3 + 80
        sbox_in = plaintexts[i, 0] ^ key[0]
        base[sbox_in] -= 50
        timings[i] = base
    result = recover_key_byte_from_cache(timings, plaintexts, 0)
    assert result == key[0]

def test_different_byte_idx():
    """Recover byte_idx = 0, 3, 7 and 15 separately."""
    np.random.seed(456)
    key = np.array([0x3A, 0xC7, 0x91, 0x22, 0x55, 0xBE, 0x13, 0x8F,
                    0xCC, 0xDD, 0xEE, 0xFF, 0x12, 0x34, 0x56, 0x78], dtype=np.uint8)
    M = 60
    plaintexts = np.random.randint(0, 256, (M, 16), dtype=np.uint8)
    for byte_idx in [0, 3, 7, 15]:
        timings = np.zeros((M, 256))
        for i in range(M):
            base = np.random.randn(256) * 3 + 80
            sbox_in = plaintexts[i, byte_idx] ^ key[byte_idx]
            base[sbox_in] -= 50
            timings[i] = base
        result = recover_key_byte_from_cache(timings, plaintexts, byte_idx)
        assert result == key[byte_idx]

def test_insufficient_data():
    """Return -1 when there is not enough data."""
    np.random.seed(789)
    M = 2
    plaintexts = np.random.randint(0, 256, (M, 16), dtype=np.uint8)
    timings = np.random.randn(M, 256) * 3 + 80
    result = recover_key_byte_from_cache(timings, plaintexts, 0)
    assert result == -1 or (0 <= result <= 255)

def test_recover_full_key():
    """Recover all 16 bytes in turn."""
    np.random.seed(111)
    key = np.array([0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF,
                    0xFE, 0xDC, 0xBA, 0x98, 0x76, 0x54, 0x32, 0x10], dtype=np.uint8)
    M = 80
    plaintexts = np.random.randint(0, 256, (M, 16), dtype=np.uint8)
    for byte_idx in range(16):
        timings = np.zeros((M, 256))
        for i in range(M):
            base = np.random.randn(256) * 3 + 80
            sbox_in = plaintexts[i, byte_idx] ^ key[byte_idx]
            base[sbox_in] -= 50
            timings[i] = base
        result = recover_key_byte_from_cache(timings, plaintexts, byte_idx)
        assert result == key[byte_idx]

def test_high_noise_resilience():
    """Recovery still succeeds in a noisy setting given more traces."""
    np.random.seed(222)
    key = 0x7F
    M = 400
    plaintexts = np.random.randint(0, 256, (M, 16), dtype=np.uint8)
    timings = np.zeros((M, 256))
    for i in range(M):
        base = np.random.randn(256) * 8 + 80  # moderate noise
        sbox_in = plaintexts[i, 0] ^ key
        base[sbox_in] -= 25  # moderate signal relative to noise
        timings[i] = base
    result = recover_key_byte_from_cache(timings, plaintexts, 0)
    assert result == key

def test_deterministic():
    """Same input -> same output."""
    np.random.seed(333)
    M = 40
    plaintexts = np.random.randint(0, 256, (M, 16), dtype=np.uint8)
    timings = np.random.randn(M, 256) * 3 + 80
    timings[:, 42] -= 50
    r1 = recover_key_byte_from_cache(timings, plaintexts, 0)
    r2 = recover_key_byte_from_cache(timings, plaintexts, 0)
    assert r1 == r2

def test_boundary_candidates():
    """The candidate set shrinks to exactly 1 on the last round -> return that value without error."""
    np.random.seed(444)
    key = 0xAB
    M = 12
    plaintexts = np.random.randint(0, 256, (M, 16), dtype=np.uint8)
    timings = np.zeros((M, 256))
    for i in range(M):
        base = np.random.randn(256) * 2 + 80
        sbox_in = plaintexts[i, 0] ^ key
        base[sbox_in] -= 60
        timings[i] = base
    result = recover_key_byte_from_cache(timings, plaintexts, 0)
    assert result == key

def test_small_num_traces():
    """A limited number of traces (15) with a very strong signal -> recovery still succeeds."""
    np.random.seed(555)
    key = 0x3C
    M = 15
    plaintexts = np.random.randint(0, 256, (M, 16), dtype=np.uint8)
    timings = np.zeros((M, 256))
    for i in range(M):
        base = np.random.randn(256) * 0.5 + 80  # low noise
        sbox_in = plaintexts[i, 0] ^ key
        base[sbox_in] -= 80  # very strong signal
        timings[i] = base
    result = recover_key_byte_from_cache(timings, plaintexts, 0)
    assert result == key

def test_zero_return_when_candidates_empty():
    """When elimination empties the candidate set -> return -1."""
    np.random.seed(666)
    M = 5
    plaintexts = np.random.randint(0, 256, (M, 16), dtype=np.uint8)
    timings = np.random.randn(M, 256) * 5 + 80
    # Random timings carry no pattern, so elimination keeps shrinking the candidate set until it is empty
    result = recover_key_byte_from_cache(timings, plaintexts, 0)
    assert result == -1 or (0 <= result <= 255)

def test_byte_0_and_15_consistency():
    """byte_idx 0 and 15 are recovered independently without interfering."""
    np.random.seed(777)
    key = np.array([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
                    0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00], dtype=np.uint8)
    M = 50
    plaintexts = np.random.randint(0, 256, (M, 16), dtype=np.uint8)

    timings0 = np.zeros((M, 256))
    for i in range(M):
        base = np.random.randn(256) * 3 + 80
        sbox_in = plaintexts[i, 0] ^ key[0]
        base[sbox_in] -= 50
        timings0[i] = base
    assert recover_key_byte_from_cache(timings0, plaintexts, 0) == key[0]

    timings15 = np.zeros((M, 256))
    for i in range(M):
        base = np.random.randn(256) * 3 + 80
        sbox_in = plaintexts[i, 15] ^ key[15]
        base[sbox_in] -= 50
        timings15[i] = base
    assert recover_key_byte_from_cache(timings15, plaintexts, 15) == key[15]


# ── Algorithm-constraint checks ───────────────────────────────────────
# The statement declares a constraint on *how* the answer must be produced, and
# nothing above tested it. The primary criterion here is an import allowlist
# rather than a list of banned names: a name ban is defeated by an assignment
# alias, an import alias or getattr reflection, whereas an allowlist does not
# depend on how the candidate writes it.
import ast as _ast
import sys as _sys
import inspect as _inspect
import textwrap as _textwrap

import solution as _solmod

_EXTRA_ALLOWED = {"numpy"}
# Allowed = the Python standard library plus whatever third-party packages the
# statement permits. The criterion stays an allowlist rather than a list of banned
# names, because a name ban is defeated by an assignment alias, an import alias or
# getattr reflection. But the allowlist must not be stricter than the statement:
# these checks are blocking, so an unwarranted restriction turns a fully correct
# submission into an unscorable one.
_ALLOWED_IMPORTS = set(getattr(_sys, "stdlib_module_names", ())) | _EXTRA_ALLOWED


def _sol_tree():
    return _ast.parse(_textwrap.dedent(_inspect.getsource(_solmod)))


def _imported_modules():
    mods = set()
    for n in _ast.walk(_sol_tree()):
        if isinstance(n, _ast.Import):
            for al in n.names:
                mods.add(al.name.split(".")[0])
        elif isinstance(n, _ast.ImportFrom):
            if n.level:
                mods.add("<relative import>")
            if n.module:
                mods.add(n.module.split(".")[0])
    return mods


def test_contract_import_allowlist():
    """the statement allows numpy only."""
    extra = _imported_modules() - _ALLOWED_IMPORTS
    assert not extra, "only %s may be imported; found: %s" % (
        sorted(_ALLOWED_IMPORTS) or "nothing", sorted(extra))


def test_contract_no_dynamic_lookup():
    """getattr / eval / exec / __import__ would let a banned module back in."""
    banned = {"getattr", "eval", "exec", "compile", "__import__",
               "globals", "vars", "locals"}
    hits = sorted({n.func.id for n in _ast.walk(_sol_tree())
                   if isinstance(n, _ast.Call) and isinstance(n.func, _ast.Name)
                   and n.func.id in banned})
    assert not hits, "reflective lookup is banned; found: %s" % hits


def test_contract_no_dunder_access():
    """int.__pow__ and friends are the usual way around a ban by name."""
    hits = sorted({n.attr for n in _ast.walk(_sol_tree())
                   if isinstance(n, _ast.Attribute)
                   and n.attr.startswith("__") and n.attr.endswith("__")})
    assert not hits, "dunder attribute access is banned; found: %s" % hits
