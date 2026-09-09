# D1-T4-005: Cache timing key recovery

## Task

Implement the function `recover_key_byte_from_cache(timings, plaintexts, byte_idx)`, which recovers one AES-128 key byte with a simplified synchronous cache-state probing distinguisher inspired by Osvik-Shamir-Tromer 2006.

## Background

This task abstracts each S-box index as a synthetic timing score; real hardware observes at cache-line / cache-set granularity, not at the granularity of an individual entry.

The attack flow:
1. Flush the cache
2. Run the victim's AES (16x10=160 S-box lookups)
3. Run the spy process: sweep the access time of every entry of the S-box table
4. hit/fast = that entry has been accessed by the victim; miss/slow = not accessed
5. For each key hypothesis k: x = p xor k; if x is not in the "accessed set", rule out that k
6. Repeat with different plaintexts P until k is uniquely determined

## Parameters

- `timings`: np.ndarray of shape (M, 256), M encryptions, each with the access times (ns) of the 256 S-box table entries
- `plaintexts`: np.ndarray of shape (M, 16), the 16-byte plaintexts of the M encryptions
- `byte_idx`: int, the index of the target key byte (0-15)

## Returns

- int, the recovered key byte (0-255). **The candidate is returned if and only if exactly one candidate remains after filtering**; if there are no candidates (contradictory data) or still several (insufficient information, not uniquely determined), return **-1** in either case

## Requirements

- Implement the elimination method: for each encryption, mark the S-box table entries whose access time is below the median as "accessed"
- Eliminate repeatedly for each key hypothesis until only 1 candidate remains

Python standard-library modules are allowed, as is NumPy; no other third-party package may be used.
