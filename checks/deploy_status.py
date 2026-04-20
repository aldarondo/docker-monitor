"""
Check: did the latest GitHub Actions workflow run succeed?
Writes a Blocked entry to the project's ROADMAP.md on failure; clears it on success.
Skips repos whose latest run is still in_progress or queued.
"""

from lib import github, roadmap

CHECK = "deploy-failed"


def run(entry: dict) -> None:
    repo = entry["repo"]
    print(f"  deploy-status: {repo}")

    run_data = github.get_latest_workflow_run(repo)
    if not run_data:
        print(f"    no workflow runs found — skipping")
        return

    status = run_data.get("status", "")
    conclusion = run_data.get("conclusion", "")
    run_id = run_data.get("id", "?")
    url = run_data.get("html_url", "")

    if status in ("in_progress", "queued", "waiting"):
        print(f"    run #{run_id} still {status} — skipping")
        return

    if conclusion == "failure":
        roadmap.write_blocked(
            repo,
            CHECK,
            f"GitHub Actions deploy failed (run #{run_id}) — {url}",
        )
    elif conclusion == "success":
        roadmap.clear_blocked(repo, CHECK)
        print(f"    run #{run_id} OK")
    else:
        print(f"    run #{run_id}: conclusion={conclusion!r} — skipping")
