"""Offline reference kernel. No shell, network, model calls, or real action executors.

Authority and authenticated caller are trusted inputs. Run this in the broker, never
inside an untrusted agent process. This module is NOT a sandbox or an identity service.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import hmac
import json
from pathlib import Path
import re
import secrets
import sqlite3
import time
from typing import Callable


class Rejected(ValueError):
    """A request failed closed before admission."""


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def integer(value, name, low=0, high=2**53 - 1):
    if type(value) is not int or not low <= value <= high:
        raise Rejected(f"{name}: invalid integer")
    return value


def slug(value, name):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value):
        raise Rejected(f"{name}: invalid identifier")
    return value


def strict_loads(text):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise Rejected(f"duplicate JSON key: {key}")
            out[key] = value
        return out
    return json.loads(text, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(Rejected(value)))


PLAN_FIELDS = {"version", "proposal_id", "actor", "project", "action", "resource",
               "arguments", "source_digests", "max_tokens", "deadline", "idempotency_key"}
ACTIONS = {"research.summarize", "code.propose_patch", "test.run", "artifact.stage"}
GUARDED = {"test.run", "artifact.stage"}


def validate_plan(plan):
    if not isinstance(plan, dict) or set(plan) != PLAN_FIELDS:
        raise Rejected("plan fields mismatch")
    if type(plan["version"]) is not int or plan["version"] != 1:
        raise Rejected("unsupported plan version")
    for field in ("proposal_id", "actor", "project", "idempotency_key"):
        slug(plan[field], field)
    if not isinstance(plan["action"], str) or plan["action"] not in ACTIONS:
        raise Rejected("action is not supported; external effects and PC access are denied")
    resource = plan["resource"]
    if not isinstance(resource, str) or not resource.startswith(f"artifact:{plan['project']}/"):
        raise Rejected("resource outside project")
    path = resource.split(":", 1)[1]
    if not re.fullmatch(r"[A-Za-z0-9_./-]{1,400}", path):
        raise Rejected("invalid virtual resource")
    if any(part in ("", ".", "..") for part in path.split("/")):
        raise Rejected("noncanonical virtual resource")
    if not isinstance(plan["arguments"], dict) or set(plan["arguments"]) != {"instruction"}:
        raise Rejected("arguments: expected instruction only")
    instruction = plan["arguments"]["instruction"]
    if not isinstance(instruction, str) or len(instruction) > 10000:
        raise Rejected("instruction too long or not text")
    refs = plan["source_digests"]
    if not isinstance(refs, list) or len(refs) > 100 or any(
        not isinstance(x, str) or not re.fullmatch(r"sha256:[a-f0-9]{64}", x) for x in refs
    ):
        raise Rejected("invalid source digests")
    integer(plan["max_tokens"], "max_tokens", 1, 1_000_000)
    integer(plan["deadline"], "deadline", 1)
    canonical(plan)


def example_policy():
    return {"version": 1, "revision": "2026-11-14-demo-1", "max_approval_ttl": 600,
            "project_token_caps": {"personal": 10000},
            "grants": {"researcher": {"personal": sorted(ACTIONS)}}}


def example_plan(now, action="artifact.stage", key="demo-1"):
    return {"version": 1, "proposal_id": key, "actor": "researcher", "project": "personal",
            "action": action, "resource": "artifact:personal/notes/demo.md",
            "arguments": {"instruction": "Preparar una nota sintética para revisión."},
            "source_digests": [], "max_tokens": 250, "deadline": int(now) + 900,
            "idempotency_key": key}


class Authority:
    """Trusted in-memory demo authority. Production needs authenticated human UI.

    HMAC provides integrity to the broker, not nonrepudiation. All holders of the
    HMAC key can mint approvals. The key is never serialized by this module.
    """
    def __init__(self, key: bytes):
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("authority key must contain at least 32 bytes")
        self._key = key

    def sign(self, plan, policy, *, approved_by, now, ttl=300):
        validate_plan(plan)
        slug(approved_by, "approved_by")
        integer(now, "now", 1)
        integer(ttl, "ttl", 1, policy["max_approval_ttl"])
        claims = {"version": 1, "plan_hash": digest(plan), "policy_hash": digest(policy),
                  "actor": plan["actor"], "approved_by": approved_by,
                  "not_before": now, "expires_at": min(now + ttl, plan["deadline"]),
                  "nonce": secrets.token_hex(16)}
        return {"claims": claims, "mac": hmac.digest(self._key, canonical(claims), "sha256").hex()}

    def verify(self, token, plan, policy, now):
        if not isinstance(token, dict) or set(token) != {"claims", "mac"}:
            raise Rejected("approval required")
        claims = token["claims"]
        fields = {"version", "plan_hash", "policy_hash", "actor", "approved_by",
                  "not_before", "expires_at", "nonce"}
        if not isinstance(claims, dict) or set(claims) != fields:
            raise Rejected("approval claims malformed")
        mac = token["mac"]
        if not isinstance(mac, str) or not re.fullmatch(r"[a-f0-9]{64}", mac):
            raise Rejected("approval MAC malformed")
        if not hmac.compare_digest(mac, hmac.digest(self._key, canonical(claims), "sha256").hex()):
            raise Rejected("approval signature invalid")
        if type(claims["version"]) is not int or claims["version"] != 1:
            raise Rejected("approval version")
        slug(claims["approved_by"], "approved_by")
        if not isinstance(claims["nonce"], str) or not re.fullmatch(r"[a-f0-9]{32}", claims["nonce"]):
            raise Rejected("nonce malformed")
        integer(claims["not_before"], "not_before", 1)
        integer(claims["expires_at"], "expires_at", 1)
        if not claims["not_before"] <= now < claims["expires_at"] <= plan["deadline"]:
            raise Rejected("approval outside validity interval")
        if claims["expires_at"] - claims["not_before"] > policy["max_approval_ttl"]:
            raise Rejected("approval TTL exceeds policy")
        if claims["plan_hash"] != digest(plan) or claims["policy_hash"] != digest(policy):
            raise Rejected("approval does not bind current plan and policy")
        if claims["actor"] != plan["actor"]:
            raise Rejected("approval actor mismatch")
        return claims


class Kernel:
    def __init__(self, database, policy, authority: Authority, clock: Callable = time.time):
        # Canonical copy prevents callers mutating policy after construction.
        self.policy = strict_loads(canonical(policy).decode())
        self.authority = authority
        self.clock = clock  # trusted broker dependency, not supplied by an agent per request
        self.db = sqlite3.connect(str(database), timeout=5, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS budgets(project TEXT PRIMARY KEY, cap INTEGER NOT NULL,
             reserved INTEGER NOT NULL DEFAULT 0, spent INTEGER NOT NULL DEFAULT 0);
          CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY, project TEXT NOT NULL,
             idem TEXT NOT NULL, plan_hash TEXT NOT NULL, plan_json TEXT NOT NULL,
             state TEXT NOT NULL, reserved INTEGER NOT NULL, actual INTEGER,
             policy_hash TEXT NOT NULL, permit_expires INTEGER NOT NULL,
             UNIQUE(project, idem));
          CREATE TABLE IF NOT EXISTS nonces(nonce TEXT PRIMARY KEY, run_id TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS inbox(item_id TEXT PRIMARY KEY, source TEXT NOT NULL,
             body TEXT NOT NULL, state TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, timestamp INTEGER NOT NULL,
             kind TEXT NOT NULL, payload TEXT NOT NULL, prev_hash TEXT NOT NULL, event_hash TEXT NOT NULL);
        """)
        with self.transaction():
            for project, cap in self.policy["project_token_caps"].items():
                slug(project, "project")
                integer(cap, "project cap", 1)
                self.db.execute("INSERT OR IGNORE INTO budgets(project,cap) VALUES(?,?)", (project, cap))
                existing = self.db.execute("SELECT cap FROM budgets WHERE project=?", (project,)).fetchone()[0]
                if existing != cap:
                    raise Rejected("budget cap change requires an explicit migration")

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _event(self, kind, payload, *, timestamp=None):
        last = self.db.execute("SELECT seq,event_hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        seq, prev = (last["seq"] + 1, last["event_hash"]) if last else (1, "0" * 64)
        body = {"seq": seq, "timestamp": int(self.clock()) if timestamp is None else timestamp, "kind": kind,
                "payload": payload, "prev_hash": prev}
        event_hash = digest(body)
        self.db.execute("INSERT INTO events VALUES(?,?,?,?,?,?)",
                        (seq, body["timestamp"], kind, canonical(payload).decode(), prev, event_hash))
        return event_hash

    def capture(self, item_id, text, source="manual"):
        slug(item_id, "item_id")
        if source not in {"manual", "synthetic", "telegram-import"}:
            raise Rejected("unsupported inbox source")
        if not isinstance(text, str) or not 1 <= len(text) <= 20000:
            raise Rejected("invalid inbox text")
        with self.transaction():
            existing = self.db.execute("SELECT * FROM inbox WHERE item_id=?", (item_id,)).fetchone()
            if existing:
                if existing["body"] != text or existing["source"] != source:
                    raise Rejected("inbox idempotency conflict")
                return item_id
            self.db.execute("INSERT INTO inbox VALUES(?,?,?,?)", (item_id, source, text, "untrusted"))
            self._event("inbox.captured", {"item_id": item_id, "source": source, "body_sha256": digest(text)})
        return item_id

    def admit(self, plan, *, caller, approval=None):
        # Deep copy closes an in-process concurrent mutation race for the remaining admission path.
        plan = strict_loads(canonical(plan).decode())
        validate_plan(plan)
        now = int(self.clock())
        if caller != plan["actor"]:
            raise Rejected("caller does not match actor")
        if now >= plan["deadline"]:
            raise Rejected("plan expired")
        allowed = self.policy["grants"].get(caller, {}).get(plan["project"], [])
        if plan["action"] not in allowed:
            raise Rejected("capability not granted")
        claims = None
        if plan["action"] in GUARDED:
            claims = self.authority.verify(approval, plan, self.policy, now)
        ph = digest(plan)
        with self.transaction():
            # Lock acquisition may have waited; validity must also hold at admission.
            now = int(self.clock())
            if now >= plan["deadline"]:
                raise Rejected("plan expired while waiting for transaction")
            if claims:
                claims = self.authority.verify(approval, plan, self.policy, now)
            existing = self.db.execute("SELECT * FROM runs WHERE project=? AND idem=?",
                                       (plan["project"], plan["idempotency_key"])).fetchone()
            if existing:
                if existing["plan_hash"] != ph:
                    raise Rejected("idempotency key reused with a different plan")
                return {"run_id": existing["run_id"], "state": existing["state"], "duplicate": True}
            if claims and self.db.execute("SELECT 1 FROM nonces WHERE nonce=?", (claims["nonce"],)).fetchone():
                raise Rejected("approval nonce already consumed")
            changed = self.db.execute("""UPDATE budgets SET reserved=reserved+?
                WHERE project=? AND spent+reserved+? <= cap""",
                (plan["max_tokens"], plan["project"], plan["max_tokens"])).rowcount
            if changed != 1:
                raise Rejected("budget unavailable")
            run_id = secrets.token_hex(16)
            self.db.execute("INSERT INTO runs VALUES(?,?,?,?,?,?,?,?,?,?)",
                            (run_id, plan["project"], plan["idempotency_key"], ph,
                             canonical(plan).decode(), "admitted", plan["max_tokens"], None,
                             digest(self.policy), claims["expires_at"] if claims else plan["deadline"]))
            if claims:
                self.db.execute("INSERT INTO nonces VALUES(?,?)", (claims["nonce"], run_id))
            self._event("run.admitted", {"run_id": run_id, "plan_hash": ph,
                        "policy_hash": digest(self.policy), "reserved": plan["max_tokens"],
                        "approved_by": claims["approved_by"] if claims else "standing-policy",
                        "approval_nonce": claims["nonce"] if claims else None,
                        "permit_expires": claims["expires_at"] if claims else plan["deadline"]}, timestamp=now)
            return {"run_id": run_id, "state": "admitted", "duplicate": False}

    def start(self, run_id):
        # Atomic claim: no automatic re-dispatch after a crash at this boundary.
        with self.transaction():
            row = self.db.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if not row or row["state"] != "admitted":
                raise Rejected("run cannot be started twice")
            plan = strict_loads(row["plan_json"])
            if digest(plan) != row["plan_hash"]:
                raise Rejected("stored plan integrity mismatch")
            if row["policy_hash"] != digest(self.policy):
                raise Rejected("policy changed since admission; re-propose")
            now = int(self.clock())
            if now >= row["permit_expires"]:
                raise Rejected("dispatch permit expired; reconcile reservation")
            changed = self.db.execute("UPDATE runs SET state='started' WHERE run_id=? AND state='admitted'",
                                      (run_id,)).rowcount
            if changed != 1:
                raise Rejected("run cannot be started twice")
            self._event("run.started", {"run_id": run_id}, timestamp=now)

    def finish(self, run_id, actual_tokens, *, outcome="completed"):
        integer(actual_tokens, "actual_tokens")
        if outcome not in {"completed", "failed"}:
            raise Rejected("invalid outcome")
        with self.transaction():
            row = self.db.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if not row or row["state"] != "started":
                raise Rejected("run is not started; reconcile indeterminate effects separately")
            if actual_tokens > row["reserved"]:
                raise Rejected("actual cost exceeds reserved ceiling; reservation retained")
            self.db.execute("UPDATE budgets SET reserved=reserved-?,spent=spent+? WHERE project=?",
                            (row["reserved"], actual_tokens, row["project"]))
            self.db.execute("UPDATE runs SET state=?,actual=? WHERE run_id=?", (outcome, actual_tokens, run_id))
            self._event("run.finished", {"run_id": run_id, "outcome": outcome, "actual_tokens": actual_tokens})

    def export(self):
        with self.transaction():
            return {"schema_version": 2, "policy_sha256": digest(self.policy),
                    "policy": strict_loads(canonical(self.policy).decode()),
                    "budgets": [dict(x) for x in self.db.execute("SELECT * FROM budgets ORDER BY project")],
                    "inbox": [dict(x) for x in self.db.execute("SELECT * FROM inbox ORDER BY item_id")],
                    "runs": [dict(x) for x in self.db.execute("SELECT * FROM runs ORDER BY run_id")],
                    "nonces": [dict(x) for x in self.db.execute("SELECT * FROM nonces ORDER BY nonce")],
                    "events": [dict(x) for x in self.db.execute("SELECT * FROM events ORDER BY seq")]}

    def verify_audit(self, expected_head=None):
        prev, seq = "0" * 64, 0
        for row in self.db.execute("SELECT * FROM events ORDER BY seq"):
            seq += 1
            body = {"seq": row["seq"], "timestamp": row["timestamp"], "kind": row["kind"],
                    "payload": strict_loads(row["payload"]), "prev_hash": row["prev_hash"]}
            if row["seq"] != seq or row["prev_hash"] != prev or digest(body) != row["event_hash"]:
                raise Rejected("audit chain mismatch")
            prev = row["event_hash"]
        if expected_head is not None and not hmac.compare_digest(prev, expected_head):
            raise Rejected("audit checkpoint mismatch (including possible truncation)")
        return {"events": seq, "head_sha256": prev}


def demo(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    db = directory / "jarvis-demo.sqlite3"
    if db.exists():
        raise Rejected("demo database already exists; choose a fresh output directory")
    now = int(time.time())
    authority = Authority(secrets.token_bytes(32))
    kernel = Kernel(db, example_policy(), authority)
    try:
        kernel.capture("inbox-demo", "Investigar una propiedad de un extractor genérico.", "synthetic")
        plan = example_plan(now)
        token = authority.sign(plan, kernel.policy, approved_by="simulated-human", now=now)
        receipt = kernel.admit(plan, caller="researcher", approval=token)
        duplicate = kernel.admit(plan, caller="researcher", approval=token)
        kernel.start(receipt["run_id"])
        # No action executor. Token count is synthetic; no model call takes place.
        kernel.finish(receipt["run_id"], 125)
        export = kernel.export()
        report = {"mode": "offline-synthetic-no-executor", "receipt": receipt,
                  "idempotent_retry": duplicate, "audit": kernel.verify_audit(),
                  "budgets": export["budgets"]}
        (directory / "export.json").write_text(json.dumps(export, indent=2, ensure_ascii=False) + "\n")
        (directory / "demo-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        return report
    finally:
        kernel.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JARVIS offline policy-kernel demo; no external actions")
    parser.add_argument("--demo", metavar="OUTPUT_DIR", required=True)
    args = parser.parse_args()
    print(json.dumps(demo(args.demo), indent=2, ensure_ascii=False))
