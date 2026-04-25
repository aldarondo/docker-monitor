"""
Container status client.

Primary path (running as Docker container on NAS):
  Uses the Docker socket (/var/run/docker.sock) via the docker SDK.
  Mount the socket in docker-compose.yml: /var/run/docker.sock:/var/run/docker.sock

Fallback path (running in GitHub Actions):
  Reads container_status.json committed to this repo by the NAS container.
  Returns (None, error_message) if the file is missing or stale.
"""

import json
from datetime import datetime, timezone, timedelta

STATUS_STALE_HOURS = 2


def get_running_containers() -> list[dict]:
    """Query the local Docker daemon via socket. Returns list of {name, image, running}."""
    import docker as docker_sdk
    client = docker_sdk.from_env()
    containers = client.containers.list(all=True)
    return [
        {
            "name": c.name,
            "image": c.image.tags[0] if c.image.tags else c.image.id[:12],
            "running": c.status == "running",
        }
        for c in containers
    ]


def get_status_from_repo() -> tuple[list[dict] | None, str | None]:
    """
    Read container_status.json from the docker-monitor repo via GitHub API.
    Returns (containers, None) on success, or (None, error_message) on failure.
    """
    from . import github

    content, _ = github.get_file("aldarondo/docker-monitor", "container_status.json")
    if content is None:
        return None, "container_status.json not found — NAS container may not have run yet"

    data = json.loads(content)
    ts = datetime.fromisoformat(data["timestamp"])
    age = datetime.now(timezone.utc) - ts
    if age > timedelta(hours=STATUS_STALE_HOURS):
        hours = age.total_seconds() / 3600
        return None, f"container_status.json is {hours:.1f}h old (limit {STATUS_STALE_HOURS}h) — NAS container may have stopped"

    return data["containers"], None
