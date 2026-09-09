# -*- coding: utf-8 -*-
"""D3-T4-004 tests: montgomery_modmul."""
import pytest
from solution import montgomery_modmul, _redc

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
    (`_REDUCE = _redc`) and a default-argument capture (`def f(..., reducer=_redc)`) hold
    the same function object; rebinding the name misses them and would wrongly report
    these perfectly legitimate styles as "the helper was not used".

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


def _stub_redc(*args, **kwargs):
    """Do not hard-code the signature; tolerate legitimate call styles such as `_redc(T, N, N_prime=..., R=...)`."""
    _CESBENCH_PROBE["calls"].append((args, kwargs))       # noqa: F821
    return _CESBENCH_PROBE["value"]                       # noqa: F821

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



def _compute_N_prime(N, R):
    """Helper: compute N' = -N^{-1} mod R."""
    return (-pow(N, -1, R)) % R


# 1. A known small-integer example: MontMul(3, 5) mod 17
def test_small():
    N = 17
    R = 32
    Np = _compute_N_prime(N, R)
    # 3·5·32^{-1} mod 17 = 15·8 mod 17 = 120 mod 17 = 1
    assert montgomery_modmul(3, 5, N, Np, R) == 1


# 2. Consistency for a medium-sized N
def test_consistency_medium():
    N = 0xFD46AB9F   # an odd number of about 32 bits
    R = 1 << 32
    Np = _compute_N_prime(N, R)
    Rinv = pow(R, -1, N)
    # Check that MontMul(x, y) = x * y * R^{-1} mod N
    for x, y in [(123, 456), (0xABCDEF, 0x123456), (N - 1, 2)]:
        result = montgomery_modmul(x, y, N, Np, R)
        expected = (x * y * Rinv) % N
        assert result == expected, f'x={x} y={y}: got {result}, want {expected}'


# 3. Consistency for a large integer (512-bit)
def test_large():
    N = (1 << 511) | 7      # a large odd number
    R = 1 << 512
    Np = _compute_N_prime(N, R)
    Rinv = pow(R, -1, N)
    x = 0xDEADBEEFCAFEBABE
    y = 0x123456789ABCDEF0
    result = montgomery_modmul(x, y, N, Np, R)
    expected = (x * y * Rinv) % N
    assert result == expected


# 4. An even N raises
def test_N_even():
    with pytest.raises(ValueError):
        montgomery_modmul(3, 5, 16, 1, 32)  # N=16 is even


# 5. An R that is not a power of 2 raises
def test_R_not_power_of_two():
    with pytest.raises(ValueError):
        montgomery_modmul(3, 5, 17, 1, 30)  # R=30 is not a power of 2


# 6. R <= N raises
def test_R_too_small():
    with pytest.raises(ValueError):
        montgomery_modmul(3, 5, 17, 1, 16)  # R=16 < N=17


# 7. Boundaries: x=0 and y=0
def test_zero():
    N = 17; R = 32; Np = _compute_N_prime(N, R)
    assert montgomery_modmul(0, 5, N, Np, R) == 0
    assert montgomery_modmul(3, 0, N, Np, R) == 0


# 8. Squaring, x=y
def test_self_mul():
    N = 0xFD46AB9F
    R = 1 << 32
    Np = _compute_N_prime(N, R)
    Rinv = pow(R, -1, N)
    x = 0xABCDEF
    result = montgomery_modmul(x, x, N, Np, R)
    expected = (x * x * Rinv) % N
    assert result == expected


# 9. Using MontMul to reproduce an ordinary modular multiplication
def test_equivalent_modmul():
    """MontMul(MontMul(x·R mod N, y·R mod N), 1) = x·y mod N"""
    N = 0xFD46AB9F
    R = 1 << 32
    Np = _compute_N_prime(N, R)
    R_mod_N = R % N
    for x, y in [(123, 456), (1000, 2000)]:
        # Move into the Montgomery domain
        x_mont = (x * R_mod_N) % N
        y_mont = (y * R_mod_N) % N
        # MontMul
        z_mont = montgomery_modmul(x_mont, y_mont, N, Np, R)
        # Move back out of the Montgomery domain
        z = montgomery_modmul(z_mont, 1, N, Np, R)
        expected = (x * y) % N
        assert z == expected, f'x={x} y={y}: got {z}, want {expected}'


# 10. Determinism
def test_determinism():
    N = 17; R = 32; Np = _compute_N_prime(N, R)
    for _ in range(3):
        assert montgomery_modmul(3, 5, N, Np, R) == montgomery_modmul(3, 5, N, Np, R)


def test_redc_matches_definition():
    """Verify REDC itself: U = T*N' mod R, t = (T + U*N)/R, subtract one N when t >= N.
    This depends neither on execution speed nor on undefined behaviour under wrong
    arguments; it checks the algorithm directly."""
    for N in (1009, 2027, 65537):
        R = 1 << (N.bit_length() + 1)
        n_prime = (-pow(N, -1, R)) % R
        for T in (0, 1, N - 1, N, N * 3 + 7, (N - 1) * (N - 1), R - 1):
            U = (T * n_prime) % R
            expect = (T + U * N) // R
            if expect >= N:
                expect -= N
            got = _redc(T, N, n_prime, R)
            assert got == expect, f"_redc({T},{N},...) = {got}, but the definition gives {expect}"
            assert got == (T * pow(R, -1, N)) % N, "the REDC result does not satisfy T*R^{-1} mod N"


def test_modmul_result_comes_from_redc():
    """Runtime check of the data flow: replace _redc with a stub returning a sentinel;
    montgomery_modmul must return that sentinel unchanged.

    An implementation that merely calls _redc, discards the result and computes R^{-1}
    separately fails here -- its return value is unrelated to _redc.
    The sentinel lies in [0, N), so a redundant `% N` or a final conditional subtraction
    does not affect the verdict; two different sentinels are used in turn to rule out the
    coincidence of a result happening to equal one of them.

    This one is best-effort: a style that cannot be stubbed safely (decorator closures
    and the like) is let through,
    The correctness of _redc itself is covered by test_redc_matches_definition."""
    import solution as _m
    N = 1009
    R = 1 << (N.bit_length() + 1)
    n_prime = (-pow(N, -1, R)) % R
    x, y = 123, 456
    seen = []

    for sentinel in (N - 7, 3):
        state = {"calls": seen, "value": sentinel}
        token = _try_patch_helper(_m, "_redc", _stub_redc, state)
        if token is None:
            return
        try:
            out = _m.montgomery_modmul(x, y, N, n_prime, R)
        finally:
            _unpatch_helper(_m, token)
        assert out == sentinel, (
            f"with the return value of _redc replaced by {sentinel}, montgomery_modmul still returned {out}"
            " -- so the main function does not use the result of _redc, which does not follow the REDC flow the statement requires")

    assert seen, "montgomery_modmul never called _redc"
    args, kwargs = seen[0]
    bound = None
    try:
        import inspect
        sig = inspect.signature(_m._redc)          # restored to the original function by now
        kinds = [p.kind for p in sig.parameters.values()]
        if not any(k in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
                   for k in kinds):
            b = sig.bind(*args, **kwargs)
            b.apply_defaults()
            vals = list(b.arguments.values())
            if len(vals) >= 4:
                bound = vals[:4]
    except (TypeError, ValueError):
        bound = None                                # if it does not match, skip the check rather than fail a correct implementation
    if bound is not None:
        T, gotN, gotNp, gotR = bound
        assert (gotN, gotNp, gotR) == (N, n_prime, R), \
            f"the (N, N_prime, R) passed to _redc are wrong: {(gotN, gotNp, gotR)}"
        assert T == (x % N) * (y % N), \
            f"the T passed to _redc should be (x mod N)*(y mod N) = {(x % N) * (y % N)}, actual {T}"


def test_must_be_real_montgomery():
    """Static check (AST): the pow shortcut is banned, and a division by R (>> or //)
    must appear -- that is, (T + U*N)/R is genuinely performed rather than an ordinary modulo."""
    import ast, inspect, textwrap
    import solution as _m
    src = textwrap.dedent(inspect.getsource(_m))
    tree = ast.parse(src)
    bad = [n for n in ast.walk(tree)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
           and n.func.id == "pow" and len(n.args) >= 3]
    assert not bad, "the statement bans the pow shortcut"
    # Division by R may be written as >>, // or divmod -- all three are accepted.
    # This is only a shape hint; what actually blocks "compute R^{-1} and multiply" is the
    # data-flow probe in test_modmul_result_comes_from_redc, and that one is best-effort.
    has_div_by_R = any(
        (isinstance(n, ast.BinOp) and isinstance(n.op, (ast.RShift, ast.FloorDiv)))
        or (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "divmod")
        for n in ast.walk(tree))
    assert has_div_by_R, "no reduction step dividing by R (>>, // or divmod) was found, which does not look like a genuine Montgomery reduction"


def test_no_builtin_pow_runtime():
    """Runtime probe: the three-argument builtin pow is banned.
    An assignment alias (shortcut = pow) and reflective lookup both show up in the c_call event."""
    called = _c_calls_during(montgomery_modmul, 123, 456, 1009, (-pow(1009, -1, 1024)) % 1024, 1024)
    assert "pow" not in called, "a call to the builtin pow was detected: %s" % sorted(called)


# Note: there used to be an upper bound of 200 executed lines here, meant to block the
# "compute R^{-1} yourself" shortcut. But it treated coding style as correctness -- an
# implementation that follows REDC strictly but multiplies big integers through a
# shift-add helper runs thousands of lines and was wrongly flagged as cheating. The two
# checks above now verify REDC semantics directly, so speed is no longer used as a
# proxy for algorithm identity.
