# D2-T4-003: PFA recovery of the AES final-round key

## Problem statement

Implement the core step of **final-round key recovery** in a persistent fault analysis (PFA) attack.

The PFA attack assumes that the attacker injects a fault into the S-box table (resident in memory) of an AES implementation, replacing the original value `v_corrupt` with some other value. The fault is **persistent** — every subsequent encryption uses this "bad S-box table", so **at every byte position of the ciphertext, one particular value that should normally appear never appears at all**.

The key recovery formula:

```
K_last_round[i] = (the "missing value" of byte i over a large number of ciphertexts) XOR v_corrupt
```

---

## Function signature

```python
def pfa_recover_aes_last_round_key(
    corrupted_sbox_value: int,
    ciphertexts: list[bytes],
    byte_idx: int
) -> int:
    pass
```

| Parameter | Description |
|------|------|
| `corrupted_sbox_value` | the original value `v_corrupt` (0..255) that was "knocked out" of the standard AES S-box table |
| `ciphertexts` | the list of ciphertexts collected after encrypting with the "bad S-box table" (16 bytes each) |
| `byte_idx` | the byte index (0..15) of the round 10 subkey to recover |

---

## Output

Return `K_last_round[byte_idx]` (int, 0..255)

The formula:

```text
K_last_round[byte_idx] = (the least frequent value of byte byte_idx among the ciphertexts) XOR corrupted_sbox_value
```

> **The principle**: the last round of AES has no MixColumns, so the ciphertext c[i] = SubBytes(...) XOR K_last[i]. Since the original `v_corrupt` no longer appears in the S-box table (having been replaced), the value `v_corrupt XOR K_last[i]` never appears in the ciphertext.
> Find the "missing" byte value statistically and XOR it with `v_corrupt` to obtain `K_last[i]`.

---

## Constraints

1. Brute-forcing every possible K by decryption and then verifying is **not allowed** (a statistical method is required)
2. Frequency counting: if several byte values tie for the lowest frequency, take the **smallest** byte value
3. An empty `ciphertexts` list or an element of the wrong shape (not 16 bytes) should raise `ValueError`
4. `corrupted_sbox_value` or `byte_idx` out of range should raise `ValueError`
5. No statistics library other than `scipy` / `numpy` may be used (the standard Python `collections.Counter` is allowed)
6. The function should be deterministic (the same input returning the same result)

---

## Example

```python
import os
# Suppose K_last_round[0] = 0x42 and v_corrupt = 0x7C (the original value of S-box[1])
# Then the ciphertext value c[0] = 0x7C ⊕ 0x42 = 0x3E never appears

# Generating the simulated data: random c[0] but excluding 0x3E
ciphertexts = []
for _ in range(10000):
    c = bytearray(os.urandom(16))
    while c[0] == 0x3E:
        c[0] = os.urandom(1)[0]
    ciphertexts.append(bytes(c))

# The attack
k0 = pfa_recover_aes_last_round_key(0x7C, ciphertexts, 0)
assert k0 == 0x42  # recovered successfully
```

---

## Testing

10 test cases. The main metric = task_success (0 or 1 for the whole task, 1 only if no blocking failure occurs and every functional case passes; process and performance cases are excluded from the functional set but block on failure, the threshold above being diagnostic only), the secondary metric = pass@1.

Python standard-library modules are allowed, as are NumPy and SciPy; no other third-party package may be used.
