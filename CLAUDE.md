# docker-monitor

## Project Purpose
Audit Docker/GHCR deploy health across all hub projects and surface failures to each project's ROADMAP.md — never auto-fixes, only reports.

## Container Map (as of 2026-04-20)
GHCR containers (CI/CD monitored):
- `brian-mcp-memory` / `brian-mcp-tunnel` → aldarondo/brian-mcp
- `brian-telegram` → aldarondo/brian-telegram
- `claude-monarch` → aldarondo/claude-monarch
- `enphase-juicebox-coordinator` → aldarondo/enphase-juicebox-coordinator
- `enphase-mcp` → aldarondo/claude-enphase
- `jellyfin-mcp` → aldarondo/jellyfin-automation
- `juicebox-mcp` / `juicepassproxy` → aldarondo/claude-juicebox

Non-GHCR aldarondo containers (GHCR migration audit targets):
- `brian-email`, `brian-drive`, `claude-nirvana`, `claude-whoop`, `claude-withings`, `claude-walmart`, `claude-safeway`, `claude-kroger`

## Auth
- `GITHUB_PAT` env var — PAT stored in `~/Documents/GitHub/claude-synology/config.json` → `github.pat`
- `NAS_HOST`, `NAS_USER`, `NAS_PASS` env vars — NAS connection from same config.json
- Never commit credentials to tracked files

## Key Commands
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python monitor.py          # run the monitor
pytest                     # run all tests
pytest tests/unit/         # unit tests only
pytest tests/integration/  # integration tests only
```

## Testing Requirements (mandatory)
- Every feature or bug fix must include unit tests covering the core logic
- Every user-facing flow must have at least one integration test
- Tests live in `tests/unit/` and `tests/integration/`
- Run all tests before marking any task complete: `pytest`

## After Every Completed Task (mandatory)
- Move the task to ✅ Completed in ROADMAP.md with today's date
- Update README.md if any feature, command, setup step, or interface changed

## Git Rules
- Never create pull requests. Push directly to main.
- solo/auto-push OK

## Skills
Before implementing any custom solution, check available skills first — prefer `/skill-name` over writing new code. The full list is visible in the Claude Code session context.

@~/Documents/GitHub/CLAUDE.md
