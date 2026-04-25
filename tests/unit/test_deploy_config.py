"""Unit tests for checks/deploy_config.py."""
import os
from unittest.mock import patch

os.environ.setdefault("GH_PAT", "test-token")

from checks.deploy_config import run

ENTRY = {"name": "my-container", "repo": "aldarondo/my-repo"}
CLEAN_WORKFLOW = "on:\n  push:\nsteps:\n  - uses: docker/build-push-action@v5\n"


@patch("checks.deploy_config.roadmap")
@patch("checks.deploy_config.github")
def test_no_bad_patterns_clears_blocked(mock_github, mock_roadmap):
    mock_github.get_workflow_paths.return_value = [".github/workflows/build.yml"]
    mock_github.get_file_content.return_value = CLEAN_WORKFLOW

    run(ENTRY)

    mock_roadmap.clear_blocked.assert_called_once_with("aldarondo/my-repo", "bad-deploy-config")
    mock_roadmap.write_blocked.assert_not_called()


@patch("checks.deploy_config.roadmap")
@patch("checks.deploy_config.github")
def test_appleboy_action_writes_blocked(mock_github, mock_roadmap):
    bad_content = "steps:\n  - uses: appleboy/ssh-action@v1\n    with:\n      host: 192.168.0.64\n"
    mock_github.get_workflow_paths.return_value = [".github/workflows/build.yml"]
    mock_github.get_file_content.return_value = bad_content

    run(ENTRY)

    mock_roadmap.write_blocked.assert_called_once()
    call_args = mock_roadmap.write_blocked.call_args[0]
    assert call_args[1] == "bad-deploy-config"
    assert "appleboy/ssh-action" in call_args[2]


@patch("checks.deploy_config.roadmap")
@patch("checks.deploy_config.github")
def test_lan_ip_writes_blocked(mock_github, mock_roadmap):
    bad_content = "host: 192.168.0.64\nport: 2222\n"
    mock_github.get_workflow_paths.return_value = [".github/workflows/build.yml"]
    mock_github.get_file_content.return_value = bad_content

    run(ENTRY)

    mock_roadmap.write_blocked.assert_called_once()
    call_args = mock_roadmap.write_blocked.call_args[0]
    assert "192.168.0." in call_args[2]


@patch("checks.deploy_config.roadmap")
@patch("checks.deploy_config.github")
def test_no_workflows_clears_blocked(mock_github, mock_roadmap):
    mock_github.get_workflow_paths.return_value = []

    run(ENTRY)

    mock_roadmap.clear_blocked.assert_called_once_with("aldarondo/my-repo", "bad-deploy-config")


@patch("checks.deploy_config.roadmap")
@patch("checks.deploy_config.github")
def test_only_first_bad_pattern_written(mock_github, mock_roadmap):
    """Should write blocked once even if multiple bad patterns match."""
    bad_content = "uses: appleboy/ssh-action@v1\nhost: 192.168.0.64\n"
    mock_github.get_workflow_paths.return_value = [".github/workflows/build.yml"]
    mock_github.get_file_content.return_value = bad_content

    run(ENTRY)

    assert mock_roadmap.write_blocked.call_count == 1
