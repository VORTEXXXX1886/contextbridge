"""No-dependency CLI. Exit codes: 0=success, 1=changed, 2=error."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from .exporter import MAX_OUTPUT_CHARS, make_handoff
from .privacy import looks_sensitive
from .scanner import scan
from .store import compare_snapshot, create_snapshot, load_snapshot, snapshot_path

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="contextbridge", description="Offline project handoffs for AI coding assistants")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project directory")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Initialize a local project snapshot")
    scan_cmd = sub.add_parser("scan", help="Show safe metadata-only project manifest")
    scan_cmd.add_argument("--json", action="store_true", help="Output JSON instead of filenames")
    snap = sub.add_parser("snapshot", help="Update snapshot and optionally change progress fields")
    snap.add_argument("--note", default=None, help="Current status; omit to preserve previous value")
    snap.add_argument("--task", default=None, help="Next task; omit to preserve previous value")
    snap.add_argument("--decisions", default=None, help="Architectural decisions; omit to preserve previous value")
    exp = sub.add_parser("export", help="Print or save a portable handoff package")
    exp.add_argument("--target", choices=("generic", "codex", "claude"), default="generic")
    exp.add_argument("--format", choices=("markdown", "json"), default="markdown")
    exp.add_argument("--output", type=Path, help="Explicit output path; stdout otherwise")
    exp.add_argument("--max-chars", type=int, default=MAX_OUTPUT_CHARS)
    exp.add_argument("--strict", action="store_true", help="Refuse stale snapshots")
    check = sub.add_parser("check", help="Show changes since last snapshot")
    check.add_argument("--json", action="store_true")
    sub.add_parser("doctor", help="Check snapshot readiness and freshness")
    return parser

def _write_output(path: Path, content: str) -> None:
    path = path.expanduser().absolute()
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError("Refusing output through a symbolic link")
    if path.exists() and not path.is_file():
        raise ValueError("Output path is not a regular file")
    if path.exists():
        raise ValueError("Output already exists; choose a new path to avoid overwriting")
    path.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with path.open("x", encoding="utf-8") as f:
            created = True
            f.write(content)
    except Exception:
        # Never remove a file created by another writer between checks.
        if created:
            path.unlink(missing_ok=True)
        raise

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.expanduser().resolve()
    try:
        if not root.is_dir():
            raise ValueError("Project root must be an existing directory")
        if args.command == "init":
            if snapshot_path(root).exists():
                raise ValueError("Already initialized; use snapshot to update")
            create_snapshot(root)
            print("ContextBridge initialized. Review .contextbridge/snapshot.json before sharing.")
        elif args.command == "scan":
            files = scan(root)
            if args.json:
                print(json.dumps(files, indent=2))
            else:
                print("\n".join(entry["path"] for entry in files))
                print(f"{len(files)} files indexed", file=sys.stderr)
        elif args.command == "snapshot":
            create_snapshot(root, note=args.note, task=args.task, decisions=args.decisions)
            print("Snapshot saved locally")
        elif args.command in ("check", "doctor"):
            snapshot = load_snapshot(root)
            changes = compare_snapshot(root, snapshot)
            if args.command == "check":
                if args.json:
                    print(json.dumps(changes, indent=2))
                else:
                    for kind in ("added", "removed", "modified"):
                        print(f"{kind}: {', '.join(changes[kind]) if changes[kind] else '(none)'}")
                return 1 if any(changes.values()) else 0
            stale = any(changes.values())
            for key in ("note", "decisions", "next_task"):
                if looks_sensitive(snapshot[key]):
                    print(f"WARNING: possible secret in {key}")
            print(f"Snapshot: {'STALE' if stale else 'CURRENT'}")
            print(f"Files: {len(snapshot['files'])}; next task: {'set' if snapshot['next_task'] else 'missing'}")
            return 1 if stale else 0
        elif args.command == "export":
            snapshot = load_snapshot(root)
            changes = compare_snapshot(root, snapshot)
            if args.strict and any(changes.values()):
                raise ValueError("Snapshot stale; run 'contextbridge snapshot' first")
            content = make_handoff(snapshot, target=args.target, fmt=args.format,
                                   max_chars=args.max_chars, changes=changes)
            if args.output:
                _write_output(args.output, content)
                print(f"Saved {args.output.expanduser().absolute()}")
            else:
                print(content, end="")
        return 0
    except (OSError, ValueError, FileNotFoundError, KeyError, TypeError) as exc:
        print(f"contextbridge: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
