# docker-monitor Roadmap
> Tag key: `[Code]` = Claude Code · `[Cowork]` = Claude Cowork · `[Human]` = Charles must act

## 🔄 In Progress
- [ ] `[Code]` Define project game plan

## 🔲 Backlog

### Phase 1 — Core monitor
- [ ] `[Code]` Write `monitor.py` — main entrypoint: load container map, run all checks, write results
- [ ] `[Code]` Write `lib/synology.py` — query NAS via Synology Docker API to get running containers + images
- [ ] `[Code]` Write `lib/github.py` — GitHub REST API client (PAT from `GITHUB_PAT` env var) to fetch latest workflow run status per repo
- [ ] `[Code]` Write `lib/roadmap.py` — read/write `ROADMAP.md` for a given project: update existing `🚫 Blocked` entry if one matches the check name, otherwise append a new one
- [ ] `[Code]` Write `config/containers.yaml` — static map: container name → GitHub repo → project folder path → ROADMAP.md path

### Phase 2 — Checks
- [ ] `[Code]` Check: GHCR deploy status — for each GHCR container, fetch latest GitHub Actions workflow run; if failed, write failure to project ROADMAP.md
  - Scope: `brian-mcp`, `brian-telegram`, `claude-monarch`, `enphase-juicebox-coordinator`, `claude-enphase`, `jellyfin-automation`, `claude-juicebox`
- [ ] `[Code]` Check: weekly schedule audit — for each monitored repo, confirm `.github/workflows/` contains at least one workflow with a `schedule:` trigger; flag missing ones in their ROADMAP.md
- [ ] `[Code]` Check: GHCR migration audit — flag containers still using base images (`node:20-alpine`, `python:3.x-slim`) that belong to our repos; write to their ROADMAP.md
  - Scope: `brian-email`, `brian-drive`, `claude-nirvana`, `claude-whoop`, `claude-withings`, `claude-walmart`, `claude-safeway`, `claude-kroger`

### Phase 3 — GitHub Actions schedule
- [ ] `[Code]` Add `.github/workflows/monitor.yml` — daily cron (`schedule: '0 8 * * *'`) that runs `python monitor.py`; secrets: `GITHUB_PAT`, `NAS_HOST`, `NAS_USER`, `NAS_PASS`
- [ ] `[Code]` Add `GITHUB_PAT`, `NAS_HOST`, `NAS_USER`, `NAS_PASS` secrets to this repo via `gh secret set` (values from claude-synology config.json)

### Phase 4 — Tests
- [ ] `[Code]` Write unit tests for `lib/roadmap.py` (update-existing vs append logic)
- [ ] `[Code]` Write unit tests for `lib/github.py` (status parsing from API response)
- [ ] `[Code]` Write integration test: run monitor against a test repo with a known-failed workflow run

## ✅ Completed
- 2026-04-20 — Project scaffolded: README, CLAUDE.md, ROADMAP.md, tests/, GitHub repo, Synology deploy key

## 🚫 Blocked
<!-- log blockers here -->
