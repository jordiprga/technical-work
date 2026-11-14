"""Reproducible chronological adversarial prediction benchmark."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .experiment import run_experiment, save_result
from .sources import SOURCE_NAMES


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default='nonlinear', choices=SOURCE_NAMES)
    parser.add_argument('--models', default='all', help='all or comma-separated model names')
    parser.add_argument('--n', type=int, default=12000,
                        help='Synthetic sample count; file input uses its actual length')
    parser.add_argument('--seed', type=int, default=11)
    parser.add_argument('--seeds',
                        help='Comma-separated seeds; overrides --seed. File mode repeats fits on the same sequence')
    parser.add_argument('--window', type=int, default=32)
    parser.add_argument('--epochs', type=int, default=15)
    parser.add_argument('--params', default='{}', help='JSON synthetic-source parameters')
    parser.add_argument('--bootstrap', type=int, default=300)
    parser.add_argument('--learning-sizes',
                        help='Comma-separated training prefix sizes; same validation/test, exploratory')
    parser.add_argument('--output', default=None,
                        help='Output directory; default results for synthetic or local-results for file input')
    parser.add_argument('--input', type=Path,
                        help='Local discrete sequence file; overrides synthetic source and sample count')
    parser.add_argument('--alphabet-size', type=int,
                        help='Required with --input: declared integer alphabet 0 through A-1')
    parser.add_argument('--dtype', choices=['uint8', 'uint16le', 'uint32le'],
                        help='Raw-binary sample type, default uint8; ignored for NumPy/text')
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        seeds = [int(v) for v in args.seeds.split(',')] if args.seeds else [args.seed]
        sizes = [int(v) for v in args.learning_sizes.split(',')] if args.learning_sizes else [None]
        source_params = json.loads(args.params)
        if not isinstance(source_params, dict):
            raise ValueError('--params must be a JSON object')
        if args.bootstrap < 0:
            raise ValueError('--bootstrap must be nonnegative')
        if args.input is None and (args.dtype is not None or args.alphabet_size is not None):
            raise ValueError('--dtype and --alphabet-size require --input; use --params for synthetic sources')
        data = None
        if args.input is not None:
            if args.alphabet_size is None:
                raise ValueError('--input requires an explicit --alphabet-size')
            if source_params:
                raise ValueError('--params applies only to synthetic sources, not --input')
            from .data import load_discrete_file
            data = load_discrete_file(args.input, alphabet_size=args.alphabet_size,
                                      dtype=args.dtype or 'uint8')
        source = 'file' if data is not None else args.source
        n = len(data.x) if data is not None else args.n
        output = Path(args.output or ('local-results' if data is not None else 'results'))
        if data is not None and len(seeds) > 1:
            print('File mode: seeds repeat model fitting on one fixed sequence; '
                  'these are not independent source replications.', flush=True)
        for seed in seeds:
            for size in sizes:
                kwargs = dict(source=source, n=n, seed=seed, models=args.models,
                              window=args.window, epochs=args.epochs,
                              source_params=source_params, bootstrap=args.bootstrap,
                              train_size=size, progress=lambda text: print(text, flush=True))
                if data is not None:
                    kwargs['data'] = data
                result = run_experiment(**kwargs)
                suffix = f'_train{size}' if size is not None else ''
                path = output / f'{source}_seed{seed}_n{n}{suffix}.json'
                save_result(result, path)
                print('\nModel              Accuracy  Log-loss(bits)  Fit(s)')
                for row in result['metrics']:
                    print(f'{row["model"]:18s} {row["accuracy"]:8.4f} '
                          f'{row["log_loss_bits"]:15.4f} {row["fit_seconds"]:7.2f}')
                print(f'Selected on validation: {result["selection"]["selected_model"]}; '
                      f'saved {path}', flush=True)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
