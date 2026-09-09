import numpy as np

def recover_key_byte_from_cache(timings, plaintexts, byte_idx):
    M = timings.shape[0]
    candidates = set(range(256))

    for i in range(M):
        t_row = timings[i]
        median_time = np.median(t_row)
        accessed = set(np.where(t_row < median_time)[0])

        p_byte = plaintexts[i, byte_idx]

        new_candidates = set()
        for k in candidates:
            sbox_in = p_byte ^ k
            if sbox_in in accessed:
                new_candidates.add(k)

        candidates = new_candidates

        if len(candidates) <= 1:
            break

    # Recovery succeeds only when exactly one candidate remains; an empty or still-ambiguous set counts as "undetermined"
    if len(candidates) != 1:
        return -1
    return next(iter(candidates))
