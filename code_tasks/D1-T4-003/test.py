# -*- coding: utf-8 -*-
"""
D1-T4-003 tests: template_attack_match. 10 test cases.
"""
import numpy as np
import pytest
import time
from typing import Dict, Tuple

from solution import template_attack_match


def _make_templates(K: int, D: int, seed: int = 42) -> Dict[int, Tuple[np.ndarray, np.ndarray]]:
    """
    Build random templates for K classes: mu_k sampled uniformly, Sigma_k = A A^T + 0.1*I (guaranteeing positive definiteness).
    """
    rng = np.random.RandomState(seed)
    templates = {}
    for k in range(K):
        mu = rng.randn(D) * 2.0
        A = rng.randn(D, D)
        cov = A @ A.T / D + 0.1 * np.eye(D)
        templates[k] = (mu, cov)
    return templates


@pytest.fixture
def basic_templates():
    """Standard templates with K=256, D=20; the test_trace is the mu of the true class k_true=0x42 plus a little noise."""
    K, D = 256, 20
    templates = _make_templates(K, D, seed=42)
    k_true = 0x42
    mu_true = templates[k_true][0]
    rng = np.random.RandomState(123)
    test = mu_true + 0.05 * rng.randn(D)
    return test, templates, k_true


# ============== 1. Shape ==============
def test_shape(basic_templates):
    test, templates, _ = basic_templates
    log_lik = template_attack_match(test, templates)
    assert log_lik.shape == (256,)
    assert log_lik.dtype == np.float64


# ============== 2. Correctness (argmax = k_true) ==============
def test_recover_correct_key(basic_templates):
    test, templates, k_true = basic_templates
    log_lik = template_attack_match(test, templates)
    recovered = int(np.argmax(log_lik))
    assert recovered == k_true, f"should recover {k_true:#x}, actual {recovered:#x}"


# ============== 3. Missing class -> -inf ==============
def test_missing_class():
    D = 10
    templates = _make_templates(K=200, D=D, seed=0)  # only 0..199
    test = np.zeros(D)
    log_lik = template_attack_match(test, templates)
    assert log_lik.shape == (256,)
    # Class 250 should be -inf or extremely small
    assert log_lik[250] < -1e15, f"a missing class must give a large negative value, actual {log_lik[250]}"
    # Class 100 should be finite
    assert np.isfinite(log_lik[100])


# ============== 4. Tolerating a singular covariance ==============
def test_singular_covariance():
    D = 10
    templates = {}
    for k in range(5):
        mu = np.random.randn(D)
        cov = np.outer(np.random.randn(D), np.random.randn(D))  # rank-1 -> singular
        templates[k] = (mu, cov)
    test = np.random.randn(D)
    # Must not crash; should return a finite value (or -1e18)
    log_lik = template_attack_match(test, templates)
    assert log_lik.shape == (256,)
    # At least one class value must be finite (the regularization worked)
    finite_count = np.sum(np.isfinite(log_lik))
    assert finite_count >= 1


# ============== 5. No overflow in high dimension D=100 ==============
def test_high_dim_no_overflow():
    K, D = 100, 100
    templates = _make_templates(K, D, seed=7)
    test = np.random.RandomState(7).randn(D)
    log_lik = template_attack_match(test, templates)
    valid_mask = log_lik > -1e17
    # Not all -inf; no NaN
    assert valid_mask.sum() >= K // 2, "most log-likelihoods should still be finite in high dimension"
    assert not np.any(np.isnan(log_lik)), "there must be no NaN"


# ============== 6. A minimal class count, K=2 ==============
def test_few_classes():
    D = 5
    templates = _make_templates(K=2, D=D, seed=0)
    test = templates[0][0] + 0.01 * np.random.RandomState(0).randn(D)
    log_lik = template_attack_match(test, templates)
    assert log_lik.shape == (256,)
    assert log_lik[0] > log_lik[1], "k=0 and k=1 must be distinguishable"


# ============== 7. dtype compatibility (float32 templates) ==============
def test_dtype_compat():
    K, D = 32, 20
    templates = {}
    rng = np.random.RandomState(0)
    for k in range(K):
        mu = rng.randn(D).astype(np.float32)
        A = rng.randn(D, D).astype(np.float32)
        cov = (A @ A.T / D + 0.1 * np.eye(D)).astype(np.float32)
        templates[k] = (mu, cov)
    test = rng.randn(D).astype(np.float32)
    log_lik = template_attack_match(test, templates)
    assert log_lik.shape == (256,)
    assert log_lik.dtype == np.float64


# ============== 8. Performance (D=50, K=256, single trace) ==============
def test_performance():
    K, D = 256, 50
    templates = _make_templates(K, D, seed=99)
    test = np.random.RandomState(99).randn(D)
    start = time.time()
    log_lik = template_attack_match(test, templates)
    elapsed = time.time() - start
    assert elapsed < 1.0, f"D=50/K=256 on a single trace should take < 1s, actual {elapsed:.3f}s"
    assert log_lik.shape == (256,)


# ============== 9. Determinism ==============
def test_determinism(basic_templates):
    test, templates, _ = basic_templates
    log_lik_1 = template_attack_match(test, templates)
    log_lik_2 = template_attack_match(test, templates)
    np.testing.assert_array_equal(log_lik_1, log_lik_2)


# ============== 10. Monotonicity: closer means higher log-likelihood ==============
def test_monotone_similarity():
    D = 15
    rng = np.random.RandomState(0)
    mu = rng.randn(D)
    cov = np.eye(D)
    templates = {0: (mu, cov)}
    # test1 is close to mu, test2 is far
    test1 = mu + 0.1 * rng.randn(D)
    test2 = mu + 5.0 * rng.randn(D)
    log_lik_1 = template_attack_match(test1, templates)
    log_lik_2 = template_attack_match(test2, templates)
    assert log_lik_1[0] > log_lik_2[0], "the closer test_trace must have the larger log-likelihood"


# ── Contract checks ───────────────────────────────────────────────────────
# The statement bans ready-made implementations. Banning names one by one is
# trivially evaded by assignment aliases, import aliases and getattr reflection,
# so an import whitelist is enforced instead: it does not depend on how the code
# is written. A contract violation is a hard failure, not a partial score.
import ast as _c_ast
import pathlib as _c_path

_ALLOWED_IMPORTS = {'typing', 'numpy', 'math'}


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


def test_contract_logdet_not_via_det():
    """log(det(...)) is banned: it under/overflows in high dimension, which is
    exactly what slogdet (or a Cholesky factorization) exists to avoid."""
    bad = [n for n in _c_ast.walk(_c_ast.parse(_c_source()))
           if isinstance(n, _c_ast.Attribute) and n.attr == "det"]
    assert not bad, "log(np.linalg.det(...)) is banned; use slogdet or Cholesky"
