"""Complete held-out prediction archives and independent metric verification.

Archives contain only fixed-dtype NumPy arrays and are always read with
``allow_pickle=False``. A SHA-256 binds an archive to the corresponding JSON
result; it detects modification, not authenticity of training or source data.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import math
import os
from pathlib import Path
import tempfile
from typing import Any
import zipfile

import numpy as np

from .statistics import score_predictions


FORMAT_NAME = "entropy-oracle-predictions-npz"
FORMAT_VERSION = 1
_ARCHIVE_FIELDS = {"format_version", "y", "target_indices", "model_names", "probabilities"}
_METRICS = ("accuracy", "log_loss_bits", "brier")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _integer_vector(value: Any, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != 1 or array.size == 0 or array.dtype.kind not in "iu":
        raise ValueError(f"{name} must be a nonempty one-dimensional integer array")
    if np.any(array < 0) or np.any(array > np.iinfo(np.int64).max):
        raise ValueError(f"{name} must contain nonnegative int64-compatible integers")
    return np.array(array, dtype=np.int64, copy=True)


def _validated_audit(audit: Mapping[str, Any]) -> tuple[np.ndarray, np.ndarray, list[str], np.ndarray]:
    if not isinstance(audit, Mapping):
        raise ValueError("audit must be a mapping with y, target_indices and probabilities")
    missing = {"y", "target_indices", "probabilities"} - set(audit)
    if missing:
        raise ValueError(f"audit is missing fields: {sorted(missing)}")
    y = _integer_vector(audit["y"], "y")
    indices = _integer_vector(audit["target_indices"], "target_indices")
    if indices.shape != y.shape:
        raise ValueError("target_indices and y must have identical shapes")
    if np.any(np.diff(indices) <= 0):
        raise ValueError("target_indices must be strictly increasing without duplicates")
    probabilities = audit["probabilities"]
    if not isinstance(probabilities, Mapping) or not probabilities:
        raise ValueError("probabilities must be a nonempty mapping from model names to arrays")
    names = list(probabilities)
    if any(not isinstance(name, str) or not name or "\x00" in name for name in names):
        raise ValueError("model names must be nonempty strings without NUL characters")
    arrays = []
    shape = None
    for name in names:
        raw = np.asarray(probabilities[name])
        if raw.dtype.kind not in "fiu":
            raise ValueError(f"probabilities for {name!r} must have a numeric dtype")
        q = np.asarray(raw, dtype=np.float64)
        if q.ndim != 2 or q.shape[0] != len(y) or q.shape[1] < 2:
            raise ValueError(f"probabilities for {name!r} must have shape (n_test, alphabet_size >= 2)")
        if shape is None:
            shape = q.shape
        elif q.shape != shape:
            raise ValueError("all models must have identical probability array shapes")
        if not np.all(np.isfinite(q)) or np.any(q < 0) or np.any(q > 1 + 1e-8):
            raise ValueError(f"probabilities for {name!r} must be finite and in [0, 1]")
        if not np.allclose(q.sum(axis=1), 1, rtol=1e-6, atol=1e-8):
            raise ValueError(f"probability rows for {name!r} must sum to one")
        if np.any(y >= q.shape[1]):
            raise ValueError("y contains a label outside the probability alphabet")
        # Preserve original values: scoring handles numerical normalization.
        arrays.append(q)
    return y, indices, names, np.stack(arrays, axis=0)


def write_prediction_archive(audit: Mapping[str, Any], path: str | Path) -> dict[str, Any]:
    """Atomically write all final-test predictions and return JSON-safe metadata.

    The destination is used exactly as given (NumPy cannot append a suffix).
    Model insertion order is preserved; names are stored as Unicode, never
    object arrays. Labels and target indices are signed int64 and probabilities
    are float64 without precision reduction or re-normalization.
    """
    y, indices, names, probabilities = _validated_audit(audit)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=destination.parent, prefix=f".{destination.name}.", suffix=".tmp", delete=False
        ) as output:
            temporary = Path(output.name)
            np.savez_compressed(
                output,
                format_version=np.array(FORMAT_VERSION, dtype=np.int64),
                y=y,
                target_indices=indices,
                model_names=np.array(names, dtype=np.str_),
                probabilities=probabilities,
            )
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, destination)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return {
        "format": FORMAT_NAME,
        "format_version": FORMAT_VERSION,
        "filename": destination.name,
        "sha256": _sha256(destination),
        "models": names,
        "n_test": int(len(y)),
        "alphabet_size": int(probabilities.shape[2]),
        "bytes": int(destination.stat().st_size),
    }


def load_prediction_archive(path: str | Path) -> dict[str, Any]:
    """Load and validate a complete test archive without ever enabling pickle."""
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Prediction archive not found: {source}")
    try:
        loaded = np.load(source, allow_pickle=False)
        if not isinstance(loaded, np.lib.npyio.NpzFile):
            raise ValueError("expected an NPZ archive, not a standalone NPY array")
        with loaded as archive:
            if set(archive.files) != _ARCHIVE_FIELDS or len(archive.files) != len(_ARCHIVE_FIELDS):
                raise ValueError(f"archive fields must be exactly {sorted(_ARCHIVE_FIELDS)}")
            version = archive["format_version"]
            if version.shape != () or version.dtype.kind not in "iu" or int(version) != FORMAT_VERSION:
                raise ValueError(f"unsupported prediction archive format_version; expected {FORMAT_VERSION}")
            names_array = archive["model_names"]
            if names_array.ndim != 1 or names_array.dtype.kind != "U" or len(names_array) == 0:
                raise ValueError("model_names must be a nonempty one-dimensional Unicode array")
            names = names_array.tolist()
            if len(set(names)) != len(names):
                raise ValueError("duplicate model names in prediction archive")
            probabilities = archive["probabilities"]
            if probabilities.ndim != 3 or probabilities.shape[0] != len(names):
                raise ValueError("probabilities must have shape (n_models, n_test, alphabet_size)")
            audit = {
                "y": archive["y"],
                "target_indices": archive["target_indices"],
                "probabilities": {name: probabilities[i] for i, name in enumerate(names)},
            }
            y, indices, names, validated = _validated_audit(audit)
    except (ValueError, TypeError, KeyError, OSError, EOFError, zipfile.BadZipFile) as error:
        raise ValueError(f"Invalid prediction archive {source.name}: {error}") from error
    return {
        "y": y,
        "target_indices": indices,
        "probabilities": {name: validated[i] for i, name in enumerate(names)},
    }


def _required_int(value: Any, expected: int, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or int(value) != expected:
        raise ValueError(f"{label} mismatch: expected {expected}, found {value!r}")


def verify_prediction_metrics(
    result: Mapping[str, Any], archive_path: str | Path, atol: float = 1e-10
) -> dict[str, Any]:
    """Recompute each model's test accuracy, log-loss and Brier score.

    If ``result['prediction_archive']`` is present, its SHA-256 and structural
    metadata are checked before reporting success. Otherwise metrics can still
    be checked, but ``sha256_verified`` is False. Test size, model names, target
    endpoints and the optional displayed trace are also checked. Any discrepancy
    raises ValueError; no files are modified.
    """
    if not isinstance(result, Mapping):
        raise ValueError("result must be a mapping")
    if isinstance(atol, bool) or not isinstance(atol, (int, float)) or not math.isfinite(atol) or atol < 0:
        raise ValueError("atol must be a finite nonnegative number")
    source = Path(archive_path)
    if not source.is_file():
        raise FileNotFoundError(f"Prediction archive not found: {source}")
    digest = _sha256(source)
    metadata = result.get("prediction_archive")
    hash_verified = False
    if metadata is not None:
        if not isinstance(metadata, Mapping):
            raise ValueError("prediction_archive metadata must be a mapping")
        expected_digest = metadata.get("sha256")
        if not isinstance(expected_digest, str) or len(expected_digest) != 64:
            raise ValueError("prediction_archive metadata must contain a SHA-256 hex digest")
        if expected_digest.lower() != digest:
            raise ValueError("prediction archive SHA-256 mismatch; archive or result metadata has changed")
        hash_verified = True
    audit = load_prediction_archive(source)
    n = len(audit["y"])
    probabilities = audit["probabilities"]
    names = list(probabilities)
    alphabet = next(iter(probabilities.values())).shape[1]
    if metadata is not None:
        if metadata.get("format") != FORMAT_NAME:
            raise ValueError("prediction_archive format metadata mismatch")
        _required_int(metadata.get("format_version"), FORMAT_VERSION, "prediction_archive format_version")
        _required_int(metadata.get("n_test"), n, "prediction_archive n_test")
        _required_int(metadata.get("alphabet_size"), alphabet, "prediction_archive alphabet_size")
        _required_int(metadata.get("bytes"), source.stat().st_size, "prediction_archive bytes")
        if metadata.get("models") != names:
            raise ValueError("prediction_archive models metadata does not match archive order")
        # A caller may relocate the archive; filename is a locator, not an
        # identity. Its hash and contents still have to match exactly.
    split = result.get("split")
    if not isinstance(split, Mapping):
        raise ValueError("result must contain split.test_count")
    _required_int(split.get("test_count"), n, "split.test_count")
    if "test_target_range" in split:
        endpoints = [int(audit["target_indices"][0]), int(audit["target_indices"][-1])]
        if split["test_target_range"] != endpoints:
            raise ValueError("split.test_target_range does not match archive target indices")
    rows = result.get("metrics")
    if not isinstance(rows, list) or not rows or any(not isinstance(row, Mapping) for row in rows):
        raise ValueError("result metrics must be a nonempty list of model metric mappings")
    row_names = [row.get("model") for row in rows]
    if any(not isinstance(name, str) for name in row_names) or len(set(row_names)) != len(row_names):
        raise ValueError("result metrics require unique string model names")
    if set(row_names) != set(names):
        raise ValueError("model names in result metrics and prediction archive must match exactly")
    max_error = 0.0
    for row in rows:
        name = row["model"]
        if "n_test" in row:
            _required_int(row["n_test"], n, f"{name}.n_test")
        computed = score_predictions(audit["y"], probabilities[name], bootstrap=0)
        for metric in _METRICS:
            observed = row.get(metric)
            if isinstance(observed, bool) or not isinstance(observed, (int, float)) or not math.isfinite(observed):
                raise ValueError(f"{name}.{metric} must be a finite numeric metric")
            error = abs(float(observed) - computed[metric])
            if error > atol:
                raise ValueError(
                    f"Metric mismatch for {name}.{metric}: result={observed:.17g}, "
                    f"archive={computed[metric]:.17g}, absolute error={error:.3g} > atol={atol:g}"
                )
            max_error = max(max_error, error)
    trace = result.get("trace")
    if trace is not None:
        if not isinstance(trace, Mapping) or "y" not in trace or "indices" not in trace:
            raise ValueError("result trace must contain y and indices")
        trace_y = np.asarray(trace["y"])
        if trace_y.ndim != 1 or len(trace_y) > n:
            raise ValueError("trace labels have invalid shape or exceed archive test size")
        length = len(trace_y)
        if not np.array_equal(trace_y, audit["y"][:length]):
            raise ValueError("trace labels do not match prediction archive prefix")
        if not np.array_equal(np.asarray(trace["indices"]), audit["target_indices"][:length]):
            raise ValueError("trace target indices do not match prediction archive prefix")
        trace_probs = trace.get("probabilities", {})
        if not isinstance(trace_probs, Mapping):
            raise ValueError("trace probabilities must be a model mapping")
        for name, q in trace_probs.items():
            if name not in probabilities:
                raise ValueError(f"unknown model {name!r} in result trace")
            q = np.asarray(q)
            expected = probabilities[name][:length]
            if q.dtype.kind not in "fiu" or q.shape != expected.shape or not np.allclose(q, expected, rtol=0, atol=atol):
                raise ValueError(f"trace probabilities for {name!r} do not match archive prefix")
    return {
        "verified": True,
        "sha256": digest,
        "sha256_verified": hash_verified,
        "n_test": n,
        "models": names,
        "metrics_checked": list(_METRICS),
        "max_absolute_error": max_error,
    }
