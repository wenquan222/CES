def parity_check(data: bytes, expected_parity: int) -> bool:
    """Take the low bit of the XOR of all bytes and compare it with expected_parity, in constant time."""
    if expected_parity not in (0, 1):
        raise ValueError("expected_parity must be 0 or 1")
    # XOR all the bytes
    acc = 0
    for b in data:
        acc ^= b
    # Take the LSB
    actual = acc & 1
    # Constant-time comparison: build the return value with bit operations as the statement requires, without == or if
    # actual and expected_parity are both normalized to {0, 1}, so a zero XOR means equal
    match = 1 - (actual ^ expected_parity)
    return bool(match)
