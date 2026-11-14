import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from jarvis_kernel import Authority, Kernel, Rejected, digest, example_plan, example_policy
from verify_snapshot import verify_snapshot


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.now = 1800000000
        authority = Authority(b"s" * 32)
        self.kernel = Kernel(Path(self.tmp.name) / "db", example_policy(), authority, lambda: self.now)
        self.kernel.capture("item", "synthetic")
        p = example_plan(self.now)
        t = authority.sign(p, self.kernel.policy, approved_by="demo", now=self.now)
        receipt = self.kernel.admit(p, caller="researcher", approval=t)
        self.kernel.start(receipt["run_id"])
        self.kernel.finish(receipt["run_id"], 99)
        self.snapshot = self.kernel.export()
        self.head = self.kernel.verify_audit()["head_sha256"]
        self.policy_hash = digest(self.kernel.policy)

    def tearDown(self):
        self.kernel.close()
        self.tmp.cleanup()

    def verify(self, snapshot=None):
        return verify_snapshot(snapshot or self.snapshot, expected_head=self.head, expected_policy=self.policy_hash)

    def test_valid_snapshot_projection(self):
        self.assertTrue(self.verify()["verified"])

    def test_materialized_budget_tampering(self):
        self.snapshot["budgets"][0]["spent"] = 0
        with self.assertRaises(Rejected):
            self.verify()

    def test_run_state_tampering(self):
        self.snapshot["runs"][0]["state"] = "admitted"
        with self.assertRaises(Rejected):
            self.verify()

    def test_inbox_body_tampering(self):
        self.snapshot["inbox"][0]["body"] = "changed"
        with self.assertRaises(Rejected):
            self.verify()

    def test_nonce_loss_is_not_safe_restore(self):
        self.snapshot["nonces"] = []
        with self.assertRaises(Rejected):
            self.verify()

    def test_unexplained_run_rejected(self):
        row = copy.deepcopy(self.snapshot["runs"][0])
        row["run_id"] = "orphan"
        self.snapshot["runs"].append(row)
        with self.assertRaises(Rejected):
            self.verify()

    def test_policy_tampering(self):
        self.snapshot["policy"]["project_token_caps"]["personal"] = 999999
        with self.assertRaises(Rejected):
            self.verify()

    def test_event_truncation_rejected(self):
        self.snapshot["events"].pop()
        with self.assertRaises(Rejected):
            self.verify()

    def test_stored_permit_extension_rejected(self):
        self.snapshot["runs"][0]["permit_expires"] += 1
        with self.assertRaises(Rejected):
            self.verify()

    def test_export_policy_is_detached_from_live_kernel(self):
        self.snapshot["policy"]["revision"] = "changed-export"
        self.assertNotEqual(self.snapshot["policy"]["revision"], self.kernel.policy["revision"])


if __name__ == "__main__":
    unittest.main()
