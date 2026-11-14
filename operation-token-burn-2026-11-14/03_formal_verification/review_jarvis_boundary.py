#!/usr/bin/env python3
"""Comprueba consistencia entre decisión temporal y replay del kernel JARVIS."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
JARVIS = ROOT.parent / "06_jarvis_architecture" / "src"
sys.path.insert(0, str(JARVIS))
from jarvis_kernel import Authority, Kernel, Rejected, digest, example_plan, example_policy
from verify_snapshot import verify_snapshot


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        now = 1800000000
        authority = Authority(b"q" * 32)  # Clave pública sintética; nunca producción.
        kernel = Kernel(Path(directory) / "review.sqlite3", example_policy(), authority, lambda: now)
        plan = example_plan(now)
        token = authority.sign(plan, kernel.policy, approved_by="review-human", now=now, ttl=10)
        receipt = kernel.admit(plan, caller="researcher", approval=token)
        ticks = iter([now + 9, now + 10])
        kernel.clock = lambda: next(ticks)
        kernel.start(receipt["run_id"])
        snapshot = kernel.export()
        head = kernel.verify_audit()["head_sha256"]
        result = {
            "kernel_source_sha256": hashlib.sha256((JARVIS / "jarvis_kernel.py").read_bytes()).hexdigest(),
            "verifier_source_sha256": hashlib.sha256((JARVIS / "verify_snapshot.py").read_bytes()).hexdigest(),
            "runtime_start": "accepted", "permit_expires": now + 10,
            "recorded_start_time": snapshot["events"][-1]["timestamp"],
        }
        try:
            verify_snapshot(snapshot, expected_head=head, expected_policy=digest(kernel.policy))
            result["snapshot_verify"] = "accepted"
        except Rejected as error:
            result.update(snapshot_verify="rejected", reason=str(error))
        finally:
            kernel.close()
        target = ROOT / "results" / "jarvis_time_boundary_after_fix.json"
        target.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        if result["snapshot_verify"] != "accepted":
            raise SystemExit("FAIL: replay rechaza una transición admitida en tiempo válido")


if __name__ == "__main__":
    main()
