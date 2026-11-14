"""Conservative impact analysis between two sealed evidence baselines."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import canonical, confined, parse_json, read_bounded
from .engine import artifact_snapshots, parse_run, read_verified_bundle, validate_profile_binding
from .schema import validate_profile


def compare_bundles(old: Path, new: Path, old_root: str | None = None,
                    new_root: str | None = None) -> dict[str, Any]:
    old_verification, old_files = read_verified_bundle(old, old_root)
    new_verification, new_files = read_verified_bundle(new, new_root)
    old_profile = validate_profile(parse_json(old_files["profile.json"]))
    new_profile = validate_profile(parse_json(new_files["profile.json"]))
    old_run = parse_run(old_files["run.json"])
    new_run = parse_run(new_files["run.json"])
    validate_profile_binding(old_profile, old_run)
    validate_profile_binding(new_profile, new_run)
    artifact_snapshots(old_run, old_files)
    artifact_snapshots(new_run, new_files)
    old_reqs = {row["id"]: row for row in old_profile["requirements"]}
    new_reqs = {row["id"]: row for row in new_profile["requirements"]}
    artifact_ids = set(old_run["artifacts"]) | set(new_run["artifacts"])
    changed_artifacts = sorted(aid for aid in artifact_ids if
                               old_run["artifacts"].get(aid) != new_run["artifacts"].get(aid))
    content_changed = sorted(aid for aid in artifact_ids if
                             old_run["artifacts"].get(aid, {}).get("sha256") !=
                             new_run["artifacts"].get(aid, {}).get("sha256"))
    tool_changed = old_run["tool"] != new_run["tool"]
    git_changed = old_run["git"] != new_run["git"]
    metadata_changed = {key: {"old": old_profile[key], "new": new_profile[key]}
                        for key in ("id", "version", "title", "standard", "limitations")
                        if old_profile[key] != new_profile[key]}
    impacts = []
    for rid in sorted(set(old_reqs) | set(new_reqs)):
        reasons = []
        if rid not in old_reqs:
            reasons.append("requirement_added")
        elif rid not in new_reqs:
            reasons.append("requirement_removed")
        elif canonical(old_reqs[rid]) != canonical(new_reqs[rid]):
            reasons.append("requirement_definition_changed")
        req = new_reqs.get(rid, old_reqs.get(rid))
        referenced = set(req["artifacts"]) | {check["artifact"] for check in req["checks"]}
        for aid in sorted(referenced & set(changed_artifacts)):
            reasons.append(f"evidence_changed:{aid}")
        if tool_changed:
            reasons.append("tool_version_or_source_changed")
        if git_changed:
            reasons.append("git_baseline_changed")
        if metadata_changed:
            reasons.append("profile_metadata_changed")
        if reasons:
            impacts.append({"requirement_id": rid, "review_required": True, "reasons": reasons})
    return {"schema_version": 1, "old_root_sha256": old_verification["root_sha256"],
            "new_root_sha256": new_verification["root_sha256"],
            "both_externally_pinned": old_root is not None and new_root is not None,
            "profile_bindings_verified": True, "artifact_bindings_verified": True, "semantic_replay_verified": False,
            "changed_artifacts": changed_artifacts, "content_changed_artifacts": content_changed,
            "profile_metadata_changes": metadata_changed, "tool_changed": tool_changed,
            "git_changed": git_changed, "impacted_requirements": impacts,
            "review_required": bool(impacts),
            "limitation": "Análisis conservador de entradas; no verifica adecuación, no hereda aprobaciones y no prueba ausencia de impacto."}
