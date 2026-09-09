# 006-karatsuba-mul solution
def karatsuba_mul(x: int, y: int) -> int:
    """Karatsuba big-integer multiplication, returning x*y."""
    if x < 0 or y < 0:
        raise ValueError("only non-negative integers are supported")
    if x < 1000 or y < 1000:
        return x * y

    n = max(x.bit_length(), y.bit_length())
    half = n // 2
    mask = (1 << half) - 1

    x1 = x >> half
    x0 = x & mask
    y1 = y >> half
    y0 = y & mask

    z2 = karatsuba_mul(x1, y1)
    z0 = karatsuba_mul(x0, y0)
    z1 = karatsuba_mul(x1 + x0, y1 + y0) - z2 - z0

    return (z2 << (2 * half)) + (z1 << half) + z0
