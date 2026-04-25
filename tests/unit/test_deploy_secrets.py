"""Unit tests for checks/deploy_secrets.py."""
import os
from unittest.mock import patch

os.environ.setdefault("GH_PAT", "test-token")

from checks.deploy_secrets import run, REQUIRED_SECRETS

ENTRY = {"name": "my-container", "repo": "aldarondo/my-repo"}
ALL_SECRETS = set(REQUIRED_SECRETS) | {"OTHER_SECRET"}


@patch("checks.deploy_secrets.roadmap")
@patch("checks.deploy_secrets.github")
def test_all_secrets_present_clears_blocked(mock_github, mock_roadmap):
    mock_github.list_secrets.return_value = ALL_SECRETS

    run(ENTRY)

    mock_roadmap.clear_blocked.assert_called_once_with("aldarondo/my-repo", "missing-deploy-secrets")
    mock_roadmap.write_blocked.assert_not_called()


@patch("checks.deploy_secrets.roadmap")
@patch("checks.deploy_secrets.github")
def test_missing_secrets_writes_blocked(mock_github, mock_roadmap):
    mock_github.list_secrets.return_value = {"NAS_SSH_PASSWORD"}  # missing CF secrets

    run(ENTRY)

    mock_roadmap.write_blocked.assert_called_once()
    call_args = mock_roadmap.write_blocked.call_args[0]
    assert call_args[1] == "missing-deploy-secrets"
    assert "CF_ACCESS_CLIENT_ID" in call_args[2]
    assert "CF_ACCESS_CLIENT_SECRET" in call_args[2]


@patch("checks.deploy_secrets.roadmap")
@patch("checks.deploy_secrets.github")
def test_empty_set_skips_silently(mock_github, mock_roadmap):
    """Empty set means PAT lacks secrets:read — should not write blocked."""
    mock_github.list_secrets.return_value = set()

    run(ENTRY)

    mock_roadmap.write_blocked.assert_not_called()
    mock_roadmap.clear_blocked.assert_not_called()


@patch("checks.deploy_secrets.roadmap")
@patch("checks.deploy_secrets.github")
def test_all_missing_writes_all_names(mock_github, mock_roadmap):
    mock_github.list_secrets.return_value = {"SOME_OTHER_SECRET"}

    run(ENTRY)

    call_args = mock_roadmap.write_blocked.call_args[0]
    for secret in REQUIRED_SECRETS:
        assert secret in call_args[2]
