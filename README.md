# AgentTeam

**Status: alpha.** AgentTeam is being built gate by gate from an approved
plan. The repository holds the discovery/planning documentation and the first
implementation slices of gate G2 (Python packaging, the `atm` CLI skeleton,
and hosted-CI smoke checks). There is no released package and no public
distribution; interfaces and records are not stable yet.

AgentTeam provides portable, harness-independent **Assistant definitions**
(reusable specialised colleagues) and reusable **Team templates**, executed as
fresh **TeamRuns** over existing coding-agent harnesses (Claude Code, Codex,
and Grok Build first; OpenClaw, Hermes, and others later). The product CLI is
`atm`. AgentTeam supersedes the legacy ATM experiment (agent-team-manager),
which remains a source of requirements, experiments, and evidence only.

## What exists today

| Area | Where | State |
| --- | --- | --- |
| Discovery package (M0 / M0.1) | [`docs/discovery/`](docs/discovery/README.md) | delivered; living documents carry dated amendments |
| Independent review of the discovery baseline | [`docs/reviews/`](docs/reviews/2026-08-23-m0-review-at-3407ec9.md) | dated record |
| M1a direct-harness PoC plan, revision r3 | [`docs/plans/m1a-direct-harness-poc.md`](docs/plans/m1a-direct-harness-poc.md) | approved for implementation (DECISIONS 0021) |
| Project state: charter, plan, decisions, questions, risks, verification, handoff | [`.project-steward/`](.project-steward/) | current |
| Product scaffold: packaging, `atm` CLI skeleton, unit tests, CI smoke matrix | `pyproject.toml`, [`src/agentteam/`](src/agentteam/), [`tests/`](tests/), [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | alpha (M1a G2); the CLI has `--help`/`--version` only |
| V1 domain records + checked-in JSON Schemas | [`src/agentteam/domain/`](src/agentteam/domain/), [`schemas/`](schemas/README.md) | alpha (M1a G2); closed records, vendor-facing review/synthesis contracts |
| Harness adapters, runner, live evidence | — | not yet (M1a gates G3–G8) |

## Planned stack

Python `>=3.11` managed with `uv` and built with Hatchling; checked-in JSON
Schema records; the `atm` CLI (later also an MCP server) as the
language-neutral edge; a built-in shell-free direct runner; coordination
substrates (ClawTeam first) as optional providers. The approved plan holds the
gates, contracts, budgets, and stop rules.

## Orientation

- Current state and next steps: [`.project-steward/HANDOFF.md`](.project-steward/HANDOFF.md);
  milestones and gates: [`.project-steward/PLAN.md`](.project-steward/PLAN.md).
- Decisions: [`.project-steward/DECISIONS.md`](.project-steward/DECISIONS.md);
  open questions: [`.project-steward/QUESTIONS.md`](.project-steward/QUESTIONS.md);
  risks: [`.project-steward/RISKS.md`](.project-steward/RISKS.md);
  verification: [`.project-steward/VERIFY.md`](.project-steward/VERIFY.md).
- Discovery reading order: [`docs/discovery/README.md`](docs/discovery/README.md);
  terminology: [`docs/discovery/evidence/glossary.md`](docs/discovery/evidence/glossary.md).
- Instructions for coding agents working in this repository: [`AGENTS.md`](AGENTS.md)
  (`CLAUDE.md` imports it).

## Development

Prerequisites: [`uv`](https://docs.astral.sh/uv/) (0.11+) — it provisions
Python (`uv python install 3.11`) and the virtual environment.

```text
uv sync --all-groups          # create .venv and install dev tools
uv run ruff check .           # lint
uv run ruff format --check .  # formatting
uv run mypy                   # typecheck (strict)
uv run pytest                 # unit tests (no vendor CLI, no model call)
uv build                      # wheel + sdist
uv run python -m agentteam.schema check   # checked-in schemas reproduce
uv run atm --version
```

The nine V1 JSON Schemas under [`schemas/`](schemas/README.md) are generated
from the Pydantic models; regenerate with
`uv run python -m agentteam.schema export`.

The optional coordination provider is installed with `--extra clawteam`
(exact upstream revision; qualified at gate G4 — not needed for development).
Tests and CI never invoke a vendor model; live evidence is a separate,
owner-attended gate of the approved plan.

## Naming

- **AgentTeam** — the product and this repository (planned public home:
  `WSH95/AgentTeam`).
- **`atm`** — the product CLI.
- **legacy ATM** — the superseded agent-team-manager experiment.
- Dated discovery records (panel, critics, evidence, early plans) also use the
  working name "Assistant Team System" and a working CLI name `ats`. They are
  preserved as written and were not rewritten for the rename.

## License

MIT — see [`LICENSE`](LICENSE). Copyright (c) 2026 ShuhanWang.
Code origins and third-party notices: [`docs/provenance.md`](docs/provenance.md).
