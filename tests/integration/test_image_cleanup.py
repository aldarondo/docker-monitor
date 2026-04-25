"""
Integration test: image_cleanup.run() against the real Docker socket.

Skipped automatically when the Docker socket is not available (CI, dev machines).
On the NAS (where the monitor runs), this verifies the prune call actually works.
"""

import pytest
import docker as docker_sdk
from checks import image_cleanup


def _docker_available() -> bool:
    try:
        docker_sdk.from_env().ping()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _docker_available(), reason="Docker socket not available")
def test_run_does_not_raise():
    """Prune completes without error against a real Docker daemon."""
    image_cleanup.run()  # dangling images may or may not exist — just verify no crash
