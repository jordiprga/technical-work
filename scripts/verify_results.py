#!/usr/bin/env python3
"""Recompute saved experiment metrics from their complete prediction archives.

Examples:
    python scripts/verify_results.py results/audited --require-audit
    python scripts/verify_results.py results/run_11.json results/run_29.json

A verified archive checks reproducibility of recorded prediction metrics. It does
not establish independence, provenance of model training, or source min-entropy.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

# Make invocation work from an arbitrary working directory without installing
# the repository as a package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from entropy_oracle.artifacts import verify_prediction_metrics


def _arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('paths', nargs='+', type=Path,
                        help='One or more result JSON files or directories searched recursively.')
    parser.add_argument('--require-audit', action='store_true',
                        help='Fail for an experiment JSON that has no prediction archive.')
    parser.add_argument('--atol', type=float, default=1e-10,
                        help='Absolute metric-comparison tolerance (default: 1e-10).')
    args = parser.parse_args(argv)
    if not math.isfinite(args.atol) or args.atol < 0:
        parser.error('--atol must be a finite nonnegative number')
    return args


def _collect_paths(paths):
    files, failures, seen = [], [], set()
    for supplied in paths:
        if supplied.is_dir():
            candidates = sorted(supplied.rglob('*.json'))
        elif supplied.is_file():
            candidates = [supplied]
        else:
            failures.append(f'{supplied}: path does not exist or is not a regular file/directory')
            continue
        for candidate in candidates:
            canonical = candidate.resolve()
            if canonical not in seen:
                files.append(candidate)
                seen.add(canonical)
    return files, failures


def _archive_path(result, result_path):
    metadata = result['prediction_archive']
    if not isinstance(metadata, dict):
        raise ValueError('prediction_archive must be an object')
    filename = metadata.get('filename')
    if (not isinstance(filename, str) or not filename or filename in ('.', '..')
            or '/' in filename or '\\' in filename or Path(filename).name != filename):
        raise ValueError('prediction_archive.filename must be a basename, without path components')
    return result_path.parent / filename


def main(argv=None):
    args = _arguments(argv)
    files, discovery_failures = _collect_paths(args.paths)
    verified = skipped = 0
    failed = len(discovery_failures)
    for failure in discovery_failures:
        print(f'FAIL {failure}', file=sys.stderr)
    for result_path in files:
        try:
            with result_path.open(encoding='utf-8') as handle:
                result = json.load(handle)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            failed += 1
            print(f'FAIL {result_path}: cannot read JSON: {error}', file=sys.stderr)
            continue
        if not (isinstance(result, dict) and 'metrics' in result and 'config' in result):
            skipped += 1
            print(f'SKIP {result_path}: not an experiment result (summary/configuration).')
            continue
        if 'prediction_archive' not in result:
            if args.require_audit:
                failed += 1
                print(f'FAIL {result_path}: experiment has no prediction archive; independent metric audit unavailable.',
                      file=sys.stderr)
            else:
                skipped += 1
                print(f'SKIP {result_path}: legacy experiment has no prediction archive; metrics were not verified.')
            continue
        try:
            archive = _archive_path(result, result_path)
            verify_prediction_metrics(result, archive, atol=args.atol)
        except Exception as error:
            failed += 1
            print(f'FAIL {result_path}: {type(error).__name__}: {error}', file=sys.stderr)
        else:
            verified += 1
            model_count = len(result['metrics']) if isinstance(result['metrics'], list) else '?'
            print(f'VERIFIED {result_path}: full archive metric audit passed ({model_count} model rows).')
    print(f'Verified {verified} auditable experiment(s); skipped {skipped}; failed {failed}.')
    if verified == 0:
        print('No auditable experiment was successfully verified.', file=sys.stderr)
    return 0 if verified > 0 and failed == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
