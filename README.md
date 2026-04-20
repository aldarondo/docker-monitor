# docker-monitor

Watches Docker containers across GitHub projects, verifies deploys succeeded, and audits GHCR/weekly-maintenance workflow configuration.

## Features
- Polls GitHub Actions and GHCR to confirm deploys completed successfully
- Writes deploy failures to the affected project's `ROADMAP.md` (read-only audit — never auto-fixes)
- Audits each project's workflow to confirm it uses GHCR for auto-deploy
- Validates that each project has a weekly scheduled workflow trigger for dependency refreshes

## Tech Stack
| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| GitHub API | httpx + GitHub REST API v3 |
| Auth | `GITHUB_TOKEN` env var |

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run the monitor
python monitor.py

# Run tests
pytest
```

## Project Status
Early development. See [ROADMAP.md](ROADMAP.md) for what's planned.

---
**Publisher:** Xity Software, LLC
