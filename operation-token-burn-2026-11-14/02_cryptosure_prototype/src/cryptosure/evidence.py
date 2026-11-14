"""Single-writer local content-addressed evidence store."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .common import (CryptoSureError, atomic_write, canonical, confined, exact_keys,
                     parse_json, read_bounded, sha256, text_field)
from .schema import identifier


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validate_index(index: Any) -> dict[str, Any]:
    exact_keys(index, {"schema_version", "artifacts"}, {"schema_version", "artifacts"}, "index")
    if type(index["schema_version"]) is not int or index["schema_version"] != 1:
        raise CryptoSureError("Unsupported evidence schema")
    if not isinstance(index["artifacts"], dict) or len(index["artifacts"]) > 10000:
        raise CryptoSureError("Invalid artifacts mapping")
    for aid, entry in index["artifacts"].items():
        identifier(aid, "artifact id")
        exact_keys(entry, {"sha256", "size_bytes", "media_type", "source_name", "imported_at"},
                   {"sha256", "size_bytes", "media_type", "source_name", "imported_at"}, aid)
        if not isinstance(entry["sha256"], str) or len(entry["sha256"]) != 64 or any(
                c not in "0123456789abcdef" for c in entry["sha256"]):
            raise CryptoSureError("Invalid SHA-256 digest")
        if type(entry["size_bytes"]) is not int or entry["size_bytes"] < 0:
            raise CryptoSureError("Invalid artifact size")
        for key in ("media_type", "source_name", "imported_at"):
            text_field(entry[key], f"{aid}.{key}")
    return index


def load_index(store: Path) -> dict[str, Any]:
    path = confined(store, "index.json")
    return validate_index(parse_json(read_bounded(path)))


def import_artifact(store: Path, artifact_id: str, source_root: Path, relative: str,
                    media_type: str = "application/octet-stream") -> dict[str, Any]:
    identifier(artifact_id, "artifact_id")
    text_field(media_type, "media_type", 256)
    data = read_bounded(confined(source_root, relative))
    digest = sha256(data)
    store.mkdir(parents=True, exist_ok=True)
    index_path = confined(store, "index.json", must_exist=False)
    index = load_index(store) if index_path.exists() else {"schema_version": 1, "artifacts": {}}
    existing = index["artifacts"].get(artifact_id)
    if existing and existing["sha256"] != digest:
        raise CryptoSureError(f"Artifact id {artifact_id} already binds different bytes; use a new id")
    blob = confined(store, f"blobs/{digest}", must_exist=False)
    if blob.exists():
        if sha256(read_bounded(blob)) != digest:
            raise CryptoSureError("Existing content-addressed blob was modified")
    else:
        atomic_write(blob, data)
    entry = existing or {"sha256": digest, "size_bytes": len(data), "media_type": media_type,
                         "source_name": Path(relative).name, "imported_at": utc_now()}
    index["artifacts"][artifact_id] = entry
    atomic_write(index_path, canonical(index))
    return {"artifact_id": artifact_id, **entry}


def snapshot_artifact(store: Path, entry: dict[str, Any]) -> bytes:
    data = read_bounded(confined(store, f"blobs/{entry['sha256']}"))
    if len(data) != entry["size_bytes"] or sha256(data) != entry["sha256"]:
        raise CryptoSureError("Evidence integrity mismatch")
    return data
