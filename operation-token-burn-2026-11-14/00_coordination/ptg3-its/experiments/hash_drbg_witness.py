"""Enumerate the first byte of SHA-256 Hash_DRBG.Generate for each fresh byte.

SP 800-90A Rev. 1, §§10.1.1.2, 10.1.1.4 and 10.3.1. Public test values.
Each call starts from the same instantiated state. Only the returned byte is needed.
"""
from collections import Counter
from hashlib import sha256
from math import log2


def instantiation_v():
    # One possible realization of 32 entropy bytes and 16 nonce bytes.
    material = bytes(range(32)) + bytes(range(32, 48))
    length = (440).to_bytes(4, "big")
    digest = b"".join(sha256(bytes([i]) + length + material).digest() for i in (1, 2))
    return digest[:55]


def first_byte(v, a):
    w = sha256(b"\x02" + v + bytes([a])).digest()
    updated = (int.from_bytes(v, "big") + int.from_bytes(w, "big")) % (1 << 440)
    return sha256(updated.to_bytes(55, "big")).digest()[0]


if __name__ == "__main__":
    v = instantiation_v()
    outputs = [first_byte(v, a) for a in range(256)]
    counts = Counter(outputs)
    largest = max(counts.values())
    target = next(y for y in outputs if counts[y] == largest)
    inputs = [f"{a:02x}" for a, y in enumerate(outputs) if y == target]
    missing = 256 - len(counts)
    print(f"V={v.hex()}")
    print(f"inputs {', '.join(inputs)} -> {target:02x} (hex)")
    print(f"support={len(counts)}, max_fibre={largest}, TV={missing}/256")
    print(f"H_min={8-log2(largest):.8f} bits")
