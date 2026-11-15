# Changelog

## 0.3.0 — 2026-11-15
- Add structured task statuses (`planned`, `in_progress`, `blocked`, `done`) and up to eight explicit next steps, preserving compatibility with schema-v1 snapshots from v0.2.
- Add opt-in `export --git` metadata: current Git revision, safe branch name, and dirty-tree flag. Never export Git diffs, remotes, commit messages, or Git file paths.
- Expand cross-platform tests for invalid input, legacy snapshots, sensitive branch metadata, and injection-resistant Markdown export.
- Add a reproducible Codex-to-Claude Code handoff walkthrough (from PR #2).

## 0.2.0 — 2026-11-12
- Preserve previous progress notes when refreshing only one field.
- Add doctor, JSON scan/change reports, freshness detection, and strict stale-export checks.
- Add snapshot validation, character budgets, and safe no-overwrite output.
- Expand regression tests and documentation.

## 0.1.0
- Initial offline scanner, snapshots, and Markdown/JSON handoffs.
