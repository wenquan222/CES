import pytest
from solution import xor_sharewise

def test_equal_inputs():
    a = bytes(range(16))
    b = bytes(range(16))
    result = xor_sharewise(a, b)
    assert result == bytes(16)  # all zeros

def test_different_inputs():
    a = b'\x00' * 16
    b = b'\xFF' * 16
    result = xor_sharewise(a, b)
    assert result == b'\xFF' * 16

def test_mask_xor_property():
    """Check the masking-context property (x^m) ^ (y^n) = (x^y) ^ (m^n)."""
    x = bytes(range(16))
    y = bytes(reversed(range(16)))
    m = bytes([i ^ 0xAA for i in range(16)])
    n = bytes([i ^ 0x55 for i in range(16)])
    share_x = xor_sharewise(x, m)
    share_y = xor_sharewise(y, n)
    result = xor_sharewise(share_x, share_y)
    expected = xor_sharewise(xor_sharewise(x, y), xor_sharewise(m, n))
    assert result == expected

def test_single_byte():
    assert xor_sharewise(b'\xA5', b'\x5A') == b'\xFF'

def test_length_mismatch():
    with pytest.raises(ValueError):
        xor_sharewise(b'\x00' * 8, b'\x00' * 16)

def test_empty():
    assert xor_sharewise(b'', b'') == b''

def test_deterministic():
    a = bytes(range(32))
    b = bytes([i ^ 0xFF for i in range(32)])
    r1 = xor_sharewise(a, b)
    r2 = xor_sharewise(a, b)
    assert r1 == r2


def test_commutative():
    a = bytes(range(16)); b = bytes([i ^ 0x3C for i in range(16)])
    assert xor_sharewise(a, b) == xor_sharewise(b, a)

def test_self_inverse():
    a = bytes(range(20))
    assert xor_sharewise(a, a) == bytes(20)

def test_xor_zero_identity():
    a = bytes([i ^ 0x99 for i in range(16)])
    assert xor_sharewise(a, bytes(16)) == a


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
    """the statement bans any cryptographic library."""
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
