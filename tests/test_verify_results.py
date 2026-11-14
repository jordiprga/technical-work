"""CLI-level regression tests for full saved-prediction metric audits."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

from entropy_oracle.experiment import run_experiment, save_result

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'verify_results.py'


def _run(*paths, require=False):
    command = [sys.executable, str(SCRIPT), *map(str, paths)]
    if require:
        command.append('--require-audit')
    return subprocess.run(command, text=True, capture_output=True, cwd=SCRIPT.parent.parent,
                          timeout=30, check=False)


@pytest.fixture
def audited_result(tmp_path):
    result = run_experiment(source='bernoulli', n=400, seed=1021,
                            models=['marginal', 'markov1'], window=8, bootstrap=0)
    path = save_result(result, tmp_path / 'audited.json')
    stored = json.loads(path.read_text())
    assert stored['schema_version'] >= 2
    assert stored['prediction_archive']['filename']
    return path


def test_verified_result_and_recursive_directory_discovery(audited_result):
    summary = audited_result.parent / 'summary.json'
    summary.write_text(json.dumps({'note': 'summary, not a model experiment'}))
    completed = _run(audited_result.parent, audited_result, require=True)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert 'Verified 1 auditable experiment(s); skipped 1; failed 0.' in completed.stdout


def test_changed_metric_is_detected(audited_result):
    result = json.loads(audited_result.read_text())
    result['metrics'][0]['accuracy'] = float(result['metrics'][0]['accuracy']) + .1
    audited_result.write_text(json.dumps(result))
    completed = _run(audited_result)
    assert completed.returncode == 1
    assert 'FAIL' in completed.stderr
    assert 'Verified 0' in completed.stdout


def test_archive_tampering_is_detected_by_declared_digest(audited_result):
    result = json.loads(audited_result.read_text())
    archive = audited_result.parent / result['prediction_archive']['filename']
    # Appending bytes can leave ZIP/NPZ contents readable; the declared digest
    # must still detect alteration independently of metric recomputation.
    with archive.open('ab') as handle:
        handle.write(b'altered archive bytes')
    completed = _run(audited_result)
    assert completed.returncode == 1
    assert 'FAIL' in completed.stderr


@pytest.mark.parametrize('filename', ['../outside.npz', '/tmp/outside.npz', '..\\outside.npz'])
def test_archive_path_traversal_is_rejected(audited_result, filename):
    result = json.loads(audited_result.read_text())
    result['prediction_archive']['filename'] = filename
    audited_result.write_text(json.dumps(result))
    completed = _run(audited_result)
    assert completed.returncode == 1
    assert 'must be a basename' in completed.stderr


def test_missing_archive_is_a_failure(audited_result):
    result = json.loads(audited_result.read_text())
    (audited_result.parent / result['prediction_archive']['filename']).unlink()
    completed = _run(audited_result)
    assert completed.returncode == 1
    assert 'FAIL' in completed.stderr


def test_legacy_results_are_skipped_and_require_audit_fails(audited_result):
    legacy = audited_result.parent / 'legacy.json'
    legacy.write_text(json.dumps({'schema_version': 1, 'config': {}, 'metrics': []}))
    completed = _run(audited_result.parent)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert 'legacy experiment' in completed.stdout and 'metrics were not verified' in completed.stdout
    required = _run(audited_result.parent, require=True)
    assert required.returncode == 1
    assert 'experiment has no prediction archive' in required.stderr


def test_only_summary_or_legacy_does_not_count_as_success(tmp_path):
    (tmp_path / 'summary.json').write_text(json.dumps({'summary': []}))
    (tmp_path / 'legacy.json').write_text(json.dumps({'config': {}, 'metrics': []}))
    completed = _run(tmp_path)
    assert completed.returncode == 1
    assert 'No auditable experiment' in completed.stderr
    assert 'Verified 0 auditable experiment(s); skipped 2;' in completed.stdout


def test_invalid_input_path_and_malformed_json_fail(tmp_path):
    missing = _run(tmp_path / 'missing.json')
    assert missing.returncode == 1
    assert 'path does not exist' in missing.stderr
    malformed = tmp_path / 'malformed.json'
    malformed.write_text('{')
    completed = _run(malformed)
    assert completed.returncode == 1
    assert 'cannot read JSON' in completed.stderr
