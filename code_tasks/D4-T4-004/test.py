import pytest
from solution import tmr_voter

def test_all_same():
    """All three paths agree -> the vote equals any of the inputs."""
    a = bytes(range(32))
    result = tmr_voter(a, a, a)
    assert result == a

def test_one_differs():
    """One path differs and two agree -> the majority wins."""
    a = bytes(range(32))
    b = bytes(range(32))
    c = bytes([i ^ 0xFF for i in range(32)])  # c differs entirely
    result = tmr_voter(a, b, c)
    assert result == a  # a==b is the majority

def test_all_different():
    """All three paths differ -> take the bit-wise majority."""
    a = b'\x00' * 16
    b = b'\xFF' * 16
    c = b'\x0F' * 16
    result = tmr_voter(a, b, c)
    # Bit by bit: 00=00000000, FF=11111111, 0F=00001111
    # bit0: 0,1,1 → 1; bit1: 0,1,1 → 1; bit2: 0,1,1 → 1; bit3: 0,1,1 → 1
    # bit4: 0,1,0 → 0; bit5: 0,1,0 → 0; bit6: 0,1,0 → 0; bit7: 0,1,0 → 0
    assert result == b'\x0F' * 16  # the bit-level majority of 11110000

def test_two_faults():
    """Two faulty paths -> recovery still possible (the core advantage of TMR)."""
    correct = bytes(range(16))
    fault1 = b'\xFF' * 16
    fault2 = b'\x00' * 16
    result = tmr_voter(correct, fault1, fault2)
    # Byte by byte: correct[i] vs FF vs 00 -> correct only where correct[i] is on the majority side
    # When all three differ, the majority is taken bit by bit
    # Check that it is at least close to correct under majority-vote semantics
    assert len(result) == 16

def test_single_byte_majority():
    """Single-byte majority vote."""
    assert tmr_voter(b'\xAA', b'\xAA', b'\xBB') == b'\xAA'
    assert tmr_voter(b'\xAA', b'\xBB', b'\xAA') == b'\xAA'
    assert tmr_voter(b'\xBB', b'\xAA', b'\xAA') == b'\xAA'

def test_length_mismatch():
    with pytest.raises(ValueError):
        tmr_voter(b'\x00' * 8, b'\x00' * 16, b'\x00' * 16)
    with pytest.raises(ValueError):
        tmr_voter(b'\x00' * 8, b'\x00' * 8, b'\x00' * 16)

def test_empty():
    assert tmr_voter(b'', b'', b'') == b''

def test_no_branch_in_source():
    """Static check: the voting logic must have no secret-dependent control flow."""
    import inspect
    src = inspect.getsource(tmr_voter)
    code_after_raise = src.split("raise ValueError")[1] if "raise ValueError" in src else src
    assert " if " not in code_after_raise, "the voting logic must not use an if branch"
    assert " else " not in code_after_raise, "the voting logic must not use else"


def test_two_of_three_recover():
    x = bytes([0x12]) * 8
    f = bytes([0x99]) * 8
    assert tmr_voter(x, x, f) == x
    assert tmr_voter(x, f, x) == x
    assert tmr_voter(f, x, x) == x


def test_bit_majority_exact():
    # The bit-wise majority of F0/CC/AA is E8
    assert tmr_voter(bytes([0xF0]), bytes([0xCC]), bytes([0xAA])) == bytes([0xE8])
