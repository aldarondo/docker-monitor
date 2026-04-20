"""
Check: is the container using a custom GHCR image (ghcr.io/aldarondo/...)?
Flags containers still on generic base images like node:20-alpine or python:3.x-slim.
"""

from lib import roadmap

CHECK = "no-ghcr-image"


def run(entry: dict) -> None:
    name = entry["name"]
    image = entry.get("image", "")
    repo = entry["repo"]
    print(f"  ghcr-migration: {name} ({image})")

    if image.startswith("ghcr.io/aldarondo/"):
        roadmap.clear_blocked(repo, CHECK)
        print(f"    already on GHCR")
    else:
        roadmap.write_blocked(
            repo,
            CHECK,
            f"Container `{name}` uses `{image}` — migrate to `ghcr.io/aldarondo/...` with a GitHub Actions build-push workflow",
        )
