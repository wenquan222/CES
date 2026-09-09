# D2-T4-001: Classifying AES fault patterns

## Problem statement

Implement a function that judges, from the difference pattern between the correct and the faulty ciphertext, at which stage of AES-128 the fault was most likely injected.

---

## Function signature

```python
def classify_fault_pattern(correct_cipher: bytes,
                           faulty_cipher: bytes) -> dict:
    pass
```

---

## Input

- correct_cipher: the correct AES-128 ciphertext (16 bytes)
- faulty_cipher: the faulty AES-128 ciphertext (16 bytes)

Raise `ValueError` if the length is not 16.

---

## Output

```python
{
    "diff_bytes": list[int], # indices of differing bytes, ascending
    "diff_pattern": str,
    "estimated_stage": str
}
```

`diff_pattern` ∈ `{"none", "single", "diagonal", "column", "multiple"}`
`estimated_stage` ∈ `{"no_fault", "final_round", "penultimate_round", "early_round", "unknown"}`

---

## AES state byte numbering (column-major)

The 16 bytes are laid out **column-major**: byte index = 4·column + row.

- **Column 0** = {0, 1, 2, 3} **column 1** = {4, 5, 6, 7} **column 2** = {8, 9, 10, 11} **column 3** = {12, 13, 14, 15}

ShiftRows moves the byte at `(row r, column c)` to `(r, (c - r) mod 4)`.
The set of positions to which "the 4 positions that belonged to one column before ShiftRows" land after ShiftRows is called a
**ShiftRows diagonal**. The 4 diagonals are disjoint and cover the 16 positions exactly. Derive them yourself from the definition of ShiftRows — the problem statement does not list them.

> A reminder: {0, 4, 8, 12} is one **row** (one byte from each of the four columns); it is neither a column nor a diagonal.

---

## How faults propagate (the basis of classification)

```text
A single-byte fault injected in round 10 (the final round): the final round has
    no MixColumns → only 1 ciphertext byte changes
A single-byte fault injected before the MixColumns of round 9:
    MixColumns → the difference fills all 4 bytes of that column
    ShiftRows → those 4 bytes are scattered into 4 different columns, landing
                  on one ShiftRows diagonal
    (the final round has no MixColumns, so the positions change no further)
  ⇒ the 4 differing bytes of the final ciphertext form one diagonal, not a column
Injection in an earlier round: after at least one full MixColumns diffusion →
    the difference disperses, usually far more than 4 bytes
```

**A 4-byte difference within one column cannot arise from a single-byte fault** — the final round's ShiftRows necessarily scatters a difference within a column. Observing that pattern means the fault model is not as expected (a multi-byte fault, a key schedule fault, or injection after ShiftRows), so it is classified as `unknown` rather than as any particular round.

---

## Decision rules

| Difference | diff_pattern | estimated_stage |
|---|---|---|
| 0 bytes differ | `none` | `no_fault` |
| 1 byte differs | `single` | `final_round` |
| exactly 4 bytes, forming one complete ShiftRows diagonal | `diagonal` | `penultimate_round` |
| exactly 4 bytes, all in the same AES column | `column` | `unknown` |
| anything else (2-3 bytes; 4 bytes that are neither a diagonal nor a column; 5 bytes or more) | `multiple` | `early_round` |

---

## Examples

```python
correct = bytes(16)

f = bytearray(correct); f[0] ^= 0xFF
classify_fault_pattern(correct, bytes(f))
# {"diff_bytes": [0], "diff_pattern": "single", "estimated_stage": "final_round"}

f = bytearray(correct)
for i in (0, 7, 10, 13): # one complete ShiftRows diagonal
    f[i] ^= 0xFF
classify_fault_pattern(correct, bytes(f))
# {"diff_bytes": [0, 7, 10, 13], "diff_pattern": "diagonal",
# "estimated_stage": "penultimate_round"}

f = bytearray(correct)
for i in (0, 1, 2, 3): # the same column -- a single-byte fault cannot produce this
    f[i] ^= 0xFF
classify_fault_pattern(correct, bytes(f))
# {..., "diff_pattern": "column", "estimated_stage": "unknown"}
```

---

## Constraints

1. The inputs must be bytes of length 16, or raise `ValueError`
2. Use the pure Python standard library, without depending on numpy / cryptography
3. `diff_bytes` must be in ascending order
4. Determinism: the same input returns the same result

---

## Testing

15 cases: ① the four diagonals form a partition (a self-check up front); ② no difference;
③ a single-byte difference;
④⑤⑥⑦ one case for each of the four diagonals → `diagonal` / `penultimate_round`;
⑧⑨ 4 bytes in the same column (column 0, column 3) → `column` / `unknown`;
⑩ the same row {0,4,8,12} → `multiple` / `early_round`; ⑪ 2-byte and 3-byte differences;
⑫ 6-byte and all-16-byte differences; ⑬ 4 bytes that are neither a column nor a diagonal;
⑭ diff_bytes ascending + determinism; ⑮ a non-16-byte input raising ValueError.

pass@1 pass rate ≥ 0.8.
