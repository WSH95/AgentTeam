# Decisions (ADR-lite, append-only)

## 0001 — 2026-08-22T01:42:57Z — Adopt Project Steward

**Context**: The project needs durable, cross-agent continuity.
**Decision**: Manage state in `.project-steward/` with AGENTS.md as the
canonical instruction file and CLAUDE.md as a thin Claude Code adapter.
**Consequences**: Sessions are resumable across tools and devices via git.

## 0002 — 2026-08-21 — ATM is superseded, not the baseline

**Context**: The prior experiment (agent-team-manager-dev) centered on runtime deployment reconciliation, persistent runtime agents, sessions/workspaces, OpenClaw materialization and project-level A2A isolation; its pipeline never ran end-to-end.
**Decision**: ATM is a source of requirements, experiments, failure evidence and research only. Its demoted concepts (OpenClaw-centered reconciliation, persistent runtime Agent identity as Core, ProjectRoleContext/workspace/session as central model, custom A2A router, hard same-user cross-project isolation, OpenClaw agent-ID/adoption machinery, Telegram topology as Team semantics) may not re-enter the architecture without fresh evidence.
**Consequences**: `docs/discovery/legacy-atm-disposition.md` records keep/demote/discard per concept.

## 0003 — 2026-08-21 — The portable Assistant definition is the product object

**Context**: Product brief §1–§3.
**Decision**: Assistant (definition) ≠ Skill ≠ harness ≠ runtime agent. Persistent: Assistant definitions, TeamTemplates, reviewed evolution. Fresh by default: AssistantInstances, TeamRuns, sessions; project/workspace supplied at execution time.
**Consequences**: Normative glossary in `docs/discovery/evidence/glossary.md`; requirement register in `docs/discovery/product-intent.md`.

## 0004 — 2026-08-21 — ClawTeam is the leading candidate substrate for team execution, to be fit-gapped, not presumed

**Context**: Brief §12; reconnaissance shows ClawTeam provides dynamic spawning, task DAG, inbox, worktrees, multi-CLI adapters, MCP server; it lacks persona/role packages, nested teams, and per-team harness policy.
**Decision**: Evaluate ClawTeam as-is / configured / extended upstream / wrapped, against every requirement, alongside the other systems. No architecture is chosen before `existing-systems-fit-gap.md` and `architecture-options.md` exist.
**Consequences**: W1 includes an isolated ClawTeam probe on this tmux-less host.

## 0005 — 2026-08-21 — Discovery deliverables live in `docs/discovery/`; messaging surfaces are optional

**Decision**: The nine discovery documents and their evidence files live under `docs/discovery/` with the exact filenames from the brief. Telegram/OpenClaw are treated as optional Surfaces; no Core concept depends on them.
**Consequences**: PoCs A–C are defined without Telegram/OpenClaw unless analysis proves necessity.

## 0006 — 2026-08-21 — Discovery method: multi-agent workflows with owner-held anchors

**Context**: ~19k LOC ClawTeam, a 112-commit fork, six other repos and web verification exceed one context; the brief demands source-level analysis and adversarial pressure tests.
**Decision**: Evidence (W1) → fit-gap/reuse/models (W2a) → architecture judge panel (W2b) → adversarial critics (W3) as workflows; the owner (this session) writes the glossary, requirement register, product-intent prose, merges fit-gap, tiebreaks the panel, and performs the final read-through. Web verification and isolated probes approved by the user.
**Consequences**: Evidence files follow one schema and never recommend; each pressure test has exactly one owning document.
