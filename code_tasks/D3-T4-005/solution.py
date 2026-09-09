def gf28_mul(a: int, b: int) -> int:
    """GF(2^8) multiplication (irreducible polynomial 0x11B), branchless throughout."""
    p = 0
    for _ in range(8):
        # Accumulate a when the low bit of b is 1 -- multiplication replaces the conditional
        p ^= a * (b & 1)
        b >>= 1
        # XOR 0x1B on high-bit overflow -- again multiplication replaces the conditional
        carry = (a >> 7) & 1
        a = ((a << 1) & 0xFF) ^ (0x1B * carry)
    return p & 0xFF


def gf28_inv(x: int) -> int:
    """GF(2^8) inversion by Fermat's little theorem, inv(x) = x^254; x=0 naturally gives 0, so no special case is needed."""
    r = 1
    p = x
    for _ in range(7):
        p = gf28_mul(p, p)      # x^2, x^4, x^8, ..., x^128
        r = gf28_mul(r, p)      # the running product gives x^(2+4+8+...+128) = x^254
    return r


def aes_ct_sbox(byte: int) -> int:
    """AES S-box = affine transform of the GF(2^8) inverse; pure bit operations, no lookup table, no branch."""
    # The stated constraints require ValueError on an out-of-range argument. This happens
    # before the cryptographic computation and depends only on the public range, so it
    # introduces no secret-dependent branch.
    if not isinstance(byte, int) or isinstance(byte, bool) or not 0 <= byte <= 255:
        raise ValueError('byte must be an int in [0, 255]')
    b = gf28_inv(byte)
    result = 0
    c = 0x63
    for i in range(8):
        bit = ((b >> i) ^ (b >> ((i + 4) & 7)) ^ (b >> ((i + 5) & 7)) ^
               (b >> ((i + 6) & 7)) ^ (b >> ((i + 7) & 7)) ^ ((c >> i) & 1)) & 1
        result |= bit << i
    return result
