#!/usr/bin/env python3
"""Compile the dossier in a clean directory and audit each public theorem."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
MODULES = ("AISProfile", "CTRProfile", "ITS", "CQ", "Reduction", "SourceBudget", "NISTProfiles", "TransitionPreimage", "CTRHybrid", "EffectiveCTR", "Composition")
TRUSTED = {"Classical.choice", "propext", "Quot.sound"}


def invoke(args, clean, env):
    run = subprocess.run(args, cwd=clean, env=env, text=True, capture_output=True, timeout=180)
    output = run.stdout + run.stderr
    if run.returncode or "warning:" in output:
        raise ValueError(output.strip())
    return output


def names(source):
    # Each authored module has one top-level namespace; private helper theorems
    # are checked transitively by the public theorems and by kernel compilation.
    body = re.sub(r"/-.*?-/", "", source, flags=re.S)
    body = re.sub(r"--[^\n]*", "", body)
    if re.search(r"\b(sorry|admit|native_decide|unsafe|skipKernelTC|trustCompiler)\b|^\s*axiom\s", body, re.M):
        raise ValueError("Unreviewed proof shortcut")
    namespaces = re.findall(r"^namespace\s+([\w.]+)", body, re.M)
    if len(namespaces) != 1:
        raise ValueError("Expected one namespace per source")
    symbols = re.findall(r"^(?:theorem|lemma)\s+([\w.]+)", body, re.M)
    if not symbols:
        raise ValueError("No public theorem found")
    return [f"{namespaces[0]}.{name}" for name in symbols]


def check(lean):
    version = subprocess.check_output([lean, "--version"], text=True).strip()
    if "version 4.19.0," not in version:
        raise ValueError(f"Required Lean 4.19.0, found {version}")
    actual = {path.stem for path in (ROOT / "formal").glob("*.lean")}
    if actual != set(MODULES):
        raise ValueError(f"Mismatch between source modules and audit: {sorted(actual ^ set(MODULES))}")
    hashes, theorems = {}, []
    with tempfile.TemporaryDirectory(prefix="ptg3-lean-") as tmp:
        clean = Path(tmp)
        env = dict(os.environ, LEAN_PATH=str(clean))
        for module in MODULES:
            name = module + ".lean"
            src = (ROOT / "formal" / name).read_bytes()
            hashes[name] = hashlib.sha256(src).hexdigest()
            (clean / name).write_bytes(src)
            theorems.extend(names(src.decode()))
            invoke([lean, "-o", module + ".olean", name], clean, env)
        audit = [f"import {module}" for module in MODULES]
        audit.extend(f"#print axioms {name}" for name in theorems)
        (clean / "Audit.lean").write_text("\n".join(audit) + "\n")
        output = invoke([lean, "Audit.lean"], clean, env)
    dependencies = {}
    for name, detail in re.findall(r"^'([^']+)' (.*)$", output, re.M):
        if detail == "does not depend on any axioms":
            deps = []
        else:
            match = re.fullmatch(r"depends on axioms: \[(.*)\]", detail)
            if not match:
                raise ValueError(f"Unrecognized axiom report for {name}: {detail}")
            deps = match[1].split(", ")
        if set(deps) - TRUSTED:
            raise ValueError(f"Unapproved dependency for {name}: {deps}")
        dependencies[name] = deps
    if set(dependencies) != set(theorems):
        raise ValueError("Incomplete axiom audit")
    return {"status": "kernel_checked", "lean": version, "sha256": hashes,
            "theorem_count": len(dependencies), "theorems_and_axioms": dependencies}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean", default=os.getenv("LEAN_BIN", "lean"))
    parser.add_argument("--report", type=Path, help="Save the result as JSON")
    args = parser.parse_args()
    try:
        lean = shutil.which(args.lean)
        if not lean:
            raise ValueError("Lean 4.19.0 unavailable; set --lean or LEAN_BIN")
        result = check(str(Path(lean).resolve()))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result = {"status": "failed", "error": str(exc)}
    if args.report:
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    if result["status"] == "failed":
        raise SystemExit(result["error"])
    print(f'Lean checked {result["theorem_count"]} public theorems across {len(MODULES)} modules.')


if __name__ == "__main__":
    main()
