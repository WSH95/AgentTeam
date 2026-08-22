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

## 0007 — 2026-08-22 — Architecture answer: thin format-independent layer over ClawTeam CLI with two declared seams

**Context**: Architecture panel (three biased architects — ClawTeam-maximalist, independent layer, upstream-extension-first — scored by two judges on a shared R1–R10 rubric; records in `docs/discovery/evidence/panel/`). Both judges independently endorsed the same composition; the session owner confirmed it as tiebreak.
**Decision**: The smallest new software layer = A's O2 scope with B's two seams: substrate-neutral data (Assistant definitions + exclusion validator, TeamTemplates by reference, overlays + Proposal/review record, HarnessProfiles + selection policy, invocation ledger + ensemble record, artifact manifest/lock/resolution report, TeamRun record/rosters/nesting contract/archive) behind exactly two seams — HarnessAdapter and CoordinationSubstrate — with one implementation each today (five harness adapters; ClawTeam 0.3.0@0119833 over its CLI, subprocess backend, no tmux) plus a trivial `direct` launcher for solo/ensemble legs. No second team substrate, no ClawTeam fork, no library-seam coupling (in-process backend = documented Windows fallback only), no surface adapters (OpenClaw/Telegram remain optional O4), no artifact installer, no UI. Build by slice: PoC-A slice first (≈2–3k LOC), run layer gated on PoC A.
**Consequences**: `docs/discovery/architecture-options.md` states the answer (one paragraph + one table); `minimal-poc-plan.md` tests it; ClawTeam PRs are filed as intent and planned as if none merges; TC-05/TE-05 enforcement levels are labeled honestly (gate+convention; recorded isolation). Owner-level open questions recorded in `QUESTIONS.md`.

## 0008 — 2026-08-23 — AGENTS.md left untouched at the end of M0 (owner decision)

**Context**: The session proposed a one-time addition to `AGENTS.md` (pointers to `docs/discovery/`, normative glossary/register rules, read-only reference repos, phase-gate note) outside the managed blocks.
**Decision**: The owner chose to keep `AGENTS.md` unchanged for now. The same guidance lives in `.project-steward/HANDOFF.md` and `docs/discovery/README.md`.
**Consequences**: Successor sessions must read `HANDOFF.md` first (per the session protocol) to find the discovery deliverables and conventions; any future AGENTS.md change still requires a diff + explicit approval.

## 0009 — 2026-08-23 — W3 fix-pass owner decisions (D1–D15) amend tiebreak assumption (e)

**Context**: Adversarial critics (9 per-document + completeness) found two blockers and ~25 majors, several needing a single cross-document decision. The owner wrote binding decisions D1–D15 (`docs/discovery/evidence/critics/owner-decisions-fix-pass.md`).
**Decision**: Notably — D1: the nested-run result carrier is the layer-owned outer `run.json` + inner archive, signalled by `clawteam inbox send`, delegated task closed by `task update --status completed` (`task update --metadata` does not exist in ClawTeam 0.3.0@0119833), amending tiebreak assumption (e); D3: `independence {declared: advisory|mechanical, achieved: namespace|data-dir|mechanical}`; D7: fit-gap cells where "our layer carries it" are `Xs`, not `P` (TE-05/TE-07/HB-04 CT re-scored); fit-gap rung columns are non-binding; D8: reuse bolding rule restated, new rung tally 17/7/0/1/0/28/1; D9: Ephemeral origin lives on the Member, never in the definition; D10: TC-05 = gate + convention + `CLAWTEAM_BIN` shim + post-hoc reconciliation until enforced.
**Consequences**: All nine documents say one thing on these points; `architecture-options.md` §5.0 enumerates the owner assumptions with attribution; the answer paragraph is byte-identical across architecture-options §5, minimal-poc-plan §1 and README.
