def xor_sharewise(a: bytes, b: bytes) -> bytes:
    if len(a) != len(b):
        raise ValueError("the inputs must have the same length")
    return bytes(x ^ y for x, y in zip(a, b))
