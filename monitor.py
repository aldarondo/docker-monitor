"""
docker-monitor — main entrypoint.

Runs on a daily schedule (APScheduler). On each tick:
1. Queries the Synology NAS for all running containers.
2. Cross-references config/containers.yaml to find monitored containers.
3. For GHCR containers: checks latest GitHub Actions run + weekly schedule trigger.
4. For non-GHCR aldarondo containers: flags GHCR migration needed.
5. Writes results to each project's ROADMAP.md via the GitHub API.

Environment variables required:
  GH_PAT     — GitHub Personal Access Token (needs repo + workflow scopes)

When running as a Docker container on the NAS, mount the Docker socket:
  volumes: [/var/run/docker.sock:/var/run/docker.sock]

When running in GitHub Actions, no NAS access is needed — the container
pushes container_status.json to the repo, and GitHub Actions reads it.

Set RUN_ONCE=true to run a single check and exit (useful for testing).
"""

import os
import yaml
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from lib import synology
from checks import deploy_status, weekly_schedule, ghcr_migration, container_status, deploy_config, deploy_secrets

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "containers.yaml")


def load_config() -> list[dict]:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)["containers"]


def _load_container_status() -> set[str] | None:
    """
    Get container running-state.

    Strategy:
    1. Direct Synology API query (works when running as Docker container on NAS).
       On success, also pushes container_status.json to the repo so GitHub Actions
       can use it as a fallback.
    2. Repo file fallback — container_status.json committed by the NAS container.
       Used when running in GitHub Actions (no LAN access).

    Returns set of running container names, or None if both sources are unavailable.
    Errors are written to docker-monitor's own ROADMAP.md.
    """
    if os.path.exists("/var/run/docker.sock"):
        try:
            live = synology.get_running_containers()
            running = {c["name"] for c in live if c["running"]}
            print(f"Container status from Docker socket: {len(running)} running")
            _push_container_status(live)  # keep repo file fresh for GitHub Actions
            container_status.clear_nas_error()
            return running
        except Exception as exc:
            print(f"  Docker socket query failed: {exc} — trying repo file")

    containers, error = synology.get_status_from_repo()
    if error:
        print(f"  NAS status error: {error}")
        container_status.write_nas_error(error)
        return None
    container_status.clear_nas_error()
    running = {c["name"] for c in containers if c["running"]}
    print(f"Container status from repo file: {len(running)} running")
    return running


def _push_container_status(containers: list[dict]) -> None:
    """Commit container_status.json to the repo so GitHub Actions can use it."""
    import json
    from datetime import datetime, timezone
    from lib import github

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "containers": containers,
    }
    content = json.dumps(payload, indent=2) + "\n"
    _, sha = github.get_file("aldarondo/docker-monitor", "container_status.json")
    try:
        github.update_file(
            "aldarondo/docker-monitor", "container_status.json",
            content, sha, "chore: update container status"
        )
        print(f"  Pushed container_status.json ({len(containers)} containers)")
    except Exception as exc:
        print(f"  Warning: failed to push container_status.json: {exc}")


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
                deploy_config.run(entry)
                deploy_secrets.run(entry)
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
