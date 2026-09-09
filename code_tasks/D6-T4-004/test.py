# -*- coding: utf-8 -*-
"""D6-T4-004 tests: pbkdf2_hmac_sha256 (PBKDF2-HMAC-SHA256, RFC 8018).

Grading reference: the standard library hashlib.pbkdf2_hmac('sha256', ...) -- banned in the reference implementation, but usable in the tests as the authority.
"""
import hashlib
import pytest
from solution import pbkdf2_hmac_sha256

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

_ALLOWED_IMPORTS = {'struct', 'hmac', 'hashlib'}


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



# 1. Against the standard library: several iteration counts x key lengths
def test_vs_stdlib_basic():
    pwd, salt = b"password", b"salt"
    for it in [1, 2, 1000]:
        for dk in [16, 32, 40]:
            assert pbkdf2_hmac_sha256(pwd, salt, it, dk) == \
                hashlib.pbkdf2_hmac("sha256", pwd, salt, it, dk)


# 2. Against the standard library: a dklen spanning several blocks (>32)
def test_vs_stdlib_long():
    assert pbkdf2_hmac_sha256(b"pw", b"NaCl", 100, 100) == \
        hashlib.pbkdf2_hmac("sha256", b"pw", b"NaCl", 100, 100)


# 3. A single iteration
def test_iterations_one():
    assert pbkdf2_hmac_sha256(b"p", b"s", 1, 32) == \
        hashlib.pbkdf2_hmac("sha256", b"p", b"s", 1, 32)


# 4. Various dklen values (including non-multiples of 32 and block boundaries)
def test_dklen_lengths():
    for dk in [1, 7, 33, 64, 65]:
        assert pbkdf2_hmac_sha256(b"pw", b"salt", 50, dk) == \
            hashlib.pbkdf2_hmac("sha256", b"pw", b"salt", 50, dk)


# 5. A different salt gives a different output
def test_different_salt():
    a = pbkdf2_hmac_sha256(b"pw", b"s1", 100, 32)
    b = pbkdf2_hmac_sha256(b"pw", b"s2", 100, 32)
    assert a != b


# 6. Returns dklen bytes
def test_returns_dklen():
    out = pbkdf2_hmac_sha256(b"pw", b"salt", 10, 20)
    assert isinstance(out, bytes) and len(out) == 20


# 7. Error: iterations < 1
def test_bad_iterations():
    with pytest.raises(ValueError):
        pbkdf2_hmac_sha256(b"pw", b"salt", 0, 32)


# 8. Error: dklen < 1
def test_bad_dklen():
    with pytest.raises(ValueError):
        pbkdf2_hmac_sha256(b"pw", b"salt", 10, 0)


# 9. Error: password or salt is not bytes
def test_bad_types():
    with pytest.raises(ValueError):
        pbkdf2_hmac_sha256("pw", b"salt", 10, 32)
    with pytest.raises(ValueError):
        pbkdf2_hmac_sha256(b"pw", "salt", 10, 32)


# 10. Determinism
def test_determinism():
    assert pbkdf2_hmac_sha256(b"pw", b"salt", 1000, 32) == \
        pbkdf2_hmac_sha256(b"pw", b"salt", 1000, 32)


def test_no_stdlib_pbkdf2():
    """Static check (AST): calling hashlib.pbkdf2_hmac is banned.
    Import aliases are checked too -- `from hashlib import pbkdf2_hmac as f` counts."""
    import ast, inspect, textwrap
    import solution as _m
    tree = ast.parse(textwrap.dedent(inspect.getsource(_m)))
    bad = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and n.attr == "pbkdf2_hmac":
            bad.append("hashlib.pbkdf2_hmac")
        elif isinstance(n, ast.Name) and n.id == "pbkdf2_hmac":
            bad.append("pbkdf2_hmac")
        elif isinstance(n, ast.alias) and n.name.split(".")[-1] == "pbkdf2_hmac":
            bad.append("import alias -> %s" % (n.asname or n.name))
    assert not bad, "the statement bans calling hashlib.pbkdf2_hmac; found: %s" % sorted(set(bad))


def test_no_stdlib_pbkdf2_runtime():
    """Runtime probe: whatever name it is imported under, the same C function is triggered in the end."""
    called = _c_calls_during(pbkdf2_hmac_sha256, b"pw", b"salt", 3, 32)
    assert "pbkdf2_hmac" not in called, (
        "a call to hashlib.pbkdf2_hmac was detected: %s" % sorted(called))


def test_actually_does_the_work():
    """Work check: 200 iterations of block iteration and XOR run tens of thousands of Python lines.
    Calling any ready-made PBKDF2 (from hashlib or a third-party library) runs only a single-digit number of lines."""
    used = _lines_executed(pbkdf2_hmac_sha256, b"pw", b"salt", 200, 32)
    assert used >= 500, (
        f"with iterations=200 only {used} Python lines ran, which does not look like the iteration was done here"
        " (the reference implementation runs about 16000)")
