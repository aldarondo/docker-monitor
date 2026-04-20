"""
Check: is a configured container actually running on the NAS?
Writes a container-stopped Blocked entry if the container is present in
container_status.json but not running.
"""

from lib import roadmap

CHECK = "container-stopped"
NAS_CHECK = "nas-status-stale"
SELF_REPO = "aldarondo/docker-monitor"


def write_nas_error(message: str) -> None:
    """Write NAS unreachable/stale to docker-monitor's own ROADMAP."""
    roadmap.write_blocked(SELF_REPO, NAS_CHECK, message)


def clear_nas_error() -> None:
    roadmap.clear_blocked(SELF_REPO, NAS_CHECK)


def run(entry: dict, running_names: set[str]) -> None:
    name = entry["name"]
    repo = entry["repo"]

    if name not in running_names:
        print(f"  container-status: {name} — STOPPED")
        roadmap.write_blocked(
            repo,
            CHECK,
            f"Container `{name}` is not running on the NAS — check `docker logs {name}` and restart",
        )
    else:
        roadmap.clear_blocked(repo, CHECK)
        print(f"  container-status: {name} — running OK")
