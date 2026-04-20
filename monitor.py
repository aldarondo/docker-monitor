"""
docker-monitor — main entrypoint.

Runs on a daily schedule (APScheduler). On each tick:
1. Queries the Synology NAS for all running containers.
2. Cross-references config/containers.yaml to find monitored containers.
3. For GHCR containers: checks latest GitHub Actions run + weekly schedule trigger.
4. For non-GHCR aldarondo containers: flags GHCR migration needed.
5. Writes results to each project's ROADMAP.md via the GitHub API.

Environment variables required:
  NAS_HOST   — e.g. http://192.168.0.64:5000
  NAS_USER   — Synology username
  NAS_PASS   — Synology password
  GH_PAT     — GitHub Personal Access Token (needs repo + workflow scopes)

Set RUN_ONCE=true to run a single check and exit (useful for testing).
"""

import os
import yaml
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from lib import synology
from checks import deploy_status, weekly_schedule, ghcr_migration

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "containers.yaml")


def load_config() -> list[dict]:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)["containers"]


def _get_running_containers() -> set[str] | None:
    """
    Query Synology for running container names.
    Returns None if NAS credentials are absent or the NAS is unreachable,
    which causes all configured containers to be treated as running.
    """
    if not os.environ.get("NAS_HOST"):
        print("NAS_HOST not set — skipping live container filter, checking all configured repos")
        return None
    try:
        live = synology.get_running_containers()
        names = {c["name"] for c in live if c["running"]}
        print(f"Running containers on NAS: {len(names)}")
        return names
    except Exception as exc:
        print(f"Warning: Synology query failed ({exc}) — checking all configured repos")
        return None


def run_checks() -> None:
    print("=== docker-monitor run ===")
    entries = load_config()
    running = _get_running_containers()  # None = check all

    seen_repos: set[str] = set()

    for entry in entries:
        name = entry["name"]
        repo = entry["repo"]
        needs_migration = entry.get("ghcr_migration_needed", False)

        if running is not None and name not in running:
            print(f"\n[{name}] not running — skipping")
            continue

        print(f"\n[{name}]")

        if needs_migration:
            ghcr_migration.run(entry)
        else:
            if repo not in seen_repos:
                deploy_status.run(entry)
                weekly_schedule.run(entry)
                seen_repos.add(repo)
            else:
                print(f"  {repo} already checked this run")

    print("\n=== done ===")


def main() -> None:
    if os.environ.get("RUN_ONCE", "").lower() == "true":
        run_checks()
        return

    scheduler = BlockingScheduler()
    scheduler.add_job(run_checks, CronTrigger(hour=8, minute=0, timezone="UTC"))
    print("docker-monitor started — runs daily at 08:00 UTC")
    run_checks()  # immediate first run on startup
    scheduler.start()


if __name__ == "__main__":
    main()
