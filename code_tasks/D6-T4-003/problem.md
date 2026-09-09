# D6-T4-003: TPM PCR extension (the Measured Boot measurement hash chain)

## Task

Implement the "extend" operation of a Trusted Platform Module (TPM) Platform Configuration Register (PCR), simulating the accumulation of the measurement chain in Measured Boot.

```text
PCR_new = SHA256( PCR_old ‖ measurement )
The stage-by-stage measurements (BootROM → BootLoader → OS → App) are extended
into the same PCR in turn, forming a hash chain.
```

---

## Function signature

```python
def pcr_extend(initial_pcr, measurements):
    """
    Args:
        initial_pcr: bytes, the initial PCR value (must be 32 bytes; all zeros
            in the reset state, usually)
        measurements: list[bytes], the measurements to extend in order (each of
            arbitrary length)
    Returns:
        bytes, the final 32-byte PCR value
    """
```

---

## Constraints

1. Implement with `hashlib.sha256`, the extension formula being `PCR_new = SHA256(PCR_old ‖ measurement)`.
2. `initial_pcr` must be 32 bytes and every element of `measurements` must be `bytes`, or raise `ValueError`.
3. An empty `measurements` returns `initial_pcr` unchanged.
4. **The difference from a real TPM (which must be understood)**: the `TPM2_PCR_Extend` of TPM 2.0 takes a **digest** the same length as the hash algorithm (32 bytes under SHA-256); raw event data goes through `TPM2_PCR_Event`, which hashes it once first and then extends, that is `PCR_new = H(PCR_old ‖ H(event))`. For simplicity this problem applies `PCR_new = H(PCR_old ‖ measurement)` to a `measurement` of arbitrary length directly; it is a teaching model and must not be taken for TPM specification behaviour.
5. Return 32 `bytes`.
6. Deterministic, and order-sensitive (a different measurement order → a different PCR).

---

## Examples

```python
init = b"\x00" * 32
pcr_extend(init, [])              # == init (unchanged)
pcr_extend(init, [b"hello"])      # == sha256(init + b"hello").digest()
# Order-sensitive:
pcr_extend(init, [b"m1", b"m2"]) != pcr_extend(init, [b"m2", b"m1"])
```

---

## Background

That PCR extension uses a "hash chain" rather than overwriting is the core mechanism of Measured Boot and remote attestation:

- **Unforgeable / irreversible**: only measuring exactly the same content in exactly the same order yields a matching final PCR value. An attacker cannot insert a malicious component partway and "roll back" to the clean value (once extended, the old value cannot be recovered).
- **The difference from Secure Boot**: Secure Boot refuses to boot when verification fails; Measured Boot does not stop the boot but extends each stage's measurement into the PCR, leaving an evidence chain that remote attestation can check.
- **Remote attestation**: the verifier takes the attester's PCR values (+ a TPM-signed Quote) and compares them against the expected "golden measurements" to judge whether the boot chain has been tampered with.

Note: a real TPM also distinguishes different PCR slots and records an event log (the TCG Event Log); this problem focuses on the extension arithmetic of a single PCR.

---

## Testing

10 cases: ① an empty list leaving the PCR unchanged; ② a single extension = SHA256(init‖m); ③ a two-step hash chain; ④ order sensitivity; ⑤ a known vector; ⑥ returning 32 bytes; ⑦ an initial that is not 32 bytes / not bytes raising ValueError; ⑧ a measurement that is not bytes raising ValueError; ⑨ determinism; ⑩ irreversibility (the final value ≠ the initial or any intermediate state).

pass@1 pass rate ≥ 0.8.
