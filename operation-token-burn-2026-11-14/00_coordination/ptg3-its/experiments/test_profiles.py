"""Run with python -m unittest -v from this directory."""
import json
from pathlib import Path
from unittest import TestCase
from profiles import (CTRState, MOD, ZERO16, ZERO32, aes, ais_step, cmac_two_blocks, ctr_step,
                      encrypt_counters, generate, instantiate, reseed, update, word, xor)

HERE = Path(__file__).resolve().parent


def as_hex(state):
    return [state.key.hex(), word(state.v).hex(), state.reseed_counter]


class Profiles(TestCase):
    def test_official_cavp_instantiate_reseed_two_generates(self):
        vectors = json.loads((HERE / 'nist_vectors.json').read_text())['vectors']
        self.assertEqual(len(vectors), 4)
        for record in vectors:
            with self.subTest(member=record['member'], extra=record['additional_input_len']):
                state = instantiate(bytes.fromhex(record['entropy']))
                self.assertEqual(as_hex(state), record['states']['INSTANTIATE'] + [1])
                if record['reseed_entropy']:
                    state = reseed(state, bytes.fromhex(record['reseed_entropy']), bytes.fromhex(record['reseed_additional']))
                    self.assertEqual(as_hex(state), record['states']['RESEED'] + [1])
                for i, label in enumerate(['GENERATE (FIRST CALL)', 'GENERATE (SECOND CALL)']):
                    output, state = generate(state, record['returned_bits_len'] // 128, bytes.fromhex(record['additional'][i]))
                    self.assertEqual(as_hex(state), record['states'][label] + [i + 2])
                self.assertEqual(output.hex(), record['second_output'])

    def test_openssl_traces_and_procedure_equivalence(self):
        vector = json.loads((HERE / 'profile_traces.json').read_text())
        state = CTRState(bytes.fromhex(vector['initial_ctr'][0]), int(vector['initial_ctr'][1], 16), 1)
        ais_state = bytes.fromhex(vector['initial_ais'])
        constant = bytes.fromhex(vector['ais_constant'])
        for step in vector['steps']:
            block = bytes.fromhex(step['block'])
            result = ctr_step(state, block)
            self.assertEqual(generate(state, 1, ZERO32 + block), result)
            out, state = result
            self.assertEqual([out.hex(), as_hex(state)], [step['ctr_output'], step['ctr_state']])
            old = ais_state
            out, ais_state = ais_step(ais_state, block, constant)
            self.assertEqual([out.hex(), ais_state.hex()], [step['ais_output'], step['ais_state']])
            self.assertEqual(xor(aes(old, out, inverse=True), constant), block)

    def test_additional_empty_zero_and_right_padding(self):
        state = instantiate(bytes(range(48)))
        fresh = bytes(range(16))
        self.assertNotEqual(generate(state, 1), ctr_step(state, ZERO16))
        self.assertNotEqual(generate(state, 1, fresh), ctr_step(state, fresh))
        self.assertEqual(generate(state, 1, fresh), generate(state, 1, fresh + ZERO32))

    def test_adjacent_states_and_terminal_exclusions(self):
        sample_states = [CTRState(bytes(range(32)), v, 1) for v in [0, 2**32-1, MOD-1]]
        for state in sample_states:
            fresh = bytes(range(16))
            output, post = ctr_step(state, fresh)
            derived = encrypt_counters(state.key, state.v, 3)
            prime = derived[:32]
            pre_from_y = int.from_bytes(aes(prime, output, inverse=True), 'big') - 1
            self.assertEqual(xor(word(pre_from_y), derived[32:]), fresh)
            c1, c2 = post.key[:16], post.key[16:]
            self.assertEqual(len({output, c1, c2}), 3)
            dec_c1 = int.from_bytes(aes(prime, c1, inverse=True), 'big')
            self.assertEqual(aes(prime, word(dec_c1 - 1)), output)

    def test_omitting_postupdate(self):
        state = instantiate(bytes(range(48)))
        block = bytes(range(16))
        expected, correct = ctr_step(state, block)
        pre = update(state, ZERO32 + block, 1)
        mutant = CTRState(pre.key, (pre.v + 1) % MOD, 2)
        self.assertEqual(aes(mutant.key, word(mutant.v)), expected)
        self.assertNotEqual(correct, mutant)
        self.assertNotEqual(ctr_step(correct, block)[0], ctr_step(mutant, block)[0])

    def test_32_bit_increment_mutation(self):
        key = bytes(range(32))
        v = (0xA1B2C3 << 32) + (1 << 32) - 1
        self.assertNotEqual(encrypt_counters(key, v, 1), aes(key, word(v & ~((1 << 32) - 1))))

    def test_full_cmac_in_last_block(self):
        key = bytes(range(32))
        prefix = bytes(range(16))
        fresh = bytes(range(16,32))
        l = int.from_bytes(aes(key, ZERO16), 'big')
        l1 = word((l << 1) ^ (0x87 if l >> 127 else 0))
        tag = cmac_two_blocks(key, prefix, fresh)
        mask = xor(aes(key, prefix), l1)
        self.assertEqual(tag, aes(key, xor(mask, fresh)))
        self.assertEqual(xor(mask, aes(key, tag, inverse=True)), fresh)
        self.assertEqual(ctr_step(instantiate(bytes(range(48))), tag),
                         generate(instantiate(bytes(range(48))), 1, ZERO32 + tag))

    def test_reseed_limit(self):
        exhausted = CTRState(ZERO32, 0, (1 << 48) + 1)
        with self.assertRaises(ValueError):
            generate(exhausted, 1)
        with self.assertRaises(ValueError):
            ctr_step(exhausted, ZERO16)
        self.assertEqual(reseed(exhausted, bytes(range(48))).reseed_counter, 1)

    def test_ais_reseed_incorporates_old_state(self):
        from profiles import ais_instantiate, ais_reseed
        b0, b1 = bytes(range(16)), bytes(range(16,32))
        old = bytes([0xA5]) * 32
        new = ais_reseed(old, b0, b1)
        self.assertEqual(ais_instantiate(b0,b1), b0+b1)
        self.assertEqual(xor(old,new), b0+b1)
        self.assertNotEqual(new, ais_reseed(ZERO32,b0,b1))
