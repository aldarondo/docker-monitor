# docker-monitor Roadmap
> Tag key: `[Code]` = Claude Code · `[Cowork]` = Claude Cowork · `[Human]` = Charles must act

## 🔄 In Progress
<!-- nothing active -->

## 🔲 Backlog

<!-- nothing pending -->

## ✅ Completed
- 2026-04-20 — Project scaffolded: README, CLAUDE.md, ROADMAP.md, tests/, GitHub repo, Synology deploy key
- 2026-04-20 — Defined project game plan (CLAUDE.md, ROADMAP.md, container map)
- 2026-04-20 — Phase 1: `monitor.py`, `lib/synology.py`, `lib/github.py`, `lib/roadmap.py`, `config/containers.yaml`
- 2026-04-20 — Phase 2: Checks — `deploy_status.py`, `weekly_schedule.py`, `ghcr_migration.py`
- 2026-04-20 — Phase 3: `.github/workflows/monitor.yml` (daily 08:00 UTC, GitHub Actions runner) + `build-push.yml` (weekly GHCR image rebuild); secrets set via `gh secret set`
- 2026-04-20 — Phase 4: 20 unit + integration tests passing (roadmap writer, GitHub API client, deploy status check, full end-to-end mock run)
- 2026-04-20 — GHCR image built and pushed to `ghcr.io/aldarondo/docker-monitor:latest`
- 2026-04-21 — Cloudflare Tunnel `nas-ssh` deployed (`cloudflared-nas-ssh` container on NAS); all 7 GHCR repos updated to use `cloudflared access ssh --id/--secret` + individual service tokens via `create-access-service-token.mjs`
- 2026-04-21 — Added `checks/deploy_config.py` (flags appleboy/ssh-action and hardcoded LAN IPs) and `checks/deploy_secrets.py` (flags missing NAS_SSH_PASSWORD/CF_ACCESS_CLIENT_ID/CF_ACCESS_CLIENT_SECRET); 9 new unit tests passing
- 2026-04-23 — GHCR migration complete for all 8 containers: `brian-email`, `brian-drive`, `claude-nirvana`, `claude-whoop`, `claude-withings`, `claude-walmart`, `claude-safeway`, `claude-kroger` — each got Dockerfile (node:22-alpine), build.yml (CF service token deploy), updated docker-compose.yml, individual CF Access service tokens, and `NAS_SSH_PASSWORD` set; `containers.yaml` updated to remove `ghcr_migration_needed` flags

## 🚫 Blocked
- ❌ [docker-monitor:nas-status-stale] container_status.json is 9.9h old (limit 2h) — NAS container may have stopped — 2026-04-25 17:55 UTC

<!-- log blockers here -->
