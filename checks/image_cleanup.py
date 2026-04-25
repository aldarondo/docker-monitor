"""
Check: prune stopped containers and dangling Docker images on each monitor run.

Stopped containers can hold references to old image layers, preventing them from
being freed. Pruning containers first maximises how many dangling images can be removed.

This runs automatically on every monitor tick when USE_DOCKER_SOCKET=true.
For a full prune (all unused images, not just dangling), run cleanup.sh on the NAS.
"""

import docker as docker_sdk


def run() -> None:
    """Remove stopped containers then dangling images. No-op if socket is unavailable."""
    try:
        client = docker_sdk.from_env()
    except Exception as exc:
        print(f"  image-cleanup: Docker socket unavailable — {exc}")
        return

    total_reclaimed = 0

    try:
        cr = client.containers.prune()
        deleted_containers = cr.get("ContainersDeleted") or []
        container_space = cr.get("SpaceReclaimed", 0)
        total_reclaimed += container_space
        if deleted_containers:
            print(f"  image-cleanup: removed {len(deleted_containers)} stopped container(s)")
    except Exception as exc:
        print(f"  image-cleanup: container prune failed — {exc}")

    try:
        ir = client.images.prune(filters={"dangling": True})
        removed = ir.get("ImagesDeleted") or []
        image_space = ir.get("SpaceReclaimed", 0)
        total_reclaimed += image_space
        count = len(removed)
        mb = total_reclaimed / (1024 * 1024)
        if count:
            print(f"  image-cleanup: removed {count} dangling image(s), freed {mb:.1f} MB total")
        else:
            print(f"  image-cleanup: no dangling images")
    except Exception as exc:
        print(f"  image-cleanup: image prune failed — {exc}")
