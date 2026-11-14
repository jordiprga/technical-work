import json
import subprocess
import sys

import numpy as np
import pytest

from entropy_oracle.cli import main


def test_cli_synthetic_run(tmp_path, capsys):
    assert main(['--source', 'nonlinear', '--models', 'marginal,markov5',
                 '--n', '500', '--bootstrap', '0', '--output', str(tmp_path)]) == 0
    result = json.loads((tmp_path / 'nonlinear_seed11_n500.json').read_text())
    assert result['config']['n'] == 500
    assert result['config']['models'] == ['marginal', 'markov5']
    assert result['split']['test_count'] == 100
    assert 'Selected on validation:' in capsys.readouterr().out


def test_cli_file_uses_actual_length(tmp_path):
    path = tmp_path / 'private_capture.npy'
    np.save(path, np.arange(500, dtype=np.uint8) % 2)
    output = tmp_path / 'results'
    assert main(['--input', str(path), '--alphabet-size', '2', '--n', '9999',
                 '--models', 'marginal', '--bootstrap', '0', '--output', str(output)]) == 0
    result = json.loads((output / 'file_seed11_n500.json').read_text())
    assert result['config']['n'] == 500
    assert result['config']['source'] == 'file'
    assert not list(output.glob('*private_capture*'))


def test_cli_binary_dtype(tmp_path):
    path = tmp_path / 'capture.bin'
    (np.arange(500) % 2).astype('<u2').tofile(path)
    output = tmp_path / 'out'
    assert main(['--input', str(path), '--alphabet-size', '2', '--dtype', 'uint16le',
                 '--models', 'marginal', '--bootstrap', '0', '--output', str(output)]) == 0
    assert (output / 'file_seed11_n500.json').is_file()


def test_cli_file_defaults_to_local_results(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    np.save('capture.npy', np.arange(500) % 2)
    assert main(['--input', 'capture.npy', '--alphabet-size', '2',
                 '--models', 'marginal', '--bootstrap', '0']) == 0
    assert (tmp_path / 'local-results' / 'file_seed11_n500.json').is_file()
    assert not (tmp_path / 'results').exists()


@pytest.mark.parametrize('arguments', [
    ['--params', '[]'], ['--params', '{broken'], ['--alphabet-size', '2'],
    ['--bootstrap', '-1'], ['--input', 'capture.npy'],
])
def test_cli_invalid_configuration_exits_cleanly(arguments):
    with pytest.raises(SystemExit) as exc:
        main(arguments)
    assert exc.value.code == 2


def test_cli_module_help():
    run = subprocess.run([sys.executable, '-m', 'entropy_oracle.cli', '--help'],
                         capture_output=True, text=True, check=True)
    assert '--input' in run.stdout
    assert '--models' in run.stdout
