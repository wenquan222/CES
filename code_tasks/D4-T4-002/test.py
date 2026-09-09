# -*- coding: utf-8 -*-
"""D4-T4-002 tests: gen_masked_sbox."""
import pytest
from solution import gen_masked_sbox, AES_SBOX


# 1. No mask: m_in=0, m_out=0 -> equals the original S-box
def test_no_mask():
    masked = gen_masked_sbox(0, 0)
    assert len(masked) == 256
    assert masked == AES_SBOX


# 2. An all-0xFF input mask
def test_input_mask_ff():
    """m_in=0xFF, m_out=0: masked[x^0xFF] = S[x]"""
    masked = gen_masked_sbox(0xFF, 0)
    for x in range(256):
        assert masked[x ^ 0xFF] == AES_SBOX[x]


# 3. m_out only
def test_only_output_mask():
    """m_in=0, m_out=0x37: masked[x] = S[x] ^ 0x37"""
    masked = gen_masked_sbox(0, 0x37)
    for x in range(256):
        assert masked[x] == AES_SBOX[x] ^ 0x37


# 4. m_in only
def test_only_input_mask():
    """m_in=0x42, m_out=0: masked[x^0x42] = S[x]"""
    masked = gen_masked_sbox(0x42, 0)
    for x in range(256):
        assert masked[x ^ 0x42] == AES_SBOX[x]


# 5. Consistency across all 256 entries
def test_full_consistency():
    """For several random (m_in, m_out) pairs, check masked[x ^ m_in] ^ m_out == S[x]."""
    test_pairs = [(0x42, 0x37), (0xAB, 0xCD), (0x01, 0xFE), (0x80, 0x80)]
    for m_in, m_out in test_pairs:
        masked = gen_masked_sbox(m_in, m_out)
        for x in range(256):
            assert masked[x ^ m_in] ^ m_out == AES_SBOX[x], f'failed at m_in={m_in:#x} m_out={m_out:#x} x={x:#x}'


# 6. Output length
def test_length():
    for m_in, m_out in [(0, 0), (0xFF, 0xFF), (0x42, 0x37)]:
        masked = gen_masked_sbox(m_in, m_out)
        assert len(masked) == 256


# 7. Every element lies in [0, 256)
def test_output_range():
    masked = gen_masked_sbox(0xAB, 0xCD)
    for v in masked:
        assert 0 <= v < 256


# 8. Out-of-range arguments raise
def test_out_of_range():
    with pytest.raises(ValueError):
        gen_masked_sbox(256, 0)
    with pytest.raises(ValueError):
        gen_masked_sbox(0, -1)
    with pytest.raises(ValueError):
        gen_masked_sbox(-1, 0)


# 9. Determinism
def test_determinism():
    a = gen_masked_sbox(0x42, 0x37)
    b = gen_masked_sbox(0x42, 0x37)
    assert a == b


# 10. End-to-end correctness of the AES intermediate value under first-order masking
def test_e2e_aes_round():
    """
    Simulate one masked SubBytes round of first-order Boolean-masked AES:
    - input x_masked = x ^ m_in
    - look up masked_sbox[x_masked] = S(x) ^ m_out
    - unmask to get S(x) = result ^ m_out
    """
    m_in = 0x9C
    m_out = 0x4B
    masked = gen_masked_sbox(m_in, m_out)
    # Simulate 16 input bytes
    test_inputs = [0x32, 0x43, 0xF6, 0xA8, 0x88, 0x5A, 0x30, 0x8D,
                   0x31, 0x31, 0x98, 0xA2, 0xE0, 0x37, 0x07, 0x34]
    for x in test_inputs:
        x_masked = x ^ m_in
        result_masked = masked[x_masked]
        # After unmasking it must equal the unmasked S(x)
        assert result_masked ^ m_out == AES_SBOX[x]


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
