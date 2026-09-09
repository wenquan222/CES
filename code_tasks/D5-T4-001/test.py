# -*- coding: utf-8 -*-
"""D5-T4-001 tests: compute_tvla (TVLA first-order Welch t-test)."""
import math
import pytest
from solution import compute_tvla, THRESHOLD


# 1. The threshold constant is correct
def test_threshold_constant():
    assert THRESHOLD == 4.5


# 2. len(t_values) equals the number of sample points
def test_length():
    fixed = [[0, 1, 0], [1, 0, 1], [0, 1, 0]]
    random = [[0, 1, 0], [1, 0, 1], [0, 1, 0]]
    t_values, leak = compute_tvla(fixed, random)
    assert len(t_values) == 3


# 3. Two identically distributed groups -> no leakage (leak_points empty, |t| small)
def test_no_leakage():
    # Two identical alternating distributions with equal means at each point -> t = 0
    fixed = [[0, 10], [1, 11]] * 25   # 50 traces
    random = [[0, 10], [1, 11]] * 25  # 50 traces
    t_values, leak = compute_tvla(fixed, random)
    assert leak == []
    for t in t_values:
        assert abs(t) < 4.5


# 4. A large mean difference -> leakage detected (|t| >= 4.5)
def test_strong_leakage():
    # fixed sits near 0/1 and random near 100/101: small variance, large mean gap
    fixed = [[0, 0], [1, 1]] * 50    # mean 0.5
    random = [[100, 100], [101, 101]] * 50  # mean 100.5
    t_values, leak = compute_tvla(fixed, random)
    # Both time points must be flagged as leaking
    assert 0 in leak and 1 in leak
    for t in t_values:
        assert abs(t) >= 4.5


# 5. Numerical correctness of the Welch formula (against a hand computation)
def test_welch_formula_exact():
    # fixed=[1,2,3] → mf=2, vf=1 ; random=[4,5,6] → mr=5, vr=1
    # denom = sqrt(1/3 + 1/3) = sqrt(2/3) ; t = (2-5)/denom
    fixed = [[1], [2], [3]]
    random = [[4], [5], [6]]
    t_values, leak = compute_tvla(fixed, random)
    expected = (2 - 5) / math.sqrt(1 / 3 + 1 / 3)
    assert abs(t_values[0] - expected) < 1e-9


# 6. Unequal group sizes are handled (the advantage of Welch)
def test_unequal_group_sizes():
    fixed = [[0], [1], [0], [1]]        # 4 traces
    random = [[10], [11], [10]]          # 3 traces
    t_values, leak = compute_tvla(fixed, random)
    assert len(t_values) == 1
    # A mean gap of about 10.17 with small variance -> strong leakage
    assert abs(t_values[0]) >= 4.5


# 7. leak_points is exactly the set of above-threshold indices (one leaking point, one not)
def test_leak_points_indices():
    # Time point 0 shows no difference; time point 1 shows a large one
    fixed = [[5, 0], [6, 1]] * 30
    random = [[5, 100], [6, 101]] * 30
    t_values, leak = compute_tvla(fixed, random)
    assert 0 not in leak       # the two groups are identical at point 0
    assert 1 in leak           # point 1 differs greatly
    assert abs(t_values[0]) < 4.5
    assert abs(t_values[1]) >= 4.5


# 8. Empty input raises ValueError
def test_empty_raises():
    with pytest.raises(ValueError):
        compute_tvla([], [[1, 2]])
    with pytest.raises(ValueError):
        compute_tvla([[1, 2]], [])


# 9. A single trace (variance not estimable) raises ValueError
def test_too_few_traces():
    with pytest.raises(ValueError):
        compute_tvla([[1, 2]], [[3, 4], [5, 6]])
    with pytest.raises(ValueError):
        compute_tvla([[1, 2], [3, 4]], [[5, 6]])


# 10. Inconsistent lengths raise ValueError; plus determinism
def test_length_mismatch_and_determinism():
    with pytest.raises(ValueError):
        compute_tvla([[1, 2], [3]], [[4, 5], [6, 7]])     # ragged fixed group
    with pytest.raises(ValueError):
        compute_tvla([[1, 2], [3, 4]], [[5, 6, 7], [8, 9, 10]])  # the two groups differ in L
    # Determinism: the same input twice gives the same result
    fixed = [[1, 2], [3, 4], [5, 6]]
    random = [[2, 1], [4, 3], [6, 5]]
    a = compute_tvla(fixed, random)
    b = compute_tvla(fixed, random)
    assert a == b


# ── Contract checks ───────────────────────────────────────────────────────
# The statement bans ready-made implementations. Banning names one by one is
# trivially evaded by assignment aliases, import aliases and getattr reflection,
# so an import whitelist is enforced instead: it does not depend on how the code
# is written. A contract violation is a hard failure, not a partial score.
import ast as _c_ast
import pathlib as _c_path

_ALLOWED_IMPORTS = {'math'}


def _c_source():
    return _c_path.Path(__file__).with_name("solution.py").read_text(encoding="utf-8")


def test_contract_import_whitelist():
    """Only the whitelisted modules may be imported."""
    used = set()
    for node in _c_ast.walk(_c_ast.parse(_c_source())):
        if isinstance(node, _c_ast.Import):
            used |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, _c_ast.ImportFrom) and node.module:
            used.add(node.module.split(".")[0])
    extra = sorted(used - _ALLOWED_IMPORTS)
    assert not extra, (
        "the statement permits only %s; extra imports found: %s"
        % (sorted(_ALLOWED_IMPORTS) or "no module at all", extra))


def test_contract_no_reflection():
    """getattr / eval / exec / __import__ would let a banned module back in."""
    bad = sorted({
        n.func.id
        for n in _c_ast.walk(_c_ast.parse(_c_source()))
        if isinstance(n, _c_ast.Call) and isinstance(n.func, _c_ast.Name)
        and n.func.id in {"getattr", "eval", "exec", "__import__", "globals", "vars"}
    })
    assert not bad, "reflective lookup may not be used to evade the import whitelist: %s" % bad
