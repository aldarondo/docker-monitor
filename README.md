# docker-monitor

Monitors Docker containers running on the Synology NAS, audits GitHub Actions deploy health, and writes findings directly to each affected project's `ROADMAP.md` via the GitHub API. Never auto-fixes — read-only reporter only.

## How It Works

Two runners cooperate:

| Runner | Trigger | Container source |
|--------|---------|-----------------|
| **NAS Docker container** | APScheduler — daily at 08:00 UTC, immediate on start | Docker socket (`/var/run/docker.sock`) — live data |
| **GitHub Actions** (`monitor.yml`) | Daily cron 08:00 UTC + `workflow_dispatch` | `container_status.json` committed by the NAS container |

The NAS container runs first, pushes a fresh `container_status.json` to this repo, then runs all checks. GitHub Actions reads that file as a fallback. If `container_status.json` goes stale (>2h), a `nas-status-stale` entry is written to this repo's own `ROADMAP.md`.

## Checks

| Check | Trigger | Result |
|-------|---------|--------|
| `container-stopped` | Container not running on NAS | Writes `🚫 Blocked` to project ROADMAP |
| `deploy-failed` | Latest GitHub Actions run concluded `failure` | Writes `🚫 Blocked` to project ROADMAP |
| `no-weekly-schedule` | No `schedule:` trigger in any workflow file | Writes `🚫 Blocked` to project ROADMAP |
| `no-ghcr-image` | Container uses a base image instead of `ghcr.io/aldarondo/...` | Writes `🚫 Blocked` to project ROADMAP |
| `nas-status-stale` | `container_status.json` missing or >2h old | Writes `🚫 Blocked` to **this** repo's ROADMAP |

All entries are self-healing: cleared automatically when the issue resolves on the next run.

## Monitored Projects

**GHCR containers** (deploy status + weekly schedule + container-stopped checks):

| Container | GitHub Repo |
|-----------|------------|
| `brian-mcp-memory` | `aldarondo/brian-mcp` |
| `brian-telegram` | `aldarondo/brian-telegram` |
| `claude-monarch` | `aldarondo/claude-monarch` |
| `enphase-juicebox-coordinator` | `aldarondo/enphase-juicebox-coordinator` |
| `enphase-mcp` | `aldarondo/claude-enphase` |
| `jellyfin-mcp` | `aldarondo/jellyfin-automation` |
| `juicebox-mcp` / `juicepassproxy` | `aldarondo/claude-juicebox` |

**Non-GHCR containers** (GHCR migration check + container-stopped):

`brian-email`, `brian-drive`, `claude-nirvana`, `claude-whoop`, `claude-withings`, `claude-walmart`, `claude-safeway`, `claude-kroger`

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Container discovery | Docker SDK (`docker` package) via `/var/run/docker.sock` |
| GitHub API | `httpx` + GitHub REST API v3 |
| Scheduler | APScheduler (NAS container) |
| Auth | `GH_PAT` env var (GitHub PAT, `repo` + `workflow` scopes) |

## NAS Deployment

```bash
# Clone to NAS (one-time, via synology skill)
python skills/synology.py deploy git@github-docker-monitor:aldarondo/docker-monitor.git /volume1/docker/docker-monitor

# Write credentials (SFTP — never appears in shell history)
MSYS_NO_PATHCONV=1 python skills/edit_env.py /volume1/docker/docker-monitor/.env \
  "GH_PAT=<pat>"

# Update running container
MSYS_NO_PATHCONV=1 python skills/synology.py deploy /volume1/docker/docker-monitor --update
```

The `docker-compose.yml` mounts the Docker socket — no NAS API credentials required.

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run a single check pass (requires GH_PAT env var)
GH_PAT=... RUN_ONCE=true python monitor.py

# Run tests (no credentials needed — all mocked)
pytest
```

## GitHub Actions Secrets

| Secret | Value |
|--------|-------|
| `GH_PAT` | GitHub PAT with `repo` + `workflow` scopes |

Set with: `gh secret set GH_PAT --body "<pat>"`

## Project Status

Live. See [ROADMAP.md](ROADMAP.md) for task history.

---
**Publisher:** Xity Software, LLC
