# -*- coding: utf-8 -*-
"""D5-T4-004 tests: compute_nicv (point-wise NICV leakage detection)."""
import pytest
from solution import compute_nicv


# 1. Perfect leakage: zero within-group variance, between-group = total -> NICV = 1.0
def test_perfect_leakage():
    traces = [[0.0], [0.0], [10.0], [10.0]]
    labels = [0, 0, 1, 1]
    nicv = compute_nicv(traces, labels)
    assert abs(nicv[0] - 1.0) < 1e-12


# 2. No leakage (the point is constant): total variance 0 -> NICV = 0.0
def test_no_variance():
    traces = [[3.0], [3.0], [3.0], [3.0]]
    labels = [0, 0, 1, 1]
    nicv = compute_nicv(traces, labels)
    assert nicv[0] == 0.0


# 3. No leakage (variance present but independent of the label, equal group means) -> NICV near 0
def test_independent_of_label():
    traces = [[1.0], [5.0], [1.0], [5.0]]
    labels = [0, 0, 1, 1]
    nicv = compute_nicv(traces, labels)
    assert abs(nicv[0]) < 1e-12


# 4. Partial leakage: 0 < NICV < 1 (hand-computed as 0.9)
def test_partial_leakage():
    traces = [[1.0], [3.0], [7.0], [9.0]]
    labels = [0, 0, 1, 1]
    nicv = compute_nicv(traces, labels)
    assert abs(nicv[0] - 0.9) < 1e-12


# 5. Every NICV lies in [0,1]
def test_range():
    traces = [[1.0, 2.0], [2.0, 2.0], [9.0, 2.0], [8.0, 2.0]]
    labels = [0, 0, 1, 1]
    nicv = compute_nicv(traces, labels)
    for v in nicv:
        assert 0.0 <= v <= 1.0


# 6. Several sample points: the return length is M, point 0 leaks and point 1 is constant
def test_multi_point():
    traces = [[0.0, 3.0], [0.0, 3.0], [10.0, 3.0], [10.0, 3.0]]
    labels = [0, 0, 1, 1]
    nicv = compute_nicv(traces, labels)
    assert len(nicv) == 2
    assert abs(nicv[0] - 1.0) < 1e-12
    assert nicv[1] == 0.0


# 7. More than two classes
def test_multiclass():
    traces = [[0.0], [0.0], [5.0], [5.0], [10.0], [10.0]]
    labels = [0, 0, 1, 1, 2, 2]
    nicv = compute_nicv(traces, labels)
    assert abs(nicv[0] - 1.0) < 1e-12  # zero within-group variance -> NICV=1


# 8. Error: mismatched lengths
def test_length_mismatch():
    with pytest.raises(ValueError):
        compute_nicv([[1.0], [2.0]], [0, 1, 0])


# 9. Errors: ragged traces / empty input / zero sample points
def test_invalid():
    with pytest.raises(ValueError):
        compute_nicv([[1.0, 2.0], [3.0]], [0, 1])
    with pytest.raises(ValueError):
        compute_nicv([], [])
    with pytest.raises(ValueError):
        compute_nicv([[], []], [0, 1])


# 10. Determinism
def test_determinism():
    traces = [[1.0], [3.0], [7.0], [9.0]]
    labels = [0, 0, 1, 1]
    a = compute_nicv(traces, labels)
    b = compute_nicv(traces, labels)
    assert a == b


# ── Contract checks ───────────────────────────────────────────────────────
# The statement bans ready-made implementations. Banning names one by one is
# trivially evaded by assignment aliases, import aliases and getattr reflection,
# so an import whitelist is enforced instead: it does not depend on how the code
# is written. A contract violation is a hard failure, not a partial score.
import ast as _c_ast
import pathlib as _c_path

_ALLOWED_IMPORTS = set()


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
