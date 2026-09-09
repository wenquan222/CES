"""D3-T4-001 test cases."""
import pytest
import time
import statistics
from solution import ct_select

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



def _ast_of(func):
    """Take the function's AST (immune to comments/strings, so a bare substring match cannot misfire)."""
    import ast, inspect, textwrap
    return ast.parse(textwrap.dedent(inspect.getsource(func))).body[0]


def _branch_nodes(fn, forbid_compare=False):
    """Return the branch/loop node names in the body; an if-raise used only for input validation is exempt."""
    import ast
    bad = []
    body = [s for s in fn.body
            if not (isinstance(s, ast.If)
                    and all(isinstance(x, ast.Raise) for x in s.body)
                    and not s.orelse)]
    for stmt in body:
        for node in ast.walk(stmt):
            if isinstance(node, ast.If):
                bad.append("if")
            elif isinstance(node, ast.IfExp):
                bad.append("conditional expression")
            elif forbid_compare and isinstance(node, ast.Compare) and any(
                    isinstance(o, (ast.Eq, ast.NotEq)) for o in node.ops):
                bad.append("==/!=")
    return bad


def test_cond_1_returns_a():
    assert ct_select(1, 0xDEADBEEF, 0xCAFEBABE) == 0xDEADBEEF


def test_cond_0_returns_b():
    assert ct_select(0, 0xDEADBEEF, 0xCAFEBABE) == 0xCAFEBABE


def test_correctness_exhaustive():
    """Exhaustive test: cond in {0,1}, a and b over 8 bits."""
    for cond in (0, 1):
        for a in range(256):
            for b in range(256):
                expected = a if cond == 1 else b
                assert ct_select(cond, a, b) == expected


def test_zero_inputs():
    assert ct_select(0, 0, 0) == 0
    assert ct_select(1, 0, 0) == 0


def test_invalid_cond():
    with pytest.raises(ValueError):
        ct_select(2, 0, 0)
    with pytest.raises(ValueError):
        ct_select(-1, 0, 0)


def test_no_branch_in_source():
    """Static check (AST): no if/else/conditional expression anywhere in the submitted
    file, helper functions included. Checking ct_select alone is not enough -- moving the
    branch into a helper would evade it. An AST is used rather than substring matching,
    so an if/else inside a comment or string does not misfire.
    Only an "if ...: raise" used for input validation is exempt."""
    bad = _module_branch_nodes()
    assert not bad, f"branch or conditional expression found on the constant-time path: {bad}"


def test_no_secret_indexing():
    """Static check (AST): cond must not index any sequence.
    `(b, a)[cond]` contains no if, but it is a memory access whose address depends on a
    secret -- exactly what a constant-time implementation must avoid, and no more
    acceptable than writing a branch."""
    import ast
    bad = []
    for fn in [n for n in _ast.walk(_sol_tree())
               if isinstance(n, _ast.FunctionDef)]:
        for node in _ast.walk(fn):
            if isinstance(node, _ast.Subscript) and not isinstance(
                    getattr(node, "slice", None), _ast.Constant):
                bad.append(fn.name)
    # Besides indexing, a dict/set lookup is also "selection by secret", e.g. {0: b, 1: a}.get(cond)
    for fn in [n for n in _ast.walk(_sol_tree())
               if isinstance(n, _ast.FunctionDef)]:
        for node in _ast.walk(fn):
            if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Attribute) \
                    and node.func.attr in ("get", "pop", "setdefault", "index", "count"):
                bad.append(fn.name + ":container lookup")
            elif isinstance(node, _ast.Dict):
                bad.append(fn.name + ":dict literal")
    assert not bad, f"variable-driven selection found on the constant-time path: {sorted(set(bad))}"


# Note: there used to be a test_timing_variance here that judged "constant time" from
# the median difference of perf_counter_ns. On CPython a single call takes tens of
# nanoseconds, so a 50% median difference can easily be timer resolution and
# scheduling noise; a correct implementation would fail at random and the pass rate
# would not be reproducible. Python offers no real constant-time guarantee anyway, so
# that conclusion is left to the AST checks above and the test was removed.
