# D2-T4-004: Fault sensitivity analysis (FSA) key recovery

## Task

Implement the key distinguisher of fault sensitivity analysis (FSA), recovering a single key byte from a sequence of "fault sensitivities".

```text
The core observation of FSA (Li-Sakiyama-Gomisawa, CHES 2010):
the critical path delay of a hardware S-box implementation is approximately
linearly and positively correlated with the Hamming weight of its input value.
The attacker shortens the clock glitch width gradually, and the critical glitch
width at which an error "just" occurs is the critical path delay
(= the fault sensitivity).

The round 1 S-box input = plaintext ⊕ key, so the key distinguisher is:
  for each key byte guess k, compute the correlation coefficient between
  HW(plaintext ⊕ k) and the sensitivity sequence, and take the k with the
  greatest positive correlation.
```

---

## Function signature

```python
def fsa_recover(plaintexts, sensitivities):
    """
    Args:
        plaintexts:    list[int], the plaintext byte (0..255) of each injection
        sensitivities: list[float], the corresponding fault sensitivities
            (critical path delay / critical glitch width)
    Returns:
        int, 0..255, the key byte maximizing corr(HW(p^k), sensitivities)
        (positive correlation)
    """
```

---

## Module-level names that must be exported (the evaluation imports them directly, so name them exactly as below)

Besides `fsa_recover`, the two helper functions **must** be defined at module top level under the following names (the evaluation calls them separately):

```python
def _hw(x: int) -> int:            # Hamming weight
def _pearson(xs: list, ys: list) -> float:   # Pearson correlation coefficient; returns 0.0 when either variance is 0
```

The evaluation code runs `from solution import fsa_recover, _hw, _pearson`.

## Constraints

1. **Libraries such as numpy/scipy must not be called**; implement the Hamming weight and the Pearson correlation coefficient yourself (that is, the `_hw` / `_pearson` above)
2. **The signed maximum positive correlation must be used**, not `|correlation|` — otherwise `k` and `k⊕0xFF` are indistinguishable under the HW model (their HWs being complementary and their correlation coefficients exactly opposite). In the FSA physical model the critical path delay increases monotonically with the input HW (positive correlation)
3. Return 0.0 when either variance in the Pearson correlation is 0 (avoiding division by zero)
4. Exceptions (`ValueError`): the two sequences having unequal lengths / fewer than 2 samples / a plaintext byte outside [0,255]
5. Determinism: the same input returns the same key byte

---

## Example

```python
def hw(x): return bin(x).count('1')
pts = list(range(256))
k_true = 0x2B
# The ideal sensitivity: sens = 2*HW(p^k_true) + 10
sens = [2.0 * hw(p ^ k_true) + 10.0 for p in pts]
fsa_recover(pts, sens)   # 0x2B
```

---

## Background

FSA is a hybrid of fault attacks and side-channel correlation analysis — it does not read power consumption but uses the "critical fault glitch width / critical path delay" as the leakage quantity and then recovers the key by correlation analysis. This is a direction studied in depth by research groups in China (the group of Wang An among others), which later developed into fault rate analysis (FRA, IEEE TCAS-II 2013) and meta-stability attacks (Ren-Wang-Wu, CHES 2015). It is structurally similar to power CPA but entirely different in physical origin.

**A key engineering detail**: under the HW model the `HW(p^k)` of `k` and of `k⊕0xFF` are complementary, so `|correlation|` cannot tell them apart; in FSA the delay increases monotonically with HW (positive correlation), so "the greatest positive correlation" determines `k` uniquely.

---

## Testing

10 cases: ① noise-free recovery over all 256 plaintexts (several k_true); ② recovery from a subset of plaintexts; ③ recovery with a little noise; ④ the Hamming weight correct; ⑤ Pearson perfect positive correlation = 1; ⑥ zero variance = 0; ⑦ unequal lengths ValueError; ⑧ too few samples ValueError; ⑨ plaintext out of range ValueError; ⑩ determinism + the return range.

pass@1 pass rate ≥ 0.8.
