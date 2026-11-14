"""Conservative Git metadata without status/diff or working-tree filter execution."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from .common import CryptoSureError, confined, read_bounded, sha256


def capture_git(repo: Path | None) -> dict[str, Any]:
    if repo is None:
        return {"requested": False, "status": "not_captured"}
    if repo.is_symlink() or not repo.is_dir():
        raise CryptoSureError("Git repository path must be a non-symlink directory")
    # Linked worktrees and redirected gitdirs need a separate authorization model.
    git_directory = confined(repo, ".git")
    if not git_directory.is_dir():
        raise CryptoSureError("Only a repository root with an internal .git directory is supported")
    environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LC_ALL": "C",
                   "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                   "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"}
    prefix = ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(repo)]

    def run(args: list[str], optional: bool = False) -> bytes | None:
        try:
            process = subprocess.run(prefix + args, env=environment, check=False,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise CryptoSureError(f"Git unavailable: {type(exc).__name__}") from exc
        if process.returncode:
            if optional:
                return None
            raise CryptoSureError("Git metadata capture failed (repository must be explicitly selected)")
        if len(process.stdout) > 2 * 1024 * 1024:
            raise CryptoSureError("Git metadata exceeds size limit")
        return process.stdout

    if run(["rev-parse", "--is-inside-work-tree"]).strip() != b"true":
        raise CryptoSureError("A working-tree Git repository is required")
    commit = run(["rev-parse", "--verify", "HEAD"], optional=True)
    tree = run(["rev-parse", "--verify", "HEAD^{tree}"], optional=True)
    index_path = confined(repo, ".git/index", must_exist=False)
    index_digest = sha256(read_bounded(index_path)) if index_path.exists() else None
    return {"requested": True, "status": "captured", "repository_name": repo.name,
            "head_commit": commit.decode("ascii").strip() if commit else None,
            "head_tree": tree.decode("ascii").strip() if tree else None,
            "index_sha256": index_digest, "dirty": None, "working_tree_status": "not_assessed",
            "limitation": "No se ejecuta git status/diff: pueden activar filtros del repositorio. HEAD e index no identifican bytes del working tree; importar explícitamente los artefactos relevantes."}
