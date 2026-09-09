# D4-T4-005: Montgomery Ladder elliptic curve scalar multiplication

## Problem statement

Implement Montgomery Ladder elliptic curve scalar multiplication. The Montgomery Ladder (Joye-Yen CHES 2002) is a constant-time scalar multiplication algorithm — every scalar bit performs the same Double and Add operation pattern, so it defends against SPA (no difference in the operation sequence) and Safe-Error attacks (no dummy operation to inject a fault into) at the same time.

## Function signature

```python
def montgomery_ladder(k: int, gx: int, gy: int, p: int, a: int) -> tuple:
    """
    The Montgomery Ladder computing Q = k * G, where G=(gx, gy) is a point on
    the elliptic curve.

    The curve: y² = x³ + a*x + b (mod p), in Weierstrass form.
    Note: the point addition and doubling formulas use only the parameter a
    (the doubling slope λ=(3x²+a)/(2y)), and b takes part in no computation, so
    b is not passed in the function signature -- the tests verify on curves with
    arbitrary valid (a, b).
    The point at infinity O is represented by (0, 0); k=0 returns (0, 0).

    The algorithm (every bit performing the same pattern, constant time):
        R0 = (0, 0)  # the point at infinity
        R1 = (gx, gy)
        for each bit of k from MSB to LSB:
            if bit == 0:
                R1 = point_add(R0, R1, p)
                R0 = point_double(R0, p)
            else:
                R0 = point_add(R0, R1, p)
                R1 = point_double(R1, p)
        return R0

    Security requirement:
        within each iteration, the execution of point_add and point_double must
        not depend on the bit value.
        Use a conditional-assignment swap_mask or bit operations to remove the
        branch.

    Args:
        k: the scalar (a non-negative integer, k >= 0; k = 0 returns the point
            at infinity (0, 0))
        gx, gy: the x and y coordinates of the base point G (mod p)
        p: the modulus (a large prime)
        a: the curve parameter a

    Returns:
        (qx, qy): the affine coordinates of Q = k*G (mod p)
    """
```

## Constraints

1. Avoid bit-dependent control flow within each iteration (an if/else selecting different code by the bit)
2. Use the Montgomery Ladder structure (R0 and R1 updated in lockstep)
3. No external elliptic curve cryptography library is called
4. p is prime and all operations are mod p
5. Point addition and doubling must handle the point at infinity (O) correctly
6. The requirement of a constant operation pattern applies to **each ladder iteration**: every bit must really perform one point addition and one point doubling and select the result branch-free. Special cases for the point at infinity and for doubling inside point_add/point_double fall outside this requirement — no true constant-time guarantee is possible at the Python level, and this problem examines only the algorithmic property that "the operation pattern is the same for every bit, with no dummy operation".

Python standard-library modules are allowed; no external elliptic-curve library may be used.
