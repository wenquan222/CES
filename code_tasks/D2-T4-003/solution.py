# -*- coding: utf-8 -*-
"""
D2-T4-004 solution: PFA recovery of the AES last-round key.
Formula: K_last_round[byte_idx] = (the "missing" ciphertext byte value) XOR corrupted_sbox_value
"""
from collections import Counter


def pfa_recover_aes_last_round_key(
    corrupted_sbox_value: int,
    ciphertexts: list,
    byte_idx: int,
) -> int:
    # Argument validation
    if not isinstance(corrupted_sbox_value, int) or not (0 <= corrupted_sbox_value <= 255):
        raise ValueError(f"corrupted_sbox_value must be in 0..255, got {corrupted_sbox_value}")
    if not isinstance(byte_idx, int) or not (0 <= byte_idx <= 15):
        raise ValueError(f"byte_idx must be in 0..15, got {byte_idx}")
    if not ciphertexts:
        raise ValueError("ciphertexts must not be empty")
    for i, c in enumerate(ciphertexts):
        if not isinstance(c, (bytes, bytearray)) or len(c) != 16:
            raise ValueError(f"ciphertexts[{i}] must be 16 bytes, got {len(c) if hasattr(c, '__len__') else type(c)}")

    # Count the frequencies of byte byte_idx
    cnt = Counter(c[byte_idx] for c in ciphertexts)

    # Find the "missing" or least frequent byte value (all of 0..255, including zero counts)
    min_freq = float('inf')
    missing_byte = None
    for b in range(256):
        freq = cnt.get(b, 0)
        if freq < min_freq:
            min_freq = freq
            missing_byte = b
        # On a tie take the smallest byte value (range(256) ascends, so the first minimum wins)

    # Work back to K_last_round
    return missing_byte ^ corrupted_sbox_value
