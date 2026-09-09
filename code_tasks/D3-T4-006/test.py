import pytest
from solution import crt_rsa_sign

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


def test_small_prime():
    p, q = 61, 53
    n = p * q  # 3233
    phi = (p-1)*(q-1)
    e = 17
    d = pow(e, -1, phi)
    dp = d % (p-1)
    dq = d % (q-1)
    qinv = pow(q, -1, p)
    m = 123
    sig = crt_rsa_sign(m, p, q, dp, dq, qinv)
    assert pow(sig, e, n) == m % n

def test_rsa_1024_sim():
    p = 1000000007
    q = 1000000009
    n = p * q
    phi = (p-1)*(q-1)
    e = 65537
    d = pow(e, -1, phi)
    dp = d % (p-1)
    dq = d % (q-1)
    qinv = pow(q, -1, p)
    m = 999888777
    sig = crt_rsa_sign(m, p, q, dp, dq, qinv)
    assert pow(sig, e, n) == m % n

def test_sign_zero():
    p, q = 61, 53
    d = pow(17, -1, (p-1)*(q-1))
    sig = crt_rsa_sign(0, p, q, d%(p-1), d%(q-1), pow(q,-1,p))
    assert sig == 0

def test_sign_one():
    p, q = 61, 53
    d = pow(17, -1, (p-1)*(q-1))
    sig = crt_rsa_sign(1, p, q, d%(p-1), d%(q-1), pow(q,-1,p))
    assert sig == 1

def test_sp_less_than_sq():
    p, q = 97, 89
    d = pow(65537, -1, (p-1)*(q-1))
    dp = d % (p-1)
    dq = d % (q-1)
    qinv = pow(q, -1, p)
    for m in [50, 100, 200, 500, 1000]:
        sig = crt_rsa_sign(m, p, q, dp, dq, qinv)
        n = p * q
        e = 65537
        assert pow(sig, e, n) == m % n

def test_deterministic():
    p, q = 61, 53
    d = pow(17, -1, (p-1)*(q-1))
    dp, dq = d%(p-1), d%(q-1)
    qinv = pow(q, -1, p)
    for m in [0, 1, 10, 100, 500]:
        assert crt_rsa_sign(m, p, q, dp, dq, qinv) == crt_rsa_sign(m, p, q, dp, dq, qinv)

def test_negative_sp_minus_sq():
    p, q = 61, 53
    d = pow(17, -1, (p-1)*(q-1))
    dp, dq = d%(p-1), d%(q-1)
    qinv = pow(q, -1, p)
    for m in [0, 1, 2, 3, 10, 100]:
        sig = crt_rsa_sign(m, p, q, dp, dq, qinv)
        n = p * q
        assert 0 <= sig < n

def test_different_keys():
    keys = [(61, 53), (97, 89), (101, 103)]
    e = 65537
    for p, q in keys:
        n = p * q
        d = pow(e, -1, (p-1)*(q-1))
        dp, dq = d%(p-1), d%(q-1)
        qinv = pow(q, -1, p)
        for m in range(0, 200, 37):
            sig = crt_rsa_sign(m, p, q, dp, dq, qinv)
            assert pow(sig, e, n) == m % n

def test_full_message():
    p, q = 499, 503
    n = p * q
    e = 17
    d = pow(e, -1, (p-1)*(q-1))
    dp, dq = d%(p-1), d%(q-1)
    qinv = pow(q, -1, p)
    for m in [0, 1, n-2, n-1]:
        sig = crt_rsa_sign(m % n, p, q, dp, dq, qinv)
        assert pow(sig, e, n) == m % n

def test_large_m():
    p, q = 1009, 1013
    n = p * q
    e = 17
    d = pow(e, -1, (p-1)*(q-1))
    dp, dq = d%(p-1), d%(q-1)
    qinv = pow(q, -1, p)
    m = n - 123
    sig = crt_rsa_sign(m, p, q, dp, dq, qinv)
    assert pow(sig, e, n) == m % n


def test_no_builtin_pow_for_modexp():
    """Static check (AST): the exponentiation must be implemented by hand and the three-argument pow is banned (square-and-multiply, window methods and so on are all fine)."""
    import ast, inspect, textwrap
    import solution as _m
    tree = ast.parse(textwrap.dedent(inspect.getsource(_m)))
    bad = [n for n in ast.walk(tree)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
           and n.func.id == "pow" and len(n.args) >= 3]
    assert not bad, "the statement requires a hand-written exponentiation and bans pow(x, d, N); any correct algorithm is acceptable"


def test_no_builtin_pow_runtime():
    """Runtime probe: the three-argument builtin pow is banned.
    An assignment alias (shortcut = pow) and reflective lookup both show up in the c_call event."""
    called = _c_calls_during(crt_rsa_sign, 12345, 61, 53, 7, 11, 30)
    assert "pow" not in called, "a call to the builtin pow was detected: %s" % sorted(called)


def test_actually_does_the_work():
    """Work check: both exponentiations must be computed here, not delegated to a library."""
    p = 0xE3B5A1F7C9D2408B6F1E7A3C5D9B2E4F1A7C3E5B9D2F4A6C8E1B3D5F7A9C2E4B
    q = 0xC7F1E39D5B2A4681C3E5A79B1D3F5A7C9E2B4D6F8A1C3E5B7D9F2A4C6E8B1D3F
    e = 65537
    dp, dq = pow(e, -1, p - 1), pow(e, -1, q - 1)
    qinv = pow(q, -1, p)
    used = _lines_executed(crt_rsa_sign, 12345, p, q, dp, dq, qinv)
    assert used >= 200, (
        f"the whole call executed only {used} Python lines, which does not look like two hand-written exponentiations")
