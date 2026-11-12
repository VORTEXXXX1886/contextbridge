# Example: Codex to Claude Code

A fictional project handoff workflow:

```bash
contextbridge init
contextbridge snapshot --note "CLI implemented and tested" --task "Add API error tests" --decisions "Keep offline mode available"
contextbridge export --target claude --strict --output handoff-claude.md
```

Review the output before sharing it with an authorized assistant. The assistant should verify the real repository state and ask for permission before acting. ContextBridge does not transmit data automatically.
