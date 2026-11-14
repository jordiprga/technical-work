from __future__ import annotations

import copy
import csv
import io
import itertools
import json
import os
import subprocess
import tempfile
import unittest
import shutil
from pathlib import Path
from unittest.mock import patch

from cryptosure.checks import REGISTRY, adaptive_proportion, execute, repetition_count
from cryptosure.change_control import compare_bundles
from cryptosure.cli import main
from cryptosure.common import CryptoSureError, canonical, confined, parse_json, sha256
from cryptosure.engine import aggregate, replay_bundle, run_profile, verify_bundle
from cryptosure.engine import read_verified_bundle
from cryptosure.evidence import import_artifact, load_index
from cryptosure.gitmeta import capture_git
from cryptosure.report import csv_safe, md, render_csv
from cryptosure.schema import validate_profile


def profile(check_type="json_field_equals", params=None, human=False):
    return {"schema_version": 1, "id": "synthetic-test", "version": "1.0", "title": "Synthetic test",
            "standard": {"family": "DEMO", "edition": "1", "source_url": "https://example.invalid"},
            "limitations": "No certification claim.", "requirements": [{"id": "R1", "title": "Synthetic",
            "clause": "DEMO", "human_review": human, "artifacts": ["data"], "checks": [{"id": "C1",
            "type": check_type, "artifact": "data", "parameters": params if params is not None else
            {"path": ["synthetic"], "expected": True}}]}]}


class JSONAndSchemaTests(unittest.TestCase):
    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(CryptoSureError):
            parse_json(b'{"x":1,"x":2}')

    def test_nonfinite_values_rejected(self):
        for data in (b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}', b'{"x":1e999}'):
            with self.subTest(data=data), self.assertRaises(CryptoSureError):
                parse_json(data)

    def test_canonical_rejects_nonfinite_and_surrogate(self):
        for value in (float("nan"), float("inf"), "\ud800"):
            with self.subTest(value=repr(value)), self.assertRaises(CryptoSureError):
                canonical(value)

    def test_canonical_key_order_stable(self):
        self.assertEqual(canonical({"b": 1, "a": 2}), canonical({"a": 2, "b": 1}))

    def test_profile_unknown_keys_rejected(self):
        obj = profile()
        obj["run_shell"] = "echo surprise"
        with self.assertRaises(CryptoSureError):
            validate_profile(obj)

    def test_duplicate_requirement_and_check_ids_rejected(self):
        for duplicate_requirement in (True, False):
            obj = profile()
            second = copy.deepcopy(obj["requirements"][0])
            second["id"] = "R1" if duplicate_requirement else "R2"
            obj["requirements"].append(second)
            with self.assertRaises(CryptoSureError):
                validate_profile(obj)

    def test_false_boolean_schema_version_not_integer(self):
        obj = profile()
        obj["schema_version"] = True
        with self.assertRaises(CryptoSureError):
            validate_profile(obj)

    def test_empty_requirement_cannot_pass(self):
        obj = profile()
        obj["requirements"][0]["checks"] = []
        with self.assertRaises(CryptoSureError):
            validate_profile(obj)

    def test_json_size_limit(self):
        with self.assertRaises(CryptoSureError):
            parse_json(b'"123456"', limit=4)


class CheckTests(unittest.TestCase):
    def test_rct_exact_boundary(self):
        self.assertEqual(repetition_count(bytes([0, 0, 1]), {"cutoff": 3})["status"], "PASS")
        outcome = repetition_count(bytes([0, 0, 0]), {"cutoff": 3})
        self.assertEqual(outcome["status"], "FAIL")
        self.assertEqual(outcome["metrics"]["first_failure_index_zero_based"], 2)

    def test_rct_exhaustive_against_run_length_model(self):
        for length in range(1, 10):
            for bits in itertools.product((0, 1), repeat=length):
                maximum = max(len(list(group)) for _, group in itertools.groupby(bits))
                for cutoff in (2, 3, 5):
                    result = repetition_count(bytes(bits), {"cutoff": cutoff})
                    self.assertEqual(result["status"], "FAIL" if maximum >= cutoff else "PASS")

    def test_apt_exhaustive_reference_count(self):
        for window in range(2, 9):
            for bits in itertools.product((0, 1), repeat=window):
                for cutoff in range(2, window + 1):
                    result = adaptive_proportion(bytes(bits), {"window": window, "cutoff": cutoff})
                    expected = sum(bit == bits[0] for bit in bits)
                    self.assertEqual(result["status"], "FAIL" if expected >= cutoff else "PASS")

    def test_apt_resets_reference_each_window(self):
        data = bytes([0, 1, 1, 1, 1, 0, 0, 0])
        result = adaptive_proportion(data, {"window": 4, "cutoff": 3})
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["metrics"]["max_reference_count"], 1)

    def test_partial_window_is_blocked(self):
        self.assertEqual(execute("adaptive_proportion", bytes([0, 1, 0]),
                                 {"window": 2, "cutoff": 2})["status"], "BLOCKED")

    def test_deterministic_zero_entropy_stream_passes_health_tests(self):
        data = bytes([0, 1]) * 512
        self.assertEqual(execute("repetition_count", data, {"cutoff": 8})["status"], "PASS")
        self.assertEqual(execute("adaptive_proportion", data, {"window": 16, "cutoff": 14})["status"], "PASS")

    def test_empty_and_invalid_binary_data_blocked(self):
        for data in (b"", b"0101", b"\x00\x02"):
            self.assertEqual(execute("repetition_count", data, {"cutoff": 3})["status"], "BLOCKED")

    def test_boolean_cutoff_does_not_become_integer(self):
        self.assertEqual(execute("repetition_count", b"\x00", {"cutoff": True})["status"], "BLOCKED")

    def test_json_comparison_is_type_sensitive(self):
        result = execute("json_field_equals", b'{"x":true}', {"path": ["x"], "expected": 1})
        self.assertEqual(result["status"], "FAIL")

    def test_sha256_wrong_expected_digest_fails(self):
        vectors = canonical([{"message_hex": "616263", "digest_hex": "0" * 64}])
        self.assertEqual(execute("sha256_vectors", vectors, {})["status"], "FAIL")

    def test_unknown_check_and_malformed_plugin_blocked(self):
        self.assertEqual(execute("shell", b"anything", {"command": "echo bad"})["status"], "BLOCKED")
        with patch.dict(REGISTRY, {"broken": lambda data, params: {"status": "BOGUS"}}):
            self.assertEqual(execute("broken", b"", {})["status"], "BLOCKED")
        with patch.dict(REGISTRY, {"broken": lambda data, params: {"status": []}}):
            self.assertEqual(execute("broken", b"", {})["status"], "BLOCKED")

    def test_fail_closed_aggregation(self):
        self.assertEqual(aggregate(["BOGUS"]), "BLOCKED")
        self.assertEqual(aggregate([]), "REVIEW")
        self.assertEqual(aggregate(["PASS"], True), "REVIEW")
        self.assertEqual(aggregate(["FAIL", "BLOCKED"]), "FAIL")


class FileFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="cryptosure-tests-")
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.store = self.root / "store"
        self.bundle = self.root / "bundle"
        self.profile_path = self.root / "profile.json"
        self.profile_path.write_bytes(canonical(profile()))
        (self.source / "data.json").write_bytes(b'{"synthetic":true}')
        import_artifact(self.store, "data", self.source, "data.json", "application/json")

    def tearDown(self):
        self.temporary.cleanup()

    def run_demo(self):
        return run_profile(self.profile_path, self.store, self.bundle)

    def reseal(self):
        seal = parse_json((self.bundle / "seal.json").read_bytes())
        for relative in seal["files"]:
            data = (self.bundle / relative).read_bytes()
            seal["files"][relative] = {"sha256": sha256(data), "size_bytes": len(data)}
        raw = canonical(seal)
        (self.bundle / "seal.json").write_bytes(raw)
        (self.bundle / "root.sha256").write_text(sha256(raw) + "\n")
        return sha256(raw)


class EvidenceAndBundleTests(FileFixture):
    def test_traversal_and_absolute_paths_rejected(self):
        for relative in ("../profile.json", "/etc/passwd", "a/../data.json", "./data.json", "a\\data.json"):
            with self.subTest(path=relative), self.assertRaises(CryptoSureError):
                confined(self.source, relative)

    def test_symlink_artifact_and_parent_rejected(self):
        (self.source / "link.json").symlink_to(self.source / "data.json")
        (self.source / "linkdir").symlink_to(self.source, target_is_directory=True)
        for relative in ("link.json", "linkdir/data.json"):
            with self.assertRaises(CryptoSureError):
                import_artifact(self.store, "linked", self.source, relative)

    def test_source_mutation_after_import_does_not_change_executed_bytes(self):
        (self.source / "data.json").write_bytes(b'{"synthetic":false}')
        result = self.run_demo()
        self.assertEqual(result["overall_status"], "PASS")
        self.assertTrue(replay_bundle(self.bundle, result["root_sha256"])["replay_matches"])

    def test_store_tampering_blocks_requirement(self):
        entry = load_index(self.store)["artifacts"]["data"]
        (self.store / "blobs" / entry["sha256"]).write_bytes(b'{"synthetic":false}')
        self.assertEqual(self.run_demo()["overall_status"], "BLOCKED")

    def test_reimport_changed_bytes_under_same_id_rejected(self):
        (self.source / "data.json").write_bytes(b'{"synthetic":false}')
        with self.assertRaises(CryptoSureError):
            import_artifact(self.store, "data", self.source, "data.json")

    def test_missing_evidence_cannot_pass(self):
        obj = profile()
        obj["requirements"][0]["artifacts"].append("missing")
        self.profile_path.write_bytes(canonical(obj))
        self.assertEqual(self.run_demo()["overall_status"], "BLOCKED")

    def test_snapshot_budget_cannot_silently_drop_required_evidence(self):
        with patch("cryptosure.engine.MAX_SNAPSHOT_BYTES", 1):
            self.assertEqual(self.run_demo()["overall_status"], "BLOCKED")

    def test_check_input_budget_cannot_silently_skip_check(self):
        with patch("cryptosure.engine.MAX_CHECK_INPUT_BYTES", 1):
            self.assertEqual(self.run_demo()["overall_status"], "BLOCKED")

    def test_human_review_cannot_automatically_pass(self):
        self.profile_path.write_bytes(canonical(profile(human=True)))
        self.assertEqual(self.run_demo()["overall_status"], "REVIEW")

    def test_shell_requirement_never_executes(self):
        marker = self.root / "executed"
        self.profile_path.write_bytes(canonical(profile("shell", {"command": f"touch {marker}"})))
        self.assertEqual(self.run_demo()["overall_status"], "BLOCKED")
        self.assertFalse(marker.exists())

    def test_bundle_roundtrip_and_pinned_digest(self):
        result = self.run_demo()
        verified = verify_bundle(self.bundle, result["root_sha256"])
        self.assertTrue(verified["integrity_verified"])
        self.assertFalse(verified["authenticity_verified"])
        self.assertFalse(verified["evidence_adequacy_verified"])

    def test_replay_and_verify_enforce_total_byte_limits(self):
        self.run_demo()
        with patch("cryptosure.engine.MAX_SNAPSHOT_BYTES", 1):
            with self.assertRaises(CryptoSureError):
                replay_bundle(self.bundle)
        with patch("cryptosure.engine.MAX_BUNDLE_BYTES", 1):
            with self.assertRaises(CryptoSureError):
                verify_bundle(self.bundle)

    def test_tampered_report_detected(self):
        self.run_demo()
        (self.bundle / "report.md").write_text("Counterfeit report")
        with self.assertRaises(CryptoSureError):
            verify_bundle(self.bundle)

    def test_recomputed_seal_needs_external_pin_to_detect_attacker(self):
        result = self.run_demo()
        (self.bundle / "report.md").write_text("Counterfeit report")
        self.reseal()
        self.assertTrue(verify_bundle(self.bundle)["integrity_verified"])
        with self.assertRaises(CryptoSureError):
            verify_bundle(self.bundle, result["root_sha256"])
        with self.assertRaises(CryptoSureError):
            replay_bundle(self.bundle)

    def test_replay_detects_forged_check_results_even_after_reseal(self):
        self.run_demo()
        run = parse_json((self.bundle / "run.json").read_bytes())
        run["requirements"][0]["checks"][0]["status"] = "FAIL"
        (self.bundle / "run.json").write_bytes(canonical(run))
        new_root = self.reseal()
        with self.assertRaises(CryptoSureError):
            replay_bundle(self.bundle, new_root)

    def test_replay_uses_verified_snapshot_after_directory_replacement(self):
        first = self.run_demo()
        obj = profile(params={"path": ["synthetic"], "expected": False})
        self.profile_path.write_bytes(canonical(obj))
        replacement = self.root / "replacement"
        run_profile(self.profile_path, self.store, replacement)
        original_reader = read_verified_bundle

        def snapshot_then_swap(bundle, expected_root=None):
            verified = original_reader(bundle, expected_root)
            shutil.rmtree(bundle)
            replacement.rename(bundle)
            return verified

        with patch("cryptosure.engine.read_verified_bundle", snapshot_then_swap):
            result = replay_bundle(self.bundle, first["root_sha256"])
        self.assertEqual(result["root_sha256"], first["root_sha256"])
        self.assertEqual(result["overall_status"], "PASS")
        self.assertTrue(result["replay_matches"])

    def test_extra_file_and_symlink_in_bundle_rejected(self):
        self.run_demo()
        extra = self.bundle / "extra.txt"
        extra.write_text("unsealed")
        with self.assertRaises(CryptoSureError):
            verify_bundle(self.bundle)
        extra.unlink()
        extra.symlink_to(self.profile_path)
        with self.assertRaises(CryptoSureError):
            verify_bundle(self.bundle)

    def test_output_cannot_overwrite_existing_bundle(self):
        self.run_demo()
        with self.assertRaises(CryptoSureError):
            self.run_demo()

    def test_profile_change_changes_digest_and_bound_result(self):
        first = self.run_demo()
        original = parse_json((self.bundle / "run.json").read_bytes())["profile_sha256"]
        obj = profile()
        obj["version"] = "2.0"
        self.profile_path.write_bytes(canonical(obj))
        run_profile(self.profile_path, self.store, self.root / "bundle2")
        changed = parse_json((self.root / "bundle2" / "run.json").read_bytes())["profile_sha256"]
        self.assertNotEqual(original, changed)
        self.assertTrue(verify_bundle(self.bundle, first["root_sha256"])["integrity_verified"])

    def test_cli_review_exit_code_is_not_success(self):
        self.profile_path.write_bytes(canonical(profile(human=True)))
        with patch("sys.stdout", new=io.StringIO()):
            code = main(["run", "--profile", str(self.profile_path), "--store", str(self.store), "--out", str(self.bundle)])
        self.assertEqual(code, 3)

    def test_change_control_identifies_affected_requirement(self):
        first = self.run_demo()
        obj = profile()
        obj["requirements"][0]["checks"][0]["parameters"]["expected"] = False
        self.profile_path.write_bytes(canonical(obj))
        other = self.root / "bundle2"
        second = run_profile(self.profile_path, self.store, other)
        diff = compare_bundles(self.bundle, other, first["root_sha256"], second["root_sha256"])
        self.assertTrue(diff["review_required"])
        self.assertEqual(diff["impacted_requirements"][0]["requirement_id"], "R1")
        self.assertIn("requirement_definition_changed", diff["impacted_requirements"][0]["reasons"])

    def test_change_control_identical_inputs_do_not_invalidate_for_timestamp(self):
        self.run_demo()
        other = self.root / "bundle2"
        run_profile(self.profile_path, self.store, other)
        diff = compare_bundles(self.bundle, other)
        self.assertFalse(diff["review_required"])

    def test_diff_rejects_resealed_blob_inconsistent_with_run_metadata(self):
        self.run_demo()
        other = self.root / "bundle2"
        shutil.copytree(self.bundle, other)
        run = parse_json((self.bundle / "run.json").read_bytes())
        blob = self.bundle / "artifacts" / run["artifacts"]["data"]["sha256"]
        blob.write_bytes(b'{"synthetic":false}')
        self.reseal()
        with self.assertRaises(CryptoSureError):
            compare_bundles(self.bundle, other)

    def test_diff_uses_verified_snapshot_after_directory_replacement(self):
        first = self.run_demo()
        self.profile_path.write_bytes(canonical(profile(params={"path": ["synthetic"], "expected": False})))
        other = self.root / "bundle2"
        second = run_profile(self.profile_path, self.store, other)
        original_reader = read_verified_bundle

        def snapshot_then_swap(bundle, expected_root=None):
            verified = original_reader(bundle, expected_root)
            if bundle == self.bundle:
                shutil.rmtree(bundle)
                shutil.copytree(other, bundle)
            return verified

        with patch("cryptosure.change_control.read_verified_bundle", snapshot_then_swap):
            result = compare_bundles(self.bundle, other, first["root_sha256"], second["root_sha256"])
        self.assertTrue(result["review_required"])
        self.assertIn("requirement_definition_changed", result["impacted_requirements"][0]["reasons"])


class RenderingTests(unittest.TestCase):
    def test_markdown_escapes_active_content(self):
        rendered = md("![x](https://example.invalid/pixel) <script> `bad`")
        self.assertNotIn("![x](", rendered)
        self.assertNotIn("<script>", rendered)
        self.assertIn("\\`bad\\`", rendered)

    def test_csv_formula_injection_escaped(self):
        for text in ("=HYPERLINK(\"https://example.invalid\")", "+cmd", "-2", "@SUM(A1)", "  =1"):
            self.assertTrue(csv_safe(text).startswith("'"))


class GitTests(unittest.TestCase):
    def test_git_not_requested_explicitly(self):
        self.assertFalse(capture_git(None)["requested"])

    def test_git_unborn_repo_does_not_execute_fsmonitor_or_clean_filter(self):
        with tempfile.TemporaryDirectory(prefix="cryptosure-git-") as temp:
            repo = Path(temp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
            (repo / "public-synthetic.txt").write_text("synthetic")
            marker = repo / "hook-ran"
            hook = repo / "monitor.sh"
            hook.write_text(f"#!/bin/sh\ntouch '{marker}'\n")
            hook.chmod(0o700)
            subprocess.run(["git", "-C", str(repo), "config", "core.fsmonitor", str(hook)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "filter.evil.clean", str(hook)], check=True)
            (repo / ".gitattributes").write_text("*.txt filter=evil\n")
            result = capture_git(repo)
            self.assertIsNone(result["dirty"])
            self.assertEqual(result["working_tree_status"], "not_assessed")
            self.assertIsNone(result["head_commit"])
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
