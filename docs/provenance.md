# Provenance and third-party notices

AgentTeam is licensed under the MIT License (`LICENSE`,
Copyright (c) 2026 ShuhanWang). This file records where code comes from; it is
a pre-first-push checklist artefact of the approved M1a plan (section 16) and
is updated whenever code is copied or adapted from elsewhere.

## Legacy ATM

AgentTeam supersedes the owner-authored **legacy ATM** experiment
(agent-team-manager). The owner authorized internal copy/adaptation of ATM
material (DECISIONS 0011 item 6; QUESTIONS Q7), with provenance and any
third-party obligations retained.

**As of 2026-08-23, no code has been copied or adapted from legacy ATM.**
Every future copy or adaptation must be recorded here with: source path and
commit, destination path, date, what was changed, and any third-party notices
that travel with it.

| Date | Source (path @ commit) | Destination | Adaptation | Notices |
| --- | --- | --- | --- | --- |
| — | *(none yet)* | | | |

## Dependencies (used, not vendored)

Runtime dependencies are declared in `pyproject.toml` and used under their own
licences; none of their code is copied into this repository: **Typer** (MIT),
**Pydantic** (MIT), **PyYAML** (MIT), plus their transitive dependencies as
resolved in `uv.lock` (inspect with `uv tree --no-dev`). Development-only
tools (pytest, Ruff, mypy, jsonschema, type stubs) are likewise declared in
the `dev` dependency group.

## Optional ClawTeam provider

The optional `clawteam` extra is a **direct Git reference** to upstream
[HKUDS/ClawTeam](https://github.com/HKUDS/ClawTeam) at the exact revision
`01198332ef9270c32c5460b8a178f964fc0df451` (package version 0.3.0), licensed
MIT (Copyright (c) 2025 HKUDS; see
`docs/discovery/evidence/clawteam-spawn-platform.md` section 4). ClawTeam is
never vendored into this repository and is imported only from the
`src/agentteam/compat/` provider module (from gate G4). Because the extra is a
direct reference, the built distribution is not uploadable to PyPI as is; no
package is published during M1a.
