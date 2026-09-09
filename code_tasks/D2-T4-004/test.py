# -*- coding: utf-8 -*-
"""D2-T4-005 tests: fsa_recover (key recovery by fault sensitivity analysis)."""
import pytest
from solution import fsa_recover, _hw, _pearson


def _make_sens(plaintexts, k_true, a=2.0, b=10.0):
    """Build ideal fault sensitivities: sens = a*HW(p^k_true) + b."""
    return [a * _hw(p ^ k_true) + b for p in plaintexts]


# 1. All 256 plaintexts, no noise, positive correlation -> k_true recovered uniquely
def test_recover_clean():
    pts = list(range(256))
    for k_true in [0x2B, 0x00, 0xFF, 0x53]:
        sens = _make_sens(pts, k_true)
        assert fsa_recover(pts, sens) == k_true


# 2. Recovery also works on a subset of plaintexts (a deterministic, varied subset)
def test_recover_subset():
    pts = [(i * 73 + 11) % 256 for i in range(120)]
    sens = _make_sens(pts, 0x42)
    assert fsa_recover(pts, sens) == 0x42


# 3. Recovery still works with a little noise
def test_recover_with_noise():
    pts = list(range(256))
    k_true = 0x7C
    base = _make_sens(pts, k_true)
    # Deterministic "noise": a slight perturbation indexed by plaintext (far smaller than the HW step)
    sens = [s + 0.05 * ((i * 37) % 7 - 3) for i, s in enumerate(base)]
    assert fsa_recover(pts, sens) == k_true


# 4. _hw computes the Hamming weight correctly
def test_hw():
    assert _hw(0x00) == 0
    assert _hw(0xFF) == 8
    assert _hw(0x0F) == 4
    assert _hw(0x80) == 1


# 5. _pearson gives 1 for a perfect positive correlation
def test_pearson_perfect():
    xs = [1, 2, 3, 4, 5]
    ys = [2, 4, 6, 8, 10]
    assert abs(_pearson(xs, ys) - 1.0) < 1e-9


# 6. _pearson returns 0 on zero variance
def test_pearson_zero_var():
    assert _pearson([3, 3, 3], [1, 2, 3]) == 0.0


# 7. Unequal lengths raise ValueError
def test_length_mismatch():
    with pytest.raises(ValueError):
        fsa_recover([1, 2, 3], [1.0, 2.0])


# 8. Too few samples raise ValueError
def test_too_few():
    with pytest.raises(ValueError):
        fsa_recover([5], [1.0])


# 9. An out-of-range plaintext raises ValueError
def test_byte_out_of_range():
    with pytest.raises(ValueError):
        fsa_recover([1, 256], [1.0, 2.0])
    with pytest.raises(ValueError):
        fsa_recover([1, -1], [1.0, 2.0])


# 10. Determinism, and the return value lies in [0,255]
def test_determinism_and_range():
    pts = list(range(128))
    sens = _make_sens(pts, 0x19)
    a = fsa_recover(pts, sens)
    b = fsa_recover(pts, sens)
    assert a == b == 0x19
    assert 0 <= a <= 255


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
