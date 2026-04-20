"""
Synology Docker API client — lists running containers from inside the NAS network.
Auth pattern mirrors claude-synology/lib/auth.py; keep in sync if DSM auth changes.
Credentials come from env vars (NAS_HOST, NAS_USER, NAS_PASS).

Primary usage from GitHub Actions: call get_status_from_repo() which reads the
container_status.json file committed by scripts/push_status.py (runs on NAS hourly).
Direct API calls (get_running_containers) work only when run on the LAN.
"""

import json
import os
from datetime import datetime, timezone, timedelta

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

STATUS_STALE_HOURS = 2  # flag nas-status-stale if file older than this


def get_status_from_repo() -> tuple[list[dict] | None, str | None]:
    """
    Read container_status.json from the docker-monitor repo via GitHub API.
    Returns (containers, error_message).
    containers is None and error_message is set if the file is missing or stale.
    """
    from . import github  # avoid circular import at module level

    content, _ = github.get_file("aldarondo/docker-monitor", "container_status.json")
    if content is None:
        return None, "container_status.json not found in repo — run scripts/push_status.py on the NAS to create it"

    data = json.loads(content)
    ts = datetime.fromisoformat(data["timestamp"])
    age = datetime.now(timezone.utc) - ts
    if age > timedelta(hours=STATUS_STALE_HOURS):
        hours = age.total_seconds() / 3600
        return None, f"container_status.json is {hours:.1f}h old (limit {STATUS_STALE_HOURS}h) — NAS push script may not be running"

    return data["containers"], None


def _login(host, user, password):
    resp = requests.post(
        f"{host}/webapi/auth.cgi",
        data={
            "api": "SYNO.API.Auth",
            "version": "3",
            "method": "login",
            "account": user,
            "passwd": password,
            "session": "DockerMonitor",
            "format": "sid",
        },
        verify=False,
        timeout=10,
    )
    resp.raise_for_status()
    result = resp.json()
    if not result.get("success"):
        raise RuntimeError(f"Synology auth failed: {result.get('error')}")
    return result["data"]["sid"]


def _logout(host, sid):
    try:
        requests.post(
            f"{host}/webapi/auth.cgi",
            data={
                "api": "SYNO.API.Auth",
                "version": "3",
                "method": "logout",
                "session": "DockerMonitor",
                "_sid": sid,
            },
            verify=False,
            timeout=5,
        )
    except Exception:
        pass


def get_running_containers() -> list[dict]:
    """Return list of {name, image, running} for all containers on the NAS."""
    host = os.environ["NAS_HOST"].rstrip("/")
    user = os.environ["NAS_USER"]
    password = os.environ["NAS_PASS"]

    sid = _login(host, user, password)
    try:
        resp = requests.get(
            f"{host}/webapi/entry.cgi",
            params={
                "api": "SYNO.Docker.Container",
                "version": "1",
                "method": "list",
                "limit": 200,
                "offset": 0,
                "_sid": sid,
            },
            verify=False,
            timeout=10,
        )
        resp.raise_for_status()
        containers = resp.json().get("data", {}).get("containers", [])
        return [
            {
                "name": c.get("name", ""),
                "image": c.get("image", ""),
                "running": c.get("State", {}).get("Running", False),
            }
            for c in containers
        ]
    finally:
        _logout(host, sid)
