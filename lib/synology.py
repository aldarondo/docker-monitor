"""
Synology Docker API client — lists running containers from inside the NAS network.
Auth pattern mirrors claude-synology/lib/auth.py; keep in sync if DSM auth changes.
Credentials come from env vars (NAS_HOST, NAS_USER, NAS_PASS).
"""

import os
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
