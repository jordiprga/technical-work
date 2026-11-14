"""Allowlisted pure checks; profile data never becomes code or a subprocess."""

from __future__ import annotations

import hashlib
from typing import Any, Callable

from .common import CryptoSureError, exact_keys, parse_json

Check = Callable[[bytes, dict[str, Any]], dict[str, Any]]
REGISTRY: dict[str, Check] = {}


def register(name: str) -> Callable[[Check], Check]:
    def decorator(function: Check) -> Check:
        if name in REGISTRY:
            raise RuntimeError(f"Duplicate check: {name}")
        REGISTRY[name] = function
        return function
    return decorator


def integer(params: dict[str, Any], key: str, low: int, high: int) -> int:
    value = params.get(key)
    if type(value) is not int or not low <= value <= high:
        raise CryptoSureError(f"{key} must be an integer in [{low}, {high}]")
    return value


def result(ok: bool, detail: str, metrics: dict[str, Any]) -> dict[str, Any]:
    return {"status": "PASS" if ok else "FAIL", "detail": detail, "metrics": metrics,
            "claim_kind": "experiment"}


def binary_data(data: bytes) -> None:
    if not data or any(value not in (0, 1) for value in data):
        raise CryptoSureError("Expected nonempty raw bytes, each exactly 0x00 or 0x01")


@register("sha256_vectors")
def sha256_vectors(data: bytes, params: dict[str, Any]) -> dict[str, Any]:
    exact_keys(params, set(), set(), "sha256_vectors.parameters")
    vectors = parse_json(data)
    if not isinstance(vectors, list) or not 1 <= len(vectors) <= 10000:
        raise CryptoSureError("Expected 1..10000 SHA-256 vectors")
    failures = []
    for position, vector in enumerate(vectors):
        exact_keys(vector, {"message_hex", "digest_hex"}, {"message_hex", "digest_hex"}, "vector")
        if not isinstance(vector["message_hex"], str) or not isinstance(vector["digest_hex"], str):
            raise CryptoSureError("Vector fields must be strings")
        try:
            message = bytes.fromhex(vector["message_hex"])
        except ValueError as exc:
            raise CryptoSureError("Invalid message hex") from exc
        expected = vector["digest_hex"]
        if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
            raise CryptoSureError("Expected digest must be 64 lowercase hex characters")
        if hashlib.sha256(message).hexdigest() != expected:
            failures.append(position)
    return result(not failures, "Comparación con vectores proporcionados; no validación CAVP/ACVP.",
                  {"vectors": len(vectors), "failed_indices": failures[:32], "failures": len(failures)})


@register("repetition_count")
def repetition_count(data: bytes, params: dict[str, Any]) -> dict[str, Any]:
    exact_keys(params, {"cutoff"}, {"cutoff"}, "repetition_count.parameters")
    cutoff = integer(params, "cutoff", 2, 1_000_000)
    binary_data(data)
    current = maximum = 1
    first_failure = None
    previous = data[0]
    for index, value in enumerate(data[1:], 1):
        current = current + 1 if value == previous else 1
        previous = value
        maximum = max(maximum, current)
        if current >= cutoff and first_failure is None:
            first_failure = index
    return result(first_failure is None,
                  "Alarma cuando longitud de racha >= cutoff; no estima entropía ni valida el cutoff.",
                  {"samples": len(data), "cutoff": cutoff, "max_run": maximum,
                   "first_failure_index_zero_based": first_failure})


@register("adaptive_proportion")
def adaptive_proportion(data: bytes, params: dict[str, Any]) -> dict[str, Any]:
    exact_keys(params, {"window", "cutoff"}, {"window", "cutoff"}, "adaptive_proportion.parameters")
    window = integer(params, "window", 2, 65536)
    cutoff = integer(params, "cutoff", 2, window)
    binary_data(data)
    if len(data) < window or len(data) % window:
        raise CryptoSureError("APT requires complete non-overlapping windows; partial tail not silently ignored")
    failed, maximum = [], 0
    for start in range(0, len(data), window):
        count = data[start:start + window].count(data[start])
        maximum = max(maximum, count)
        if count >= cutoff:
            failed.append(start // window)
    return result(not failed,
                  "Cada ventana toma su primer símbolo como referencia y lo cuenta; umbrales no calibrados.",
                  {"samples": len(data), "window": window, "cutoff": cutoff,
                   "windows": len(data) // window, "max_reference_count": maximum,
                   "failed_windows": failed[:32], "failures": len(failed)})


@register("json_field_equals")
def json_field_equals(data: bytes, params: dict[str, Any]) -> dict[str, Any]:
    exact_keys(params, {"path", "expected"}, {"path", "expected"}, "json_field_equals.parameters")
    path = params["path"]
    if not isinstance(path, list) or not 1 <= len(path) <= 32 or any(not isinstance(v, str) for v in path):
        raise CryptoSureError("path must contain 1..32 object-key strings")
    value = parse_json(data)
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return result(False, "Campo requerido ausente.", {"path": path, "exists": False})
        value = value[key]
    # JSON equality is type-sensitive: Python's True == 1 must not become a PASS.
    from .common import canonical
    ok = canonical(value) == canonical(params["expected"])
    return result(ok, "Comparación literal de un campo JSON; no evalúa expresiones.",
                  {"path": path, "exists": True, "equal": ok})


def execute(check_type: str, data: bytes, params: dict[str, Any]) -> dict[str, Any]:
    if check_type not in REGISTRY:
        return {"status": "BLOCKED", "detail": f"Plugin no disponible: {check_type}",
                "metrics": {}, "claim_kind": "experiment"}
    try:
        outcome = REGISTRY[check_type](data, params)
        if (not isinstance(outcome, dict) or not isinstance(outcome.get("status"), str)
                or outcome.get("status") not in {"PASS", "FAIL", "REVIEW", "BLOCKED"}
                or not isinstance(outcome.get("detail"), str) or not isinstance(outcome.get("metrics"), dict)):
            raise CryptoSureError("Plugin violated result contract")
        return outcome
    except CryptoSureError as exc:
        return {"status": "BLOCKED", "detail": str(exc), "metrics": {}, "claim_kind": "experiment"}
