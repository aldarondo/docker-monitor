"""
Check: do any workflow files contain known bad deploy patterns?

Flags repos where workflows still use:
  - appleboy/ssh-action (no Cloudflare Tunnel support, will fail)
  - hardcoded LAN IP 192.168.0. (unreachable from GitHub Actions runners)

These are proactive config checks — caught before a deploy run fails or times out.
"""

from lib import github, roadmap

CHECK = "bad-deploy-config"

BAD_PATTERNS = [
    ("appleboy/ssh-action", "uses appleboy/ssh-action — replace with cloudflared tunnel deploy"),
    ("192.168.0.", "hardcoded LAN IP — unreachable from GitHub Actions cloud runners"),
]


def run(entry: dict) -> None:
    repo = entry["repo"]
    print(f"  deploy-config: {repo}")

    paths = github.get_workflow_paths(repo)
    for path in paths:
        content = github.get_file_content(repo, path)
        if not content:
            continue
        for pattern, message in BAD_PATTERNS:
            if pattern in content:
                roadmap.write_blocked(
                    repo,
                    CHECK,
                    f"`{path}` contains `{pattern}` — {message}",
                )
                print(f"    bad pattern found: {pattern!r} in {path}")
                return

    roadmap.clear_blocked(repo, CHECK)
    print(f"    ok — no bad patterns found")
