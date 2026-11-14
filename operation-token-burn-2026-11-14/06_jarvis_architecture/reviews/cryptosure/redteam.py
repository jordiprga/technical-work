"""Independent local adversarial checks. Writes only under its temporary directory.

Run: python3 reviews/cryptosure/redteam.py
All payloads are synthetic; no network or external commands are executed.
"""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[3] / "02_cryptosure_prototype"
sys.path.insert(0, str(PROJECT / "src"))
from cryptosure.common import CryptoSureError, canonical, parse_json, sha256
from cryptosure.engine import replay_bundle, verify_bundle, run_profile
from cryptosure.evidence import import_artifact
from cryptosure.report import csv_safe, md
from cryptosure import engine


def reseal(bundle):
    files = {}
    for path in sorted(bundle.rglob("*")):
        if path.is_file() and path.name not in {"seal.json", "root.sha256"}:
            data = path.read_bytes()
            files[path.relative_to(bundle).as_posix()] = {"sha256": sha256(data), "size_bytes": len(data)}
    seal = canonical({"schema_version": 1, "algorithm": "sha256", "files": files})
    (bundle / "seal.json").write_bytes(seal)
    root = sha256(seal)
    (bundle / "root.sha256").write_text(root + "\n")
    return root


def rejected(call):
    try:
        call()
    except CryptoSureError as exc:
        return {"rejected": True, "reason": str(exc)}
    return {"rejected": False}


def main():
    report = {"reviewer": "jarvis_architecture", "scope": "independent local synthetic checks",
              "source_files_sha256": {p.name: sha256(p.read_bytes()) for p in sorted((PROJECT / "src/cryptosure").glob("*.py"))},
              "checks": {}}
    check = report["checks"]
    with tempfile.TemporaryDirectory(prefix="cryptosure-redteam-") as tmp:
        root = Path(tmp)
        source = root / "baseline"
        data = root / "data"
        data.mkdir()
        (data / "binary.bin").write_bytes(bytes([0, 1]) * 512)
        store = root / "store"
        for aid, name in (("sha256-vectors", "sha256-vectors.json"),
                          ("build-manifest", "build-manifest.json"),
                          ("source-model", "source-model.md")):
            import_artifact(store, aid, PROJECT / "examples/data", name)
        import_artifact(store, "binary-samples", data, "binary.bin")
        baseline = run_profile(PROJECT / "examples/profile.json", store, source)
        pinned = baseline["root_sha256"]
        check["baseline_replay"] = replay_bundle(source, pinned)
        bundle = root / "tampered"
        shutil.copytree(source, bundle)
        path = bundle / "report.md"
        path.write_bytes(path.read_bytes() + b"\nFORGED CLAIM\n")
        check["byte_tamper_without_reseal"] = rejected(lambda: verify_bundle(bundle, pinned))
        reseal(bundle)
        check["rehash_without_external_pin"] = verify_bundle(bundle)
        check["rehash_with_external_pin"] = rejected(lambda: verify_bundle(bundle, pinned))
        check["rehash_semantic_replay"] = rejected(lambda: replay_bundle(bundle))

        extra = root / "extra"
        shutil.copytree(source, extra)
        (extra / "unsealed.txt").write_text("not sealed")
        check["unsealed_file"] = rejected(lambda: verify_bundle(extra))

        linked = root / "linked"
        shutil.copytree(source, linked)
        (linked / "link").symlink_to(root / "never-read")
        check["symlink"] = rejected(lambda: verify_bundle(linked))

        # Small stand-in for an otherwise large-memory attack: lower the producer
        # budget to one byte and check whether replay enforces the same contract.
        with patch("cryptosure.engine.MAX_SNAPSHOT_BYTES", 1):
            check["replay_aggregate_budget_one_byte"] = rejected(lambda: replay_bundle(source, pinned))

        # Deterministic TOCTOU adversary: replace a fully verified bundle after
        # integrity verification returns and before semantic replay reopens it.
        alternate = root / "alternate"
        other_store = root / "other-store"
        (data / "zeros.bin").write_bytes(bytes([0]) * 1024)
        for aid, name in (("sha256-vectors", "sha256-vectors.json"),
                          ("build-manifest", "build-manifest.json"),
                          ("source-model", "source-model.md")):
            import_artifact(other_store, aid, PROJECT / "examples/data", name)
        import_artifact(other_store, "binary-samples", data, "zeros.bin")
        other_result = run_profile(PROJECT / "examples/profile.json", other_store, alternate)
        victim = root / "victim"
        shutil.copytree(source, victim)
        hook_name = "read_verified_bundle" if hasattr(engine, "read_verified_bundle") else "verify_bundle"
        original_verify = getattr(engine, hook_name)
        replaced = False
        def replace_after_verification(bundle, expected_root=None):
            nonlocal replaced
            checked = original_verify(bundle, expected_root)
            if not replaced:
                shutil.rmtree(victim)
                shutil.copytree(alternate, victim)
                replaced = True
            return checked
        with patch("cryptosure.engine." + hook_name, side_effect=replace_after_verification):
            try:
                replay = replay_bundle(victim, pinned)
                check["replace_after_verify"] = {
                    "rejected": False, "old_root_returned": replay["root_sha256"] == pinned,
                    "baseline_status": baseline["overall_status"],
                    "alternate_status": other_result["overall_status"],
                    "replayed_status": replay["overall_status"],
                    "different_root": other_result["root_sha256"] != pinned,
                    "attack_injected": replaced,
                    "safe_snapshot_used": replaced and replay["overall_status"] == baseline["overall_status"]}
            except CryptoSureError as exc:
                check["replace_after_verify"] = {"rejected": True, "reason": str(exc)}

    markdown = md('<script>alert(1)</script> [x](javascript:alert(1)) | `code`')
    check["markdown_escaping"] = {"raw_html_absent": "<script>" not in markdown,
                                  "raw_link_absent": "](" not in markdown, "rendered": markdown}
    for value in ("=1+1", "\t=1+1", "\r@SUM(1)", "+1", "-1"):
        check["csv_" + repr(value)] = {"neutralized": csv_safe(value).startswith("'")}
    check["json_duplicate_key"] = rejected(lambda: parse_json(b'{"status":"FAIL","status":"PASS"}'))
    check["json_nonfinite"] = rejected(lambda: parse_json(b'{"x":1e999}'))
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
