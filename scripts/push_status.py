"""
push_status.py — standalone script that queries the Docker daemon via socket
and commits container_status.json to the docker-monitor repo.

Can be run:
  - From inside the docker-monitor container (socket mounted at /var/run/docker.sock)
  - Via `docker exec docker-monitor python scripts/push_status.py`

Environment variable required:
  GH_PAT  — GitHub PAT (repo + contents:write scope)
"""

import base64
import json
import os
import sys

# Allow running from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.synology import get_running_containers
from lib import github
from datetime import datetime, timezone


REPO = os.environ.get("GH_REPO", "aldarondo/docker-monitor")
FILE_PATH = "container_status.json"


def push_status() -> None:
    containers = get_running_containers()
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "containers": containers,
    }
    content = json.dumps(payload, indent=2) + "\n"
    _, sha = github.get_file(REPO, FILE_PATH)
    github.update_file(REPO, FILE_PATH, content, sha, "chore: update container status")
    print(f"Pushed {len(containers)} containers ({sum(1 for c in containers if c['running'])} running)")


if __name__ == "__main__":
    push_status()
