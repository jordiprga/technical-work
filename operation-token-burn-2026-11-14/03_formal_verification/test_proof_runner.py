"""Regresiones de procedencia de bytes y recibos obsoletos; usa Lean real si disponible."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_checks

LEAN = os.environ.get("LEAN_BIN") or shutil.which("lean")
if not LEAN:
    candidate = Path("/tmp/cryptosure-lean/lean-4.19.0-linux/bin/lean")
    LEAN = str(candidate) if candidate.is_file() else None
SOURCE = Path(__file__).resolve().parent / "HealthGate.lean"


class ReceiptTests(unittest.TestCase):
    def run_in(self, root):
        with patch.object(run_checks, "ROOT", root), patch.object(run_checks, "MODULES", ("HealthGate",)), \
                patch.object(sys, "argv", ["run_checks.py", "--lean", LEAN, "--skip-mutations"]), \
                contextlib.redirect_stdout(io.StringIO()):
            return run_checks.main()

    @unittest.skipUnless(LEAN, "Lean 4.19.0 required for real compiler regression")
    def test_hash_and_compiler_use_same_captured_bytes(self):
        original = SOURCE.read_bytes()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            target = root / "HealthGate.lean"
            target.write_bytes(original)
            original_read = Path.read_bytes
            reads = []

            def racing_read(path):
                captured = original_read(path)
                if path == target:
                    reads.append(path)
                    target.write_text("def changed_after_capture := 7\n")
                return captured

            with patch.object(Path, "read_bytes", racing_read):
                self.assertEqual(self.run_in(root), 0)
            report = json.loads((root / "results/verification.json").read_text())
            self.assertEqual(report["status"], "verified")
            self.assertEqual(report["source_sha256"]["HealthGate.lean"], hashlib.sha256(original).hexdigest())
            self.assertNotEqual(report["source_sha256"]["HealthGate.lean"], hashlib.sha256(target.read_bytes()).hexdigest())
            self.assertEqual(len(reads), 1)
            archived = root / "results" / f"verification-{report['run_id']}.json"
            self.assertEqual(json.loads(archived.read_text()), report)

    @unittest.skipUnless(LEAN, "Lean 4.19.0 required")
    def test_sanity_failure_replaces_previous_verified_receipt(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "results").mkdir()
            (root / "results/verification.json").write_text('{"status":"verified"}')
            (root / "HealthGate.lean").write_text("theorem invalid : False := by sorry\n")
            with self.assertRaises(RuntimeError):
                self.run_in(root)
            report = json.loads((root / "results/verification.json").read_text())
            self.assertEqual(report["status"], "failed")
            self.assertIn("Unexpected proof construct", report["error"])

    def test_post_kernel_failure_cannot_leave_verified(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)

            def fail_after_kernel(args, results, report):
                report["kernel_check_status"] = "passed"
                raise RuntimeError("regression mutant survived")

            with patch.object(run_checks, "ROOT", root), \
                    patch.object(run_checks, "execute_checks", fail_after_kernel), \
                    patch.object(sys, "argv", ["run_checks.py"]):
                with self.assertRaises(RuntimeError):
                    run_checks.main()
            report = json.loads((root / "results/verification.json").read_text())
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["kernel_check_status"], "passed")


if __name__ == "__main__":
    unittest.main()
