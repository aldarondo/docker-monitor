"""
Runs on the NAS as a Synology Task Scheduler job (every hour).
Queries the local Synology Docker API, then commits container_status.json
to the docker-monitor repo via the GitHub API.

Uses only Python stdlib — no pip install required.

Environment variables (set in Task Scheduler user-defined scripts or .env):
  NAS_HOST  — default http://192.168.0.64:5000
  NAS_USER  — Synology username
  NAS_PASS  — Synology password
  GH_PAT    — GitHub PAT (repo + contents:write scope)
  GH_REPO   — target repo, default aldarondo/docker-monitor
"""

import base64
import json
import os
import ssl
import urllib.request
from datetime import datetime, timezone

NAS_HOST = os.environ.get("NAS_HOST", "http://192.168.0.64:5000").rstrip("/")
NAS_USER = os.environ["NAS_USER"]
NAS_PASS = os.environ["NAS_PASS"]
GH_PAT = os.environ["GH_PAT"]
REPO = os.environ.get("GH_REPO", "aldarondo/docker-monitor")
FILE_PATH = "container_status.json"

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


def _post(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, context=_SSL_CTX, timeout=10) as r:
        return json.loads(r.read())


def _get(url: str) -> dict:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, context=_SSL_CTX, timeout=10) as r:
        return json.loads(r.read())


def _gh_request(method: str, path: str, body: dict | None = None) -> dict:
    url = f"https://api.github.com/repos/{REPO}/{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {GH_PAT}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {}
        raise


def _login() -> str:
    import urllib.parse
    result = _post(
        f"{NAS_HOST}/webapi/auth.cgi",
        {
            "api": "SYNO.API.Auth",
            "version": "3",
            "method": "login",
            "account": NAS_USER,
            "passwd": NAS_PASS,
            "session": "StatusPush",
            "format": "sid",
        },
    )
    if not result.get("success"):
        raise RuntimeError(f"Synology auth failed: {result.get('error')}")
    return result["data"]["sid"]


def _logout(sid: str) -> None:
    import urllib.parse
    try:
        _post(
            f"{NAS_HOST}/webapi/auth.cgi",
            {"api": "SYNO.API.Auth", "version": "3", "method": "logout",
             "session": "StatusPush", "_sid": sid},
        )
    except Exception:
        pass


def _get_containers(sid: str) -> list[dict]:
    import urllib.parse
    params = urllib.parse.urlencode({
        "api": "SYNO.Docker.Container",
        "version": "1",
        "method": "list",
        "limit": "200",
        "offset": "0",
        "_sid": sid,
    })
    data = _get(f"{NAS_HOST}/webapi/entry.cgi?{params}")
    return data.get("data", {}).get("containers", [])


def push_status() -> None:
    sid = _login()
    try:
        raw = _get_containers(sid)
    finally:
        _logout(sid)

    containers = [
        {
            "name": c.get("name", ""),
            "image": c.get("image", ""),
            "running": c.get("State", {}).get("Running", False),
        }
        for c in raw
    ]

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "containers": containers,
    }
    content = json.dumps(payload, indent=2) + "\n"
    encoded = base64.b64encode(content.encode()).decode()

    existing = _gh_request("GET", f"contents/{FILE_PATH}")
    sha = existing.get("sha")

    body: dict = {"message": "chore: update container status", "content": encoded}
    if sha:
        body["sha"] = sha

    _gh_request("PUT", f"contents/{FILE_PATH}", body)
    print(f"Pushed {len(containers)} containers ({sum(1 for c in containers if c['running'])} running)")


if __name__ == "__main__":
    import urllib.parse  # used by _post/_login
    push_status()
