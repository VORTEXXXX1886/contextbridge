"""Local metadata snapshots. No repository source code is exported."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .scanner import scan

STATE_DIR = ".contextbridge"
STATE_FILE = "snapshot.json"
MAX_NOTE_CHARS = 10_000
MAX_SNAPSHOT_BYTES = 2_000_000
MAX_MANIFEST_ENTRIES = 3000

def snapshot_path(root: Path) -> Path:
    return root / STATE_DIR / STATE_FILE

def _validate_snapshot(data: Any) -> dict:
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Unsupported or invalid snapshot schema")
    for field in ("project_name", "created_at", "note", "next_task", "decisions"):
        if not isinstance(data.get(field), str):
            raise ValueError(f"Invalid snapshot field: {field}")
    for field in ("note", "next_task", "decisions"):
        if len(data[field]) > MAX_NOTE_CHARS:
            raise ValueError(f"Snapshot field is too long: {field}")
    files = data.get("files")
    if not isinstance(files, list) or len(files) > MAX_MANIFEST_ENTRIES:
        raise ValueError("Invalid file manifest")
    seen: set[str] = set()
    for entry in files:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "size"}:
            raise ValueError("Invalid manifest entry")
        path, digest, size = entry["path"], entry["sha256"], entry["size"]
        if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path:
            raise ValueError("Invalid manifest path")
        if any(part in ("", ".", "..") for part in path.split("/")) or path in seen:
            raise ValueError("Unsafe or duplicate manifest path")
        seen.add(path)
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("Invalid file digest")
        if type(size) is not int or size < 0:
            raise ValueError("Invalid file size")
    return data

def load_snapshot(root: Path) -> dict:
    path = snapshot_path(root)
    if path.is_symlink() or not path.is_file() or path.parent.is_symlink():
        raise FileNotFoundError("No safe ContextBridge snapshot. Run 'contextbridge init' first.")
    if path.stat().st_size > MAX_SNAPSHOT_BYTES:
        raise ValueError("Snapshot exceeds size limit")
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValueError("Snapshot contains invalid JSON") from exc
    return _validate_snapshot(content)

def create_snapshot(root: Path, *, note: str | None = None, task: str | None = None,
                    decisions: str | None = None) -> dict:
    root = root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Project root must be a directory")
    state = root / STATE_DIR
    if state.is_symlink():
        raise ValueError("Refusing symlinked state directory")
    previous: dict = {}
    target = snapshot_path(root)
    if target.is_symlink():
        raise ValueError("Refusing symlinked snapshot")
    if target.exists():
        previous = load_snapshot(root)
    entries = {"note": note, "next_task": task, "decisions": decisions}
    for key, value in entries.items():
        if value is None:
            entries[key] = previous.get(key, "")
        elif len(value) > MAX_NOTE_CHARS:
            raise ValueError(f"{key} exceeds size limit")
    data = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project_name": root.name,
        "note": entries["note"],
        "next_task": entries["next_task"],
        "decisions": entries["decisions"],
        "files": scan(root),
    }
    state.mkdir(exist_ok=True)
    if state.is_symlink():
        raise ValueError("Refusing symlinked state directory")
    temp = state / f"snapshot.{os.getpid()}.tmp"
    try:
        with temp.open("x", encoding="utf-8") as out:
            json.dump(data, out, ensure_ascii=False, indent=2)
            out.write("\n")
        temp.replace(target)
    finally:
        temp.unlink(missing_ok=True)
    return data

def compare_snapshot(root: Path, previous: dict) -> dict[str, list[str]]:
    _validate_snapshot(previous)
    old = {entry["path"]: entry["sha256"] for entry in previous["files"]}
    new = {entry["path"]: entry["sha256"] for entry in scan(root)}
    return {
        "added": sorted(new.keys() - old.keys()),
        "removed": sorted(old.keys() - new.keys()),
        "modified": sorted(path for path in new.keys() & old.keys() if new[path] != old[path]),
    }
