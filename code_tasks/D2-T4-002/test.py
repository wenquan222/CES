from solution import ineffective_fault_bias_score

def test_basic():

    ref = bytes([0]*16)

    faults = [bytes([0]*16)] * 20

    score = ineffective_fault_bias_score(ref, faults)

    assert score == 1.0

def test_half():

    ref = bytes([0]*16)

    faults = []

    for _ in range(10):
        faults.append(bytes([0]*16))

    for _ in range(10):
        faults.append(bytes([1]*16))

    score = ineffective_fault_bias_score(ref, faults)

    assert score == 0.5

def test_small_sample():

    ref = bytes([0]*16)

    faults = [bytes([0]*16)] * 5

    score = ineffective_fault_bias_score(ref, faults)

    assert score == 0.0

def test_empty():
    ref = bytes([0]*16)
    faults = []

    score = ineffective_fault_bias_score(ref, faults)

    assert score == 0.0

def test_exactly_10_all_same():
    ref = bytes([0]*16)
    faults = [bytes([0]*16)] * 10

    score = ineffective_fault_bias_score(ref, faults)

    assert score == 1.0

def test_exactly_10_half():
    ref = bytes([0]*16)
    faults = [bytes([0]*16)] * 5 + [bytes([1]*16)] * 5

    score = ineffective_fault_bias_score(ref, faults)

    assert score == 0.5

def test_all_different():
    ref = bytes([0]*16)
    faults = [bytes([i % 256]*16) for i in range(1, 21)]

    score = ineffective_fault_bias_score(ref, faults)

    assert score == 0.0

def test_one_third():
    ref = bytes([0]*16)
    faults = [bytes([0]*16)] * 10 + [bytes([1]*16)] * 20

    score = ineffective_fault_bias_score(ref, faults)

    assert score == 10 / 30

def test_large_sample():
    ref = bytes([0]*16)
    faults = [bytes([0]*16)] * 25 + [bytes([1]*16)] * 75

    score = ineffective_fault_bias_score(ref, faults)

    assert score == 0.25

def test_nine():
    ref = bytes([0]*16)
    faults = [bytes([0]*16)] * 9

    score = ineffective_fault_bias_score(ref, faults)

    assert score == 0.0


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


def test_contract_import_allowlist():
    """the statement bans scipy; nothing needs to be imported here."""
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
