"""Small fail-closed helpers for bounded, canonical, unambiguous artifacts."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_ARTIFACT_BYTES = 16 * 1024 * 1024


class CryptoSureError(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> bytes:
    try:
        return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                           allow_nan=False) + "\n").encode("utf-8")
    except (ValueError, TypeError, RecursionError, UnicodeError) as exc:
        raise CryptoSureError(f"Cannot canonicalize JSON: {type(exc).__name__}") from exc


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CryptoSureError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(data: bytes, *, limit: int = MAX_JSON_BYTES) -> Any:
    if len(data) > limit:
        raise CryptoSureError(f"JSON exceeds {limit} bytes")
    try:
        def finite_float(value: str) -> float:
            number = float(value)
            if not math.isfinite(number):
                raise CryptoSureError("Nonfinite JSON number")
            return number
        return json.loads(data, object_pairs_hook=_unique_pairs, parse_float=finite_float,
                          parse_constant=lambda value: (_ for _ in ()).throw(
                              CryptoSureError(f"Nonfinite JSON constant: {value}")))
    except CryptoSureError:
        raise
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise CryptoSureError(f"Invalid JSON: {exc}") from exc


def read_bounded(path: Path, limit: int = MAX_ARTIFACT_BYTES) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise CryptoSureError(f"Not a regular, non-symlink file: {path}")
    if path.stat().st_size > limit:
        raise CryptoSureError(f"Artifact exceeds {limit} bytes")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise CryptoSureError(f"Artifact exceeds {limit} bytes")
    return data


def confined(root: Path, relative: str, *, must_exist: bool = True) -> Path:
    """Reject absolute paths, traversal, backslashes and every existing symlink."""
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise CryptoSureError("Invalid relative path")
    parts = relative.split("/")
    if any(part in {"", ".", ".."} for part in parts) or Path(relative).is_absolute():
        raise CryptoSureError(f"Unsafe relative path: {relative}")
    root = root.absolute()
    for parent in (root, *root.parents):
        if parent.is_symlink():
            raise CryptoSureError("Symlink in root path")
    candidate = root
    for part in parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise CryptoSureError("Symlink in artifact path")
    try:
        candidate.resolve(strict=must_exist).relative_to(root.resolve(strict=True))
    except (ValueError, FileNotFoundError, OSError) as exc:
        raise CryptoSureError(f"Path outside root or missing: {relative}") from exc
    return candidate


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".tmp-{os.getpid()}")
    try:
        with temp.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def exact_keys(value: dict[str, Any], allowed: set[str], required: set[str], where: str) -> None:
    if not isinstance(value, dict):
        raise CryptoSureError(f"{where} must be an object")
    unknown, missing = set(value) - allowed, required - set(value)
    if unknown or missing:
        raise CryptoSureError(f"{where}: unknown={sorted(unknown)} missing={sorted(missing)}")


def text_field(value: Any, where: str, maximum: int = 4096) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise CryptoSureError(f"{where} must be a nonempty string <= {maximum} characters")
    return value
