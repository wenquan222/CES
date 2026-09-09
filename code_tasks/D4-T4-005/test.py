"""D4-T4-005 test cases."""
import pytest
from solution import montgomery_ladder

# Test curve: y² = x³ + 2x + 3 mod 97, with base point G = (1, 54).
# Check: 54² = 2916 ≡ 6 (mod 97) and 1³ + 2·1 + 3 = 6, so G is on the curve.
# b = 3 ≠ 0, so (0, 0) is not a curve point and is unambiguous as the
# point-at-infinity sentinel the statement specifies.
P = 97
A = 2
GX, GY = 1, 54

def test_identity_k1():
    """k=1 returns the point itself"""
    result = montgomery_ladder(1, GX, GY, P, A)
    assert result == (GX, GY)

def test_double_consistency():
    """k*G + k*G should equal 2k*G (but we can't easily do addition, just check basic consistency)"""
    r1 = montgomery_ladder(2, GX, GY, P, A)
    r2 = montgomery_ladder(3, GX, GY, P, A)
    # Ensure they return valid points on the curve
    for x, y in [r1, r2]:
        lhs = (y * y) % P
        rhs = (x * x * x + A * x + 3) % P  # b=3
        assert lhs == rhs, f"Point ({x},{y}) is not on curve"

def test_small_k():
    """Test with small k values"""
    for k in [1, 2, 3, 5, 10]:
        x, y = montgomery_ladder(k, GX, GY, P, A)
        lhs = (y * y) % P
        rhs = (x * x * x + A * x + 3) % P
        assert lhs == rhs, f"k={k}: point not on curve"

def test_identity_point():
    """k=0 or large multiple should be identity"""
    result = montgomery_ladder(0, GX, GY, P, A)
    # Identity is (0,0) in our convention — but k=0 with MSB→LSB iteration might give (0,0)
    # Actually k=0 has bit_length()=0 so the loop doesn't execute, returning R0=(0,0)
    assert result == (0, 0)

def test_deterministic():
    r1 = montgomery_ladder(7, GX, GY, P, A)
    r2 = montgomery_ladder(7, GX, GY, P, A)
    assert r1 == r2


def test_2g_exact():
    # 2G on y^2=x^3+2x+3 mod 97 with G=(1,54) -> (92,81) (verified by hand)
    assert montgomery_ladder(2, GX, GY, P, A) == (92, 81)

def test_distinct_points():
    pts = [montgomery_ladder(k, GX, GY, P, A) for k in (2, 3, 5)]
    assert len(set(pts)) == 3

def test_more_k_on_curve():
    for k in (4, 6, 8, 11, 20):
        x, y = montgomery_ladder(k, GX, GY, P, A)
        assert (y * y) % P == (x * x * x + A * x + 3) % P, f"k={k} not on curve"

def test_large_k_on_curve():
    x, y = montgomery_ladder(96, GX, GY, P, A)
    assert (y * y) % P == (x * x * x + A * x + 3) % P

def test_k4_equals_double_double_on_curve():
    # 4G must lie on the curve and differ from 2G and 3G
    p4 = montgomery_ladder(4, GX, GY, P, A)
    assert p4 != montgomery_ladder(2, GX, GY, P, A)
    x, y = p4
    assert (y * y) % P == (x * x * x + A * x + 3) % P


# ── Algorithm-constraint checks ───────────────────────────────────────
# The statement declares four process constraints (no bit-dependent control
# flow inside a ladder iteration; the R0/R1 lockstep structure; no external
# elliptic-curve library; one point addition and one doubling per bit, selected
# branch-free). None of them was tested: the ten functional cases above check
# outputs on one curve, which an ordinary double-and-add, a bit-branching
# implementation, or a table hard-coded for the k values used here would all
# pass. The checks below test the constraints themselves.
import ast as _ast
import inspect as _inspect
import sys as _sys
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


def _ladder_function():
    for n in _ast.walk(_sol_tree()):
        if isinstance(n, _ast.FunctionDef) and n.name == "montgomery_ladder":
            return n
    raise AssertionError("montgomery_ladder is not defined at module level")


def _ladder_loop_branches():
    """Branches inside the ladder loop itself.

    Nested helper definitions are skipped on purpose: the statement exempts the
    point-at-infinity and doubling special cases inside point_add / point_double,
    and bans only a branch that selects different work per scalar bit.
    """
    bad = []
    for loop in [n for n in _ast.walk(_ladder_function())
                 if isinstance(n, (_ast.For, _ast.While))]:
        for stmt in loop.body:
            if isinstance(stmt, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                continue
            for node in _ast.walk(stmt):
                if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef, _ast.Lambda)):
                    break
                if isinstance(node, _ast.If):
                    bad.append("if")
                elif isinstance(node, _ast.IfExp):
                    bad.append("conditional expression")
                elif isinstance(node, getattr(_ast, "Match", ())):
                    bad.append("match/case")
    return bad


def _lines_executed(fn, *args):
    count = [0]

    def _trace(_frame, event, _arg):
        if event == "line":
            count[0] += 1
        return _trace

    old = _sys.gettrace()
    _sys.settrace(_trace)
    try:
        fn(*args)
    finally:
        _sys.settrace(old)
    return count[0]


def test_contract_import_allowlist():
    """Constraint 3: no external elliptic-curve library."""
    extra = _imported_modules() - _ALLOWED_IMPORTS
    assert not extra, "the statement permits no import; found: %s" % sorted(extra)


def test_contract_no_dynamic_lookup():
    """getattr / eval / exec / __import__ would let a banned library back in."""
    banned = {"getattr", "eval", "exec", "compile", "__import__", "globals", "vars", "locals"}
    hits = sorted({n.func.id for n in _ast.walk(_sol_tree())
                   if isinstance(n, _ast.Call) and isinstance(n.func, _ast.Name)
                   and n.func.id in banned})
    assert not hits, "reflective lookup is banned; found: %s" % hits


def test_contract_no_branch_in_ladder_iteration():
    """Constraints 1 and 6: the iteration must select branch-free, not by if/else."""
    bad = _ladder_loop_branches()
    assert not bad, (
        "a ladder iteration must not branch on the scalar bit; found %s. "
        "Select with an arithmetic conditional swap instead." % bad)


@pytest.mark.parametrize("bits", [12, 20])
def test_contract_work_independent_of_hamming_weight(bits):
    """The security property itself: equal work per bit whatever the bit is.

    Two scalars of the same bit length but very different Hamming weight must
    execute the same number of Python lines. A Montgomery ladder does one
    addition and one doubling per bit either way, so the counts match exactly.
    Double-and-add does an extra addition per set bit and diverges by hundreds
    of lines, which is precisely the SPA signal the statement asks to remove.
    """
    k_dense = (1 << bits) - 1
    k_sparse = 1 << (bits - 1)
    n_dense = _lines_executed(montgomery_ladder, k_dense, GX, GY, P, A)
    n_sparse = _lines_executed(montgomery_ladder, k_sparse, GX, GY, P, A)
    assert n_dense == n_sparse, (
        "work depends on the Hamming weight of the scalar: %d lines for %d "
        "set bits against %d lines for 1 set bit. Every bit must cost one "
        "addition and one doubling." % (n_dense, bits, n_sparse))
