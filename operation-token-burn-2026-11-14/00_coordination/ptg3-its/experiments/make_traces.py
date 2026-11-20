"""Use the OpenSSL CLI as an independent primitive backend for the two trace fixtures."""
import hashlib
import json
import subprocess


def encrypt(key, value):
    return subprocess.run(['openssl', 'enc', '-aes-256-ecb', '-nopad', '-nosalt', '-K', key.hex()],
                          input=value, capture_output=True, check=True).stdout


def increment(value):
    return ((int.from_bytes(value, 'big') + 1) % (1 << 128)).to_bytes(16, 'big')


def transition(key, counter, supplied):
    buffer = b''
    for _ in range(3):
        counter = increment(counter)
        buffer += encrypt(key, counter)
    new = bytes(a ^ b for a, b in zip(buffer, supplied, strict=True))
    return new[:32], new[32:]


def build():
    ais_state = bytes(range(32))
    constant = bytes(range(16, 32))
    key = bytes(range(32))
    counter = bytes.fromhex('fffffffffffffffffffffffffffffffe')
    result = dict(initial_ais=ais_state.hex(), ais_constant=constant.hex(), initial_ctr=[key.hex(), counter.hex(), 1], steps=[])
    for idx, block in enumerate([bytes(16), bytes(range(240, 256))]):
        plain = bytes(a ^ b for a,b in zip(block, constant, strict=True))
        ais_y = encrypt(ais_state, plain)
        ais_state = hashlib.sha256(ais_state + plain).digest()
        supplied = bytes(32) + block
        key, counter = transition(key, counter, supplied)
        counter = increment(counter)
        ctr_y = encrypt(key, counter)
        key, counter = transition(key, counter, supplied)
        result['steps'].append(dict(block=block.hex(), ctr_output=ctr_y.hex(), ctr_state=[key.hex(), counter.hex(), 2+idx],
                                    ais_output=ais_y.hex(), ais_state=ais_state.hex()))
    return result


if __name__ == '__main__':
    print(json.dumps(build(), indent=2))
