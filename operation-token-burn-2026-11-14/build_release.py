#!/usr/bin/env python3
"""Create an original-work snapshot, manifest and ZIP with fixed entry metadata.

No network or GitHub action. External research caches remain in the working tree.
The timestamped manifest intentionally makes distinct snapshots have distinct hashes.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent
SKIP_DIRS = {'.git', '.lake', '__pycache__', 'research_cache', '.venv', 'node_modules', '.pytest_cache'}
SKIP_SUFFIXES = {'.pyc', '.olean', '.ilean', '.sqlite3', '.sqlite3-wal', '.sqlite3-shm', '.npz'}


def collect():
    files, excluded = [], []
    for path in sorted(ROOT.rglob('*')):
        rel = path.relative_to(ROOT)
        if path.is_symlink():
            excluded.append({'path': rel.as_posix(), 'reason': 'symlink'})
            continue
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in rel.parts) or path.suffix in SKIP_SUFFIXES:
            excluded.append({'path': rel.as_posix(), 'reason': 'cache, build, database or regenerable full trace'})
            continue
        files.append(path)
    return files, excluded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT.parent/'operation-token-burn-release')
    args = parser.parse_args()
    target = args.out.resolve()
    if target == ROOT or ROOT in target.parents:
        raise ValueError('release target must be outside the source tree')
    if target.exists():
        raise ValueError('release target exists; use a new path for an immutable snapshot')
    archive = Path(str(target)+'.zip')
    if archive.exists():
        raise ValueError('archive exists; refusing to overwrite another snapshot')
    checks = json.loads((ROOT/'00_coordination/results/checks/summary.json').read_text())
    if not checks['all_executed_checks_passed'] or checks['lean_skipped']:
        raise ValueError('release requires successful final checks including Lean')
    for result in checks['results']:
        for relative, expected in result['source_sha256'].items():
            source = ROOT/result['directory']/relative
            if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
                raise ValueError(f'source changed after verification: {source}')
    files, excluded = collect()
    target.mkdir(parents=True)
    entries = []
    for source in files:
        relative = source.relative_to(ROOT)
        data = source.read_bytes()
        output = target/relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
        entries.append({'path': relative.as_posix(), 'size_bytes': len(data),
                        'sha256': hashlib.sha256(data).hexdigest()})
    manifest = {'schema_version': 1, 'created_at_utc': datetime.now(timezone.utc).isoformat(),
                'scope': 'Original deliverables; third-party research caches excluded',
                'files': entries, 'excluded': excluded,
                'limitations': 'Hash consistency only; no digital signature, authorship or certification claim'}
    encoded = (json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()
    (target/'RELEASE_MANIFEST.json').write_bytes(encoded)
    (target/'RELEASE_MANIFEST.sha256').write_text(hashlib.sha256(encoded).hexdigest()+'\n')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(target.rglob('*')):
            if not path.is_file():
                continue
            info = zipfile.ZipInfo(f'operation-token-burn/{path.relative_to(target).as_posix()}',
                                   date_time=(2026, 11, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, path.read_bytes())
    print(json.dumps({'release_directory': str(target), 'archive': str(archive),
                      'files': len(entries), 'source_bytes': sum(e['size_bytes'] for e in entries),
                      'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}, indent=2))


if __name__ == '__main__':
    main()
