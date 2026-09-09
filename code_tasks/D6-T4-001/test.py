# -*- coding: utf-8 -*-
"""D6-T4-001 tests: Shamir (t,n) threshold secret sharing."""
import pytest
from solution import shamir_split, shamir_reconstruct

P = 7919  # a prime


# 1. reconstruct against a hand computation: f(x)=100+50x mod 2087, f(1)=150, f(2)=200 -> f(0)=100
def test_reconstruct_manual():
    assert shamir_reconstruct([(1, 150), (2, 200)], 2087) == 100


# 2. split uses the coefficients correctly: with t=2, f(x)=S+c1*x
def test_split_values():
    shares = shamir_split(100, 2, 3, 2087, coeffs=[50])
    assert shares == [(1, 150), (2, 200), (3, 250)]


# 3. Round trip with (3,5): any 3 shares recover the secret
def test_roundtrip_3_of_5():
    secret = 1234
    shares = shamir_split(secret, 3, 5, P, coeffs=[111, 222])
    assert shamir_reconstruct(shares[:3], P) == secret


# 4. Different subsets of t shares all recover the same secret
def test_different_subsets():
    secret = 4567
    shares = shamir_split(secret, 3, 5, P, coeffs=[321, 654])
    assert shamir_reconstruct([shares[0], shares[2], shares[4]], P) == secret
    assert shamir_reconstruct([shares[1], shares[3], shares[4]], P) == secret


# 5. t = n, all shares needed
def test_t_equals_n():
    secret = 2000
    shares = shamir_split(secret, 4, 4, P, coeffs=[1, 2, 3])
    assert shamir_reconstruct(shares, P) == secret


# 6. t = 2, the minimal threshold
def test_min_threshold():
    secret = 42
    shares = shamir_split(secret, 2, 6, P, coeffs=[999])
    assert shamir_reconstruct([shares[0], shares[5]], P) == secret


# 7. Boundary: secret = 0
def test_secret_zero():
    shares = shamir_split(0, 3, 5, P, coeffs=[7, 8])
    assert shamir_reconstruct(shares[:3], P) == 0


# 8. Invalid arguments raise ValueError
def test_invalid_params():
    with pytest.raises(ValueError):
        shamir_split(10, 5, 3, P, coeffs=[1, 2, 3, 4])   # t > n
    with pytest.raises(ValueError):
        shamir_split(99999, 2, 3, P, coeffs=[1])          # secret >= prime
    with pytest.raises(ValueError):
        shamir_split(10, 3, 5, P, coeffs=[1])             # wrong coeffs length (2 required)
    with pytest.raises(ValueError):
        shamir_reconstruct([], P)                          # no shares
    with pytest.raises(ValueError):
        shamir_reconstruct([(1, 5), (1, 9)], P)            # duplicate x


# 9. A large prime (the Mersenne prime 2^31-1)
def test_large_prime():
    bigp = 2147483647  # 2^31 - 1
    secret = 123456789
    shares = shamir_split(secret, 3, 7, bigp, coeffs=[987654321, 111111111])
    assert shamir_reconstruct(shares[2:5], bigp) == secret


# 10. Determinism, and fewer than t shares cannot recover the secret
def test_determinism_and_insufficient():
    secret = 3000
    a = shamir_split(secret, 3, 5, P, coeffs=[10, 20])
    b = shamir_split(secret, 3, 5, P, coeffs=[10, 20])
    assert a == b                                    # determinism
    # Interpolating f(0) from only 2 shares (< t=3) generally differs from the secret
    wrong = shamir_reconstruct(a[:2], P)
    assert wrong != secret


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

_EXTRA_ALLOWED = set()
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
    """the statement bans any third-party cryptographic or mathematical library."""
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
