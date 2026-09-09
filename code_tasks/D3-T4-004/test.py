import pytest
from solution import karatsuba_mul

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


def test_basic_small():
    assert karatsuba_mul(3, 7) == 21

def test_zero():
    assert karatsuba_mul(0, 12345) == 0
    assert karatsuba_mul(99999, 0) == 0

def test_one():
    assert karatsuba_mul(1, 10**50) == 10**50

def test_large_numbers():
    a = 12345678901234567890
    b = 98765432109876543210
    assert karatsuba_mul(a, b) == a * b

def test_power_of_two():
    a = 1 << 100
    b = 1 << 200
    assert karatsuba_mul(a, b) == a * b

def test_same_number():
    x = 10**100 + 7
    assert karatsuba_mul(x, x) == x * x

def test_very_large():
    a = 10**500 + 10**300 + 1
    b = 10**400 + 10**200 + 2
    assert karatsuba_mul(a, b) == a * b

def test_negative_raises():
    with pytest.raises(ValueError):
        karatsuba_mul(-5, 10)

def test_base_case_small():
    for a in range(100):
        for b in range(100):
            assert karatsuba_mul(a, b) == a * b

def test_asymmetric():
    big = 2**1024 - 1
    small = 2**256 + 1
    assert karatsuba_mul(big, small) == big * small


def test_must_recurse():
    """Static check (AST): the module must contain a genuinely self-recursive function.
    The recursion may live in a helper (with karatsuba_mul as a mere entry point), but
    dead code such as `if False: karatsuba_mul(...)` will not fool the runtime check below."""
    import ast, inspect, textwrap
    import solution as _m
    tree = ast.parse(textwrap.dedent(inspect.getsource(_m)))
    fns = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    assert fns, "no function definition was found"
    recursive = any(
        any(isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == fn.name
            for c in ast.walk(fn))
        for fn in fns)
    assert recursive, "no function calls itself recursively, but the statement requires Karatsuba divide and conquer"


def test_recursion_splits_operands():
    """Runtime check: genuine Karatsuba splits the operands roughly in half and recurses.
    This records the integer arguments received by each Python function during the call and
    requires at least 3 calls whose argument bit-width falls between 1/4 and 3/4 of the
    original operands -- Karatsuba makes exactly three sub-multiplications per level.
    Wrapping `return x * y` in a dummy recursion (whose arguments are just small counters)
    fails this check."""
    big_x = 0xDEADBEEFCAFEBABE1234567890ABCDEF * (1 << 900) + 12345
    big_y = 0x0FEDCBA0987654321BADC0FFEE123456 * (1 << 900) + 67891
    n = max(big_x.bit_length(), big_y.bit_length())
    lo, hi = n // 4, (3 * n) // 4
    hits = []

    def _prof(frame, event, _arg):
        if event == "call":
            for v in list(frame.f_locals.values())[:4]:
                if isinstance(v, int) and not isinstance(v, bool) \
                        and lo <= v.bit_length() <= hi:
                    hits.append(v.bit_length())
                    break
        return None

    old = _sys.getprofile()
    _sys.setprofile(_prof)
    try:
        got = karatsuba_mul(big_x, big_y)
    finally:
        _sys.setprofile(old)
    assert got == big_x * big_y
    assert len(hits) >= 3, (
        f"only {len(hits)} calls receiving roughly half-width operands were observed, "
        "which does not look like Karatsuba's splitting recursion")


def test_actually_does_the_work():
    """Work check: the work of a divide-and-conquer algorithm must grow with the input size.
    `return x * y` (even wrapped in a dummy recursion to inflate the call count) runs a
    constant number of lines; genuine Karatsuba runs thousands on a 1024-bit input, far
    more than on a 64-bit one."""
    big_x = 0xDEADBEEFCAFEBABE1234567890ABCDEF * (1 << 900) + 12345
    big_y = 0x0FEDCBA0987654321BADC0FFEE123456 * (1 << 900) + 67891
    small_x, small_y = 0xDEADBEEFCAFEBABE, 0x0FEDCBA098765432
    assert karatsuba_mul(big_x, big_y) == big_x * big_y

    big = _lines_executed(karatsuba_mul, big_x, big_y)
    small = _lines_executed(karatsuba_mul, small_x, small_y)
    assert big >= 300, (
        f"a 1024-bit input executed only {big} Python lines, which does not look like real divide and conquer"
        " (the reference implementation runs about 6000)")
    assert big >= 4 * max(small, 1), (
        f"{big} lines on the large input vs {small} on the small one -- the work barely grows with size, "
        "which does not look like a divide-and-conquer recursion")
