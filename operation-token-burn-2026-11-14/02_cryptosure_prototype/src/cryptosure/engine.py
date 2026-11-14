"""Snapshot once, check those bytes, export a self-contained integrity bundle."""

from __future__ import annotations

import shutil
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from . import __version__
from .checks import execute
from .common import CryptoSureError, canonical, confined, exact_keys, parse_json, read_bounded, sha256, text_field
from .evidence import load_index, snapshot_artifact, utc_now, validate_index
from .gitmeta import capture_git
from .report import render_csv, render_markdown
from .schema import load_profile, validate_profile

DISCLAIMER = "Resultados técnicos de demostración; nunca una certificación ni estimación validada de entropía."
MAX_SNAPSHOT_BYTES = 64 * 1024 * 1024
MAX_CHECK_INPUT_BYTES = 128 * 1024 * 1024
MAX_BUNDLE_BYTES = 96 * 1024 * 1024


def source_digest() -> str:
    root = Path(__file__).parent
    data = b"".join(path.name.encode() + b"\0" + path.read_bytes() + b"\0"
                    for path in sorted(root.glob("*.py")))
    return sha256(data)


def aggregate(statuses: list[str], human_review: bool = False) -> str:
    if any(not isinstance(status, str) or status not in {"PASS", "FAIL", "REVIEW", "BLOCKED"} for status in statuses):
        return "BLOCKED"
    if "FAIL" in statuses:
        return "FAIL"
    if "BLOCKED" in statuses:
        return "BLOCKED"
    if human_review or "REVIEW" in statuses or not statuses:
        return "REVIEW"
    return "PASS"


def evaluate(profile: dict[str, Any], artifacts: dict[str, dict[str, Any]],
             snapshots: dict[str, bytes], errors: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    checked_bytes = 0
    for requirement in profile["requirements"]:
        artifact_ids = sorted(set(requirement["artifacts"]) | {check["artifact"] for check in requirement["checks"]})
        issues = [f"{aid}: {errors.get(aid, 'evidencia ausente')}" for aid in artifact_ids if aid not in snapshots]
        check_results = []
        for check in requirement["checks"]:
            aid = check["artifact"]
            if aid not in snapshots:
                outcome = {"status": "BLOCKED", "detail": errors.get(aid, "Evidencia ausente"),
                           "metrics": {}, "claim_kind": "experiment"}
            elif checked_bytes + len(snapshots[aid]) > MAX_CHECK_INPUT_BYTES:
                outcome = {"status": "BLOCKED", "detail": "Run check-input byte budget exceeded",
                           "metrics": {}, "claim_kind": "experiment"}
            else:
                checked_bytes += len(snapshots[aid])
                outcome = execute(check["type"], snapshots[aid], check["parameters"])
            check_results.append({**check, **outcome, "artifact_sha256": artifacts.get(aid, {}).get("sha256")})
        statuses = [check["status"] for check in check_results] + (["BLOCKED"] if issues else [])
        rows.append({"id": requirement["id"], "title": requirement["title"], "clause": requirement["clause"],
                     "human_review": requirement["human_review"], "artifact_ids": artifact_ids,
                     "status": aggregate(statuses, requirement["human_review"]),
                     "checks": check_results, "issues": issues})
    return rows


def run_profile(profile_path: Path, store: Path, output: Path, repo: Path | None = None) -> dict[str, Any]:
    if output.exists() or output.is_symlink():
        raise CryptoSureError("Output already exists; choose a new bundle path")
    profile = load_profile(profile_path)
    index = load_index(store)
    profile_bytes = canonical(profile)
    referenced = {aid for requirement in profile["requirements"] for aid in requirement["artifacts"]}
    referenced |= {check["artifact"] for requirement in profile["requirements"] for check in requirement["checks"]}
    snapshots, errors, artifacts = {}, {}, {}
    snapshot_bytes = 0
    for aid in sorted(referenced):
        if aid not in index["artifacts"]:
            errors[aid] = "Evidencia no importada"
            continue
        entry = index["artifacts"][aid]
        if snapshot_bytes + entry["size_bytes"] > MAX_SNAPSHOT_BYTES:
            errors[aid] = "Run evidence byte budget exceeded"
            continue
        try:
            snapshots[aid] = snapshot_artifact(store, entry)
            artifacts[aid] = entry
            snapshot_bytes += len(snapshots[aid])
        except (CryptoSureError, OSError) as exc:
            errors[aid] = str(exc)
    rows = evaluate(profile, artifacts, snapshots, errors)
    run = {"schema_version": 1, "created_at": utc_now(), "disclaimer": DISCLAIMER,
           "profile_id": profile["id"], "profile_version": profile["version"],
           "profile_sha256": sha256(profile_bytes), "standard": profile["standard"],
           "limitations": profile["limitations"], "tool": {"name": "cryptosure-prototype",
           "version": __version__, "source_sha256": source_digest()}, "git": capture_git(repo),
           "artifacts": artifacts, "artifact_errors": errors, "requirements": rows,
           "overall_status": aggregate([row["status"] for row in rows]),
           "status_counts": dict(Counter(row["status"] for row in rows))}
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".cryptosure-", dir=output.parent))
    try:
        files = {"profile.json": profile_bytes, "run.json": canonical(run),
                 "report.md": render_markdown(run), "traceability.csv": render_csv(run)}
        for aid, data in snapshots.items():
            files[f"artifacts/{artifacts[aid]['sha256']}"] = data
        for relative, data in files.items():
            path = temporary / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        seal = {"schema_version": 1, "algorithm": "sha256", "files": {
            relative: {"sha256": sha256(data), "size_bytes": len(data)} for relative, data in sorted(files.items())}}
        seal_bytes = canonical(seal)
        (temporary / "seal.json").write_bytes(seal_bytes)
        root_digest = sha256(seal_bytes)
        (temporary / "root.sha256").write_text(root_digest + "\n", encoding="ascii")
        temporary.rename(output)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return {"output": str(output), "root_sha256": root_digest, "overall_status": run["overall_status"],
            "status_counts": run["status_counts"], "disclaimer": DISCLAIMER}


def read_verified_bundle(bundle: Path, expected_root: str | None = None) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Return the exact sealed bytes checked against this root, without later reopening."""
    if expected_root is not None and (len(expected_root) != 64 or any(c not in "0123456789abcdef" for c in expected_root)):
        raise CryptoSureError("Expected root must be 64 lowercase hexadecimal characters")
    seal_bytes = read_bounded(confined(bundle, "seal.json"))
    root_digest = sha256(seal_bytes)
    sidecar = read_bounded(confined(bundle, "root.sha256"), 128).decode("ascii").strip()
    if sidecar != root_digest:
        raise CryptoSureError("Root sidecar does not match seal")
    if expected_root is not None and expected_root != root_digest:
        raise CryptoSureError("Externally pinned root digest does not match")
    seal = parse_json(seal_bytes)
    exact_keys(seal, {"schema_version", "algorithm", "files"}, {"schema_version", "algorithm", "files"}, "seal")
    if type(seal["schema_version"]) is not int or seal["schema_version"] != 1 or seal["algorithm"] != "sha256":
        raise CryptoSureError("Unsupported seal format")
    if not isinstance(seal.get("files"), dict) or not 4 <= len(seal["files"]) <= 10004:
        raise CryptoSureError("Invalid sealed file list")
    required = {"profile.json", "run.json", "report.md", "traceability.csv"}
    if not required <= seal["files"].keys():
        raise CryptoSureError("Bundle misses required files")
    actual_paths = set()
    for path in bundle.rglob("*"):
        if path.is_symlink():
            raise CryptoSureError("Bundle contains symlink")
        if path.is_file():
            actual_paths.add(path.relative_to(bundle).as_posix())
            if len(actual_paths) > 10006:
                raise CryptoSureError("Bundle exceeds file-count limit")
        elif not path.is_dir():
            raise CryptoSureError("Bundle contains non-regular filesystem object")
    if actual_paths != set(seal["files"]) | {"seal.json", "root.sha256"}:
        raise CryptoSureError("Unsealed or missing files in bundle")
    sealed_total = 0
    verified_files = {}
    for relative, entry in seal["files"].items():
        if not isinstance(entry, dict) or set(entry) != {"sha256", "size_bytes"}:
            raise CryptoSureError("Invalid seal entry")
        if type(entry["size_bytes"]) is not int or entry["size_bytes"] < 0:
            raise CryptoSureError("Invalid sealed size")
        sealed_total += entry["size_bytes"]
        if sealed_total > MAX_BUNDLE_BYTES:
            raise CryptoSureError("Bundle exceeds total byte limit")
        if not isinstance(entry["sha256"], str) or len(entry["sha256"]) != 64 or any(c not in "0123456789abcdef" for c in entry["sha256"]):
            raise CryptoSureError("Invalid sealed digest")
        data = read_bounded(confined(bundle, relative))
        if len(data) != entry["size_bytes"] or sha256(data) != entry["sha256"]:
            raise CryptoSureError(f"Sealed bytes mismatch: {relative}")
        verified_files[relative] = data
    return ({"integrity_verified": True, "root_sha256": root_digest,
            "externally_pinned": expected_root is not None, "files_verified": len(seal["files"]),
            "authenticity_verified": False, "evidence_adequacy_verified": False}, verified_files)


def verify_bundle(bundle: Path, expected_root: str | None = None) -> dict[str, Any]:
    return read_verified_bundle(bundle, expected_root)[0]


def parse_run(data: bytes) -> dict[str, Any]:
    run = parse_json(data)
    keys = {"schema_version", "created_at", "disclaimer", "profile_id", "profile_version", "profile_sha256",
            "standard", "limitations", "tool", "git", "artifacts", "artifact_errors", "requirements",
            "overall_status", "status_counts"}
    exact_keys(run, keys, keys, "run")
    if type(run["schema_version"]) is not int or run["schema_version"] != 1:
        raise CryptoSureError("Unsupported run schema")
    validate_index({"schema_version": 1, "artifacts": run["artifacts"]})
    if not isinstance(run["artifact_errors"], dict) or any(not isinstance(v, str) for v in run["artifact_errors"].values()):
        raise CryptoSureError("Invalid artifact error mapping")
    if not isinstance(run["requirements"], list) or len(run["requirements"]) > 1000:
        raise CryptoSureError("Invalid recorded requirements")
    if not isinstance(run["overall_status"], str) or run["overall_status"] not in {"PASS", "FAIL", "REVIEW", "BLOCKED"}:
        raise CryptoSureError("Invalid overall status")
    if not isinstance(run["tool"], dict) or set(run["tool"]) != {"name", "version", "source_sha256"}:
        raise CryptoSureError("Invalid tool provenance")
    for key in ("name", "version"):
        text_field(run["tool"][key], f"run.tool.{key}", 256)
    for value in (run["profile_sha256"], run["tool"]["source_sha256"]):
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise CryptoSureError("Invalid run digest")
    for key in ("created_at", "profile_id", "profile_version", "limitations", "disclaimer"):
        text_field(run[key], f"run.{key}")
    if not isinstance(run["git"], dict) or not isinstance(run["status_counts"], dict):
        raise CryptoSureError("Invalid run metadata")
    return run


def load_run(bundle: Path) -> dict[str, Any]:
    return parse_run(read_bounded(confined(bundle, "run.json")))


def validate_profile_binding(profile: dict[str, Any], run: dict[str, Any]) -> None:
    if sha256(canonical(profile)) != run["profile_sha256"]:
        raise CryptoSureError("Profile digest inconsistent with recorded run")
    for key, expected in (("profile_id", profile["id"]), ("profile_version", profile["version"]),
                          ("standard", profile["standard"]), ("limitations", profile["limitations"]),
                          ("disclaimer", DISCLAIMER)):
        if run[key] != expected:
            raise CryptoSureError(f"Recorded profile metadata is inconsistent: {key}")


def artifact_snapshots(run: dict[str, Any], files: dict[str, bytes]) -> dict[str, bytes]:
    """Bind run metadata to bytes already authenticated against the selected seal."""
    snapshots = {}
    total_snapshot_bytes = 0
    for aid, entry in run["artifacts"].items():
        total_snapshot_bytes += entry["size_bytes"]
        if total_snapshot_bytes > MAX_SNAPSHOT_BYTES:
            raise CryptoSureError("Replay exceeds evidence byte budget")
        relative = f"artifacts/{entry['sha256']}"
        if relative not in files:
            raise CryptoSureError("Recorded artifact is missing from verified snapshot")
        data = files[relative]
        if sha256(data) != entry["sha256"] or len(data) != entry["size_bytes"]:
            raise CryptoSureError("Artifact inconsistent with recorded run")
        snapshots[aid] = data
    return snapshots


def replay_bundle(bundle: Path, expected_root: str | None = None) -> dict[str, Any]:
    verification, files = read_verified_bundle(bundle, expected_root)
    profile = validate_profile(parse_json(files["profile.json"]))
    run = parse_run(files["run.json"])
    validate_profile_binding(profile, run)
    snapshots = artifact_snapshots(run, files)
    rows = evaluate(profile, run["artifacts"], snapshots, run["artifact_errors"])
    same_results = canonical(rows) == canonical(run["requirements"])
    if not same_results:
        raise CryptoSureError("Replay differs from recorded check results")
    if aggregate([row["status"] for row in rows]) != run["overall_status"]:
        raise CryptoSureError("Recorded overall status is inconsistent")
    if dict(Counter(row["status"] for row in rows)) != run["status_counts"]:
        raise CryptoSureError("Recorded status counts are inconsistent")
    if render_markdown(run) != files["report.md"]:
        raise CryptoSureError("Rendered report differs from recorded run")
    if render_csv(run) != files["traceability.csv"]:
        raise CryptoSureError("Rendered traceability differs from recorded run")
    return {**verification, "replay_matches": True,
            "same_tool_source": source_digest() == run["tool"]["source_sha256"],
            "overall_status": run["overall_status"]}
