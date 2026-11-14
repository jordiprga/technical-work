"""Command-line interface; all execution remains local and offline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .checks import REGISTRY
from .change_control import compare_bundles
from .common import CryptoSureError
from .engine import replay_bundle, run_profile, verify_bundle
from .evidence import import_artifact
from .schema import load_profile


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="cryptosure", description="Offline evidence demonstrator; never a certification decision")
    sub = root.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="Validate a versioned requirement profile")
    validate.add_argument("profile", type=Path)
    ingest = sub.add_parser("import", help="Snapshot a regular artifact into a local evidence store")
    ingest.add_argument("--store", required=True, type=Path)
    ingest.add_argument("--id", required=True)
    ingest.add_argument("--source-root", required=True, type=Path)
    ingest.add_argument("--path", required=True, help="Relative path under source-root; no symlinks")
    ingest.add_argument("--media-type", default="application/octet-stream")
    run = sub.add_parser("run", help="Evaluate a profile against snapshotted evidence")
    run.add_argument("--profile", required=True, type=Path)
    run.add_argument("--store", required=True, type=Path)
    run.add_argument("--out", required=True, type=Path)
    run.add_argument("--repo", type=Path, help="Optional explicitly chosen Git working tree; read-only metadata")
    for name, help_text in (("verify", "Verify sealed files; a pinned digest is an external trust anchor"),
                            ("replay", "Re-execute implemented checks from sealed bundle bytes")):
        verify = sub.add_parser(name, help=help_text)
        verify.add_argument("bundle", type=Path)
        verify.add_argument("--expected-root", help="SHA-256 of seal.json obtained through a trusted channel")
    sub.add_parser("plugins", help="List allowlisted plugins; no dynamic imports from profiles")
    diff = sub.add_parser("diff", help="Conservative change-impact analysis between evidence bundles")
    diff.add_argument("old", type=Path)
    diff.add_argument("new", type=Path)
    diff.add_argument("--old-root")
    diff.add_argument("--new-root")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "validate":
            profile = load_profile(args.profile)
            unknown = sorted({check["type"] for requirement in profile["requirements"]
                              for check in requirement["checks"] if check["type"] not in REGISTRY})
            output = {"valid_schema": True, "profile_id": profile["id"], "profile_version": profile["version"],
                      "requirements": len(profile["requirements"]), "unsupported_plugins": unknown}
        elif args.command == "import":
            output = import_artifact(args.store, args.id, args.source_root, args.path, args.media_type)
        elif args.command == "run":
            output = run_profile(args.profile, args.store, args.out, args.repo)
        elif args.command == "verify":
            output = verify_bundle(args.bundle, args.expected_root)
        elif args.command == "replay":
            output = replay_bundle(args.bundle, args.expected_root)
        elif args.command == "diff":
            output = compare_bundles(args.old, args.new, args.old_root, args.new_root)
        else:
            output = {"plugins": sorted(REGISTRY), "profile_can_execute_commands": False}
        print(json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False))
        if args.command == "run":
            return {"PASS": 0, "REVIEW": 3, "FAIL": 4, "BLOCKED": 5}[output["overall_status"]]
        return 0
    except (CryptoSureError, OSError, UnicodeError) as exc:
        print(json.dumps({"error": str(exc), "error_type": type(exc).__name__}, ensure_ascii=False), file=sys.stderr)
        return 2
