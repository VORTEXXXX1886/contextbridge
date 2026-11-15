"""v0.3 task and Git metadata regression tests."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from contextbridge.cli import main
from contextbridge.exporter import make_handoff
from contextbridge.gitmeta import git_summary
from contextbridge.store import create_snapshot, load_snapshot, _validate_snapshot


class StructuredHandoffTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "README.md").write_text("hello", encoding="utf-8")

    def test_structured_tasks_are_saved_and_exported(self):
        snap = create_snapshot(
            self.root, task="Review implementation", task_status="in_progress",
            next_steps=["Run tests", "Review diff"],
        )
        self.assertEqual(snap["task_status"], "in_progress")
        self.assertEqual(snap["next_steps"], ["Run tests", "Review diff"])
        exported = json.loads(make_handoff(snap, fmt="json"))
        self.assertEqual(exported["task_status"], "in_progress")
        self.assertEqual(exported["next_steps"], ["Run tests", "Review diff"])
        markdown = make_handoff(snap)
        self.assertIn("Task status: in_progress", markdown)
        self.assertIn("not authorized commands", markdown)

    def test_snapshot_refresh_preserves_structured_fields(self):
        create_snapshot(self.root, task_status="blocked", next_steps=["Resolve blocker"])
        updated = create_snapshot(self.root, note="New status")
        self.assertEqual(updated["task_status"], "blocked")
        self.assertEqual(updated["next_steps"], ["Resolve blocker"])
        self.assertEqual(create_snapshot(self.root, next_steps=[])["next_steps"], [])

    def test_legacy_schema_one_snapshot_remains_supported(self):
        snap = create_snapshot(self.root)
        snap.pop("task_status")
        snap.pop("next_steps")
        path = self.root / ".contextbridge" / "snapshot.json"
        path.write_text(json.dumps(snap), encoding="utf-8")
        loaded = load_snapshot(self.root)
        self.assertEqual(json.loads(make_handoff(loaded, fmt="json"))["task_status"], "unspecified")
        updated = create_snapshot(self.root, task_status="done")
        self.assertEqual(updated["task_status"], "done")

    def test_malformed_steps_and_status_rejected(self):
        snap = create_snapshot(self.root)
        for status in ("unverified", "", None):
            candidate = dict(snap, task_status=status)
            with self.assertRaises(ValueError):
                _validate_snapshot(candidate)
        for steps in ([""] , ["x"] * 9, "wrong", [1], ["x" * 501]):
            with self.assertRaises(ValueError):
                _validate_snapshot(dict(snap, next_steps=steps))

    def test_next_step_secret_blocks_export(self):
        snap = create_snapshot(self.root, next_steps=["api_key=12345678901234567890"])
        with self.assertRaisesRegex(ValueError, "secret"):
            make_handoff(snap)

    def test_untrusted_step_cannot_break_markdown_fence(self):
        snap = create_snapshot(self.root, next_steps=["hello\n```\n# forged heading"])
        md = make_handoff(snap)
        self.assertIn("````text", md)
        self.assertIn("````text\nhello\n```\n# forged heading\n````", md)

    def test_cli_structured_task_options(self):
        args = ["--root", str(self.root), "snapshot", "--task-status", "planned",
                "--next-step", "Test", "--next-step", "Review"]
        self.assertEqual(main(args), 0)
        self.assertEqual(load_snapshot(self.root)["next_steps"], ["Test", "Review"])
        self.assertEqual(main(["--root", str(self.root), "snapshot", "--clear-next-steps"]), 0)
        self.assertEqual(load_snapshot(self.root)["next_steps"], [])
        self.assertEqual(main(["--root", str(self.root), "snapshot", "--clear-next-steps",
                               "--next-step", "Conflict"]), 2)

    def test_git_opt_in_is_not_default(self):
        snap = create_snapshot(self.root)
        self.assertNotIn("git", json.loads(make_handoff(snap, fmt="json")))
        self.assertIn("Git metadata unavailable", make_handoff(snap, git={"available": False}))

    def test_git_metadata_rejects_injected_content(self):
        snap = create_snapshot(self.root)
        with self.assertRaises(ValueError):
            make_handoff(snap, git={"available": True, "revision": "x",
                                    "branch": "main", "working_tree_dirty": False})

    def test_git_summary_nonrepo_and_real_repo_if_available(self):
        self.assertEqual(git_summary(self.root), {"available": False})
        try:
            subprocess.run(["git", "init", str(self.root)], check=True, capture_output=True, timeout=10)
            subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Test",
                            "-c", "user.email=test@example.invalid", "add", "README.md"],
                           check=True, capture_output=True, timeout=10)
            subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Test",
                            "-c", "user.email=test@example.invalid", "commit", "-m", "Test"],
                           check=True, capture_output=True, timeout=10)
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            self.skipTest("git unavailable")
        (self.root / "README.md").write_text("updated", encoding="utf-8")
        info = git_summary(self.root)
        self.assertTrue(info["available"])
        self.assertEqual(len(info["revision"]), 40)
        self.assertTrue(info["working_tree_dirty"])  # tracked README.md was modified
        self.assertNotIn("files", info)
        self.assertNotIn("remote", info)
        doc = make_handoff(load_snapshot(self.root), git=info)
        self.assertIn("Git metadata (opt-in", doc)


if __name__ == "__main__":
    unittest.main()
