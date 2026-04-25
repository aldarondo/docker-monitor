# All features require unit + integration tests before a task is marked complete.
from unittest.mock import patch, MagicMock
from lib import roadmap


SAMPLE_ROADMAP = """# Test Project Roadmap

## 🔲 Backlog
- [ ] Some task

## ✅ Completed
<!-- dated entries go here -->

## 🚫 Blocked
<!-- log blockers here -->
"""

ROADMAP_WITH_ENTRY = """# Test Project Roadmap

## 🚫 Blocked
- ❌ [docker-monitor:deploy-failed] Old message — 2026-01-01 00:00 UTC
"""


@patch("lib.roadmap.github")
def test_write_blocked_new_entry(mock_github):
    mock_github.get_file.return_value = (SAMPLE_ROADMAP, "abc123")
    mock_github.update_file = MagicMock()

    roadmap.write_blocked("aldarondo/test", "deploy-failed", "Build broke on run #99")

    mock_github.update_file.assert_called_once()
    _, args, _ = mock_github.update_file.mock_calls[0]
    updated_content = args[2]
    assert "[docker-monitor:deploy-failed]" in updated_content
    assert "Build broke on run #99" in updated_content


@patch("lib.roadmap.github")
def test_write_blocked_updates_existing(mock_github):
    mock_github.get_file.return_value = (ROADMAP_WITH_ENTRY, "abc123")
    mock_github.update_file = MagicMock()

    roadmap.write_blocked("aldarondo/test", "deploy-failed", "New failure message")

    mock_github.update_file.assert_called_once()
    _, args, _ = mock_github.update_file.mock_calls[0]
    updated = args[2]
    assert "New failure message" in updated
    assert "Old message" not in updated
    # Only one entry should exist
    assert updated.count("[docker-monitor:deploy-failed]") == 1


@patch("lib.roadmap.github")
def test_write_blocked_no_roadmap(mock_github, capsys):
    mock_github.get_file.return_value = (None, None)
    roadmap.write_blocked("aldarondo/test", "deploy-failed", "msg")
    mock_github.update_file.assert_not_called()
    assert "skip" in capsys.readouterr().out


@patch("lib.roadmap.github")
def test_clear_blocked_removes_entry(mock_github):
    mock_github.get_file.return_value = (ROADMAP_WITH_ENTRY, "abc123")
    mock_github.update_file = MagicMock()

    roadmap.clear_blocked("aldarondo/test", "deploy-failed")

    mock_github.update_file.assert_called_once()
    _, args, _ = mock_github.update_file.mock_calls[0]
    assert "[docker-monitor:deploy-failed]" not in args[2]


@patch("lib.roadmap.github")
def test_clear_blocked_noop_when_no_entry(mock_github):
    mock_github.get_file.return_value = (SAMPLE_ROADMAP, "abc123")
    mock_github.update_file = MagicMock()

    roadmap.clear_blocked("aldarondo/test", "deploy-failed")

    mock_github.update_file.assert_not_called()
