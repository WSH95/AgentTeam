# AgentTeam

**Status: alpha — pre-implementation.** AgentTeam is being built gate by gate
from an approved plan. As of this commit the repository holds discovery and
planning documentation only: there is no product code, no released package,
and no public distribution. Nothing here is stable yet.

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
| Product code, JSON Schemas, tests, CI | — | not yet (M1a gates G2–G7) |

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
