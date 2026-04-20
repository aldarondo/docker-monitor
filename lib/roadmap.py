"""
Read/write ROADMAP.md entries in remote GitHub repos via the GitHub API.

Entry format:  - ❌ [docker-monitor:<check>] <message> — <timestamp>

Update logic:
  - If an entry for the same check already exists in Blocked, replace it in-place.
  - If no entry exists, insert after the "## 🚫 Blocked" header.
  - clear_blocked() removes the entry when a check passes.
"""

import re
from datetime import datetime, timezone
from . import github

_BLOCKED_HEADER = "## 🚫 Blocked"
_PLACEHOLDER = "<!-- log blockers here -->"


def _pattern(check: str) -> re.Pattern:
    return re.compile(
        rf"^- [^\n]*\[docker-monitor:{re.escape(check)}\][^\n]*$",
        re.MULTILINE,
    )


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def write_blocked(repo: str, check: str, message: str) -> None:
    """Write or update a blocked entry in the repo's ROADMAP.md."""
    content, sha = github.get_file(repo, "ROADMAP.md")
    if content is None:
        print(f"    [skip] {repo}: no ROADMAP.md")
        return

    entry = f"- ❌ [docker-monitor:{check}] {message} — {_timestamp()}"
    pat = _pattern(check)

    if pat.search(content):
        updated = pat.sub(entry, content)
    elif _BLOCKED_HEADER in content:
        updated = content.replace(
            _BLOCKED_HEADER,
            f"{_BLOCKED_HEADER}\n{entry}",
            1,
        )
    else:
        updated = content.rstrip() + f"\n\n{_BLOCKED_HEADER}\n{entry}\n"

    if updated == content:
        print(f"    [unchanged] {repo}: {check}")
        return

    github.update_file(repo, "ROADMAP.md", updated, sha, f"chore: docker-monitor {check}")
    print(f"    [wrote] {repo}: {check}")


def clear_blocked(repo: str, check: str) -> None:
    """Remove a resolved blocked entry."""
    content, sha = github.get_file(repo, "ROADMAP.md")
    if content is None:
        return

    pat = _pattern(check)
    if not pat.search(content):
        return

    updated = pat.sub("", content)
    updated = re.sub(r"\n{3,}", "\n\n", updated)

    github.update_file(repo, "ROADMAP.md", updated, sha, f"chore: docker-monitor cleared {check}")
    print(f"    [cleared] {repo}: {check}")
