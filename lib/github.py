"""
GitHub REST API client. All calls use GITHUB_PAT env var.
"""

import base64
import os
import httpx


def _client() -> httpx.Client:
    return httpx.Client(
        headers={
            "Authorization": f"Bearer {os.environ['GH_PAT']}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=15,
    )


def get_latest_workflow_run(repo: str) -> dict | None:
    """Latest workflow run across all workflows for a repo."""
    with _client() as client:
        resp = client.get(
            f"https://api.github.com/repos/{repo}/actions/runs",
            params={"per_page": 1},
        )
        resp.raise_for_status()
        runs = resp.json().get("workflow_runs", [])
        return runs[0] if runs else None


def get_workflow_paths(repo: str) -> list[str]:
    """Return .github/workflows/* file paths for a repo."""
    with _client() as client:
        resp = client.get(
            f"https://api.github.com/repos/{repo}/contents/.github/workflows"
        )
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        return [f["path"] for f in resp.json() if f["name"].endswith((".yml", ".yaml"))]


def get_file_content(repo: str, path: str) -> str | None:
    """Fetch a text file from a repo. Returns None if not found."""
    with _client() as client:
        resp = client.get(f"https://api.github.com/repos/{repo}/contents/{path}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return base64.b64decode(resp.json()["content"]).decode()


def get_file(repo: str, path: str) -> tuple[str | None, str | None]:
    """Fetch a file, returning (content, sha). Both None if not found."""
    with _client() as client:
        resp = client.get(f"https://api.github.com/repos/{repo}/contents/{path}")
        if resp.status_code == 404:
            return None, None
        resp.raise_for_status()
        data = resp.json()
        return base64.b64decode(data["content"]).decode(), data["sha"]


def update_file(repo: str, path: str, content: str, sha: str | None, message: str) -> None:
    """Commit an updated (or new) file to a repo. Pass sha=None to create."""
    body: dict = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
    }
    if sha:
        body["sha"] = sha
    with _client() as client:
        resp = client.put(
            f"https://api.github.com/repos/{repo}/contents/{path}",
            json=body,
        )
        resp.raise_for_status()
