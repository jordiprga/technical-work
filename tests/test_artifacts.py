import copy
import hashlib
import json

import numpy as np
import pytest

from entropy_oracle.artifacts import (
    load_prediction_archive,
    verify_prediction_metrics,
    write_prediction_archive,
)
from entropy_oracle.statistics import score_predictions


@pytest.fixture
def audit():
    return {
        "y": np.array([0, 1, 2, 1], dtype=np.int64),
        "target_indices": np.array([90, 91, 93, 94], dtype=np.int64),
        "probabilities": {
            "modelo-α": np.array([[.8, .1, .1], [.1, .7, .2], [.1, .2, .7], [.1, .6, .3]]),
            "ensemble": np.array([[.2, .7, .1], [.1, .7, .2], [.8, .1, .1], [.3, .6, .1]]),
        },
    }


def result_from_audit(audit, metadata=None):
    result = {
        "split": {"test_count": len(audit["y"]), "test_target_range": [90, 94]},
        "metrics": [
            {"model": name, **score_predictions(audit["y"], q, bootstrap=0)}
            for name, q in audit["probabilities"].items()
        ],
        "trace": {
            "y": audit["y"][:2].tolist(),
            "indices": audit["target_indices"][:2].tolist(),
            "probabilities": {name: q[:2].tolist() for name, q in audit["probabilities"].items()},
        },
    }
    if metadata is not None:
        result["prediction_archive"] = metadata
    return result


def test_archive_roundtrip_keeps_all_positions_precision_and_unicode(tmp_path, audit):
    path = tmp_path / "nested" / "predictions.npz"
    metadata = write_prediction_archive(audit, path)
    restored = load_prediction_archive(path)
    assert metadata["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert metadata["n_test"] == 4
    assert metadata["alphabet_size"] == 3
    assert metadata["models"] == list(audit["probabilities"])
    json.dumps(metadata, allow_nan=False)
    assert np.array_equal(restored["y"], audit["y"])
    assert np.array_equal(restored["target_indices"], audit["target_indices"])
    for name in audit["probabilities"]:
        assert np.array_equal(restored["probabilities"][name], audit["probabilities"][name])
    with np.load(path, allow_pickle=False) as raw:
        assert raw["probabilities"].shape == (2, 4, 3)
        assert raw["probabilities"].dtype == np.float64
        assert all(raw[key].dtype.kind != "O" for key in raw.files)


def test_exact_destination_no_implicit_extension_and_no_temporary_files(tmp_path, audit):
    path = tmp_path / "audit.data"
    write_prediction_archive(audit, path)
    assert path.is_file()
    assert list(tmp_path.iterdir()) == [path]
    assert len(load_prediction_archive(path)["y"]) == 4


def test_verify_recomputes_all_metrics_and_trace(tmp_path, audit):
    path = tmp_path / "prediction.npz"
    metadata = write_prediction_archive(audit, path)
    result = result_from_audit(audit, metadata)
    report = verify_prediction_metrics(result, path)
    assert report["verified"] is True
    assert report["sha256_verified"] is True
    assert report["max_absolute_error"] == 0
    assert report["metrics_checked"] == ["accuracy", "log_loss_bits", "brier"]
    json.dumps(report, allow_nan=False)
    del result["prediction_archive"]
    assert verify_prediction_metrics(result, path)["sha256_verified"] is False


@pytest.mark.parametrize("metric", ["accuracy", "log_loss_bits", "brier"])
def test_tampered_metric_is_rejected(tmp_path, audit, metric):
    path = tmp_path / "prediction.npz"
    metadata = write_prediction_archive(audit, path)
    result = result_from_audit(audit, metadata)
    result["metrics"][0][metric] += .01
    with pytest.raises(ValueError, match=f"Metric mismatch.*{metric}"):
        verify_prediction_metrics(result, path)


def test_replaced_archive_fails_hash_verification(tmp_path, audit):
    path = tmp_path / "prediction.npz"
    metadata = write_prediction_archive(audit, path)
    result = result_from_audit(audit, metadata)
    changed = copy.deepcopy(audit)
    changed["y"][0] = 1
    write_prediction_archive(changed, path)
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_prediction_metrics(result, path)


@pytest.mark.parametrize("mutation, expected", [
    (lambda r: r["split"].update(test_count=5), "split.test_count mismatch"),
    (lambda r: r["split"].update(test_target_range=[91, 94]), "test_target_range"),
    (lambda r: r["metrics"].pop(), "model names"),
    (lambda r: r["trace"]["y"].__setitem__(0, 2), "trace labels"),
    (lambda r: r["prediction_archive"].update(n_test=7), "n_test mismatch"),
])
def test_inconsistent_result_structure_fails(tmp_path, audit, mutation, expected):
    path = tmp_path / "prediction.npz"
    result = result_from_audit(audit, write_prediction_archive(audit, path))
    mutation(result)
    with pytest.raises(ValueError, match=expected):
        verify_prediction_metrics(result, path)


@pytest.mark.parametrize("mutation, expected", [
    (lambda a: a["probabilities"]["ensemble"].__setitem__((0, 0), np.nan), "finite"),
    (lambda a: a["probabilities"]["ensemble"].__setitem__((0, 0), -.1), "in \\[0, 1\\]"),
    (lambda a: a["probabilities"]["ensemble"].__setitem__((0, 0), .5), "sum to one"),
    (lambda a: a["target_indices"].__setitem__(1, 90), "strictly increasing"),
    (lambda a: a["y"].__setitem__(0, 3), "outside.*alphabet"),
])
def test_invalid_audit_is_never_written(tmp_path, audit, mutation, expected):
    path = tmp_path / "prediction.npz"
    mutation(audit)
    with pytest.raises(ValueError, match=expected):
        write_prediction_archive(audit, path)
    assert not path.exists()


@pytest.mark.parametrize("malformation", ["missing_field", "object_names", "duplicate_names", "wrong_shape", "wrong_version"])
def test_malformed_npz_is_rejected(tmp_path, audit, malformation):
    path = tmp_path / "bad.npz"
    arrays = {
        "format_version": np.array(1),
        "y": audit["y"],
        "target_indices": audit["target_indices"],
        "model_names": np.array(list(audit["probabilities"])),
        "probabilities": np.stack(list(audit["probabilities"].values())),
    }
    if malformation == "missing_field":
        del arrays["y"]
    elif malformation == "object_names":
        arrays["model_names"] = np.array(["a", "b"], dtype=object)
    elif malformation == "duplicate_names":
        arrays["model_names"] = np.array(["a", "a"])
    elif malformation == "wrong_shape":
        arrays["probabilities"] = arrays["probabilities"][0]
    else:
        arrays["format_version"] = np.array(999)
    np.savez_compressed(path, **arrays)
    with pytest.raises(ValueError, match="Invalid prediction archive"):
        load_prediction_archive(path)


def test_missing_or_nonarchive_file_has_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="not found"):
        load_prediction_archive(tmp_path / "missing.npz")
    bad = tmp_path / "bad.npz"
    bad.write_text("this is not an npz archive")
    with pytest.raises(ValueError, match="Invalid prediction archive"):
        load_prediction_archive(bad)


def test_truncated_zip_reports_clear_archive_error(tmp_path, audit):
    path = tmp_path / "truncated.npz"
    write_prediction_archive(audit, path)
    path.write_bytes(path.read_bytes()[:100])
    with pytest.raises(ValueError, match="Invalid prediction archive"):
        load_prediction_archive(path)


def test_invalid_tolerance_is_rejected(tmp_path, audit):
    path = tmp_path / "prediction.npz"
    result = result_from_audit(audit, write_prediction_archive(audit, path))
    with pytest.raises(ValueError, match="atol"):
        verify_prediction_metrics(result, path, atol=float("nan"))
