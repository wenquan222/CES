# D5-T4-003: Statistical randomness testing — the monobit frequency test

## Task

Implement the most basic randomness test of NIST SP 800-22 — the monobit frequency test — computing a P-value for a binary sequence to judge whether the counts of 0s and 1s are close to balanced.

```text
H0: the sequence is random (0/1 roughly balanced)
  εi ∈ {0,1},  Xi = 2εi − 1 ∈ {−1,+1}
  Sn = Σ Xi
  Sobs = |Sn| / sqrt(n)
  P-value = erfc( Sobs / sqrt(2) )
Decision: P-value ≥ α (=0.01) → accept H0 (no departure from randomness found)
```

---

## Function signature

```python
def monobit_frequency_test(bits):
    """
    Args:
        bits: list[int], each element ∈ {0, 1}
    Returns:
        float, a P-value ∈ [0, 1]
    """
```

---

## Module-level names that must be exported (the evaluation imports them directly, so name them exactly as below)

Besides `monobit_frequency_test`, your own complementary error function **must be named `_erfc` (with the leading underscore)** and defined at module top level:

```python
def _erfc(x: float) -> float:   # the complementary error function; the evaluation verifies its accuracy separately
```

The evaluation code runs `from solution import monobit_frequency_test, _erfc`.

## Constraints

1. **`math.erfc` / `scipy.special.erfc` must not be called**; implement the complementary error function by numerical approximation yourself (that is, the `_erfc` above; `math.exp` / `math.sqrt` are allowed). This is the core of the problem — an RNG evaluation tool must compute its own statistics.
2. numpy / scipy must not be used.
3. Exceptions (`ValueError`): an empty sequence / an element outside `{0,1}`.
4. The P-value returned must lie in `[0,1]`.
5. Determinism: the same input returns the same P-value.

---

## Examples

```python
# The official NIST SP 800-22 example: ε = 1011010101 (n=10)
bits = [1,0,1,1,0,1,0,1,0,1]   # 6 ones, 4 zeros
monobit_frequency_test(bits)   # ≈ 0.527089  (P-value ≥ 0.01 → pass)

monobit_frequency_test([0,1]*50)   # 1.0   (perfectly balanced, Sn=0)
monobit_frequency_test([0]*100)    # ≈ 0   (all zeros, thoroughly non-random)
```

---

## Background

The monobit frequency test is the "entry gate" of SP 800-22: if a sequence cannot even pass this (0s and 1s severely imbalanced), the remaining 14 tests need not be run. Its statistical core is to map the bits to ±1 and sum, use the central limit theorem to approximate `Sobs` as a standard normal, and then compute the two-sided tail probability with `erfc`.

**Why erfc must be implemented yourself**: an evaluation tool cannot assume scipy is present in the runtime environment; more importantly, understanding the relation between `erfc` and the P-value is what allows the hypothesis testing framework behind "P-value ≥ 0.01 means pass" (the type I error α) to be read correctly. Note that passing a statistical test is a **necessary but not sufficient** condition for randomness — a deterministic sequence (the binary expansion of π, say) can pass too, so a SP 800-90B min-entropy assessment is also needed.

A reference numerical approximation of erfc is the `erfcc` of Numerical Recipes (fractional error < 1.2e-7).

---

## Testing

10 cases: ① all zeros → P<0.01; ② all ones → P<0.01; ③ alternating balanced 0/1 → P=1.0; ④ the official NIST example P≈0.527089; ⑤ erfc(0)=1; ⑥ erfc(1)≈0.15730; ⑦ the symmetry erfc(−x)=2−erfc(x); ⑧ P-value∈[0,1]; ⑨ empty / non-0-1 elements ValueError; ⑩ determinism + a slight imbalance giving P∈(0,1).

pass@1 pass rate ≥ 0.8.
