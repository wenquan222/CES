# -*- coding: utf-8 -*-
"""D5-T4-002 tests: min_entropy (min-entropy estimation)."""
import math
import pytest
from solution import min_entropy


# 1. A uniform binary sequence -> H_min = 1.0
def test_uniform_binary():
    assert abs(min_entropy([0, 1] * 50) - 1.0) < 1e-9


# 2. All identical -> H_min = 0.0
def test_constant():
    assert abs(min_entropy([5] * 10) - 0.0) < 1e-9


# 3. Uniform over 4 values -> H_min = 2.0
def test_uniform_four():
    assert abs(min_entropy([0, 1, 2, 3] * 25) - 2.0) < 1e-9


# 4. Uniform over 8 values -> H_min = 3.0
def test_uniform_eight():
    assert abs(min_entropy(list(range(8)) * 10) - 3.0) < 1e-9


# 5. A biased sequence with max_p=0.75 -> H_min = -log2(0.75) = 0.4150 approx.
def test_biased_075():
    # [0,0,0,1]: the value 0 occurs 3/4 of the time
    assert abs(min_entropy([0, 0, 0, 1]) - (-math.log2(0.75))) < 1e-9


# 6. A bias of max_p=0.7 -> H_min = -log2(0.7) = 0.5146 approx.
def test_biased_070():
    # seven 0s and three 1s
    samples = [0] * 7 + [1] * 3
    assert abs(min_entropy(samples) - (-math.log2(0.7))) < 1e-9


# 7. Empty input raises ValueError
def test_empty_raises():
    with pytest.raises(ValueError):
        min_entropy([])


# 8. A single sample -> H_min = 0.0
def test_single_sample():
    assert abs(min_entropy([7]) - 0.0) < 1e-9


# 9. H_min <= Shannon entropy (min-entropy is the more conservative measure)
def test_min_entropy_le_shannon():
    samples = [0, 0, 0, 1]  # a biased sequence
    h_min = min_entropy(samples)
    # Shannon entropy
    p0, p1 = 0.75, 0.25
    h_shannon = -(p0 * math.log2(p0) + p1 * math.log2(p1))
    assert h_min <= h_shannon + 1e-12
    assert abs(h_min - (-math.log2(0.75))) < 1e-9


# 10. Determinism, plus support for non-numeric hashable types (bytes / strings)
def test_determinism_and_hashable():
    samples = ['a', 'a', 'b', 'c']  # max_p = 0.5 → H_min = 1.0
    a = min_entropy(samples)
    b = min_entropy(samples)
    assert a == b
    assert abs(a - 1.0) < 1e-9


# ── Contract checks ───────────────────────────────────────────────────────
# The statement bans ready-made implementations. Banning names one by one is
# trivially evaded by assignment aliases, import aliases and getattr reflection,
# so an import whitelist is enforced instead: it does not depend on how the code
# is written. A contract violation is a hard failure, not a partial score.
import ast as _c_ast
import pathlib as _c_path

_ALLOWED_IMPORTS = {'math', 'collections'}


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
