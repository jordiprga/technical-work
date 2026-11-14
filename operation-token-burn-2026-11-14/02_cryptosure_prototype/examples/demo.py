"""Generate a portable synthetic demonstration. Run with PYTHONPATH=src."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cryptosure.engine import replay_bundle, run_profile, verify_bundle
from cryptosure.evidence import import_artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("results/demo"))
    args = parser.parse_args()
    root = Path(__file__).parent
    args.out.mkdir(parents=True, exist_ok=True)
    generated = args.out / "generated"
    generated.mkdir(exist_ok=True)
    (generated / "binary-samples.bin").write_bytes(bytes([0, 1]) * 512)
    store = args.out / "store"
    for aid, filename, media_type in [
        ("sha256-vectors", "sha256-vectors.json", "application/json"),
        ("build-manifest", "build-manifest.json", "application/json"),
        ("source-model", "source-model.md", "text/markdown"),
    ]:
        import_artifact(store, aid, root / "data", filename, media_type)
    import_artifact(store, "binary-samples", generated, "binary-samples.bin")
    result = run_profile(root / "profile.json", store, args.out / "bundle")
    verification = verify_bundle(args.out / "bundle", result["root_sha256"])
    replay = replay_bundle(args.out / "bundle", result["root_sha256"])
    summary = {"run": result, "verification": verification, "replay": replay,
               "critical_observation": "A deterministic alternating sequence passes the selected RCT/APT checks; PASS is not entropy."}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
