"""Reproduce two finite witnesses in the information-theoretic audit. All inputs are public."""
from hashlib import sha256

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def aes_block(key, block, decrypt=False):
    cipher = Cipher(algorithms.AES(key), modes.ECB())
    operation = cipher.decryptor() if decrypt else cipher.encryptor()
    return operation.update(block) + operation.finalize()


def main():
    zero, one = bytes(16), (1).to_bytes(16, "big")
    k0, k1 = bytes(32), (1).to_bytes(32, "big")
    previous_output = aes_block(k0, zero)
    doubled_output = aes_block(k1, zero)
    other_input = aes_block(k0, doubled_output, decrypt=True)
    assert previous_output != doubled_output and other_input != zero
    assert aes_block(k0, other_input) == doubled_output
    print("Correlated-key example (hex)")
    print("Missing output:", previous_output.hex())
    print("Doubled output:", doubled_output.hex())
    print("Two inputs:", zero.hex(), other_input.hex())

    first_digest, second_digest = (sha256(k0 + a).digest() for a in (zero, one))
    assert first_digest != second_digest
    print("Two attainable next states for the same previous key:")
    print(first_digest.hex(), second_digest.hex(), sep="\n")


if __name__ == "__main__":
    main()
