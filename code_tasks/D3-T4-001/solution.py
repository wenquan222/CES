"""D3-T4-001 solution: constant-time conditional selection."""


def ct_select(cond: int, a: int, b: int) -> int:
    """Constant-time conditional selection: return a when cond=1, b when cond=0."""
    if cond not in (0, 1):
        raise ValueError("cond must be 0 or 1")
    # cond=1 → mask=0xFFFFFFFF; cond=0 → mask=0x00000000
    mask = (-cond) & 0xFFFFFFFF
    return ((a & mask) | (b & (~mask & 0xFFFFFFFF))) & 0xFFFFFFFF
