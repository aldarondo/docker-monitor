"""
Integration test: run the full monitor pipeline against mocked external calls.

Simulates a NAS with two running containers:
  - brian-telegram (GHCR, latest Actions run failed) → expect Blocked entry written
  - brian-drive    (non-GHCR, migration needed)      → expect GHCR migration entry written

All network calls are mocked; no live credentials required.
"""
import base64
import os
import pytest
from unittest.mock import MagicMock, patch

os.environ.setdefault("GH_PAT", "test-token")
os.environ.setdefault("NAS_HOST", "http://nas.local:5000")
os.environ.setdefault("NAS_USER", "admin")
os.environ.setdefault("NAS_PASS", "pass")


SAMPLE_ROADMAP = "# Project\n\n## 🚫 Blocked\n<!-- log blockers here -->\n"
ROADMAP_B64 = base64.b64encode(SAMPLE_ROADMAP.encode()).decode()

WORKFLOW_WITH_SCHEDULE_B64 = base64.b64encode(b"on:\n  schedule:\n    - cron: '0 8 * * 0'\n").decode()


def _make_resp(json_data, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


@patch("lib.github.httpx.Client")
@patch("lib.synology.requests")
def test_full_run_failed_deploy_and_migration(mock_requests, mock_client_cls):
    # ── NAS: two running containers ──────────────────────────────────────
    mock_requests.post.return_value = _make_resp({"success": True, "data": {"sid": "SID"}})
    mock_requests.get.return_value = _make_resp({
        "data": {
            "containers": [
                {"name": "brian-telegram", "image": "ghcr.io/aldarondo/brian-telegram", "State": {"Running": True}},
                {"name": "brian-drive",    "image": "node:20-alpine",                   "State": {"Running": True}},
            ]
        }
    })

    # ── GitHub API responses (in call order) ─────────────────────────────
    # brian-telegram: latest run failed
    failed_run = {
        "id": 999,
        "status": "completed",
        "conclusion": "failure",
        "html_url": "https://github.com/aldarondo/brian-telegram/actions/runs/999",
    }
    # brian-telegram: has a schedule workflow
    workflow_listing = [{"name": "build.yml", "path": ".github/workflows/build.yml"}]
    # roadmap reads/writes for brian-telegram deploy-failed check
    roadmap_file = {"content": ROADMAP_B64, "sha": "sha-telegram"}
    # roadmap for weekly-schedule check (has schedule, so clear_blocked)
    workflow_content = {"content": WORKFLOW_WITH_SCHEDULE_B64, "sha": "sha-wf"}
    # brian-drive: roadmap for ghcr-migration check
    roadmap_drive = {"content": ROADMAP_B64, "sha": "sha-drive"}

    http_client = mock_client_cls.return_value.__enter__.return_value

    http_client.get.side_effect = [
        # deploy_status: get_latest_workflow_run → returns failed run
        _make_resp({"workflow_runs": [failed_run]}),
        # roadmap.write_blocked (deploy-failed): get_file → ROADMAP
        _make_resp(roadmap_file),
        # weekly_schedule: get_workflow_paths → listing
        _make_resp(workflow_listing),
        # weekly_schedule: get_file_content → workflow file with schedule:
        _make_resp(workflow_content),
        # roadmap.clear_blocked (no-weekly-schedule): get_file → ROADMAP (no entry to clear)
        _make_resp(roadmap_file),
        # ghcr_migration: roadmap.write_blocked → get_file → drive ROADMAP
        _make_resp(roadmap_drive),
    ]
    http_client.put.return_value = _make_resp({})

    from monitor import run_checks
    run_checks()

    put_calls = http_client.put.call_args_list
    # At least two PUT calls: one for deploy-failed, one for ghcr-migration
    assert len(put_calls) >= 2

    written_bodies = [c[1]["json"]["content"] for c in put_calls]
    decoded = [base64.b64decode(b).decode() for b in written_bodies]

    deploy_entry = next((d for d in decoded if "docker-monitor:deploy-failed" in d), None)
    assert deploy_entry is not None, "Expected deploy-failed blocked entry to be written"
    assert "run #999" in deploy_entry

    migration_entry = next((d for d in decoded if "docker-monitor:no-ghcr-image" in d), None)
    assert migration_entry is not None, "Expected no-ghcr-image blocked entry to be written"
    assert "brian-drive" in migration_entry
