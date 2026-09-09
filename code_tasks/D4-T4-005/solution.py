def montgomery_ladder(k: int, gx: int, gy: int, p: int, a: int) -> tuple:
    """Montgomery Ladder ECC scalar multiplication (constant-time pattern per bit)."""
    def modinv(x, p):
        return pow(x, p - 2, p)  # Fermat

    def point_add(P, Q, p):
        x1, y1 = P
        x2, y2 = Q
        if x1 == 0 and y1 == 0:
            return x2, y2
        if x2 == 0 and y2 == 0:
            return x1, y1
        if x1 == x2 and y1 != y2:
            return 0, 0
        if x1 == x2 and y1 == y2:
            lam = (3 * x1 * x1 + a) * modinv(2 * y1, p) % p
        else:
            lam = (y2 - y1) * modinv(x2 - x1, p) % p
        x3 = (lam * lam - x1 - x2) % p
        y3 = (lam * (x1 - x3) - y1) % p
        return x3, y3

    def point_double(P, p):
        return point_add(P, P, p)

    R0 = (0, 0)
    R1 = (gx, gy)
    bits = k.bit_length()

    def _cswap(P, Q, b):
        """Swap the two points when b=1 and keep them when b=0 -- done arithmetically, without a branch."""
        nb = 1 - b
        return ((P[0] * nb + Q[0] * b, P[1] * nb + Q[1] * b),
                (Q[0] * nb + P[0] * b, Q[1] * nb + P[1] * b))

    for i in range(bits - 1, -1, -1):
        bit = (k >> i) & 1
        # The standard cswap ladder: swap branchlessly by the bit, then always do one point
        # addition and one doubling, then swap back. Each bit costs exactly 1 add + 1 double and
        # no result is discarded -- the earlier version computed sum_pt / dbl_R0 / dbl_R1 and used
        # only two of them, and the discarded doubling was exactly the dummy operation the
        # statement bans (it can be exploited by safe-error).
        R0, R1 = _cswap(R0, R1, bit)
        R1 = point_add(R0, R1, p)
        R0 = point_double(R0, p)
        R0, R1 = _cswap(R0, R1, bit)

    return R0
