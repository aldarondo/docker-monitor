"""
Check: does the repo have at least one GitHub Actions workflow with a schedule: trigger?
Flags repos that lack a weekly cron for dependency rebuilds.
"""

from lib import github, roadmap

CHECK = "no-weekly-schedule"


def run(entry: dict) -> None:
    repo = entry["repo"]
    print(f"  weekly-schedule: {repo}")

    paths = github.get_workflow_paths(repo)
    if not paths:
        roadmap.write_blocked(
            repo,
            CHECK,
            "No GitHub Actions workflows found — add a workflow with a `schedule:` trigger for weekly dependency rebuilds",
        )
        return

    for path in paths:
        content = github.get_file_content(repo, path)
        if content and "schedule:" in content:
            roadmap.clear_blocked(repo, CHECK)
            print(f"    schedule: found in {path}")
            return

    roadmap.write_blocked(
        repo,
        CHECK,
        "No `schedule:` trigger found in any workflow — add a weekly cron to auto-rebuild with latest dependencies",
    )
