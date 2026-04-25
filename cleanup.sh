#!/usr/bin/env bash
# Docker cleanup — run on the NAS via SSH or /synology skill
#
# Default (no args): remove stopped containers + dangling images (safe, same as monitor auto-prune)
# --aggressive:      also remove ALL unused images older than 7 days (frees more space)
# --dry-run:         show what would be removed without deleting anything

set -euo pipefail

AGGRESSIVE=false
DRY_RUN=false

for arg in "$@"; do
  case $arg in
    --aggressive) AGGRESSIVE=true ;;
    --dry-run)    DRY_RUN=true ;;
    *) echo "Unknown flag: $arg" && exit 1 ;;
  esac
done

echo "=== Docker image cleanup ==="
echo "Disk before:"
df -h /volume1 2>/dev/null || df -h /

if $DRY_RUN; then
  echo ""
  echo "--- Stopped containers (would remove) ---"
  docker ps -a --filter status=exited --filter status=dead --format "{{.Names}}  {{.Status}}"
  echo ""
  echo "--- Dangling images (would remove) ---"
  docker images --filter "dangling=true" --format "{{.ID}}  {{.Size}}  {{.CreatedSince}}"
  if $AGGRESSIVE; then
    echo ""
    echo "--- Unused images older than 7 days (would also remove) ---"
    docker images --filter "until=168h" --format "{{.Repository}}:{{.Tag}}  {{.Size}}  {{.CreatedSince}}"
  fi
  echo ""
  echo "Dry run complete — no changes made."
  exit 0
fi

echo ""
echo "--- Removing stopped containers ---"
docker container prune -f

echo ""
echo "--- Removing dangling images ---"
docker image prune -f

if $AGGRESSIVE; then
  echo ""
  echo "--- Removing all unused images older than 7 days ---"
  docker image prune -a -f --filter "until=168h"
fi

echo ""
echo "Disk after:"
df -h /volume1 2>/dev/null || df -h /
echo "=== done ==="
