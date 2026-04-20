# docker-monitor Roadmap
> Tag key: `[Code]` = Claude Code · `[Cowork]` = Claude Cowork · `[Human]` = Charles must act

## 🔄 In Progress
<!-- nothing active -->

## 🔲 Backlog

### Phase 3 — GitHub Actions schedule
- [ ] `[Human]` Add `GH_PAT`, `NAS_HOST`, `NAS_USER`, `NAS_PASS` secrets to this repo via `gh secret set` (values from claude-synology config.json) — reassigned from [Code]: requires account credentials

## ✅ Completed
- 2026-04-20 — Project scaffolded: README, CLAUDE.md, ROADMAP.md, tests/, GitHub repo, Synology deploy key
- 2026-04-20 — Defined project game plan (CLAUDE.md, ROADMAP.md)
- 2026-04-20 — Phase 1: Wrote `monitor.py`, `lib/synology.py`, `lib/github.py`, `lib/roadmap.py`, `config/containers.yaml`
- 2026-04-20 — Phase 2: Wrote checks — `deploy_status.py`, `weekly_schedule.py`, `ghcr_migration.py`
- 2026-04-20 — Phase 3: Added `.github/workflows/monitor.yml` (daily cron at 08:00 UTC, `RUN_ONCE=true`)
- 2026-04-20 — Phase 4: Unit tests for `lib/roadmap.py` (update-existing vs append), `lib/github.py` (status parsing), `checks/deploy_status.py`; integration test for full monitor pipeline; conftest.py for import resolution; `__init__.py` in test dirs — 20 passing, 2 skipped
- 2026-04-20 — Aligned env var `GITHUB_PAT` → `GH_PAT` across `lib/github.py`, `monitor.py`, `docker-compose.yml`, `monitor.yml`

## 🚫 Blocked
<!-- log blockers here -->
