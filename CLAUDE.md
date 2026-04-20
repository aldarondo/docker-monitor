# docker-monitor

## Project Purpose
Audit Docker/GHCR deploy health across all hub projects and surface failures to each project's ROADMAP.md — never auto-fixes, only reports.

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
