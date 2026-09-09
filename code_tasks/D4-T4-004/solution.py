def tmr_voter(a: bytes, b: bytes, c: bytes) -> bytes:
    """TMR majority vote: byte-wise majority = (a & b) | (a & c) | (b & c)."""
    if len(a) != len(b) or len(a) != len(c):
        raise ValueError("the three inputs must have the same length")
    # Constant time: majority = (a AND b) OR (a AND c) OR (b AND c)
    return bytes((xa & xb) | (xa & xc) | (xb & xc)
                 for xa, xb, xc in zip(a, b, c))
