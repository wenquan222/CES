def ineffective_fault_bias_score(
    reference_cipher: bytes,
    faulty_ciphertexts: list[bytes]
) -> float:

    total = len(faulty_ciphertexts)

    if total < 10:
        return 0.0

    ineffective = 0

    for c in faulty_ciphertexts:
        if c == reference_cipher:
            ineffective += 1

    score = ineffective / total

    if score < 0:
        score = 0.0

    if score > 1:
        score = 1.0

    return score