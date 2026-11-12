"""Focused regression tests for the final code audit."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from contextbridge.cli import _write_output
from contextbridge.exporter import make_handoff
from contextbridge.scanner import scan
from contextbridge.store import create_snapshot


class FinalAuditRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "README.md").write_text("ok", encoding="utf-8")

    def test_exclusive_open_race_preserves_other_writer(self):
        output = self.root / "out.md"
        original_open = Path.open

        def race_open(path, *args, **kwargs):
            if path == output and args and args[0] == "x":
                output.write_text("another process", encoding="utf-8")
                raise FileExistsError("concurrent creation")
            return original_open(path, *args, **kwargs)

        with patch.object(Path, "open", autospec=True, side_effect=race_open):
            with self.assertRaises(FileExistsError):
                _write_output(output, "our content")
        self.assertEqual(output.read_text(encoding="utf-8"), "another process")

    def test_markdown_note_cannot_end_fence(self):
        snapshot = create_snapshot(self.root, note="hello\n```\n# forged heading")
        handoff = make_handoff(snapshot)
        self.assertIn("````text\nhello\n```\n# forged heading\n````", handoff)

    def test_newlines_in_filename_are_escaped(self):
        snapshot = create_snapshot(self.root)
        snapshot["files"].append({"path": "bad\n# forged heading", "sha256": "a" * 64, "size": 1})
        handoff = make_handoff(snapshot)
        self.assertIn('"bad\\n# forged heading"', handoff)
        self.assertNotIn("\n# forged heading\n", handoff)

    def test_scan_refuses_truncated_manifest(self):
        import contextbridge.scanner as scanner
        (self.root / "a.py").write_text("x", encoding="utf-8")
        with patch.object(scanner, "MAX_FILES", 1):
            with self.assertRaisesRegex(ValueError, "incomplete scan"):
                scan(self.root)

    def test_excluded_directory_case_insensitive(self):
        hidden = self.root / ".VENV"
        hidden.mkdir()
        (hidden / "file.py").write_text("private", encoding="utf-8")
        self.assertNotIn(".VENV/file.py", [item["path"] for item in scan(self.root)])


if __name__ == "__main__":
    unittest.main()
