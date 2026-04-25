from unittest.mock import patch, MagicMock
from checks import image_cleanup


def _make_client(img_deleted=None, img_reclaimed=0, ctr_deleted=None, ctr_reclaimed=0):
    client = MagicMock()
    client.containers.prune.return_value = {
        "ContainersDeleted": ctr_deleted,
        "SpaceReclaimed": ctr_reclaimed,
    }
    client.images.prune.return_value = {
        "ImagesDeleted": img_deleted,
        "SpaceReclaimed": img_reclaimed,
    }
    return client


@patch("checks.image_cleanup.docker_sdk.from_env")
def test_no_dangling_images(mock_from_env, capsys):
    mock_from_env.return_value = _make_client()
    image_cleanup.run()
    out = capsys.readouterr().out
    assert "no dangling" in out


@patch("checks.image_cleanup.docker_sdk.from_env")
def test_removes_dangling_images(mock_from_env, capsys):
    deleted = [{"Deleted": "sha256:aaa"}, {"Untagged": "sha256:bbb"}]
    mock_from_env.return_value = _make_client(img_deleted=deleted, img_reclaimed=5 * 1024 * 1024)
    image_cleanup.run()
    out = capsys.readouterr().out
    assert "removed 2 dangling" in out
    assert "5.0 MB" in out


@patch("checks.image_cleanup.docker_sdk.from_env")
def test_removes_stopped_containers(mock_from_env, capsys):
    client = _make_client(ctr_deleted=["old-container-1", "old-container-2"], ctr_reclaimed=1024)
    mock_from_env.return_value = client
    image_cleanup.run()
    out = capsys.readouterr().out
    assert "removed 2 stopped container" in out


@patch("checks.image_cleanup.docker_sdk.from_env")
def test_container_prune_runs_before_image_prune(mock_from_env):
    call_order = []
    client = MagicMock()
    client.containers.prune.side_effect = lambda: call_order.append("containers") or {"ContainersDeleted": None, "SpaceReclaimed": 0}
    client.images.prune.side_effect = lambda **_: call_order.append("images") or {"ImagesDeleted": None, "SpaceReclaimed": 0}
    mock_from_env.return_value = client
    image_cleanup.run()
    assert call_order == ["containers", "images"]


@patch("checks.image_cleanup.docker_sdk.from_env")
def test_socket_unavailable(mock_from_env, capsys):
    mock_from_env.side_effect = Exception("socket not found")
    image_cleanup.run()
    out = capsys.readouterr().out
    assert "unavailable" in out


@patch("checks.image_cleanup.docker_sdk.from_env")
def test_image_prune_error_does_not_raise(mock_from_env, capsys):
    client = MagicMock()
    client.containers.prune.return_value = {"ContainersDeleted": None, "SpaceReclaimed": 0}
    client.images.prune.side_effect = Exception("permission denied")
    mock_from_env.return_value = client
    image_cleanup.run()  # must not raise
    out = capsys.readouterr().out
    assert "prune failed" in out


@patch("checks.image_cleanup.docker_sdk.from_env")
def test_container_prune_error_continues_to_image_prune(mock_from_env, capsys):
    client = MagicMock()
    client.containers.prune.side_effect = Exception("container prune error")
    client.images.prune.return_value = {"ImagesDeleted": None, "SpaceReclaimed": 0}
    mock_from_env.return_value = client
    image_cleanup.run()
    out = capsys.readouterr().out
    assert "container prune failed" in out
    assert "no dangling" in out  # image prune still ran


@patch("checks.image_cleanup.docker_sdk.from_env")
def test_image_prune_called_with_dangling_filter(mock_from_env):
    client = _make_client()
    mock_from_env.return_value = client
    image_cleanup.run()
    client.images.prune.assert_called_once_with(filters={"dangling": True})
