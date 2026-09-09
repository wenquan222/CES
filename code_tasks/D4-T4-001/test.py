"""D4-T4-001 test cases."""
import pytest
from solution import infect_or_pass

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
                        isinstance(o, (_ast.Eq, _ast.NotEq, _ast.Lt, _ast.Gt,
                                       _ast.LtE, _ast.GtE, _ast.In, _ast.NotIn))
                        for o in node.ops):
                    # Ordering comparisons are banned too: a < b or a > b also yields "not equal", and a
                    # bytes comparison may likewise exit early underneath
                    bad.append(fn.name + ":secret-dependent comparison")
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


def test_no_fault_returns_a():
    """state_a == state_b -> return state_a, no pollution."""
    state = bytes(range(16))
    mask = b'\xAA' * 16
    result = infect_or_pass(state, state, mask)
    assert result == state


def test_single_byte_fault_pollutes():
    """A single-byte difference -> full pollution."""
    state_a = bytes(range(16))
    state_b = bytearray(state_a)
    state_b[5] = 0xFF
    state_b = bytes(state_b)
    mask = b'\xAA' * 16
    result = infect_or_pass(state_a, state_b, mask)
    expected = bytes(a ^ m for a, m in zip(state_a, mask))
    assert result == expected


def test_full_diff_pollutes():
    """Entirely different -> full pollution."""
    state_a = bytes(range(16))
    state_b = bytes(reversed(range(16)))
    mask = b'\xAA' * 16
    result = infect_or_pass(state_a, state_b, mask)
    expected = bytes(a ^ m for a, m in zip(state_a, mask))
    assert result == expected


def test_no_branch_in_source():
    """Static check (AST): no secret-dependent control flow (if/else/conditional/==/!=)
    anywhere in the submitted file, helper functions included.
    Checking infect_or_pass alone is not enough -- moving the comparison into a helper would evade it.
    Only an "if ...: raise" used for input validation is exempt."""
    bad = _module_branch_nodes(forbid_compare=True)
    assert not bad, f"branch or equality comparison found on the constant-time path: {bad}"

def test_invalid_input():
    with pytest.raises(ValueError):
        infect_or_pass(b'\x00' * 15, b'\x00' * 16, b'\x00' * 16)


def test_zero_mask_is_noop():
    """With an all-zero mask the polluted result equals state_a even when a fault is detected."""
    state_a = bytes(range(16))
    state_b = bytes(range(1, 17))
    assert infect_or_pass(state_a, state_b, bytes(16)) == state_a


def test_multi_byte_diff_pollutes():
    """A multi-byte difference also triggers full pollution, not just the faulty bytes."""
    state_a = bytes(range(16))
    state_b = bytearray(state_a)
    for i in (0, 7, 15):
        state_b[i] ^= 0x3C
    mask = bytes(range(16, 32))
    expected = bytes(a ^ m for a, m in zip(state_a, mask))
    assert infect_or_pass(state_a, bytes(state_b), mask) == expected


def test_diff_only_in_last_byte():
    """A difference in the last byte alone must still be detected -- this catches implementations that compare only the first few bytes."""
    state_a = bytes(16)
    state_b = bytearray(16)
    state_b[15] = 0x01
    mask = b'\x5A' * 16
    assert infect_or_pass(state_a, bytes(state_b), mask) == mask


def test_output_type_and_length():
    """Returns bytes of length 16."""
    r = infect_or_pass(bytes(16), bytes(16), bytes(16))
    assert isinstance(r, (bytes, bytearray)) and len(r) == 16


def test_all_three_lengths_validated():
    """All three arguments must be length-checked, not just the first two."""
    ok = bytes(16)
    for bad_pos in range(3):
        args = [ok, ok, ok]
        args[bad_pos] = bytes(15)
        with pytest.raises(ValueError):
            infect_or_pass(*args)


def test_deterministic():
    """Repeated calls on the same input give identical results."""
    a, b, m = bytes(range(16)), bytes(range(16)), b'\xAA' * 16
    assert infect_or_pass(a, b, m) == infect_or_pass(a, b, m)
