# -*- coding: utf-8 -*-
"""
D2-T4-004 tests: pfa_recover_aes_last_round_key. 10 test cases.
"""
import os
import pytest
import random
from solution import pfa_recover_aes_last_round_key


def _synth(k_last_byte_at_idx: int, v_corrupt: int, byte_idx: int, n: int = 10000, seed: int = 42):
    """
    Synthetic ciphertexts: byte byte_idx is random but excludes missing = v_corrupt XOR k_last;
    the other bytes are fully random.
    """
    r = random.Random(seed)
    missing = v_corrupt ^ k_last_byte_at_idx
    ciphertexts = []
    for _ in range(n):
        c = bytearray(r.randbytes(16))
        while c[byte_idx] == missing:
            c[byte_idx] = r.randint(0, 255)
        ciphertexts.append(bytes(c))
    return ciphertexts


# ============== 1. The standard case ==============
def test_basic_recovery():
    k_last = 0x42
    v_corrupt = 0x7C
    c = _synth(k_last, v_corrupt, byte_idx=0, n=10000, seed=42)
    r = pfa_recover_aes_last_round_key(v_corrupt, c, 0)
    assert r == k_last, f'expected {k_last:#x}, got {r:#x}'


# ============== 2. Accuracy on a large sample ==============
def test_large_sample():
    k_last = 0xAB
    v_corrupt = 0x33
    c = _synth(k_last, v_corrupt, byte_idx=5, n=50000, seed=1)
    r = pfa_recover_aes_last_round_key(v_corrupt, c, 5)
    assert r == k_last


# ============== 3. A small sample (must still run, need not be accurate) ==============
def test_small_sample_no_crash():
    k_last = 0x10
    v_corrupt = 0x20
    c = _synth(k_last, v_corrupt, byte_idx=3, n=200, seed=2)
    # Recovery need not succeed on a small sample, but the function must return an int in 0..255
    r = pfa_recover_aes_last_round_key(v_corrupt, c, 3)
    assert isinstance(r, int)
    assert 0 <= r <= 255


# ============== 4. Boundary: v_corrupt = 0 ==============
def test_v_corrupt_zero():
    k_last = 0x55
    v_corrupt = 0
    c = _synth(k_last, v_corrupt, byte_idx=8, n=10000, seed=3)
    r = pfa_recover_aes_last_round_key(v_corrupt, c, 8)
    assert r == k_last


# ============== 5. Boundary: v_corrupt = 255 ==============
def test_v_corrupt_max():
    k_last = 0xCC
    v_corrupt = 255
    c = _synth(k_last, v_corrupt, byte_idx=12, n=10000, seed=4)
    r = pfa_recover_aes_last_round_key(v_corrupt, c, 12)
    assert r == k_last


# ============== 6. byte_idx = 0 ==============
def test_byte_idx_zero():
    k_last = 0x77
    v_corrupt = 0x88
    c = _synth(k_last, v_corrupt, byte_idx=0, n=10000, seed=5)
    r = pfa_recover_aes_last_round_key(v_corrupt, c, 0)
    assert r == k_last


# ============== 7. byte_idx = 15 ==============
def test_byte_idx_last():
    k_last = 0x99
    v_corrupt = 0x66
    c = _synth(k_last, v_corrupt, byte_idx=15, n=10000, seed=6)
    r = pfa_recover_aes_last_round_key(v_corrupt, c, 15)
    assert r == k_last


# ============== 8. Input validation: empty list ==============
def test_empty_ciphertexts():
    with pytest.raises(ValueError):
        pfa_recover_aes_last_round_key(0x42, [], 0)


# ============== 9. Input validation: wrong length ==============
def test_wrong_length():
    bad = [bytes(15)] * 100  # 15 bytes instead of 16
    with pytest.raises(ValueError):
        pfa_recover_aes_last_round_key(0x42, bad, 0)


# ============== 10. Determinism ==============
def test_determinism():
    k_last = 0x33
    v_corrupt = 0x44
    c = _synth(k_last, v_corrupt, byte_idx=7, n=5000, seed=10)
    r1 = pfa_recover_aes_last_round_key(v_corrupt, c, 7)
    r2 = pfa_recover_aes_last_round_key(v_corrupt, c, 7)
    assert r1 == r2 == k_last


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

_EXTRA_ALLOWED = {"numpy", "scipy"}
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
    """the statement bans a statistics library and brute-force decryption, which would need a cipher implementation."""
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
