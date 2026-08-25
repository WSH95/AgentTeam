# AgentTeam

**Status: alpha.** AgentTeam is being built gate by gate from approved plans.
The direct runner and batch TeamRun milestones are complete. The M1c
interactive TeamRun foundation is locally green through its deterministic
lifecycle and client-protocol gates; cross-platform and current-runtime
qualification remain before any interactive live-support claim. There is no
released package and interfaces and records are not stable yet.

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
| Product CLI, packaging, tests, CI | `pyproject.toml`, [`src/agentteam/`](src/agentteam/), [`tests/`](tests/), [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | alpha; validation, libraries, profiles, direct/batch runs, and interactive lifecycle |
| Versioned domain records + checked-in JSON Schemas | [`src/agentteam/domain/`](src/agentteam/domain/), [`schemas/`](schemas/README.md) | original V1 bytes preserved; V2 Team and closed interactive records added |
| Claude/Codex/Grok adapters and direct/batch runner | [`src/agentteam/harness/`](src/agentteam/harness/), [`src/agentteam/run/`](src/agentteam/run/) | M1a/M1b complete with deterministic, hosted, and bounded live evidence |
| Interactive TeamRun foundation | [`src/agentteam/interactive/`](src/agentteam/interactive/), [`src/agentteam/execution/`](src/agentteam/execution/), [`docs/interactive-teamruns.md`](docs/interactive-teamruns.md) | deterministic G3/G4 locally green; current-runtime and live qualification pending |

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

The versioned JSON Schemas under [`schemas/`](schemas/README.md) are generated
from the Pydantic models; the original V1 direct/batch files remain
byte-stable. Regenerate with
`uv run python -m agentteam.schema export`.

## Interactive TeamRuns

Interactive chat resolves an exact immutable Assistant or Team revision,
creates fresh provider-owned Member sessions, and serializes all turns over
one user-supplied worktree. AgentTeam observes Git/tree state but never
commits, resets, stashes, checks out, or cleans user files.

```text
uv run atm assistant import examples/assistants/implementer
uv run atm runtime install direct-acp      # explicit pinned npm download, only when wanted
uv run atm runtime doctor direct-acp --harness codex  # zero model calls

uv run atm assistant chat implementer --version 1 \
  --workspace /path/to/project --goal "Fix the bounded issue" \
  --done-when "the focused tests pass"

uv run atm runs list
uv run atm runs status RUN_ID
uv run atm runs attach RUN_ID
uv run atm runs export RUN_ID /empty/audit-directory
uv run atm runs cleanup RUN_ID
```

`assistant chat` synthesizes a one-Member Team; `team chat` uses an exact
TeamTemplateV2 catalog revision. Add `--stream-json` for negotiated,
correlated bidirectional NDJSON instead of the attended TTY. Runtime
installation is never implicit, raw provider turn streams remain local, and
sanitized export omits those streams and run-scoped runtime state. Chat also
requires a current owner-only per-harness qualification bound to the exact
runtime tree, native version, profile environment, and platform; stale or
missing evidence claims no support. See
[`docs/interactive-teamruns.md`](docs/interactive-teamruns.md) for lifecycle,
permission, recovery, protocol, and provider-integration details.

Native subscription setup is deliberately owner-attended:

```text
uv run atm profile init            # creates owner-only homes and prints login commands
# run each printed vendor login command yourself
uv run atm profile doctor          # no model call; sanitized install/login/readiness status
uv run atm profile doctor --probe  # TTY required; confirms each of at most 2 calls/harness

# Deliberately retest all three even when their current evidence is ready:
uv run atm profile doctor --probe --reprobe-ready \
  --harness claude-code --harness codex --harness grok
```

Normal `--probe` skips profiles whose evidence is already current. `--harness`
limits calls (it is repeatable, and `claude` aliases `claude-code`), while
`--reprobe-ready` makes the new assessment authoritative: a failed call can
downgrade previously verified capability rows. AgentTeam still preflights all
three installations before the first selected call and prompts on stderr
immediately before every vendor invocation.

Capability rows are a vendor-specific inventory, not a requirement that every
fallback be exercised. `verified` means the exact behavior passed under the
recorded CLI version/time; `observed` means the flag or mechanism is known but
was not exercised; `unverified` means it has not passed or an assessment did
not select it. A probe stops when all required behavior and one current channel
from each fallback ladder pass, so successful primary channels intentionally
leave unused fallbacks as `observed`.

Profiles created by `profile init` explicitly inherit the standard proxy
variables already present in the launching terminal (`HTTP_PROXY`,
`HTTPS_PROXY`, `ALL_PROXY`, and `NO_PROXY`, including lowercase variants).
The printed login commands set only the dedicated vendor config-home variable;
they do not unset or replace the terminal's network configuration. An owner can
set `proxy_policy: deny` explicitly for an isolated profile.

Probe captures remain local under `~/.agentteam/probes/`; AgentTeam never
reads or copies credential files and never promotes raw captures automatically.

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
