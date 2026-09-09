"""D2-T4-001 solution: classifying AES fault patterns."""

# Column-major layout: byte index = 4*column + row
AES_COLUMNS = [{0, 1, 2, 3}, {4, 5, 6, 7}, {8, 9, 10, 11}, {12, 13, 14, 15}]


def _diagonal_of(pos: int) -> int:
    """Which ShiftRows diagonal the position pos belongs to.

    ShiftRows moves (r, c) to (r, (c - r) mod 4). Reading it backwards, the byte that
    lands on pos = r + 4*c' came from column (c' + r) mod 4 before ShiftRows, and that
    column number is the diagonal number.
    """
    row = pos % 4
    col = pos // 4
    return (col + row) % 4


def classify_fault_pattern(correct_cipher: bytes,
                           faulty_cipher: bytes) -> dict:
    if len(correct_cipher) != 16 or len(faulty_cipher) != 16:
        raise ValueError("cipher length must be 16")

    diff_bytes = [i for i in range(16) if correct_cipher[i] != faulty_cipher[i]]
    diff_set = set(diff_bytes)
    n = len(diff_bytes)

    if n == 0:
        pattern, stage = "none", "no_fault"
    elif n == 1:
        # The final round has no MixColumns, so a single-byte fault affects one ciphertext byte
        pattern, stage = "single", "final_round"
    elif n == 4 and len({_diagonal_of(i) for i in diff_bytes}) == 1:
        # MixColumns in round 9 fills a column, then the final ShiftRows scatters it onto a diagonal
        pattern, stage = "diagonal", "penultimate_round"
    elif n == 4 and diff_set in AES_COLUMNS:
        # A single-byte fault cannot produce a 4-byte same-column difference: the final
        # ShiftRows must scatter them. Such a pattern means the fault model does not match
        # the assumption, so it is not attributed to any particular round.
        pattern, stage = "column", "unknown"
    else:
        pattern, stage = "multiple", "early_round"

    return {
        "diff_bytes": diff_bytes,
        "diff_pattern": pattern,
        "estimated_stage": stage,
    }
