"""Opt-in, metadata-only Git status for agent handoffs.

Never export diffs, paths, remotes, commit messages, or source contents.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .privacy import looks_sensitive

_TIMEOUT = 5


def _git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=_TIMEOUT, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_summary(root: Path) -> dict:
    """Return conservative repository metadata, or an unavailable marker.

    Require the selected root to be the Git top-level so that parent
    repositories never leak metadata about files outside the project.
    """
    root = root.resolve(strict=True)
    top = _git(root, "rev-parse", "--show-toplevel")
    if not top or os.path.normcase(str(Path(top).resolve())) != os.path.normcase(str(root)):
        return {"available": False}
    revision = _git(root, "rev-parse", "--verify", "HEAD")
    branch = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    status = _git(root, "status", "--porcelain=v1", "--untracked-files=normal")
    if not revision or len(revision) != 40 or status is None:
        return {"available": False}
    if branch is not None and (len(branch) > 200 or looks_sensitive(branch)):
        branch = None
    return {
        "available": True,
        "revision": revision,
        "branch": branch,  # None for detached HEAD or sensitive branch name
        "working_tree_dirty": bool(status),
    }
