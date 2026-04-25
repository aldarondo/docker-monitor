"""
Check: does the repo have all required GitHub Actions secrets for NAS deploy?

Required secrets for every GHCR repo:
  - NAS_SSH_PASSWORD  — NAS user password for sudo docker compose
  - CF_ACCESS_CLIENT_ID  — Cloudflare Access service token client ID
  - CF_ACCESS_CLIENT_SECRET  — Cloudflare Access service token secret

Secret values are never returned by the GitHub API — only names are checked.
If the PAT lacks secrets:read scope, returns an empty set (no false positives).
"""

from lib import github, roadmap

CHECK = "missing-deploy-secrets"

REQUIRED_SECRETS = [
    "NAS_SSH_PASSWORD",
    "CF_ACCESS_CLIENT_ID",
    "CF_ACCESS_CLIENT_SECRET",
]


def run(entry: dict) -> None:
    repo = entry["repo"]
    print(f"  deploy-secrets: {repo}")

    present = github.list_secrets(repo)
    if not present:
        # Empty set could mean 403 (insufficient scope) — skip rather than false-positive
        print("    skipped — could not read secrets (insufficient PAT scope?)")
        return

    missing = [s for s in REQUIRED_SECRETS if s not in present]
    if missing:
        roadmap.write_blocked(
            repo,
            CHECK,
            f"missing GitHub Actions secrets: {', '.join(missing)} — deploy will fail",
        )
        print(f"    missing: {missing}")
    else:
        roadmap.clear_blocked(repo, CHECK)
        print("    ok — all required secrets present")
