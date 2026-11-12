# ContextBridge — Launch and Community Plan

## Audience and positioning
Developers switching between Codex, Claude Code, Copilot, and other coding assistants who lose project continuity.

**One-line pitch:** Stop re-explaining your project every time you switch coding assistants.

**Key difference:** ContextBridge exports a local, inspectable snapshot of your explicit status, decisions, next task, and file metadata—without requiring an AI account or reading private chat histories.

## Launch checklist
- [ ] Confirm GitHub Actions passes across Windows, Linux, and macOS.
- [ ] Run a real demonstration in an unrelated Python repository.
- [ ] Capture a short terminal demo or GIF (with only public/sample files).
- [ ] Check the repository's install instructions on Windows and Linux.
- [ ] Add accurate GitHub topics: ai-coding, cli, context-management, python, developer-tools, offline-first.
- [ ] Create a v0.2.0 release when tests are green.
- [ ] Enable GitHub Discussions or an issue template for feedback.
- [ ] Invite a handful of real users to try it; track bugs before adding major features.

## Where to introduce it
1. **GitHub:** Useful README, releases, changelog, and a short demo in the repository.
2. **Reddit:** Participate in relevant coding-agent communities only where self-promotion is allowed; describe what you built, its limits, and ask for criticism.
3. **Hacker News:** Consider a Show HN after the demo is strong and installs are reliable; answer technical questions transparently.
4. **Dev.to:** Publish a practical tutorial showing a safe Codex-to-Claude handoff using a sample project.
5. **Community discussions:** Answer existing context-handoff problems helpfully, mentioning ContextBridge only when relevant and permitted.

## Reusable introductory post
**Title:** ContextBridge: a free, offline CLI for carrying project context between AI coding assistants

I built ContextBridge because switching between coding assistants can mean re-explaining project progress and technical decisions. It saves a local snapshot of user-written status/decisions, tracks file hashes, and exports a reviewable Markdown or JSON handoff for Codex, Claude Code, or other assistants. It does not scrape conversations or upload code, and secret filtering is best-effort. I'd love feedback on what a useful handoff should include.

Repository: https://github.com/VORTEXXXX1886/contextbridge

## Success measures
- Real installation and test success rates.
- Reproducible user-reported problems fixed.
- Meaningful external issues and contributions.
- Verified examples showing reduced handoff setup work.

Do not buy stars, fabricate downloads or reviews, spam communities, or imply endorsements from AI vendors.
