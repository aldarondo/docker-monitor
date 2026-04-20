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
from checks import deploy_status, weekly_schedule, ghcr_migration, container_status

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "containers.yaml")


def load_config() -> list[dict]:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)["containers"]


def _load_container_status() -> set[str] | None:
    """
    Read container running-state from the repo-committed status file.
    Returns set of running container names, or None if unavailable (stale/missing).
    Errors are written to docker-monitor's own ROADMAP.md.
    """
    containers, error = synology.get_status_from_repo()
    if error:
        print(f"  NAS status error: {error}")
        container_status.write_nas_error(error)
        return None
    container_status.clear_nas_error()
    running = {c["name"] for c in containers if c["running"]}
    print(f"Container status loaded from repo: {len(running)} running")
    return running


def run_checks() -> None:
    print("=== docker-monitor run ===")
    entries = load_config()
    running = _load_container_status()  # None if status unavailable

    seen_repos: set[str] = set()

    for entry in entries:
        name = entry["name"]
        repo = entry["repo"]
        needs_migration = entry.get("ghcr_migration_needed", False)

        print(f"\n[{name}]")

        # Always run container-stopped check when we have live status
        if running is not None:
            container_status.run(entry, running)
            if name not in running:
                continue  # stopped container: skip deploy/schedule checks

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
