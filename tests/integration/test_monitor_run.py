"""
Integration test: run the full monitor pipeline against mocked external calls.

Simulates a NAS with two running containers:
  - brian-telegram (GHCR, latest Actions run failed) → expect Blocked entry written
  - brian-drive    (non-GHCR, migration needed)      → expect GHCR migration entry written

NAS_HOST is unset so the code uses the repo container_status.json fallback path,
keeping the GitHub API mock sequence straightforward.

All network calls are mocked; no live credentials required.
"""
import base64
import os
import pytest
from unittest.mock import MagicMock, patch

os.environ.setdefault("GH_PAT", "test-token")
os.environ.setdefault("NAS_USER", "admin")
os.environ.setdefault("NAS_PASS", "pass")
os.environ.pop("NAS_HOST", None)  # force repo-file path; direct Synology query skipped


SAMPLE_ROADMAP = "# Project\n\n## 🚫 Blocked\n<!-- log blockers here -->\n"
ROADMAP_B64 = base64.b64encode(SAMPLE_ROADMAP.encode()).decode()

WORKFLOW_WITH_SCHEDULE_B64 = base64.b64encode(b"on:\n  schedule:\n    - cron: '0 8 * * 0'\n").decode()


def _make_resp(json_data, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


STATUS_JSON_B64 = base64.b64encode(
    b'{"timestamp":"2099-01-01T00:00:00+00:00","containers":['
    b'{"name":"brian-telegram","image":"ghcr.io/aldarondo/brian-telegram","running":true},'
    b'{"name":"brian-drive","image":"node:20-alpine","running":true}'
    b']}'
).decode()


TEST_CONFIG = [
    {"name": "brian-telegram", "image": "ghcr.io/aldarondo/brian-telegram", "repo": "aldarondo/brian-telegram"},
    {"name": "brian-drive", "image": "node:20-alpine", "repo": "aldarondo/brian-drive", "ghcr_migration_needed": True},
]


@patch("monitor.load_config", return_value=TEST_CONFIG)
@patch("lib.github.httpx.Client")
def test_full_run_failed_deploy_and_migration(mock_client_cls, mock_load_config):
    # NAS_HOST is unset (popped at module level) → uses repo container_status.json

    # ── GitHub API responses (in call order) ─────────────────────────────
    failed_run = {
        "id": 999, "status": "completed", "conclusion": "failure",
        "html_url": "https://github.com/aldarondo/brian-telegram/actions/runs/999",
    }
    workflow_listing = [{"name": "build.yml", "path": ".github/workflows/build.yml"}]
    roadmap_file = {"content": ROADMAP_B64, "sha": "sha-telegram"}
    workflow_content = {"content": WORKFLOW_WITH_SCHEDULE_B64, "sha": "sha-wf"}
    roadmap_drive = {"content": ROADMAP_B64, "sha": "sha-drive"}
    container_status_file = {"content": STATUS_JSON_B64, "sha": "sha-status"}
    no_entry = {"content": ROADMAP_B64, "sha": "sha-no-entry"}  # for clear_blocked with no match

    http_client = mock_client_cls.return_value.__enter__.return_value

    http_client.get.side_effect = [
        # 1. _load_container_status: get_status_from_repo → get_file(container_status.json)
        _make_resp(container_status_file),
        # 2. clear_nas_error → clear_blocked(docker-monitor ROADMAP) → no match
        _make_resp(no_entry),
        # 3. container_status.run(brian-telegram) → clear_blocked(container-stopped) → no match
        _make_resp(no_entry),
        # 4. deploy_status: get_latest_workflow_run
        _make_resp({"workflow_runs": [failed_run]}),
        # 5. roadmap.write_blocked(deploy-failed): get_file(brian-telegram ROADMAP)
        _make_resp(roadmap_file),
        # 6. weekly_schedule: get_workflow_paths
        _make_resp(workflow_listing),
        # 7. weekly_schedule: get_file_content → workflow with schedule:
        _make_resp(workflow_content),
        # 8. roadmap.clear_blocked(no-weekly-schedule): get_file → no match
        _make_resp(no_entry),
        # 9. container_status.run(brian-drive) → clear_blocked(container-stopped) → no match
        _make_resp(no_entry),
        # 10. ghcr_migration: roadmap.write_blocked → get_file(brian-drive ROADMAP)
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
