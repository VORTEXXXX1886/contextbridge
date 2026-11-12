"""Conservative filename and note safeguards (not a DLP guarantee)."""
from __future__ import annotations

import fnmatch
import re
from pathlib import Path

BLOCKED_DIRS = frozenset({
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "__pycache__",
    ".tox", ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build",
    ".idea", ".vscode", ".ssh", ".aws", ".gnupg", ".kube",
    ".terraform", ".contextbridge", "proton_session_vault",
})
BLOCKED_NAMES = frozenset({
    ".env", ".npmrc", ".pypirc", ".netrc", "id_rsa", "id_ed25519",
    "credentials", "credentials.json", "secrets.json", "secrets.yaml", "secrets.yml",
    "config.json.enc", "token.json", "known_hosts", ".git-credentials",
})
BLOCKED_EXTENSIONS = frozenset({
    ".pem", ".key", ".p12", ".pfx", ".jks", ".keystore", ".sqlite",
    ".sqlite3", ".db", ".env", ".age", ".gpg", ".asc",
})
SECRET_PATTERNS = [
    re.compile(r"(?i)-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
    re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|secret[_-]?key|password)\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
]

def safe_relative(path: Path, root: Path) -> Path | None:
    """Reject symlinked paths, sensitive names, and paths escaping root."""
    try:
        rel = path.absolute().relative_to(root.absolute())
    except ValueError:
        return None
    if not rel.parts or path.is_symlink():
        return None
    if any(part.lower() in BLOCKED_DIRS or part == ".." or part.lower().startswith(".env") for part in rel.parts):
        return None
    name = rel.name.lower()
    if name in BLOCKED_NAMES or path.suffix.lower() in BLOCKED_EXTENSIONS:
        return None
    if any(fnmatch.fnmatch(name, pattern) for pattern in ("*secret*", "*credential*", "*token*", "*.bak")):
        return None
    return rel

def looks_sensitive(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)
