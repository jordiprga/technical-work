"""Reproducible serial microbenchmarks and explicit synthetic raw-sample budget."""
import argparse
import gc
import hashlib
import json
import math
import platform
import statistics
import time
from pathlib import Path
import cryptography
from cryptography.hazmat.backends.openssl.backend import backend
from profiles import ZERO16, ZERO32, ais_step, ctr_step, instantiate


def quantile(values, p):
    return sorted(values)[math.ceil(p * len(values)) - 1]


def model(batch, *, horizon=2**32, life_error_bits=64, entropy_rate=0.75,
          increments=2, guard=32, acceptance=0.99, acquisition_hz=100_000_000):
    """One raw bit per sample. Hypothetical selector and raw parameters; see README."""
    output = 128 * batch
    # Reserve the full error budget here for LHL's ideal selector, to reproduce the baseline.
    bits = math.ceil(output + 2 * (life_error_bits + math.log2(math.ceil(horizon / batch)) - 1))
    data = math.ceil(bits / entropy_rate)
    selector = data + output - 1
    expected = (data + increments * selector + guard) / acceptance
    return dict(blocks=batch, output_bits=output, required_data_min_entropy=bits, data_samples=data,
                selector_length=selector, samples_per_accepted_batch=expected,
                bits_per_raw_sample=output/expected, source_only_Mbit_s=output/expected*acquisition_hz/1e6)


def measure(samples, repeats, warmup):
    stream = hashlib.shake_256(b'PTG.3 synthetic timing inputs v1').digest(16*samples)
    blocks = [stream[16*i:16*i+16] for i in range(samples)]
    kernels = {'ais_aes_sha':(ais_step, ZERO32), 'ctr_v':(ctr_step,instantiate(bytes(range(48))))}
    measurements = {name:{'rates':[], 'latencies':[]} for name in kernels}
    was_enabled = gc.isenabled()
    gc.disable()
    try:
        for run in range(repeats):
            order = list(kernels) if run % 2 == 0 else list(reversed(kernels))
            for name in order:
                step, state = kernels[name]
                for i in range(warmup):
                    _, state = step(state, blocks[i % samples])
                before = time.perf_counter_ns()
                for block in blocks:
                    _, state = step(state, block)
                elapsed = time.perf_counter_ns() - before
                measurements[name]['rates'].append(128*samples*1000/elapsed)
                # Instrument latency on a separate pass; continuous state, precomputed inputs.
                for block in blocks:
                    before = time.perf_counter_ns()
                    _, state = step(state, block)
                    measurements[name]['latencies'].append(time.perf_counter_ns() - before)
    finally:
        if was_enabled:
            gc.enable()
    answer = {}
    for name, data in measurements.items():
        answer[name] = dict(median_Mbit_s=statistics.median(data['rates']), rounds_Mbit_s=data['rates'],
                            latency_p50_us=quantile(data['latencies'], .50)/1000,
                            latency_p99_us=quantile(data['latencies'], .99)/1000)
    return answer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--calls', type=int, default=16384)
    parser.add_argument('--rounds', type=int, default=7)
    parser.add_argument('--warmup', type=int, default=512)
    opts = parser.parse_args()
    if opts.calls < 1 or opts.rounds < 1 or opts.warmup < 0:
        parser.error('calls and rounds must be positive; warmup must be nonnegative')
    this_dir = Path(__file__).resolve().parent
    report = dict(python=platform.python_version(), machine=platform.machine(), os=platform.system(),
                  cryptography=cryptography.__version__, backend=backend.openssl_version_text(),
                  timing='perf_counter_ns; one serial Python process; GC disabled during samples; alternating order',
                  parameters=vars(opts), measurement='fresh block supplied from precomputed synthetic inputs',
                  digests={p:hashlib.sha256((this_dir/p).read_bytes()).hexdigest() for p in ['profiles.py','benchmark.py']},
                  model_parameters=dict(horizon_blocks=2**32, budget_bits=64, entropy_per_data_sample=.75,
                                        bits_per_raw_sample=1, selector_increments=2, guard_samples=32,
                                        acceptance=.99, assumed_raw_Hz=100_000_000),
                  models=[model(b) for b in [1,4,16]], kernels=measure(opts.calls, opts.rounds, opts.warmup))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
