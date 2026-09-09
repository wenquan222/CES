# D1-T4-006: A second-order CPA attack

## Task

Implement the function `second_order_cpa`, which mounts a second-order CPA attack on first-order Boolean-masked AES. **The function signature must be**:

```python
def second_order_cpa(traces, plaintexts, t1, t2, byte_idx=0):
    ...
```

Note that `byte_idx` **must have the default value 0** — the evaluation passes only the first 4 arguments.

## Background

The second-order distinguisher: for first-order masking S(x xor k) = y xor m (m being a random mask), second-order CPA exploits the two leakage time points t1 (the mask m being loaded) and t2 (the masked S-box output), computes combined = |T[t1] - T[t2]|, and then takes the Pearson r between combined and **HW(S(p ⊕ k))**.

> Note that the sensitive intermediate value used here is the **unmasked** `S(p ⊕ k)`: the mask m is unknown to the attacker and cannot serve as a prediction; the second-order combination `|T[t1] − T[t2]|` has already cancelled m, so the prediction model uses the Hamming weight of the unmasked S-box output directly.

## Parameters

- `traces`: np.ndarray of shape (N, T), N traces
- `plaintexts`: np.ndarray of shape (N,), the plaintext byte of each trace
- `t1`: int, the time point index at which the mask is loaded
- `t2`: int, the time point index of the masked S-box output
- `byte_idx`: int, unused for now (kept for interface consistency), **default value 0**

## Module-level names that must be exported (the evaluation imports them directly)

Besides the function, the module **must** define at top level:

```python
AES_SBOX   # the complete 256-entry standard AES S-box (a list or an ndarray)
```

The evaluation code runs `from solution import second_order_cpa, AES_SBOX`.

## Boundary conventions

- When the variance of `combined` is 0 (all traces taking the same values at t1/t2, say), all 256 correlation coefficients return `0.0` (NaN must not be returned).

## Returns

- np.ndarray of shape (256,), the Pearson correlation coefficients of the 256 key hypotheses

## Requirements

- Use the standard AES S-box
- The Pearson r formula: r = cov(X, Y) / (std(X) * std(Y))
