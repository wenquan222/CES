def modpow(base: int, exp: int, mod: int) -> int:
    result = 1
    base = base % mod
    e = exp
    while e > 0:
        if e & 1:
            result = (result * base) % mod
        base = (base * base) % mod
        e >>= 1
    return result

def crt_rsa_sign(m: int, p: int, q: int, dp: int, dq: int, qinv: int) -> int:
    sp = modpow(m % p, dp, p)
    sq = modpow(m % q, dq, q)
    diff = (sp - sq) % p
    h = (diff * qinv) % p
    result = sq + h * q
    return result
