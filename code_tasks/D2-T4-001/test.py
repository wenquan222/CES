"""D2-T4-001 test cases: classifying AES fault patterns."""
import pytest
from solution import classify_fault_pattern

# The four ShiftRows diagonals: the positions reached by the 4 bytes that shared a
# column before ShiftRows, under (r, c) -> (r, (c-r) mod 4); numbered by the
# pre-ShiftRows column.
DIAGONALS = {
    0: [0, 7, 10, 13],
    1: [1, 4, 11, 14],
    2: [2, 5, 8, 15],
    3: [3, 6, 9, 12],
}
COLUMNS = {0: [0, 1, 2, 3], 1: [4, 5, 6, 7], 2: [8, 9, 10, 11], 3: [12, 13, 14, 15]}


def _pair(positions):
    """Build a ciphertext pair whose difference falls exactly on the given positions."""
    correct = bytes(16)
    faulty = bytearray(16)
    for p in positions:
        faulty[p] = 0xFF
    return correct, bytes(faulty)


def test_diagonals_are_a_partition():
    """Self-check first: the four diagonals are disjoint, cover all 16 positions, and
    each one agrees with the definition of ShiftRows."""
    assert sorted(p for d in DIAGONALS.values() for p in d) == list(range(16))
    for c in range(4):
        assert sorted(r + 4 * ((c - r) % 4) for r in range(4)) == sorted(DIAGONALS[c])


def test_none():
    c = bytes(16)
    r = classify_fault_pattern(c, c)
    assert r["diff_pattern"] == "none"
    assert r["estimated_stage"] == "no_fault"
    assert r["diff_bytes"] == []


def test_single():
    correct, faulty = _pair([5])
    r = classify_fault_pattern(correct, faulty)
    assert r["diff_pattern"] == "single"
    assert r["estimated_stage"] == "final_round"
    assert r["diff_bytes"] == [5]


@pytest.mark.parametrize("diag", [0, 1, 2, 3])
def test_diagonal_is_penultimate_round(diag):
    """A single-byte fault before MixColumns in round 9 -> the final ShiftRows scatters it onto one diagonal."""
    correct, faulty = _pair(DIAGONALS[diag])
    r = classify_fault_pattern(correct, faulty)
    assert r["diff_pattern"] == "diagonal"
    assert r["estimated_stage"] == "penultimate_round"
    assert r["diff_bytes"] == sorted(DIAGONALS[diag])


@pytest.mark.parametrize("col", [0, 3])
def test_same_column_is_unknown(col):
    """A 4-byte same-column difference cannot come from a single-byte fault -- the final
    ShiftRows must scatter them. This is the control case: an implementation that treats
    "same column" as the signature of the second-to-last round fails here."""
    correct, faulty = _pair(COLUMNS[col])
    r = classify_fault_pattern(correct, faulty)
    assert r["diff_pattern"] == "column"
    assert r["estimated_stage"] == "unknown"


def test_same_row_is_multiple():
    """{0,4,8,12} is one row: neither a column nor a diagonal."""
    correct, faulty = _pair([0, 4, 8, 12])
    r = classify_fault_pattern(correct, faulty)
    assert r["diff_pattern"] == "multiple"
    assert r["estimated_stage"] == "early_round"


def test_two_and_three_bytes():
    for positions in ([0, 7], [2, 5, 11]):
        correct, faulty = _pair(positions)
        r = classify_fault_pattern(correct, faulty)
        assert r["diff_pattern"] == "multiple"
        assert r["estimated_stage"] == "early_round"


def test_many_bytes():
    for positions in ([0, 1, 2, 3, 4, 5], list(range(16))):
        correct, faulty = _pair(positions)
        r = classify_fault_pattern(correct, faulty)
        assert r["diff_pattern"] == "multiple"
        assert r["estimated_stage"] == "early_round"


def test_four_bytes_neither_column_nor_diagonal():
    """A 4-byte difference that is neither a column nor a diagonal -> multiple."""
    correct, faulty = _pair([0, 1, 2, 4])
    r = classify_fault_pattern(correct, faulty)
    assert r["diff_pattern"] == "multiple"
    assert r["estimated_stage"] == "early_round"


def test_sorted_and_deterministic():
    correct, faulty = _pair([13, 0, 10, 7])
    r1 = classify_fault_pattern(correct, faulty)
    r2 = classify_fault_pattern(correct, faulty)
    assert r1["diff_bytes"] == [0, 7, 10, 13]
    assert r1 == r2


def test_invalid_length():
    with pytest.raises(ValueError):
        classify_fault_pattern(b"\x00" * 15, b"\x00" * 16)
    with pytest.raises(ValueError):
        classify_fault_pattern(b"\x00" * 16, b"\x00" * 17)
