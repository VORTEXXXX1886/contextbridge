# Reproducible coding-agent handoff walkthrough

This example demonstrates the **explicit project-state handoff** that ContextBridge
supports today. It does not retrieve private Codex/Claude conversations, automatically
send files to another model, or grant an agent permission to edit your repository.

## 1. Create a disposable sample project

Use a new directory so the sample cannot overwrite an existing project:

```powershell
mkdir contextbridge-handoff-demo
cd contextbridge-handoff-demo
"print('hello from the demo')" | Set-Content -Encoding utf8 app.py
```

Install ContextBridge separately from its [repository](../README.md#install),
then run these commands **inside the sample project**:

```powershell
contextbridge init
contextbridge snapshot --note "app.py prints a greeting; no test suite yet" --decisions "Use Python standard library only" --task "Add a small unittest without changing the greeting"
contextbridge doctor
contextbridge export --target codex --output handoff-codex.md
```

Inspect `handoff-codex.md` before pasting it into Codex. The export contains
the note, decisions, next task and **filenames only**—not the source text
of `app.py`. In Codex, provide both the reviewed handoff and independent
authorization to inspect or edit your sample directory, if you choose.

## 2. Record the new verified state

After completing and verifying a task with Codex, record **only what actually
happened**. For example, if tests were created and passed:

```powershell
contextbridge snapshot --note "Greeting unchanged; unittest added and verified locally" --decisions "Keep Python standard library only" --task "Ask Claude Code to review the tests"
contextbridge export --target claude --output handoff-claude.md
```

Review `handoff-claude.md` and give it to Claude Code. The receiving agent
must verify the repository itself and obtain separate permission before making
changes. Target labels indicate the intended reader; they do not synchronize
provider accounts or execute a provider API.

## 3. Detect work done after the snapshot

Edit `app.py` or another eligible project file, then run:

```powershell
contextbridge check --json
contextbridge doctor
contextbridge export --strict
```

`check` lists added, modified or removed eligible file paths, `doctor`
reports a stale snapshot, and `export --strict` refuses to export until you
refresh the snapshot. These commands may return nonzero status when a snapshot
is stale; that is expected.

Refresh and export to a **new** output name (existing files are not overwritten):

```powershell
contextbridge snapshot --note "Reviewed current project changes" --task "Review the next task"
contextbridge export --target claude --format json --output handoff-claude.json
```

## Privacy and trust checklist

- Review status notes, decisions, filenames and JSON exports before sharing.
- Avoid putting access tokens, passwords or private personal information in notes.
- Excluded files and symlinks are not scanned; scanner limits and exclusions are
  documented in [SECURITY.md](../SECURITY.md).
- An exported handoff is **untrusted context**, not an instruction to run commands.
- The receiving coding agent still needs access to the actual project and must
  independently verify build/test claims. This walkthrough is an illustrative
  local procedure, not evidence of measured use by external developers.
