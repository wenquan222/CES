# -*- coding: utf-8 -*-
"""D3-T4-003 tests: modexp_square_multiply."""
import pytest
import time
from solution import modexp_square_multiply

# ── Algorithm-constraint helpers (V5) ─────────────────────────────────
# The first two versions used a blacklist of banned names. Assignment aliases,
# import aliases, getattr reflection, dunders such as int.__pow__, the operator
# module and third-party libraries each got around it. This version uses two
# criteria that do not depend on how the code is written:
#   (i)  an import whitelist -- only the modules listed here may be imported
#        (for most items, none at all);
#   (ii) a work count -- how many Python lines one call actually executes. A
#
#        library call, a table lookup or a direct multiply runs a single-digit
#        number of lines; genuinely running the algorithm takes hundreds to
import ast as _ast
import inspect as _inspect
import textwrap as _textwrap
import sys as _sys
import solution as _solmod

_ALLOWED_IMPORTS = set()


def _sol_tree():
    """AST of the whole submitted module -- the scope must be the module, not one function."""
    return _ast.parse(_textwrap.dedent(_inspect.getsource(_solmod)))


def _imported_modules():
    """Which top-level modules the submission imports."""
    mods = set()
    for n in _ast.walk(_sol_tree()):
        if isinstance(n, _ast.Import):
            for a in n.names:
                mods.add(a.name.split(".")[0])
        elif isinstance(n, _ast.ImportFrom):
            if n.level:
                mods.add("<relative import>")
            if n.module:
                mods.add(n.module.split(".")[0])
    return mods


def _dunder_attribute_hits():
    """Accessing any __dunder__ attribute is banned: int.__pow__ / x.__getitem__
    and the like are the usual way around a ban by name."""
    return sorted({n.attr for n in _ast.walk(_sol_tree())
                   if isinstance(n, _ast.Attribute)
                   and n.attr.startswith("__") and n.attr.endswith("__")})


def _dynamic_lookup_hits():
    """Reflective lookup is banned outright."""
    banned = {"getattr", "eval", "exec", "compile", "__import__", "globals", "vars", "locals"}
    hits = []
    for n in _ast.walk(_sol_tree()):
        if isinstance(n, _ast.Call) and isinstance(n.func, _ast.Name) and n.func.id in banned:
            hits.append(n.func.id)
    return sorted(set(hits))


def _c_calls_during(fn, *args, **kwargs):
    """Record the builtin/C function names actually triggered during one call."""
    seen = set()

    def _prof(_frame, event, arg):
        if event == "c_call":
            seen.add(getattr(arg, "__name__", ""))

    old = _sys.getprofile()
    _sys.setprofile(_prof)
    try:
        fn(*args, **kwargs)
    finally:
        _sys.setprofile(old)
    seen.discard("setprofile")
    return seen


def _lines_executed(fn, *args, **kwargs):
    """Count the Python lines executed by one call -- the key criterion in this file.
    It measures whether the computation actually happened, ignoring names and syntax."""
    count = [0]

    def _trace(_frame, event, _arg):
        if event == "line":
            count[0] += 1
        return _trace

    old = _sys.gettrace()
    _sys.settrace(_trace)
    try:
        fn(*args, **kwargs)
    finally:
        _sys.settrace(old)
    return count[0]


def _module_branch_nodes(forbid_compare=False):
    """Scan every function in the module (helpers and lambdas included); only an
    if-raise used for input validation is exempt. match/case counts as a branch too."""
    bad = []
    tree = _sol_tree()
    for fn in [n for n in _ast.walk(tree)
               if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef))]:
        body = [s for s in fn.body
                if not (isinstance(s, _ast.If)
                        and all(isinstance(x, _ast.Raise) for x in s.body)
                        and not s.orelse)]
        for stmt in body:
            for node in _ast.walk(stmt):
                if isinstance(node, _ast.If):
                    bad.append(fn.name + ":if")
                elif isinstance(node, _ast.IfExp):
                    bad.append(fn.name + ":conditional expression")
                elif isinstance(node, getattr(_ast, "Match", ())):
                    bad.append(fn.name + ":match/case")
                elif forbid_compare and isinstance(node, _ast.Compare) and any(
                        isinstance(o, (_ast.Eq, _ast.NotEq)) for o in node.ops):
                    bad.append(fn.name + ":==/!=")
    for lam in [n for n in _ast.walk(tree) if isinstance(n, _ast.Lambda)]:
        for node in _ast.walk(lam.body):
            if isinstance(node, _ast.IfExp):
                bad.append("lambda:conditional expression")
    return bad


def test_import_allowlist():
    """Only whitelisted modules may be imported. This also blocks operator,
    cryptography and any third-party library that ships a ready-made implementation --
    far more reliable than banning names one by one."""
    extra = sorted(_imported_modules() - _ALLOWED_IMPORTS)
    assert not extra, "the statement permits only %s; extra imports found: %s" % (
        sorted(_ALLOWED_IMPORTS) or "nothing from the standard library", extra)


def test_no_dunder_access():
    """Accessing __dunder__ attributes (int.__pow__, say) is banned -- that is the way around the implementation constraint."""
    hits = _dunder_attribute_hits()
    assert not hits, "evading the implementation constraint through dunder attributes is banned; found: %s" % hits


def test_no_dynamic_lookup():
    """Reflective lookup via getattr/eval/exec/__import__ is banned."""
    hits = _dynamic_lookup_hits()
    assert not hits, "evading the implementation constraint through reflection is banned; found: %s" % hits



# 1. The textbook example
def test_basic():
    assert modexp_square_multiply(2, 10, 1000) == 24  # 2^10 = 1024 mod 1000


# 2. Boundary: d = 0
def test_d_zero():
    assert modexp_square_multiply(5, 0, 7) == 1
    assert modexp_square_multiply(0, 0, 7) == 1
    assert modexp_square_multiply(100, 0, 13) == 1


# 3. Boundary: d = 1
def test_d_one():
    assert modexp_square_multiply(5, 1, 7) == 5
    assert modexp_square_multiply(13, 1, 7) == 6  # 13 mod 7 = 6


# 4. Boundary: x = 0
def test_x_zero():
    assert modexp_square_multiply(0, 1, 7) == 0
    assert modexp_square_multiply(0, 100, 13) == 0


# 5. Toy RSA encrypt/decrypt round trip
def test_rsa_toy():
    N = 3233    # = 53 × 61
    e = 17
    d = 2753
    for m in [1, 2, 42, 65, 100, 3232]:
        c = modexp_square_multiply(m, e, N)
        m_dec = modexp_square_multiply(c, d, N)
        assert m_dec == m, f'RSA roundtrip fails for m={m}: c={c}, dec={m_dec}'


# 6. Large integers (512-bit, RSA style)
def test_large():
    # Use a random 512-bit N (a known semiprime)
    p = 0xE7B4C8A2_1F30D9B8_38AAFA5E_C4D29C6F_5A8F1B3D_4D7E2A91_15F6D2A8_3B0C9F87
    q = 0xD3F18A2C_4D8C2F36_92F4D17B_3A9C6B41_F8E2C5DA_4B17AE38_5F92D4C7_3A85B6F2
    N = p * q
    assert modexp_square_multiply(2, 65537, N) == pow(2, 65537, N)


# 7. Performance: RSA-2048 style
def test_perf_rsa2048():
    N = (1 << 2047) | 7  # a simplified ~2048-bit modulus
    d = (1 << 2047) | 3
    x = 12345678
    start = time.time()
    result = modexp_square_multiply(x, d, N)
    elapsed = time.time() - start
    assert elapsed < 10.0, f'too slow: {elapsed:.2f}s'
    assert result == pow(x, d, N)


# 8. N < 2 raises ValueError
def test_n_too_small():
    with pytest.raises(ValueError):
        modexp_square_multiply(2, 3, 1)
    with pytest.raises(ValueError):
        modexp_square_multiply(2, 3, 0)


# 9. Determinism
def test_determinism():
    for _ in range(3):
        assert modexp_square_multiply(7, 13, 41) == modexp_square_multiply(7, 13, 41)


# 10. Agreement with Python's pow (several cases)
def test_consistency_with_pow():
    cases = [
        (2, 10, 1000),
        (3, 17, 19),
        (123456, 7777, 999983),
        (0xABCD, 0x1234, 0xFFFFEEEE),
    ]
    for x, d, N in cases:
        assert modexp_square_multiply(x, d, N) == pow(x, d, N)


def test_no_builtin_pow_shortcut():
    """Static check (AST): the builtin pow(x, d, N) shortcut is banned; the exponentiation must be implemented by hand."""
    import ast, inspect, textwrap
    import solution as _m
    tree = ast.parse(textwrap.dedent(inspect.getsource(_m)))
    bad = [n for n in ast.walk(tree)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
           and n.func.id == "pow" and len(n.args) >= 3]
    assert not bad, "the statement bans calling the three-argument pow(x, d, N) directly"


def test_no_builtin_pow_runtime():
    """Runtime probe: the three-argument builtin pow is banned.
    An assignment alias (shortcut = pow) and reflective lookup both show up in the c_call event."""
    called = _c_calls_during(modexp_square_multiply, 5, 117, 1009)
    assert "pow" not in called, "a call to the builtin pow was detected: %s" % sorted(called)


def test_actually_does_the_work():
    """Work check: with a 512-bit exponent, square-and-multiply runs thousands of Python
    lines. Reaching the builtin pow (under any name, in any style) runs only a single-digit number."""
    p = 0xE3B5A1F7C9D2408B6F1E7A3C5D9B2E4F1A7C3E5B9D2F4A6C8E1B3D5F7A9C2E4B
    q = 0xC7F1E39D5B2A4681C3E5A79B1D3F5A7C9E2B4D6F8A1C3E5B7D9F2A4C6E8B1D3F
    n = p * q
    used = _lines_executed(modexp_square_multiply, 3, n - 3, n)
    assert used >= 200, (
        f"the whole call executed only {used} Python lines, which does not look like a hand-written exponentiation"
        " (the reference implementation runs about 1800 lines; calling the builtin pow runs about 1)")
