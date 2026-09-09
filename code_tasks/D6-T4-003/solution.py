# -*- coding: utf-8 -*-
"""
D6-T4-003 solution: TPM PCR extension (the measured-boot hash chain).

The platform configuration registers (PCRs) of a trusted platform module (TPM) record
boot measurements and accumulate them by extension rather than overwriting:

    PCR_new = SHA256( PCR_old ‖ measurement )

the stage-by-stage measurements (BootROM -> BootLoader -> OS -> App) are extended into the same PCR in turn, forming a hash chain.
Its security property: only measuring exactly the same content in exactly the same
order yields the same final PCR -- any change of order or content gives a different
value, so it can be neither forged nor rolled back.
That is precisely the basis of measured boot plus remote attestation.

Source: the TCG TPM 2.0 specification (ISO/IEC 11889). Note that this is a teaching
model: a real TPM2_PCR_Extend takes a digest the size of the hash, and raw event data
must first be hashed by TPM2_PCR_Event before extension (PCR_new = H(PCR_old || H(event))).
"""
import hashlib


def pcr_extend(initial_pcr, measurements):
    """
    Extend a PCR with a sequence of measurements and return the final PCR.

    Args:
        initial_pcr: bytes, the initial PCR value (must be 32 bytes; the reset state is usually all zeros)
        measurements: list[bytes], the measurements to extend in order (each of any length)

    Returns:
        bytes, the final 32-byte PCR value

    Raises:
        ValueError: initial_pcr is not 32 bytes / some measurement is not bytes
    """
    if not isinstance(initial_pcr, (bytes, bytearray)) or len(initial_pcr) != 32:
        raise ValueError("initial_pcr must be 32 bytes")
    pcr = bytes(initial_pcr)
    for m in measurements:
        if not isinstance(m, (bytes, bytearray)):
            raise ValueError("every measurement must be bytes")
        pcr = hashlib.sha256(pcr + bytes(m)).digest()
    return pcr
