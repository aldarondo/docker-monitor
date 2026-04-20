# docker-monitor Roadmap
> Tag key: `[Code]` = Claude Code · `[Cowork]` = Claude Cowork · `[Human]` = Charles must act

## 🔄 In Progress
- [ ] `[Code]` Define project game plan

## 🔲 Backlog
- [ ] `[Code]` Enumerate Docker containers / GitHub Actions workflows across all hub projects
- [ ] `[Code]` Poll GHCR and GitHub Actions for deploy status; write failures to each project's ROADMAP.md
- [ ] `[Code]` Audit each project's workflow: verify GHCR is used as the container registry for auto-deploy
- [ ] `[Code]` Audit each project's workflow: verify a weekly `schedule:` trigger exists for dependency refreshes
- [ ] `[Code]` Write unit tests for core logic (status parsing, ROADMAP writer, workflow auditor)
- [ ] `[Code]` Write integration tests for end-to-end flows against real GitHub API (with VCR cassettes or test org)

## ✅ Completed
<!-- dated entries go here -->

## 🚫 Blocked
<!-- log blockers here -->
