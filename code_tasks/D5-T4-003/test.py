# -*- coding: utf-8 -*-
"""D5-T4-003 tests: monobit_frequency_test (the SP 800-22 monobit frequency test)."""
import pytest
from solution import monobit_frequency_test, _erfc


# 1. An all-zero sequence: highly non-random, the P-value should be near 0 (well below 0.01)
def test_all_zeros():
    p = monobit_frequency_test([0] * 100)
    assert p < 0.01


# 2. An all-one sequence: equally non-random
def test_all_ones():
    p = monobit_frequency_test([1] * 100)
    assert p < 0.01


# 3. Perfectly balanced (alternating 0/1): Sn=0 -> P-value = erfc(0) = 1.0
def test_balanced():
    bits = [0, 1] * 50  # fifty 0s and fifty 1s
    p = monobit_frequency_test(bits)
    assert abs(p - 1.0) < 1e-9


# 4. The official SP 800-22 example: eps = 1011010101 (n=10), P-value = 0.527089 approx.
def test_nist_example():
    bits = [1, 0, 1, 1, 0, 1, 0, 1, 0, 1]
    p = monobit_frequency_test(bits)
    assert abs(p - 0.527089) < 1e-3


# 5. erfc(0) = 1 (the approximation is accurate to about 1e-7, so the tolerance is 1e-6)
def test_erfc_zero():
    assert abs(_erfc(0.0) - 1.0) < 1e-6


# 6. A known erfc value: erfc(1) = 0.1572992 approx.
def test_erfc_known():
    assert abs(_erfc(1.0) - 0.1572992) < 1e-5


# 7. erfc symmetry: erfc(-x) = 2 - erfc(x)
def test_erfc_symmetry():
    assert abs(_erfc(-0.7) - (2.0 - _erfc(0.7))) < 1e-9


# 8. The P-value lies in [0,1]
def test_pvalue_range():
    for bits in ([0, 1, 1, 0, 1, 0, 0, 1], [1, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1]):
        p = monobit_frequency_test(bits)
        assert 0.0 <= p <= 1.0


# 9. Errors: empty sequence / an element outside 0/1
def test_invalid_input():
    with pytest.raises(ValueError):
        monobit_frequency_test([])
    with pytest.raises(ValueError):
        monobit_frequency_test([0, 1, 2, 1])
    with pytest.raises(ValueError):
        monobit_frequency_test([0, 1, -1])


# 10. Determinism, and a slight imbalance gives a P-value in (0,1)
def test_determinism_and_partial():
    bits = [1] * 60 + [0] * 40  # biased towards 1
    a = monobit_frequency_test(bits)
    b = monobit_frequency_test(bits)
    assert a == b
    assert 0.0 < a < 1.0


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


def test_contract_erfc_not_delegated():
    """math.erfc / scipy.special.erfc must not be called -- the numerical
    approximation itself is the point of this task. A runtime probe catches the
    call under any name, so an import alias does not help."""
    import sys as _c_sys
    called = []

    def _c_probe(frame, event, arg):
        if event == "c_call" and getattr(arg, "__name__", "") == "erfc":
            called.append(getattr(arg, "__module__", "?"))
        return None

    _c_sys.setprofile(_c_probe)
    try:
        _erfc(0.7)
    finally:
        _c_sys.setprofile(None)
    assert not called, "a call to a library erfc was detected: %s" % sorted(set(called))
