import numpy as np
import pytest
from solution import compute_nicv

AES_SBOX = [
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16,
]

def test_nicv_shape():
    """The output shape must be (T,)."""
    np.random.seed(42)
    N, T = 500, 100
    traces = np.random.randn(N, T) * 0.1 + 0.5
    iv = np.random.randint(0, 256, N)
    result = compute_nicv(traces, iv)
    assert result.shape == (T,)

def test_nicv_range():
    """NICV values must lie in [0, 1]."""
    np.random.seed(42)
    N, T = 500, 100
    traces = np.random.randn(N, T) * 0.1 + 0.5
    iv = np.random.randint(0, 256, N)
    result = compute_nicv(traces, iv)
    assert np.all(result >= 0)
    assert np.all(result <= 1)

def test_nicv_with_signal():
    """At a leaking time point the NICV must be markedly higher than in the signal-free region."""
    np.random.seed(42)
    N, T = 500, 100
    traces = np.random.randn(N, T) * 0.05
    key = 0x2B
    plaintexts = np.random.randint(0, 256, N)
    iv = np.array([AES_SBOX[p ^ key] for p in plaintexts])
    for i in range(N):
        traces[i, 40] += 0.15 * (iv[i] % 16)
    result = compute_nicv(traces, iv)
    assert result[40] > 0.01
    assert result[40] > np.median(result)

def test_nicv_no_signal():
    """With no signal every NICV must be near 0."""
    np.random.seed(42)
    N, T = 1000, 20
    traces = np.random.randn(N, T) * 0.03
    iv = np.random.randint(0, 16, N)
    result = compute_nicv(traces, iv)
    assert np.max(result) < 0.15

def test_nicv_constant_signal():
    """All trace values identical (zero variance) -> NICV=0."""
    np.random.seed(42)
    N, T = 200, 5
    traces = np.ones((N, T)) * 0.5
    iv = np.random.randint(0, 256, N)
    result = compute_nicv(traces, iv)
    assert np.all(result == 0.0)

def test_nicv_small_num_bins():
    """A custom num_bins argument (which must not change the result)."""
    np.random.seed(42)
    N, T = 500, 50
    traces = np.random.randn(N, T) * 0.05 + 0.3
    iv = np.random.randint(0, 256, N)
    result = compute_nicv(traces, iv, num_bins=10)
    assert result.shape == (T,)
    assert np.all(result >= 0) and np.all(result <= 1)

def test_nicv_stress_small_data():
    """A small sample (N=20) must still give the right shape without crashing."""
    np.random.seed(42)
    N, T = 20, 10
    traces = np.random.randn(N, T) * 0.05 + 0.3
    iv = np.random.randint(0, 256, N)
    result = compute_nicv(traces, iv)
    assert result.shape == (T,)
    assert not np.any(np.isnan(result))

def test_nicv_deterministic():
    """Same input -> same output."""
    np.random.seed(42)
    N, T = 200, 30
    traces = np.random.randn(N, T) * 0.05 + 0.3
    iv = np.random.randint(0, 256, N)
    r1 = compute_nicv(traces, iv)
    r2 = compute_nicv(traces, iv)
    np.testing.assert_array_almost_equal(r1, r2)

def test_nicv_few_classes():
    """The boundary case where the intermediate value takes only 2 distinct values."""
    np.random.seed(42)
    N, T = 500, 30
    traces = np.random.randn(N, T) * 0.05 + 0.3
    iv = np.random.choice([0, 255], N)
    result = compute_nicv(traces, iv)
    assert result.shape == (T,)
    assert np.all(result >= 0) and np.all(result <= 1)

def test_nicv_multi_signal():
    """Several leaking time points -> the NICV is high at each of them."""
    np.random.seed(99)
    N, T = 600, 80
    key = 0x5C
    plaintexts = np.random.randint(0, 256, N)
    iv = np.array([AES_SBOX[p ^ key] for p in plaintexts])
    traces = np.random.randn(N, T) * 0.03
    for i in range(N):
        traces[i, 20] += 0.12 * (iv[i] % 8)
        traces[i, 55] += 0.12 * ((iv[i] >> 4) % 8)
    result = compute_nicv(traces, iv)
    assert result[20] > 0.005
    assert result[55] > 0.005
    assert result[20] > np.median(result) or result[55] > np.median(result)


# ── Numeric oracle ────────────────────────────────────────────────────
# Review round 10 pointed out that 8 of the 10 cases above only checked shape /
# the [0,1] range / no NaN / reproducibility, so an all-zero implementation passed
# 8/10 -- exactly the 0.8 line in the statement. The four cases below are
# independent numeric oracles aimed at "right shape, wrong numbers".
#
# The statement gives only the definition NICV[t] = Var(E[L[t]|V]) / Var(L[t]) and
# does not say whether the between-class variance is weighted by class size. Every
# construction below uses equal class sizes, where the two conventions coincide, so
# neither is failed; the one point-wise comparison against an independent
# implementation (_matches_independent_impl) accepts both conventions.


def _nicv_pure_python(traces, iv, weighted):
    """An independent pure-Python loop implementation, sharing no code path with the vectorized one under test."""
    N = len(traces)
    T = len(traces[0])
    out = []
    for t in range(T):
        col = [float(traces[i][t]) for i in range(N)]
        mu = sum(col) / N
        var_total = sum((c - mu) ** 2 for c in col) / N
        groups = {}
        for i in range(N):
            groups.setdefault(int(iv[i]), []).append(col[i])
        stats = [(len(g), sum(g) / len(g)) for g in groups.values()]
        if weighted:
            gm = sum(n * m for n, m in stats) / N
            var_between = sum(n * (m - gm) ** 2 for n, m in stats) / N
        else:
            gm = sum(m for _, m in stats) / len(stats)
            var_between = sum((m - gm) ** 2 for _, m in stats) / len(stats)
        out.append(0.0 if var_total <= 1e-12 else var_between / var_total)
    return out


def test_nicv_oracle_no_within_class_noise():
    """Zero within-class variance -> all variance is between-class -> NICV is exactly 1;

    adding within-class spread must bring it down. This depends on no convention:
    Var(L) = Var(E[L|V]) + E[Var(L|V)], so the ratio is 1 when the within-class term is 0.
    The second half also rules out an implementation that always returns the constant 1.
    """
    N, T = 400, 8
    iv = np.array([0] * (N // 2) + [1] * (N // 2))
    sign = np.where(iv == 0, -1.0, 1.0)
    amp = np.arange(1, T + 1, dtype=float)
    traces = sign[:, None] * amp[None, :]
    result = compute_nicv(traces, iv)
    assert np.allclose(result, 1.0, atol=1e-9), f'NICV must be 1 when there is no within-class noise, got {result}'

    # Same data with a deterministic within-class spread of +/-4 added; NICV must now be clearly below 1
    within = np.where(np.arange(N) % 2 == 0, 4.0, -4.0)
    traces2 = sign[:, None] * amp[None, :] + within[:, None]
    result2 = compute_nicv(traces2, iv)
    assert np.all(result2 < 0.95), f'with within-class spread the NICV must not stay near 1, got {result2}'


def test_nicv_oracle_closed_form():
    """Closed form: with between-class amplitude a and within-class spread b,

    NICV = a^2 / (a^2 + b^2), independent of the random draw. Taking a = 3 and b = 4
    gives NICV = 9/25 = 0.36 exactly. The two classes have equal sizes, so the weighted
    and unweighted conventions agree on this construction.
    """
    a, b = 3.0, 4.0
    N, T = 400, 6
    iv = np.array([0] * (N // 2) + [1] * (N // 2))
    class_term = np.where(iv == 0, -a, a)
    within_term = np.where(np.arange(N) % 2 == 0, b, -b)
    traces = np.tile((class_term + within_term)[:, None], (1, T))
    result = compute_nicv(traces, iv)
    expected = a ** 2 / (a ** 2 + b ** 2)
    assert np.allclose(result, expected, atol=1e-9), \
        f'the closed form gives {expected}, got {result}'


def test_nicv_oracle_monotone_in_signal():
    """The signal amplitude increases point by point, so the NICV must increase strictly (ruling out any constant return)."""
    amps = np.array([0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
    b = 2.0
    N = 400
    iv = np.array([0] * (N // 2) + [1] * (N // 2))
    sign = np.where(iv == 0, -1.0, 1.0)
    within = np.where(np.arange(N) % 2 == 0, b, -b)
    traces = sign[:, None] * amps[None, :] + within[:, None]
    result = compute_nicv(traces, iv)
    assert np.all(np.diff(result) > 1e-9), f'NICV must increase strictly with the signal amplitude, got {result}'
    expected = amps ** 2 / (amps ** 2 + b ** 2)
    assert np.allclose(result, expected, atol=1e-9), \
        f'expected {expected}, got {result}'


def test_nicv_oracle_matches_independent_impl():
    """Point-wise comparison with an independent pure-Python implementation; both the weighted and unweighted between-class conventions count as correct."""
    rng = np.random.RandomState(20260805)
    N, T = 800, 12
    iv = rng.randint(0, 8, N)          # 8 classes, about 100 traces each, so no class has fewer than 2 samples
    traces = rng.randn(N, T) * 0.05
    for i in range(N):
        traces[i, 3] += 0.08 * (iv[i] % 4)
        traces[i, 9] += 0.05 * iv[i]
    result = np.asarray(compute_nicv(traces, iv), dtype=float)
    cand = [np.asarray(_nicv_pure_python(traces, iv, w), dtype=float) for w in (True, False)]
    errs = [float(np.max(np.abs(result - c))) for c in cand]
    assert min(errs) < 1e-8, \
        f'disagrees with the independent implementation: max deviation {errs[0]:.3e} weighted, {errs[1]:.3e} unweighted'


# ── Algorithm-constraint checks ───────────────────────────────────────
# The statement declares a constraint on *how* the answer must be produced, and
# nothing above tested it. The primary criterion here is an import allowlist
# rather than a list of banned names: a name ban is defeated by an assignment
# alias, an import alias or getattr reflection, whereas an allowlist does not
# depend on how the candidate writes it.
import ast as _ast
import sys as _sys
import inspect as _inspect
import textwrap as _textwrap

import solution as _solmod

_EXTRA_ALLOWED = {"numpy"}
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


def test_contract_import_allowlist():
    """the statement requires numpy vectorization and nothing else."""
    extra = _imported_modules() - _ALLOWED_IMPORTS
    assert not extra, "only %s may be imported; found: %s" % (
        sorted(_ALLOWED_IMPORTS) or "nothing", sorted(extra))


def test_contract_no_dynamic_lookup():
    """getattr / eval / exec / __import__ would let a banned module back in."""
    banned = {"getattr", "eval", "exec", "compile", "__import__",
               "globals", "vars", "locals"}
    hits = sorted({n.func.id for n in _ast.walk(_sol_tree())
                   if isinstance(n, _ast.Call) and isinstance(n.func, _ast.Name)
                   and n.func.id in banned})
    assert not hits, "reflective lookup is banned; found: %s" % hits


def test_contract_no_dunder_access():
    """int.__pow__ and friends are the usual way around a ban by name."""
    hits = sorted({n.attr for n in _ast.walk(_sol_tree())
                   if isinstance(n, _ast.Attribute)
                   and n.attr.startswith("__") and n.attr.endswith("__")})
    assert not hits, "dunder attribute access is banned; found: %s" % hits
