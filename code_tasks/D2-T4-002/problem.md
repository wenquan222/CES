# D2-T4-002: Counting the proportion of ineffective faults

## Problem statement

Implement a function that counts the "proportion of ineffective faults" in a fault experiment.

An ineffective fault means:

```text
after the fault injection, the ciphertext does not change
```

This indicator can be used to analyse the stability of fault propagation.

---

## Function signature

```python
def ineffective_fault_bias_score(
    reference_cipher: bytes,
    faulty_ciphertexts: list[bytes]
) -> float:
    pass
```

---

## Input

- reference_cipher: the reference correct ciphertext
- faulty_ciphertexts: the list of ciphertexts obtained from repeated fault experiments

---

## Output

Return:

```python
the proportion of ineffective faults
```

The formula:

```text
score = the proportion of the collected ciphertexts that are unchanged
        relative to the reference ciphertext

(the exact statistic, its normalization and the small-sample rule are part
 of what this task asks you to work out from the description above)
```

Range:

```text
0.0 ~ 1.0
```

---

## Special rule

If:

```python
len(faulty_ciphertexts) < 10
```

return:

```python
0.0
```

---

## Examples

```python
ref = bytes([0]*16)

# Note: there must be >= 10 samples, or the "special rule" returns 0.0 outright
faults = [bytes([0]*16)] * 6 + [bytes([1]*16)] * 4   # 10 entries: 6 unchanged, 4 changed

score = ineffective_fault_bias_score(ref, faults)

# 6 / 10 = 0.6
```

```python
# Counter-example: with fewer than 10 samples, 0.0 is returned whatever the proportion
ineffective_fault_bias_score(ref, [bytes([0]*16)] * 3)   # -> 0.0 (not 1.0)
```

Python standard-library modules are allowed; no third-party package may be used, SciPy included.
