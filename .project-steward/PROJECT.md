# AgentTeam — project charter

Portable, harness-independent Assistant definitions and reusable Team templates, executed as fresh TeamRuns over existing agent harnesses (Claude Code, Codex, Grok Build, ClawTeam, OpenClaw, Hermes, ...). The product CLI is `atm`. Supersedes the legacy ATM experiment (agent-team-manager), which remains a source of requirements, experiments, failure evidence and research only.

- Created: 2026-08-22T01:42:57Z (Project Steward 0.3.2)
- Primary language/stack: Python `>=3.11` with `uv` and Hatchling; JSON Schema at external boundaries; Markdown documentation. Product code starts at M1a gate G2.
- Product name: AgentTeam. CLI: `atm`. Local directory: `/home/wsh/Documents/AgentTeam` (since 2026-08-23). Planned public repository: `WSH95/AgentTeam` (MIT); its creation and the first push need their own explicit approval at M1a G2.
- Where the rest lives: milestones/gates in `PLAN.md` and `docs/plans/`; current state in `HANDOFF.md`; decisions in `DECISIONS.md`; open questions in `QUESTIONS.md`; risks in `RISKS.md`; volatile facts (installed tool versions, check results) in `VERIFY.md` and each plan's runtime baseline — never in this charter.

## Goals

- Make the **portable Assistant definition** (a reusable specialized colleague) the primary product object — not a runtime agent, process, session or workspace.
- Compose Assistants into reusable **TeamTemplates**; execute them as fresh **TeamRuns** with project/workspace supplied at run time; support ephemeral (hidden, auditable) members and **nested TeamRuns**.
- Keep Assistant identity independent of any coding harness; a **HarnessBroker** selects, falls back, or fans out (ensemble + synthesis) across Claude Code / Codex / Grok / OpenClaw / Hermes / future engines and deterministic backends.
- **Reviewed, project-independent evolution** (Base + User Overlay + Reviewed Evolution Overlay; proposals, never silent mutation).
- Portable Skill/plugin/artifact dependencies (semantic capability vs explicit artifact; no secrets in portable config).
- Messaging surfaces optional; fully useful locally; cross-platform (Ubuntu/Windows/macOS; tmux not the only path).

## Success criteria

The owner-level definition of success is `docs/discovery/product-intent.md` §1.6–§1.7 (fully useful locally; fewer re-created prompts; the same reviewer colleague giving consistent judgment across harnesses and projects; teams re-instantiated on a new project in minutes; auditable hidden and nested delegation; learning that survives projects without dragging project facts along). The project is on track when, milestone by milestone, the evidence below exists in the repository; each milestone plan states the exact gate evidence.

- **M1a (approved plan `docs/plans/m1a-direct-harness-poc.md`)**: one portable Assistant definition with its Skills is resolved unchanged and executed on Claude Code, Codex, and Grok Build through the built-in direct runner; mechanical conditions (identical definition hash, recorded invocations, attributable synthesis) and semantic conditions (product-useful review judgment) are recorded separately; deterministic credential-free evidence runs in hosted CI on Ubuntu/Windows/macOS; live subscription-backed evidence is attended, budget-capped, sanitized, and reviewed before it is committed.
- **M1b–M2**: TeamTemplates execute as fresh TeamRuns with hidden ephemeral members and nested runs over an optional coordination substrate behind the CoordinationSubstrate seam; declared vs achieved enforcement is recorded honestly; an `atm` MCP server exposes the same versioned contracts.
- **M3–M4**: Assistants evolve only through reviewed overlays and proposals; artifacts resolve portably across hosts; long-running operations run on deterministic watchers without a resident LLM.
- **Always**: no secret is stored in a portable definition or committed; every public claim (isolation, enforcement, platform support, qualification of an optional provider) matches evidence on record; nothing is pushed or published without its explicit approval.

## Non-goals

- No inheritance of the ATM architecture as baseline (ATM is a source of requirements, experiments, failure evidence and research only).
- Core is not built around Telegram groups/topics or OpenClaw deployment reconciliation.
- Not integrating every reference system; understand which layer each solves well.
- No product code outside an approved milestone plan. M0/M0.1 were documentation-only by design; every later milestone (M1b onward) needs its own reviewed plan and explicit owner approval before implementation.

## Users / stakeholders

- Primary: the project owner (researcher/engineer running code, paper and training-operations teams across several coding harnesses, locally and optionally via Telegram).
- Secondary: future users who import portable Assistant/TeamTemplate packages on other hosts/OSes.

## Constraints

- Reuse ladder: configuration/composition → thin adapter → upstream-friendly extension → selective licensed/authorized module reuse → fork only when necessary → new implementation only when nothing else satisfies. ATM is owner-authorized for internal copy/adaptation; retain provenance and third-party notices.
- Cross-platform target: Ubuntu (the owner's host; no tmux), Windows, macOS. GitHub-hosted CI verifies deterministic direct-runner plumbing and the optional ClawTeam import/coordination seam, not live auth/model behavior; live acceptance stays on the owner's Ubuntu host.
- Harness scope is decided per milestone and recorded in `DECISIONS.md`/`PLAN.md` (first pass: Claude Code + Codex + Grok Build, ADR 0011/0013; Hermes/OpenClaw deferred), not fixed by this charter.
- Runtime boundary: the direct shell-free Python process runner is built in. Coordination substrates are optional. ClawTeam is the first optional provider, pinned by full commit and imported only in one owned compatibility module; its built-in subprocess backend is excluded.
- Native and unattended live runs use vendor subscription OAuth on the owner's persistent host. API-test gateways are separate, replaceable profiles with runtime environment-key injection; never store key values or use API mode as a native-auth fallback. Hosted CI receives no live credentials.
- PoC controls may be advisory only when bypassability is visible and audited; production claims require mechanical enforcement. Hidden is a user-interface projection, not an access-control claim.
- Probes are isolated (scratch venv, throwaway data dirs); web lookups allowed with URL + date citations; nothing is pushed to a remote without explicit approval.
- Security/privacy: no secrets in portable definitions; read config structure only, never token values, when inspecting local tool state.
