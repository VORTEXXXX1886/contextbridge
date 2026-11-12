"""Regression tests for ContextBridge."""
import json
import tempfile
import unittest
from pathlib import Path
from contextbridge.cli import main
from contextbridge.exporter import make_handoff
from contextbridge.scanner import scan
from contextbridge.store import create_snapshot, load_snapshot, compare_snapshot

class ContextBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "README.md").write_text("hello", encoding="utf-8")

    def test_scan_excludes_secrets(self):
        (self.root / ".env").write_text("SECRET=private", encoding="utf-8")
        (self.root / "id_rsa").write_text("private", encoding="utf-8")
        self.assertEqual([e["path"] for e in scan(self.root)], ["README.md"])

    def test_symlink_excluded(self):
        outside = self.root.parent / "contextbridge-outside-test.txt"
        outside.write_text("not allowed", encoding="utf-8")
        self.addCleanup(lambda: outside.unlink(missing_ok=True))
        try:
            (self.root / "link.txt").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable")
        self.assertNotIn("link.txt", [e["path"] for e in scan(self.root)])

    def test_snapshot_changes(self):
        snap = create_snapshot(self.root, note="Status", task="Review")
        self.assertFalse(any(compare_snapshot(self.root, snap).values()))
        (self.root / "README.md").write_text("updated", encoding="utf-8")
        self.assertEqual(compare_snapshot(self.root, snap)["modified"], ["README.md"])

    def test_snapshot_preserves_notes(self):
        create_snapshot(self.root, note="done", decisions="offline", task="old")
        updated = create_snapshot(self.root, task="next")
        self.assertEqual(updated["note"], "done")
        self.assertEqual(updated["decisions"], "offline")
        self.assertEqual(updated["next_task"], "next")

    def test_snapshot_can_clear_note(self):
        create_snapshot(self.root, note="old")
        self.assertEqual(create_snapshot(self.root, note="")["note"], "")

    def test_handoff_formats(self):
        snap = create_snapshot(self.root, note="Status", decisions="Keep offline")
        self.assertIn("Keep offline", make_handoff(snap, target="claude"))
        self.assertEqual(json.loads(make_handoff(snap, fmt="json"))["files"], ["README.md"])

    def test_export_blocks_secrets(self):
        snap = create_snapshot(self.root, note="api_key=12345678901234567890")
        with self.assertRaises(ValueError):
            make_handoff(snap)

    def test_source_contents_not_exported(self):
        (self.root / "main.py").write_text("VERY_PRIVATE_SOURCE_CONTENT", encoding="utf-8")
        export = make_handoff(create_snapshot(self.root))
        self.assertNotIn("VERY_PRIVATE_SOURCE_CONTENT", export)
        self.assertIn("main.py", export)

    def test_export_stale_and_strict(self):
        snap = create_snapshot(self.root)
        (self.root / "README.md").write_text("changed", encoding="utf-8")
        changes = compare_snapshot(self.root, snap)
        data = json.loads(make_handoff(snap, fmt="json", changes=changes))
        self.assertEqual(data["freshness"], "stale")
        self.assertEqual(main(["--root", str(self.root), "export", "--strict"]), 2)

    def test_no_overwrite(self):
        create_snapshot(self.root)
        dest = self.root / "handoff.md"
        dest.write_text("keep", encoding="utf-8")
        self.assertEqual(main(["--root", str(self.root), "export", "--output", str(dest)]), 2)
        self.assertEqual(dest.read_text(encoding="utf-8"), "keep")

    def test_symlink_output_directory_refused(self):
        create_snapshot(self.root)
        try:
            (self.root / "linkdir").symlink_to(self.root.parent, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable")
        self.assertEqual(main(["--root", str(self.root), "export", "--output", str(self.root / "linkdir" / "x.md")]), 2)

    def test_malformed_snapshot(self):
        create_snapshot(self.root)
        p = self.root / ".contextbridge" / "snapshot.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        data["files"] = [{"path": "../outside", "sha256": "0"*64, "size": 1}]
        p.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_snapshot(self.root)

    def test_export_budget(self):
        snap = create_snapshot(self.root)
        with self.assertRaises(ValueError):
            make_handoff(snap, max_chars=499)
        snap["note"] = "x"*900
        with self.assertRaises(ValueError):
            make_handoff(snap, max_chars=500)

    def test_json_commands_and_doctor(self):
        self.assertEqual(main(["--root", str(self.root), "scan", "--json"]), 0)
        self.assertEqual(main(["--root", str(self.root), "init"]), 0)
        self.assertEqual(main(["--root", str(self.root), "doctor"]), 0)
        (self.root / "new.py").write_text("pass", encoding="utf-8")
        self.assertEqual(main(["--root", str(self.root), "check", "--json"]), 1)
        self.assertEqual(main(["--root", str(self.root), "doctor"]), 1)

    def test_case_insensitive_sensitive_extension(self):
        (self.root / "private.PEM").write_text("key", encoding="utf-8")
        self.assertNotIn("private.PEM", [e["path"] for e in scan(self.root)])

    def test_cli_init_check(self):
        self.assertEqual(main(["--root", str(self.root), "init"]), 0)
        self.assertEqual(main(["--root", str(self.root), "check"]), 0)
        (self.root / "new.py").write_text("pass", encoding="utf-8")
        self.assertEqual(main(["--root", str(self.root), "check"]), 1)

if __name__ == "__main__":
    unittest.main()
