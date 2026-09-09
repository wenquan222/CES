"""D3-T4-007 solution: sliding-window modular exponentiation."""


def _precompute_odd_powers(base: int, modulus: int, window_size: int) -> dict:
    """Precompute the odd powers {e: base^e mod modulus} for e = 1, 3, 5, ..., 2^k - 1.

    Using base^e = base^(e-2) * base^2, each additional odd power costs one multiplication.
    """
    g = {}
    b = base % modulus
    g[1] = b
    base_sq = (b * b) % modulus
    for e in range(3, 1 << window_size, 2):
        g[e] = (g[e - 2] * base_sq) % modulus
    return g


def sliding_window_modexp(base: int, exponent: int, modulus: int, window_size: int) -> int:
    if modulus == 1:
        return 0

    g = _precompute_odd_powers(base, modulus, window_size)

    bits = []
    e = exponent
    while e > 0:
        bits.append(e & 1)
        e >>= 1
    bits.reverse()

    result = 1
    i = 0
    while i < len(bits):
        if bits[i] == 0:
            # A 0 bit outside a window: square once and slide the window on by one
            result = (result * result) % modulus
            i += 1
        else:
            # Take the window starting at the current bit, at most window_size bits long, ending in a 1
            end = min(i + window_size, len(bits))
            j = end - 1
            while j >= i and bits[j] == 0:
                j -= 1
            window_len = j - i + 1
            val = 0
            for k in range(i, j + 1):
                val = (val << 1) | bits[k]
            for _ in range(window_len):
                result = (result * result) % modulus
            result = (result * g[val]) % modulus
            i = j + 1
    return result
