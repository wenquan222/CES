import pytest
from solution import sliding_window_modexp, _precompute_odd_powers

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



def _try_patch_helper(mod, name, stub, state):
    """Best-effort: swap the function object's own __code__ for a stub; if that is not
    possible, let it through (return None).

    Swap __code__ rather than rebinding the module-level name: a module alias
    (`_PREPARE = _precompute_odd_powers`) and a default-argument capture
    (`def f(..., prepare=_precompute_odd_powers)`) hold the same function object; rebinding
    the name misses them and would wrongly report these legitimate styles as "the helper
    was not used".

    Not every legitimate style can be stubbed this way: a decorator-wrapped function
    carries closure cells, and functools.partial or a callable object has no __code__
    at all. Those are legitimate implementations too, so the probe lets them through
    and the independent helper functional tests take over -- a process constraint is
    best-effort: better to miss a contrived bypass than to fail a correct implementation.
    """
    import types
    fn = getattr(mod, name, None)
    if not isinstance(fn, types.FunctionType):
        return None
    if fn.__closure__ or fn.__code__.co_freevars:
        return None
    saved = (fn.__code__, fn.__defaults__, fn.__kwdefaults__)
    try:
        orig = types.FunctionType(fn.__code__, mod.__dict__, name + "_orig", fn.__defaults__)
        orig.__kwdefaults__ = fn.__kwdefaults__
        state["orig"] = orig
        mod.__dict__["_CESBENCH_PROBE"] = state
        fn.__code__ = stub.__code__
    except (TypeError, ValueError):
        mod.__dict__.pop("_CESBENCH_PROBE", None)   # leave no trace on the failure path
        return None
    fn.__defaults__ = None
    fn.__kwdefaults__ = None
    return fn, saved


def _unpatch_helper(mod, token):
    if token is None:
        return
    fn, saved = token
    fn.__code__, fn.__defaults__, fn.__kwdefaults__ = saved
    mod.__dict__.pop("_CESBENCH_PROBE", None)


def _stub_precompute(*args, **kwargs):
    """Do not hard-code the signature; forward to the wrapped original as-is, tolerating
    keyword calls and extra optional arguments. The perturbation is no longer reduced mod
    modulus: v+delta and (v+delta) % modulus are congruent and affect
    `acc * table[e] % modulus` identically, which saves having to read modulus from the arguments."""
    _orig = _CESBENCH_PROBE["orig"]                       # noqa: F821
    _table = dict(_orig(*args, **kwargs))
    return {e: v + _CESBENCH_PROBE["delta"]               # noqa: F821
            for e, v in _table.items()}

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


def test_basic():
    assert sliding_window_modexp(3, 5, 100, 3) == pow(3, 5, 100)

def test_small():
    for b in range(1, 10):
        for e in range(0, 8):
            for m in [7, 11, 13]:
                expected = pow(b, e, m)
                assert sliding_window_modexp(b, e, m, 3) == expected

def test_exponent_zero():
    assert sliding_window_modexp(123, 0, 100, 3) == 1

def test_exponent_one():
    assert sliding_window_modexp(7, 1, 13, 3) == 7

def test_base_one():
    assert sliding_window_modexp(1, 999, 100, 3) == 1

def test_mod_one():
    assert sliding_window_modexp(123, 456, 1, 3) == 0

def test_larger():
    b = 1234567
    e = 9876543
    m = 1000000007
    k = 5
    assert sliding_window_modexp(b, e, m, k) == pow(b, e, m)

def test_window_size_four():
    b, e, m = 17, 12345, 7919
    assert sliding_window_modexp(b, e, m, 4) == pow(b, e, m)

def test_window_size_six():
    b, e, m = 2, 1000, 1009
    assert sliding_window_modexp(b, e, m, 6) == pow(b, e, m)

def test_deterministic():
    b, e, m, k = 99, 777, 10007, 5
    r1 = sliding_window_modexp(b, e, m, k)
    r2 = sliding_window_modexp(b, e, m, k)
    assert r1 == r2


def test_no_builtin_pow_shortcut():
    """Static check (AST): the pow(base, exponent, modulus) shortcut is banned."""
    import ast, inspect, textwrap
    import solution as _m
    tree = ast.parse(textwrap.dedent(inspect.getsource(_m)))
    bad = [n for n in ast.walk(tree)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
           and n.func.id == "pow" and len(n.args) >= 3]
    assert not bad, "the statement bans calling the three-argument pow directly"


def test_no_builtin_pow_runtime():
    """Runtime probe: the three-argument builtin pow is banned.
    An assignment alias (shortcut = pow) and reflective lookup both show up in the c_call event."""
    called = _c_calls_during(sliding_window_modexp, 5, 117, 1009, 4)
    assert "pow" not in called, "a call to the builtin pow was detected: %s" % sorted(called)


def test_precompute_odd_powers_correct():
    """Verify the precomputed table directly: {e: base^e mod m} for e = 1,3,5,...,2^k-1."""
    for base, mod, k in ((3, 1000003, 3), (7, 65537, 4), (12345, 1009, 5)):
        g = _precompute_odd_powers(base, mod, k)
        expect = {e: pow(base, e, mod) for e in range(1, 1 << k, 2)}
        assert dict(g) == expect, f"the precomputed table is wrong (base={base}, k={k})"


def test_result_depends_on_precomputed_table():
    """Runtime check of the data flow: perturb the whole precomputed table and the final

    result must change with it. An implementation that calls _precompute_odd_powers once,
    throws the table away and runs an ordinary binary square-and-multiply produces an
    unchanged result and fails here.

    This one is best-effort: a style that cannot be stubbed safely (decorator closures
    and the like) is let through,
    The correctness of the table itself is covered by test_precompute_odd_powers_correct."""
    import solution as _m
    base, exp, mod, k = 7, 12345, 1000003, 4

    good = _m.sliding_window_modexp(base, exp, mod, k)
    assert good == pow(base, exp, mod), "the result is already wrong before any perturbation"

    state = {"delta": 1}
    token = _try_patch_helper(_m, "_precompute_odd_powers", _stub_precompute, state)
    if token is None:
        return
    try:
        bad = _m.sliding_window_modexp(base, exp, mod, k)
    finally:
        _unpatch_helper(_m, token)

    assert bad != good, (
        "perturbing the whole precomputed table changed nothing, so the main function does not really use it, "
        "which does not follow the sliding-window algorithm the statement requires")


def test_actually_does_the_work():
    """Work check: sliding-window exponentiation must do its own precomputation and window scan."""
    p = 0xE3B5A1F7C9D2408B6F1E7A3C5D9B2E4F1A7C3E5B9D2F4A6C8E1B3D5F7A9C2E4B
    q = 0xC7F1E39D5B2A4681C3E5A79B1D3F5A7C9E2B4D6F8A1C3E5B7D9F2A4C6E8B1D3F
    n = p * q
    used = _lines_executed(sliding_window_modexp, 3, n - 3, n, 4)
    assert used >= 200, (
        f"the whole call executed only {used} Python lines, which does not look like a hand-written sliding-window exponentiation"
        " (the reference implementation runs about 4800)")
