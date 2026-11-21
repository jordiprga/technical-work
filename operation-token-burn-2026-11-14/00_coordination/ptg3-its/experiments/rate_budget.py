"""Conditional planning model for 128-bit PTG.3 candidate ports (synthetic inputs)."""
import argparse
import json
import math

WIDTH = 128
# (Toeplitz blocks per emitted word, dedicated blocks at start of each epoch)
ALLOCATION = {"ais": (1, 2), "ctr": (1, 3), "ctr_seed_cmac": (1, 6),
              "ctr_cmac": (2, 6), "rs_cmac": (6, 6), "xor_cmac": (2, 6)}


def budget(profile, raw_samples_s=1e8, sample_bits=1, entropy_per_sample=0.75,
           samples_per_data=427, selector_increments=2, guard_samples=32,
           acceptance=0.99, epoch_calls=1024, selector_error=2**-160,
           core_mbit_s=None, toeplitz_blocks_s=None, extra_s_per_epoch=0.0):
    """Assumes the *accepted* classical pointwise source and selector model in port-rates.tex.

    The RS core capacity, if supplied, must measure entire RS requests normalized
    to 128 released bits. Extra CPU time includes unmeasured conditioning/reseeds.
    """
    if profile not in ALLOCATION:
        raise ValueError("Unknown profile")
    if any(not isinstance(i, int) or i <= 0 for i in (
            sample_bits, samples_per_data, selector_increments, epoch_calls)):
        raise ValueError("Dimensions, selector increments and epoch length must be positive integers")
    if not isinstance(guard_samples, int) or guard_samples < 0:
        raise ValueError("Guard length must be a nonnegative integer")
    if not (0 <= acceptance <= 1 and 0 <= selector_error <= 1
            and 0 <= entropy_per_sample <= sample_bits):
        raise ValueError("Invalid entropy, acceptance, or statistical distance")
    if (not math.isfinite(raw_samples_s) or raw_samples_s < 0 or not math.isfinite(extra_s_per_epoch)
            or extra_s_per_epoch < 0 or any(v is not None and (not math.isfinite(v) or v <= 0)
                                            for v in (core_mbit_s, toeplitz_blocks_s))):
        raise ValueError("Invalid stage rate or duration")
    columns = samples_per_data * sample_bits
    d = columns + WIDTH - 1
    selector_samples = selector_increments * ((d + sample_bits - 1) // sample_bits)
    cost = samples_per_data + selector_samples + guard_samples
    k = entropy_per_sample * samples_per_data
    # E_U ||P_u - uniform||_2^2 <= (1-2^-m) 2^-k. A real (U,R)
    # within eta of this independent ideal adds eta to any guessing event.
    surplus = 2**(WIDTH - k/2) * math.sqrt(1 - 2**-WIDTH) + selector_error * 2**WIDTH
    # Report float approximations; round the final subtraction down by one ULP
    # so a tiny positive entropy deficit never turns into a full-width guarantee.
    loss_bits = math.log1p(surplus) / math.log(2)
    kappa = max(0.0, math.nextafter(WIDTH - loss_bits, -math.inf))
    delta = min(1.0, 2**((WIDTH-k)/2 - 1) + 2 * selector_error)
    block_rate = raw_samples_s * acceptance / cost
    c, s = ALLOCATION[profile]
    if profile == "xor_cmac" and epoch_calls > 1024:
        raise ValueError("RBG3(XOR) requires a reseed by 2^17 DRBG bits in this profile")
    epoch_blocks = c * epoch_calls + s
    source_time = epoch_blocks / block_rate if block_rate else math.inf
    toeplitz_time = epoch_blocks / toeplitz_blocks_s if toeplitz_blocks_s else 0.0
    core_time = epoch_calls * WIDTH / (core_mbit_s * 1e6) if core_mbit_s else 0.0
    core_time += extra_s_per_epoch
    pipeline = max(source_time, toeplitz_time, core_time)
    serial = source_time + toeplitz_time + core_time
    calls = epoch_calls / pipeline
    return dict(raw_bit_s=raw_samples_s * sample_bits, raw_hmin_s=raw_samples_s * entropy_per_sample,
                data_columns=columns, selector_bits=d, selector_samples=selector_samples,
                data_block_hmin=k, block_tv_bound=delta, kappa=kappa, entropy_deficit_bound=min(WIDTH, loss_bits), samples_per_attempt=cost,
                accepted_blocks_s=block_rate, accepted_data_bit_s=block_rate * columns,
                accepted_data_hmin_s=block_rate * k, selector_index_bit_s=block_rate * d,
                ptg2_bit_s=block_rate * WIDTH, ptg2_hmin_s=block_rate * kappa,
                toeplitz_blocks_per_epoch=epoch_blocks, target_calls_s=calls,
                port_bit_s=calls * WIDTH, port_hmin_s=calls * kappa,
                serial_bit_s=epoch_calls * WIDTH / serial, serial_hmin_s=epoch_calls * kappa / serial)


def resolve_raw_rates(raw_bit_s, raw_entropy_bit_s, sample_bits, raw_samples_s, entropy_per_sample):
    """Resolve rate or per-sample inputs without charging entropy twice."""
    if sample_bits < 1:
        raise ValueError("Sample width must be positive")
    if raw_bit_s is not None and raw_samples_s is not None:
        raise ValueError("Choose either --raw-bit-s or --raw-samples-s")
    if raw_entropy_bit_s is not None and entropy_per_sample is not None:
        raise ValueError("Choose either --raw-entropy-bit-s or --entropy-per-sample")
    if raw_bit_s is not None:
        raw_samples_s = raw_bit_s / sample_bits
    if raw_samples_s is None:
        raw_samples_s = 1e8
    if raw_entropy_bit_s is not None:
        if not 0 <= raw_entropy_bit_s <= raw_samples_s * sample_bits:
            raise ValueError("Raw entropy rate must be between zero and the raw bit rate")
        entropy_per_sample = raw_entropy_bit_s / raw_samples_s if raw_samples_s else 0
    if entropy_per_sample is None:
        entropy_per_sample = 0.75
    return raw_samples_s, entropy_per_sample


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("profile", choices=ALLOCATION)
    opts = {"raw_samples_s": (float, None), "sample_bits": (int, 1), "entropy_per_sample": (float, None),
            "samples_per_data": (int, 427), "selector_increments": (int, 2), "guard_samples": (int, 32),
            "acceptance": (float, .99), "epoch_calls": (int, 1024), "selector_error": (float, 2**-160),
            "core_mbit_s": (float, None), "toeplitz_blocks_s": (float, None), "extra_s_per_epoch": (float, 0)}
    for key, (type_, default) in opts.items():
        cli.add_argument("--" + key.replace("_", "-"), type=type_, default=default)
    cli.add_argument("--raw-bit-s", type=float, help="Raw digital output, bit/s")
    cli.add_argument("--raw-entropy-bit-s", type=float, help="Conditional raw entropy budget, bit/s")
    args = vars(cli.parse_args())
    try:
        args["raw_samples_s"], args["entropy_per_sample"] = resolve_raw_rates(
            args.pop("raw_bit_s"), args.pop("raw_entropy_bit_s"), args["sample_bits"],
            args["raw_samples_s"], args["entropy_per_sample"])
        print(json.dumps(budget(**args), indent=2))
    except ValueError as exc:
        cli.error(str(exc))
