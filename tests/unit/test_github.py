"""Unit tests for lib/github.py — status parsing from API responses."""
import base64
import os
import pytest
from unittest.mock import MagicMock, patch

os.environ.setdefault("GH_PAT", "test-token")

from lib import github


def _make_response(json_data, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


# ── get_latest_workflow_run ────────────────────────────────────────────────


@patch("lib.github.httpx.Client")
def test_get_latest_workflow_run_returns_first(mock_client_cls):
    run = {"id": 1, "status": "completed", "conclusion": "success"}
    mock_client_cls.return_value.__enter__.return_value.get.return_value = (
        _make_response({"workflow_runs": [run, {"id": 2}]})
    )

    result = github.get_latest_workflow_run("aldarondo/test")

    assert result == run


@patch("lib.github.httpx.Client")
def test_get_latest_workflow_run_empty_list(mock_client_cls):
    mock_client_cls.return_value.__enter__.return_value.get.return_value = (
        _make_response({"workflow_runs": []})
    )

    result = github.get_latest_workflow_run("aldarondo/test")

    assert result is None


@patch("lib.github.httpx.Client")
def test_get_latest_workflow_run_missing_key(mock_client_cls):
    mock_client_cls.return_value.__enter__.return_value.get.return_value = (
        _make_response({})
    )

    result = github.get_latest_workflow_run("aldarondo/test")

    assert result is None


# ── get_workflow_paths ─────────────────────────────────────────────────────


@patch("lib.github.httpx.Client")
def test_get_workflow_paths_returns_yml_files(mock_client_cls):
    files = [
        {"name": "build.yml", "path": ".github/workflows/build.yml"},
        {"name": "README.md", "path": ".github/workflows/README.md"},
        {"name": "release.yaml", "path": ".github/workflows/release.yaml"},
    ]
    mock_client_cls.return_value.__enter__.return_value.get.return_value = (
        _make_response(files)
    )

    result = github.get_workflow_paths("aldarondo/test")

    assert result == [".github/workflows/build.yml", ".github/workflows/release.yaml"]


@patch("lib.github.httpx.Client")
def test_get_workflow_paths_404_returns_empty(mock_client_cls):
    resp = _make_response({}, status_code=404)
    resp.raise_for_status = MagicMock()
    mock_client_cls.return_value.__enter__.return_value.get.return_value = resp

    result = github.get_workflow_paths("aldarondo/test")

    assert result == []


# ── get_file_content ───────────────────────────────────────────────────────


@patch("lib.github.httpx.Client")
def test_get_file_content_decodes_base64(mock_client_cls):
    encoded = base64.b64encode(b"schedule:\n  - cron: '0 8 * * *'").decode()
    mock_client_cls.return_value.__enter__.return_value.get.return_value = (
        _make_response({"content": encoded})
    )

    result = github.get_file_content("aldarondo/test", ".github/workflows/build.yml")

    assert result == "schedule:\n  - cron: '0 8 * * *'"


@patch("lib.github.httpx.Client")
def test_get_file_content_404_returns_none(mock_client_cls):
    resp = _make_response({}, status_code=404)
    resp.raise_for_status = MagicMock()
    mock_client_cls.return_value.__enter__.return_value.get.return_value = resp

    result = github.get_file_content("aldarondo/test", "missing.txt")

    assert result is None


# ── get_file ──────────────────────────────────────────────────────────────


@patch("lib.github.httpx.Client")
def test_get_file_returns_content_and_sha(mock_client_cls):
    encoded = base64.b64encode(b"# ROADMAP").decode()
    mock_client_cls.return_value.__enter__.return_value.get.return_value = (
        _make_response({"content": encoded, "sha": "deadbeef"})
    )

    content, sha = github.get_file("aldarondo/test", "ROADMAP.md")

    assert content == "# ROADMAP"
    assert sha == "deadbeef"


@patch("lib.github.httpx.Client")
def test_get_file_404_returns_none_none(mock_client_cls):
    resp = _make_response({}, status_code=404)
    resp.raise_for_status = MagicMock()
    mock_client_cls.return_value.__enter__.return_value.get.return_value = resp

    content, sha = github.get_file("aldarondo/test", "missing.md")

    assert content is None
    assert sha is None


# ── update_file ───────────────────────────────────────────────────────────


@patch("lib.github.httpx.Client")
def test_update_file_encodes_and_sends(mock_client_cls):
    mock_put = MagicMock()
    mock_put.raise_for_status = MagicMock()
    mock_client_cls.return_value.__enter__.return_value.put.return_value = mock_put

    github.update_file("aldarondo/test", "ROADMAP.md", "new content", "sha123", "chore: update")

    mock_client_cls.return_value.__enter__.return_value.put.assert_called_once()
    call_kwargs = mock_client_cls.return_value.__enter__.return_value.put.call_args[1]
    body = call_kwargs["json"]
    assert base64.b64decode(body["content"]).decode() == "new content"
    assert body["sha"] == "sha123"
    assert body["message"] == "chore: update"
