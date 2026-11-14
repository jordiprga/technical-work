#!/usr/bin/env python3
"""Run independent mission checks on temporary snapshots; never contacts a service."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "00_coordination" / "results" / "checks"
IGNORED = {".git", ".lake", "__pycache__", "research_cache", ".venv", "node_modules"}
JOBS = [
    ("business", "01_cryptosure_business", ["-m", "unittest", "discover", "-s", "tests", "-v"]),
    ("cryptosure", "02_cryptosure_prototype", ["-m", "unittest", "discover", "-s", "tests", "-v"]),
    ("formal_runner", "03_formal_verification", ["-m", "unittest", "discover", "-p", "test_*.py", "-v"]),
    ("extractors", "04_extractors_entropy", ["-m", "unittest", "discover", "-p", "test_*.py", "-v"]),
    ("qrng", "05_qrng_model", ["-m", "unittest", "discover", "-p", "test_*.py", "-v"]),
    ("jarvis", "06_jarvis_architecture", ["-m", "unittest", "discover", "-s", "tests", "-v"]),
    ("feedback_disclosure", "00_coordination/feedback_leakage", ["-m", "unittest", "-v"]),
]


def fingerprint(directory):
    included = {}
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory)
        if any(p in IGNORED or p in {"results", "figures"} for p in relative.parts):
            continue
        if path.is_file() and not path.is_symlink() and path.suffix in {".py", ".lean", ".toml", ".json", ".bin"}:
            included[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return included


def run_job(job):
    name, relative, arguments = job
    source = ROOT / relative
    before = fingerprint(source)
    started = time.monotonic()
    result = {"mission": name, "directory": relative, "command": [sys.executable, *arguments],
              "source_sha256": before, "status": "ERROR"}
    with tempfile.TemporaryDirectory(prefix=f"operation-check-{name}-") as temporary:
        snapshot = Path(temporary) / "snapshot"
        shutil.copytree(source, snapshot, ignore=shutil.ignore_patterns(*IGNORED, "*.pyc", "*.olean"))
        if fingerprint(snapshot) != before:
            result["status"] = "SOURCE_CHANGED_DURING_SNAPSHOT"
            return result
        environment = dict(os.environ)
        # Tests use only their local sources. No credentials or external tools are requested.
        environment["PYTHONPATH"] = str(snapshot / "src")
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["MPLBACKEND"] = "Agg"
        try:
            process = subprocess.run([sys.executable, *arguments], cwd=snapshot, env=environment,
                                     capture_output=True, text=True, timeout=180, check=False)
            log = process.stdout + process.stderr
            (OUT / f"{name}.log").write_text(log)
            result["returncode"] = process.returncode
            count = re.search(r"Ran (\d+) tests?", log)
            formal = re.search(r"PASS: (\d+) teoremas verificados; (\d+) mutaciones", log)
            result["unit_tests"] = int(count.group(1)) if count else None
            if formal:
                result["lean_theorems"] = int(formal.group(1))
                result["rejected_mutants"] = int(formal.group(2))
                for artifact in ("verification.json", "mutation_checks.json"):
                    shutil.copyfile(snapshot / "results" / artifact, OUT / f"formal_{artifact}")
            has_executed_checks = bool(formal or (count and int(count.group(1)) > 0))
            result["status"] = "PASS" if process.returncode == 0 and has_executed_checks else "FAIL"
        except subprocess.TimeoutExpired:
            result["status"] = "TIMEOUT"
        result["current_source_matches_snapshot"] = fingerprint(source) == before
        if not result["current_source_matches_snapshot"]:
            result["status"] += "_SOURCE_CHANGED_AFTER_SNAPSHOT"
    result["duration_seconds"] = round(time.monotonic()-started, 3)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean", type=Path)
    parser.add_argument("--require-lean", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = list(JOBS)
    lean = args.lean or (Path(shutil.which("lean")) if shutil.which("lean") else None)
    if lean:
        jobs.append(("formal", "03_formal_verification", ["run_checks.py", "--lean", str(lean.resolve())]))
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(run_job, jobs))
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "Local tests of source snapshots; not certification or physical validation",
              "python": sys.version, "results": results,
              "lean_requested": bool(lean), "lean_skipped": not bool(lean),
              "total_unit_tests": sum(r.get("unit_tests") or 0 for r in results),
              "all_executed_checks_passed": all(r["status"] == "PASS" for r in results)}
    (OUT / "summary.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    for result in results:
        print(result["mission"], result["status"],
              f"tests={result.get('unit_tests')}", f"theorems={result.get('lean_theorems')}")
    if not lean:
        print("Lean SKIPPED: provide --lean /path/to/lean-4.19.0-linux/bin/lean")
    print(f"Unit tests: {report['total_unit_tests']}; report: {OUT / 'summary.json'}")
    return 0 if report["all_executed_checks_passed"] and (lean or not args.require_lean) else 1


if __name__ == "__main__":
    raise SystemExit(main())
