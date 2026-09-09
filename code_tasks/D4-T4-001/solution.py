"""D4-T4-001 solution: the infection fault countermeasure."""


def infect_or_pass(state_a: bytes, state_b: bytes, mask: bytes) -> bytes:
    """Infection fault countermeasure: return state_a when state_a == state_b, otherwise state_a XOR mask, in constant time."""
    if len(state_a) != 16 or len(state_b) != 16 or len(mask) != 16:
        raise ValueError("every input must be 16 bytes")

    # 1. Byte-by-byte XOR to get diff
    diff = bytes(a ^ b for a, b in zip(state_a, state_b))

    # 2. OR all diff bytes together -- any non-zero byte makes the accumulator non-zero
    accumulator = 0
    for d in diff:
        accumulator |= d

    # 3. Build the "equal?" mask: all equal -> 0; any difference -> 1
    # Fold the 8 bits into a single-bit summary
    s = accumulator
    s = (s | (s >> 4)) & 0x0F
    s = (s | (s >> 2)) & 0x03
    s = (s | (s >> 1)) & 0x01
    byte_mask = (-s) & 0xFF # 0 → 0x00; 1 → 0xFF

    # 4. Output = state_a XOR (mask AND byte_mask)
    # byte_mask = 0 (no fault) -> no pollution, return state_a
    # byte_mask = 0xFF (fault) -> pollute with the whole mask, return state_a XOR mask
    return bytes(a ^ (m & byte_mask) for a, m in zip(state_a, mask))
