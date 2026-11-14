#!/usr/bin/env python3
"""Recompila pruebas en directorio limpio y audita axiomas; sólo biblioteca estándar.

No es un sandbox para código Lean hostil. Los fuentes deben revisarse antes de ejecutar.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
MODULES = ("HealthGate", "SaturatingCounter", "Counterexamples", "StartupGate",
           "ReferenceRuns", "FeedbackLeakage")
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
MUTATIONS = {
    "remove_failure_latch": (
        "s.failed || decide (cutoff ≤ count)", "decide (cutoff ≤ count)"
    ),
    "release_threshold_sample": (
        "if (step cutoff s x).failed then none else some x",
        "if s.failed then none else some x",
    ),
    "off_by_one_threshold": (
        "decide (cutoff ≤ count)", "decide (cutoff < count)"
    ),
    "always_deny": (
        "s.failed || decide (cutoff ≤ count)", "true"
    ),
    "ignore_symbol_change": (
        "if s.last = some x then s.run + 1 else 1", "s.run + 1"
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(lean: str, args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["LEAN_PATH"] = str(cwd)
    return subprocess.run([lean, *args], cwd=cwd, env=env, text=True,
                          capture_output=True, timeout=60, check=False)


def source_sanity(text: str) -> None:
    # Conservative audit for this small, reviewed source bundle; not a Lean lexer.
    body = re.sub(r"/\-.*?\-/", "", text, flags=re.S)
    body = re.sub(r"--[^\n]*", "", body)
    bad = re.search(r"\b(sorry|admit|native_decide|unsafe|skipKernelTC|trustCompiler|"
                    r"ofReduceBool)\b|^\s*(axiom|opaque|macro|elab)\b|#eval", body,
                    flags=re.M)
    if bad:
        raise RuntimeError(f"Unexpected proof construct: {bad.group(0)!r}")


def publish_report(results: Path, report: dict) -> None:
    """Conserva recibo por ejecución y actualiza latest sin exponer JSON parcial."""
    payload = (json.dumps(report, indent=2) + "\n").encode()
    for target in (results / f"verification-{report['run_id']}.json", results / "verification.json"):
        with tempfile.NamedTemporaryFile(dir=results, prefix=".receipt-", delete=False) as handle:
            handle.write(payload)
            temporary = Path(handle.name)
        temporary.replace(target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean", default=os.environ.get("LEAN_BIN") or shutil.which("lean"))
    parser.add_argument("--skip-mutations", action="store_true")
    args = parser.parse_args()
    results = ROOT / "results"
    results.mkdir(exist_ok=True)
    report: dict = {
        "schema": "cryptosure.formal-evidence.v1",
        "run_id": uuid.uuid4().hex,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "tool": {"name": "Lean"},
        "scope": "Propiedades del modelo formal; no conformidad ni entropía física",
        "status": "in_progress", "source_sha256": {}, "theorems": {}, "logs": {},
    }
    publish_report(results, report)
    try:
        return execute_checks(args, results, report)
    except Exception as error:
        report.update(status="failed", error=f"{type(error).__name__}: {error}")
        publish_report(results, report)
        raise


def execute_checks(args, results: Path, report: dict) -> int:
    if not args.lean:
        raise RuntimeError("Lean no encontrado; use --lean /ruta/bin/lean o LEAN_BIN")
    lean = str(Path(args.lean).resolve())
    version = subprocess.check_output([lean, "--version"], text=True).strip()
    if "version 4.19.0," not in version:
        raise RuntimeError(f"Toolchain distinta de la validada: {version}")
    report["tool"].update(version=version, binary_sha256=sha256(Path(lean)))
    source_bytes: dict[str, bytes] = {}
    with tempfile.TemporaryDirectory(prefix="cryptosure-proof-") as raw:
        clean = Path(raw)
        names = []
        for module in MODULES:
            source = ROOT / f"{module}.lean"
            captured = source.read_bytes()
            source_bytes[source.name] = captured
            text = captured.decode("utf-8")
            source_sanity(text)
            report["source_sha256"][source.name] = hashlib.sha256(captured).hexdigest()
            (clean / source.name).write_bytes(captured)
            names += re.findall(r"^theorem\s+(\w+)", text, flags=re.M)
            proc = invoke(lean, ["-o", f"{module}.olean", source.name], clean)
            output = proc.stdout + proc.stderr
            report["logs"][module] = output
            if proc.returncode or "warning:" in output:
                raise RuntimeError(f"Compilation failed: {module}\n{output}")
        audit = "\n".join(f"import {m}" for m in MODULES) + "\n"
        audit += "\n".join(f"#print axioms CryptoSure.{name}" for name in names) + "\n"
        (clean / "Audit.lean").write_text(audit)
        checked = invoke(lean, ["Audit.lean"], clean)
        if checked.returncode:
            raise RuntimeError(checked.stdout + checked.stderr)
        for line in checked.stdout.splitlines():
            found = re.fullmatch(r"'CryptoSure\.(\w+)' (.*)", line)
            if not found:
                continue
            name, statement = found.groups()
            if statement == "does not depend on any axioms":
                axioms = []
            else:
                match = re.fullmatch(r"depends on axioms: \[(.*)\]", statement)
                if not match:
                    raise RuntimeError(f"Unknown audit output: {line}")
                axioms = [x.strip() for x in match.group(1).split(",") if x.strip()]
            if not set(axioms) <= ALLOWED_AXIOMS:
                raise RuntimeError(f"Unapproved axioms in {name}: {axioms}")
            report["theorems"][name] = {"status": "kernel_checked", "axioms": axioms}
        if set(report["theorems"]) != set(names):
            raise RuntimeError("Audit did not cover every theorem declaration")
        report["kernel_check_status"] = "passed"

    mutations = []
    if not args.skip_mutations:
        original = source_bytes["HealthGate.lean"].decode("utf-8")
        for name, (old, new) in MUTATIONS.items():
            if original.count(old) != 1:
                raise RuntimeError(f"Mutation target not unique: {name}")
            with tempfile.TemporaryDirectory(prefix="cryptosure-mutant-") as raw:
                clean = Path(raw)
                (clean / "HealthGate.lean").write_text(original.replace(old, new, 1))
                proc = invoke(lean, ["-o", "HealthGate.olean", "HealthGate.lean"], clean)
                output = proc.stdout + proc.stderr
                # A counting mutation can preserve safety but violate exact reference.
                if proc.returncode == 0:
                    (clean / "ReferenceRuns.lean").write_bytes(source_bytes["ReferenceRuns.lean"])
                    proc = invoke(lean, ["ReferenceRuns.lean"], clean)
                    output += proc.stdout + proc.stderr
                killed = proc.returncode != 0 and "error:" in output
                mutations.append({"name": name, "status": "rejected" if killed else "SURVIVED",
                                  "returncode": proc.returncode, "old": old, "new": new,
                                  "compiler_output": output})
        (results / "mutation_checks.json").write_text(json.dumps(mutations, indent=2) + "\n")
        if any(x["status"] != "rejected" for x in mutations):
            raise RuntimeError("A regression mutant unexpectedly passed")
    report["mutation_check_status"] = "skipped" if args.skip_mutations else "passed"
    report["mutation_count"] = len(mutations)
    report["status"] = "verified"
    publish_report(results, report)
    print(f"PASS: {len(report['theorems'])} teoremas verificados; "
          f"{len(mutations)} mutaciones incorrectas rechazadas.")
    print(f"Evidence: {results / 'verification.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
