# Assistant Team System — project charter

Portable, harness-independent Assistant definitions and reusable Team templates, executed as fresh TeamRuns over existing agent harnesses (ClawTeam, Claude Code, Codex, OpenClaw, Hermes, ...). Supersedes the ATM experiment.

- Created: 2026-08-22T01:42:57Z (Project Steward 0.3.2)
- Primary language/stack: Markdown (discovery phase; implementation language TBD after architecture review)
- Working name: "Assistant Team System" (final name is an open question; do not assume "ATM").

## Goals

- Make the **portable Assistant definition** (a reusable specialized colleague) the primary product object — not a runtime agent, process, session or workspace.
- Compose Assistants into reusable **TeamTemplates**; execute them as fresh **TeamRuns** with project/workspace supplied at run time; support ephemeral (hidden, auditable) members and **nested TeamRuns**.
- Keep Assistant identity independent of any coding harness; a **HarnessBroker** selects, falls back, or fans out (ensemble + synthesis) across Claude Code / Codex / Grok / OpenClaw / Hermes / future engines and deterministic backends.
- **Reviewed, project-independent evolution** (Base + User Overlay + Reviewed Evolution Overlay; proposals, never silent mutation).
- Portable Skill/plugin/artifact dependencies (semantic capability vs explicit artifact; no secrets in portable config).
- Messaging surfaces optional; fully useful locally; cross-platform (Ubuntu/Windows/macOS; tmux not the only path).
- M0 (this phase): discovery only — nine documents under `docs/discovery/` answering "what is the smallest new software layer that genuinely needs to be built?", then STOP for review.

## Non-goals

- No production code and no PoC code in M0 (PoCs are defined, not built).
- No inheritance of the ATM architecture as baseline (ATM is a source of requirements, experiments, failure evidence and research only).
- Core is not built around Telegram groups/topics or OpenClaw deployment reconciliation.
- Not integrating every reference system; understand which layer each solves well.

## Users / stakeholders

- Primary: the project owner (researcher/engineer running code, paper and training-operations teams across several coding harnesses, locally and optionally via Telegram).
- Secondary: future users who import portable Assistant/TeamTemplate packages on other hosts/OSes.

## Constraints

- Reuse ladder: configuration/composition → thin adapter → upstream-friendly extension → selective licensed module reuse → fork only when necessary → new implementation only when nothing else satisfies. Verify licenses before proposing source reuse (reference repos are MIT; ATM is the owner's own).
- Cross-platform target: Ubuntu, Windows, macOS. This host: Ubuntu, **no tmux**, Claude Code 2.1.239, Codex 0.148.0, OpenClaw 2026.7.1-2, Hermes 0.20.4, Grok 1.0.5, uv Python 3.11/3.13 (system 3.8).
- Discovery probes are isolated (scratch venv, throwaway data dirs); web lookups allowed with URL + date citations; nothing pushed to remotes.
- Security/privacy: no secrets in portable definitions; read config structure only, never token values, when inspecting local tool state.
