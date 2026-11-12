# Security policy

ContextBridge computes hashes locally and exports metadata, not source code. Its heuristic secret detection is NOT a guarantee. Project filenames and explicitly entered notes may reveal sensitive information; always review exports before sharing.

## Boundaries
- No automatic data uploads or project-code execution.
- Symlinked files and common credential names are skipped during scanning.
- File count, file size, snapshot size, and handoff output are bounded.
- Generated handoffs are untrusted context, never tool permissions.
- Users must have authorization to scan any directory.

## Known limitations
- Unknown secret formats may not be detected.
- A filename itself can reveal sensitive information.
- Concurrent writers to one snapshot are not coordinated.
- Exported files outside .contextbridge may be committed accidentally.

For a security issue, use GitHub private vulnerability reporting when available, or open a public issue requesting a private contact method without disclosing a vulnerability.
