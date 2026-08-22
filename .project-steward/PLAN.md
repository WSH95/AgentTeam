# Plan

Milestones and tasks. If an external task backend is adopted, this file
holds milestones + a pointer only (never a duplicate task list).

## M0 Discovery: 9 analysis documents self-reviewed, then STOP for product/architecture review

Detailed execution plan (approved 2026-08-21): `~/.claude/plans/i-am-starting-a-lucky-coral.md` (session-local; the durable summary is this file + `docs/discovery/README.md`).

- [x] Phase 0 — steward init; `docs/discovery/README.md`; `evidence/glossary.md`; requirement register + PoC acceptance criteria in `product-intent.md`
- [x] Phase 0 — initial commit `chore: initialize Project Steward project management` (78272d8)
- [x] W1 "Understand" (189ea87) — 10 evidence agents → `docs/discovery/evidence/*.md` (clawteam-model, clawteam-spawn-platform, clawteam-probe-log, fork-delta, openclaw-native-and-telegram-verification, harness-cli-capabilities-a/-b, dsh-agent-teams-and-gui, claude-agent-teams-hermes-openbot, atm-salvage)
- [x] `product-intent.md` prose completed; register frozen 2026-08-22 (AR-06 added)
- [x] W2a-1 — fit-gap matrix (4 agents, 2 layers each) → merged `existing-systems-fit-gap.md`
- [ ] W2a-2 — `reuse-vs-build-analysis.md`, `legacy-atm-disposition.md`, `assistant-domain-model.md`, `team-execution-model.md`, `harness-broker-model.md` (script ready: scratchpad/w2a2-drafters.js)
- [ ] W2b — architecture panel (3 biased architects → 2 judges → synthesis) → `architecture-options.md`; then `minimal-poc-plan.md`
- [ ] W3 — per-document adversarial critics + completeness critic; fix pass
- [ ] Self-review: full read-through of all 9 docs; `README.md` answer paragraph
- [ ] Steward bookkeeping (PROGRESS/DECISIONS/QUESTIONS/RISKS/HANDOFF); commit `docs(discovery): M0 discovery documents (9) + evidence`
- [ ] **STOP for product/architecture review** (no writing-plans, no code)

## M1 (placeholder — only after M0 review)

- [ ] PoC A/B/C as defined in `docs/discovery/minimal-poc-plan.md` — scope and language decided at review

## Later

- [ ] Decide final project name and implementation language
