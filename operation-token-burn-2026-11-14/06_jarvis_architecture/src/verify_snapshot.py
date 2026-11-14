"""Independent export verifier; no effects, imports, network or restoration writes.

Checks event chain against an independently trusted head, then reconstructs the
materialized ledger from events. Supports one policy revision per export only.
It does not authenticate humans, recover HMAC keys, or prove external effects.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from jarvis_kernel import Rejected, digest, integer, strict_loads, validate_plan


def require(condition, message):
    if not condition:
        raise Rejected(message)


def keyed(rows, key):
    require(isinstance(rows, list) and len(rows) <= 100000, "invalid row collection")
    result = {}
    for row in rows:
        require(isinstance(row, dict) and key in row, "invalid row")
        value = row[key]
        require(isinstance(value, str) and value not in result, "duplicate or invalid row key")
        result[value] = row
    return result


def verify_snapshot(snapshot, *, expected_head, expected_policy):
    for value in (expected_head, expected_policy):
        require(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value), "invalid trusted checkpoint")
    require(isinstance(snapshot, dict) and snapshot.get("schema_version") == 2, "snapshot version must be 2")
    policy = snapshot["policy"]
    require(digest(policy) == expected_policy == snapshot["policy_sha256"], "policy checkpoint mismatch")
    runs = keyed(snapshot["runs"], "run_id")
    inbox = keyed(snapshot["inbox"], "item_id")
    nonces = keyed(snapshot["nonces"], "nonce")
    budgets = keyed(snapshot["budgets"], "project")
    require(set(budgets) == set(policy["project_token_caps"]), "budget projects mismatch")
    computed = {project: {"spent": 0, "reserved": 0} for project in budgets}
    states, actuals, seen_inbox, seen_nonces, seen_idem = {}, {}, set(), {}, set()
    prev = "0" * 64
    events = snapshot["events"]
    require(isinstance(events, list) and len(events) <= 100000, "too many events")
    for index, event in enumerate(events, 1):
        require(set(event) == {"seq", "timestamp", "kind", "payload", "prev_hash", "event_hash"}, "event fields")
        require(event["seq"] == index and event["prev_hash"] == prev, "event chain ordering")
        integer(event["timestamp"], "event timestamp", 1)
        payload = strict_loads(event["payload"])
        body = {"seq": index, "timestamp": event["timestamp"], "kind": event["kind"],
                "payload": payload, "prev_hash": prev}
        require(digest(body) == event["event_hash"], "event hash mismatch")
        prev = event["event_hash"]
        kind = event["kind"]
        if kind == "inbox.captured":
            item_id = payload["item_id"]
            require(item_id in inbox and item_id not in seen_inbox, "inbox event mismatch")
            row = inbox[item_id]
            require(row["source"] == payload["source"] and digest(row["body"]) == payload["body_sha256"]
                    and row["state"] == "untrusted", "inbox projection mismatch")
            seen_inbox.add(item_id)
            continue
        require(kind in {"run.admitted", "run.started", "run.finished"}, "unknown event kind")
        rid = payload["run_id"]
        require(rid in runs, "event references missing run")
        row = runs[rid]
        plan = strict_loads(row["plan_json"])
        validate_plan(plan)
        project = plan["project"]
        require(project in computed, "run project unknown")
        require(row["plan_hash"] == digest(plan), "run plan digest mismatch")
        require(row["project"] == project and row["idem"] == plan["idempotency_key"], "run metadata mismatch")
        require(row["reserved"] == plan["max_tokens"], "run reservation mismatch")
        require(row["policy_hash"] == expected_policy, "multi-policy history unsupported; migrate explicitly")
        integer(row["permit_expires"], "permit expiry", 1, plan["deadline"])
        if kind == "run.admitted":
            require(rid not in states, "duplicate admission")
            require((project, row["idem"]) not in seen_idem, "duplicate idempotency key")
            seen_idem.add((project, row["idem"]))
            require(payload["plan_hash"] == row["plan_hash"] and payload["policy_hash"] == expected_policy,
                    "admission binding mismatch")
            require(payload["reserved"] == row["reserved"], "admission reservation mismatch")
            require(payload["permit_expires"] == row["permit_expires"], "admission expiry mismatch")
            require(plan["action"] in policy["grants"].get(plan["actor"], {}).get(project, []), "ungranted admission")
            nonce = payload["approval_nonce"]
            if nonce is not None:
                require(nonce not in seen_nonces and nonce in nonces, "missing or replayed nonce")
                require(nonces[nonce]["run_id"] == rid, "nonce run binding")
                seen_nonces[nonce] = rid
            states[rid] = "admitted"
            actuals[rid] = None
            computed[project]["reserved"] += row["reserved"]
        elif kind == "run.started":
            require(states.get(rid) == "admitted", "invalid start transition")
            require(event["timestamp"] < row["permit_expires"], "start after permit expiry")
            states[rid] = "started"
        else:
            require(states.get(rid) == "started", "invalid finish transition")
            actual = integer(payload["actual_tokens"], "actual tokens", 0, row["reserved"])
            require(payload["outcome"] in {"completed", "failed"}, "unknown outcome")
            states[rid], actuals[rid] = payload["outcome"], actual
            computed[project]["reserved"] -= row["reserved"]
            computed[project]["spent"] += actual
        require(sum(computed[project].values()) <= policy["project_token_caps"][project], "historical budget overrun")
    require(prev == expected_head, "event head differs from trusted checkpoint")
    require(set(states) == set(runs) and seen_inbox == set(inbox) and set(seen_nonces) == set(nonces),
            "unexplained projection rows")
    for rid, row in runs.items():
        require(row["state"] == states[rid] and row["actual"] == actuals[rid], "run state projection mismatch")
    for project, row in budgets.items():
        require(row["cap"] == policy["project_token_caps"][project], "budget cap differs from trusted policy")
        require(row["spent"] == computed[project]["spent"] and row["reserved"] == computed[project]["reserved"],
                "budget projection mismatch")
    return {"verified": True, "events": len(events), "runs": len(runs), "inbox": len(inbox),
            "head_sha256": prev, "policy_sha256": expected_policy,
            "human_authorization_reverified": False, "external_effects_reverified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify a JARVIS v2 export with independent checkpoints")
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--expected-policy", required=True)
    args = parser.parse_args()
    with args.snapshot.open("rb") as stream:
        data = stream.read(32 * 1024 * 1024 + 1)
    require(len(data) <= 32 * 1024 * 1024, "snapshot too large")
    result = verify_snapshot(strict_loads(data), expected_head=args.expected_head, expected_policy=args.expected_policy)
    print(json.dumps(result, indent=2))
