# -*- coding: utf-8 -*-
"""D6-T4-002 tests: HKDF (RFC 5869, including the official test vectors)."""
import pytest
from solution import hkdf


# RFC 5869 Appendix A Test Case 1 (SHA-256)
def test_rfc5869_case1():
    ikm = bytes([0x0b] * 22)
    salt = bytes(range(0x00, 0x0d)) # 00 01 ... 0c (13 bytes)
    info = bytes(range(0xf0, 0xfa)) # f0 f1 ... f9 (10 bytes)
    okm = hkdf(ikm, salt, info, 42)
    expected = bytes.fromhex(
        "3cb25f25faacd57a90434f64d0362f2a"
        "2d2d0a90cf1a5a4c5db02d56ecc4c5bf"
        "34007208d5b887185865"
    )
    assert okm == expected


# RFC 5869 Test Case 3 (SHA-256, empty salt and empty info)
def test_rfc5869_case3():
    ikm = bytes([0x0b] * 22)
    okm = hkdf(ikm, b"", b"", 42)
    expected = bytes.fromhex(
        "8da4e775a563c18f715f802a063c5a31"
        "b8a11f5c5ee1879ec3454e5f3c738d2d"
        "9d201395faa4b61a96c8"
    )
    assert okm == expected


# 3. salt=None is equivalent to an all-zero salt (per the RFC)
def test_salt_none_equals_zero():
    ikm = bytes([0x0b] * 22)
    a = hkdf(ikm, None, b"", 42)
    b = hkdf(ikm, b"", b"", 42)
    assert a == b


# 4. The output length is exactly length
def test_output_length():
    for L in [1, 16, 32, 33, 64, 100]:
        assert len(hkdf(b"secret", b"salt", b"info", L)) == L


# 5. length=0 returns empty
def test_zero_length():
    assert hkdf(b"x", b"y", b"z", 0) == b""


# 6. Different info gives a different OKM
def test_different_info():
    a = hkdf(b"ikm", b"salt", b"app1", 32)
    b = hkdf(b"ikm", b"salt", b"app2", 32)
    assert a != b


# 7. Different salt gives a different OKM
def test_different_salt():
    a = hkdf(b"ikm", b"salt-a", b"info", 32)
    b = hkdf(b"ikm", b"salt-b", b"info", 32)
    assert a != b


# 8. An over-long length raises ValueError (> 255*32)
def test_too_long():
    with pytest.raises(ValueError):
        hkdf(b"ikm", b"salt", b"info", 255 * 32 + 1)


# 9. A negative length raises ValueError
def test_negative_length():
    with pytest.raises(ValueError):
        hkdf(b"ikm", b"salt", b"info", -1)


# 10. Determinism, and the return type is bytes
def test_determinism_and_type():
    a = hkdf(b"ikm", b"salt", b"info", 40)
    b = hkdf(b"ikm", b"salt", b"info", 40)
    assert a == b
    assert isinstance(a, bytes)


# ── Contract checks ───────────────────────────────────────────────────────
# The statement bans ready-made implementations. Banning names one by one is
# trivially evaded by assignment aliases, import aliases and getattr reflection,
# so an import whitelist is enforced instead: it does not depend on how the code
# is written. A contract violation is a hard failure, not a partial score.
import ast as _c_ast
import pathlib as _c_path

_ALLOWED_IMPORTS = {'hmac', 'hashlib', 'struct'}


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
