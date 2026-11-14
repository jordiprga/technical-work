"""Import an existing formal verification receipt; never execute Lean implicitly."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cryptosure.common import canonical, confined, parse_json, read_bounded
from cryptosure.engine import replay_bundle, run_profile
from cryptosure.evidence import import_artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--formal-root", required=True, type=Path)
    parser.add_argument("--receipt", default="results/verification.json")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("Choose a new output directory")
    args.out.mkdir(parents=True)
    receipt = parse_json(read_bounded(confined(args.formal_root, args.receipt)))
    sources = receipt.get("source_sha256")
    if not isinstance(sources, dict) or not 1 <= len(sources) <= 100:
        raise SystemExit("Receipt must expose 1..100 source_sha256 entries")
    store = args.out / "store"
    import_artifact(store, "formal-receipt", args.formal_root, args.receipt, "application/json")
    artifact_ids = ["formal-receipt"]
    checks = [{"id": "receipt-status-declared", "type": "json_field_equals", "artifact": "formal-receipt",
               "parameters": {"path": ["status"], "expected": "verified"}}]
    for index, filename in enumerate(sorted(sources)):
        artifact_id = f"formal-source-{index}"
        entry = import_artifact(store, artifact_id, args.formal_root, filename, "text/plain")
        artifact_ids.append(artifact_id)
        checks.append({"id": f"source-digest-{index}", "type": "json_field_equals", "artifact": "formal-receipt",
                       "parameters": {"path": ["source_sha256", filename], "expected": entry["sha256"]}})
    profile = {"schema_version": 1, "id": "cryptosure.formal-bridge-demo", "version": "1.0",
               "title": "Importación de recibo formal y fuentes asociadas", "standard": {
                   "family": "DEMO-NOT-A-STANDARD", "edition": "Formal evidence bridge 1.0",
                   "source_url": "https://lean-lang.org/"},
               "limitations": "Se verifica consistencia de hashes y campos declarados. CryptoSure no ejecuta Lean, no autentica al productor del recibo y no demuestra correspondencia con hardware o requisitos normativos.",
               "requirements": [{"id": "DEMO.FORMAL.001", "title": "Revisar teoremas, axiomas, toolchain y vínculo con implementación",
                                  "clause": "Demostración de integración; ninguna cláusula normativa",
                                  "human_review": True, "artifacts": artifact_ids, "checks": checks}]}
    profile_path = args.out / "profile.json"
    profile_path.write_bytes(canonical(profile))
    result = run_profile(profile_path, store, args.out / "bundle")
    summary = {"run": result, "replay": replay_bundle(args.out / "bundle", result["root_sha256"]),
               "lean_executed_by_cryptosure": False, "source_files_bound": len(sources)}
    (args.out / "summary.json").write_bytes(canonical(summary))
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
