# D3-T4-005: Constant-Time AES S-box

## Problem
Implement `aes_ct_sbox(byte: int) -> int`, computing the AES S-box substitution value with pure bit operations (no lookup table allowed).

## The mathematical definition of the AES S-box
S-box(b) = affine_transform(inverse in GF(2^8) of b)
where:
- The GF(2^8) irreducible polynomial: x^8 + x^4 + x^3 + x + 1 (0x11B)
- The affine transformation matrix (FIPS 197 §5.1.1):
  b'_i = b_i ⊕ b_{(i+4)mod8} ⊕ b_{(i+5)mod8} ⊕ b_{(i+6)mod8} ⊕ b_{(i+7)mod8} ⊕ c_i
  where c = 0x63 = 01100011

## Constraints
- No lookup table of any kind may be used (including a hard-coded S-box array)
- A pure bitwise implementation (GF(2^8) multiplication + inversion + the affine transformation)
- if/else branches are not allowed (branchless)
- Inversion in GF(2^8) may use Fermat's little theorem: inv(x) = x^254 mod p(x), or the extended Euclidean algorithm
- The range of the byte input: 0-255

## Input
- byte: int, [0, 255]

## Output
- int: AES S-box(byte), [0, 255]

## Examples
```
S-box(0x00) = 0x63
S-box(0x2B) = 0xF1  (an AES-128 standard test vector)
S-box(0xFF) = 0x16
```

---

## How the evaluation checks the implementation constraints

Besides the functional cases, the evaluation also checks that you **really wrote the required algorithm** rather than calling a library or taking a shortcut:

- **Import whitelist**: importing any module is **not allowed** in this problem.
- **No dunder channels**: no `__xxx__` attribute may be accessed (`int.__pow__`, say).
- **No reflective lookup**: `getattr` / `eval` / `exec` / `__import__` / `globals` / `vars` / `locals` must not be used.
- **Aliasing does not help**: renamings such as `shortcut = pow` or `from x import y as z` will not evade the check.
- **Dead code does not count**: a call written inside `if False:` or otherwise never reached does not count as "having implemented the algorithm".
- **Work check**: the evaluation counts the lines executed: one field inversion plus the affine transformation runs on the order of a few hundred lines, whereas any form of lookup executes only a single-digit number of lines.
  Moreover, no literal constant of ≥32 entries may appear in the module (lists, tuples, bytes and hexadecimal strings all count), and no module-level container of ≥32 entries may exist — whether the table is hard-coded or generated in a loop.

---
