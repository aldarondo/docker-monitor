# All features require unit + integration tests before a task is marked complete.
from unittest.mock import patch
from checks import container_status


@patch("checks.container_status.roadmap")
def test_running_container_clears_blocked(mock_roadmap):
    container_status.run({"name": "brian-telegram", "repo": "aldarondo/brian-telegram"}, {"brian-telegram"})
    mock_roadmap.clear_blocked.assert_called_once_with("aldarondo/brian-telegram", container_status.CHECK)
    mock_roadmap.write_blocked.assert_not_called()


@patch("checks.container_status.roadmap")
def test_stopped_container_writes_blocked(mock_roadmap):
    container_status.run({"name": "brian-telegram", "repo": "aldarondo/brian-telegram"}, set())
    mock_roadmap.write_blocked.assert_called_once()
    args = mock_roadmap.write_blocked.call_args[0]
    assert args[0] == "aldarondo/brian-telegram"
    assert args[1] == container_status.CHECK
    assert "brian-telegram" in args[2]


@patch("checks.container_status.roadmap")
def test_write_nas_error_targets_self_repo(mock_roadmap):
    container_status.write_nas_error("status file is 3h old")
    mock_roadmap.write_blocked.assert_called_once_with(
        container_status.SELF_REPO,
        container_status.NAS_CHECK,
        "status file is 3h old",
    )


@patch("checks.container_status.roadmap")
def test_clear_nas_error(mock_roadmap):
    container_status.clear_nas_error()
    mock_roadmap.clear_blocked.assert_called_once_with(
        container_status.SELF_REPO, container_status.NAS_CHECK
    )
