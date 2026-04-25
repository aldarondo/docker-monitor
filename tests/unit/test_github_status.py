# All features require unit + integration tests before a task is marked complete.
from unittest.mock import patch
from checks import deploy_status


def _mock_run(status="completed", conclusion="success", run_id=42):
    return {
        "id": run_id,
        "status": status,
        "conclusion": conclusion,
        "html_url": f"https://github.com/aldarondo/test/actions/runs/{run_id}",
    }


@patch("checks.deploy_status.roadmap")
@patch("checks.deploy_status.github")
def test_success_clears_blocked(mock_github, mock_roadmap):
    mock_github.get_latest_workflow_run.return_value = _mock_run("completed", "success")
    deploy_status.run({"repo": "aldarondo/test"})
    mock_roadmap.clear_blocked.assert_called_once_with("aldarondo/test", deploy_status.CHECK)
    mock_roadmap.write_blocked.assert_not_called()


@patch("checks.deploy_status.roadmap")
@patch("checks.deploy_status.github")
def test_failure_writes_blocked(mock_github, mock_roadmap):
    mock_github.get_latest_workflow_run.return_value = _mock_run("completed", "failure", run_id=99)
    deploy_status.run({"repo": "aldarondo/test"})
    mock_roadmap.write_blocked.assert_called_once()
    args = mock_roadmap.write_blocked.call_args[0]
    assert args[0] == "aldarondo/test"
    assert args[1] == deploy_status.CHECK
    assert "99" in args[2]


@patch("checks.deploy_status.roadmap")
@patch("checks.deploy_status.github")
def test_in_progress_skips(mock_github, mock_roadmap):
    mock_github.get_latest_workflow_run.return_value = _mock_run("in_progress", None)
    deploy_status.run({"repo": "aldarondo/test"})
    mock_roadmap.write_blocked.assert_not_called()
    mock_roadmap.clear_blocked.assert_not_called()


@patch("checks.deploy_status.roadmap")
@patch("checks.deploy_status.github")
def test_no_runs_skips(mock_github, mock_roadmap):
    mock_github.get_latest_workflow_run.return_value = None
    deploy_status.run({"repo": "aldarondo/test"})
    mock_roadmap.write_blocked.assert_not_called()
