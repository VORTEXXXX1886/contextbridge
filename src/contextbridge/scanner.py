"""Conservative read-only scanner. It never runs project code."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from .privacy import BLOCKED_DIRS, safe_relative

MAX_FILES = 3000
MAX_FILE_BYTES = 128 * 1024

def scan(root: Path) -> list[dict]:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Project root must be a directory")
    result: list[dict] = []
    for base, dirs, names in os.walk(root, followlinks=False):
        base_path = Path(base)
        dirs[:] = sorted(d for d in dirs if d.lower() not in BLOCKED_DIRS and not (base_path / d).is_symlink())
        for name in sorted(names):
            path = base_path / name
            rel = safe_relative(path, root)
            if rel is None or not path.is_file():
                continue
            try:
                stat = path.stat()
                if stat.st_size > MAX_FILE_BYTES:
                    continue
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
            except (OSError, PermissionError):
                continue
            result.append({"path": rel.as_posix(), "sha256": digest, "size": stat.st_size})
            if len(result) > MAX_FILES:
                raise ValueError(f"Project exceeds {MAX_FILES} eligible files; refusing incomplete scan")
    return result
