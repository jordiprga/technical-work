"""Executable AES/SHA and CTR profiles for synthetic experiments. Byte order is big-endian."""
from hashlib import sha256
from typing import NamedTuple
from cryptography.hazmat.primitives import cmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

MOD = 1 << 128
ZERO16 = bytes(16)
ZERO32 = bytes(32)
ZERO48 = bytes(48)


class CTRState(NamedTuple):
    key: bytes
    v: int
    reseed_counter: int


def xor(left, right):
    return bytes(a ^ b for a, b in zip(left, right, strict=True))


def word(value):
    return (value % MOD).to_bytes(16, 'big')


def aes(key, payload, *, inverse=False):
    cipher = Cipher(algorithms.AES256(key), modes.ECB())
    ctx = cipher.decryptor() if inverse else cipher.encryptor()
    return ctx.update(payload) + ctx.finalize()


def encrypt_counters(key, v, blocks):
    return aes(key, b''.join(word(v + offset) for offset in range(1, blocks + 1)))


def fields(material, counter):
    if len(material) != 48:
        raise ValueError('384 bits required')
    return CTRState(material[:32], int.from_bytes(material[32:], 'big'), counter)


def padded(data):
    if len(data) > 48:
        raise ValueError('additional input longer than seedlen')
    return data.ljust(48, b'\x00')


def update(state, material, counter):
    return fields(xor(encrypt_counters(state.key, state.v, 3), material), counter)


def instantiate(seed):
    return update(CTRState(ZERO32, 0, 0), seed, 1)


def reseed(state, seed, additional=b''):
    return update(state, xor(seed, padded(additional)), 1)


def generate(state, blocks, additional=b''):
    """90A noDF inner algorithm for whole blocks within an admitted request."""
    if not 1 <= blocks <= (1 << 12):
        raise ValueError('Request exceeds the 90A one-request limit or is empty')
    if state.reseed_counter > (1 << 48):
        raise ValueError('Reseed required')
    material = padded(additional)
    pre = update(state, material, state.reseed_counter) if additional else state
    output = encrypt_counters(pre.key, pre.v, blocks)
    advanced = CTRState(pre.key, (pre.v + blocks) % MOD, pre.reseed_counter)
    return output, update(advanced, material, pre.reseed_counter + 1)


def ctr_step(state, block):
    """Profile equation: the two keyed segments batch 3 and 4 AES blocks."""
    if len(block) != 16:
        raise ValueError('One 128-bit input per request')
    if state.reseed_counter > (1 << 48):
        raise ValueError('Reseed required')
    material = ZERO32 + block
    pre = fields(xor(encrypt_counters(state.key, state.v, 3), material), state.reseed_counter)
    segment = encrypt_counters(pre.key, pre.v, 4)
    return segment[:16], fields(xor(segment[16:], material), state.reseed_counter + 1)


def ais_step(state, block, public_constant=ZERO16):
    if len(block) != 16 or len(public_constant) != 16:
        raise ValueError('One block and a 128-bit public constant required')
    plain = xor(public_constant, block)
    return aes(state, plain), sha256(state + plain).digest()


def cmac_two_blocks(key, prefix, fresh):
    if len(prefix) != 16 or len(fresh) != 16:
        raise ValueError('Two 128-bit blocks required')
    tag = cmac.CMAC(algorithms.AES256(key))
    tag.update(prefix + fresh)
    return tag.finalize()


def ais_instantiate(first, second):
    if len(first) != 16 or len(second) != 16:
        raise ValueError('Two fresh 128-bit blocks required')
    return first + second


def ais_reseed(old_state, first, second):
    return xor(old_state, ais_instantiate(first, second))
