# D5-T4-002: Min-entropy estimation

## Task

Implement the core metric of cryptographic random number assessment — the **min-entropy** H_min. It measures the "worst case": how hard it is for an attacker to guess the most likely sample value.

```text
H_min = -log2( max_i p_i )

where p_i is the empirical frequency (count_i / n) of the i-th value in the
sample sequence.
```

Min-entropy is the gold standard for assessing entropy sources in NIST SP 800-90B — **not Shannon entropy**. Because it takes the probability of the most likely value, it gives the most conservative (worst-case) entropy estimate, and H_min ≤ H_shannon always holds.

---

## Function signature

```python
def min_entropy(samples):
    """
    Compute the (empirical) min-entropy of a sample sequence, in bits per sample.

    Args:
        samples: an iterable sequence of discrete samples (the elements being
            hashable: int / str / bytes and so on)

    Returns:
        float, H_min = -log2(max_i p_i)
          - all identical      → 0.0
          - k values, uniform  → log2(k)
    """
```

---

## Constraints

1. **External entropy estimation libraries must not be called** (scipy.stats.entropy, say); count the frequencies yourself
2. The return unit is **bits per sample**
3. Empty input raises `ValueError`
4. Support any **hashable** element type (integers, strings, bytes and so on)
5. Determinism: the same input returns the same result

---

## Examples

```python
min_entropy([0, 1] * 50)        # uniform binary → 1.0
min_entropy([5] * 10)           # all identical → 0.0
min_entropy([0, 1, 2, 3] * 25)  # 4 values, uniform → 2.0
min_entropy([0, 0, 0, 1])       # max_p=0.75 → -log2(0.75) ≈ 0.4150
```

Application: if an entropy source gives H_min = 2.385 bits per sample, gathering 160 bits of entropy needs ⌈160 / 2.385⌉ = 68 samples.

---

## Background

Statistical randomness tests (NIST SP 800-22 / GM/T 0005) are only a **necessary condition** — a deterministic sequence (the binary expansion of π, say) can pass them too. What really characterizes the security of a random source is **entropy**, and cryptography uses **min-entropy** (not Shannon entropy) for the worst-case estimate. NIST SP 800-90B estimates with a dozen or so entropy estimators separately and **takes the minimum** as the final min-entropy. What this problem implements is the most basic of them, the "most common value" empirical estimate.

---

## Testing

10 cases cover: ① uniform binary = 1.0; ② all identical = 0.0; ③ 4 values uniform = 2.0; ④ 8 values uniform = 3.0; ⑤ biased with max_p=0.75; ⑥ biased with max_p=0.7; ⑦ empty input ValueError; ⑧ a single sample = 0.0; ⑨ H_min ≤ Shannon entropy; ⑩ determinism + support for the string type.

pass@1 pass rate ≥ 0.8.
