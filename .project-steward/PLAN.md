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
- [x] W2a-2 (700485a) — `reuse-vs-build-analysis.md`, `legacy-atm-disposition.md`, `assistant-domain-model.md`, `team-execution-model.md`, `harness-broker-model.md`
- [x] W2b (e15b6f2) — architecture panel (3 biased architects → 2 judges → owner tiebreak → synthesis) → `architecture-options.md`; then `minimal-poc-plan.md`
- [x] W3 — per-document adversarial critics + completeness critic (c01b910 findings); fix pass under owner decisions D1–D15; re-checks all PASS
- [x] M0 critic/fix-pass records preserved as historical evidence; the former 2026-08-23 owner-read-through claim is not relied upon by current verification
- [x] Steward bookkeeping (PROGRESS/DECISIONS/QUESTIONS/RISKS/HANDOFF); final commit `docs(discovery): M0 discovery documents (9) + evidence`
- [x] M0 discovery package delivered; no code

## M0.1 Product/architecture review and documentation refresh (2026-08-22)

- [x] Verify current installed CLI versions, headless/isolation flags, sanitized auth state, and current OpenClaw/Telegram facts without live model calls or credential reads
- [x] Record owner decisions: hosted CI boundary; advisory PoC/mechanical production enforcement; native subscription OAuth; ATM reuse authorization; Claude Code + Codex + Grok Build first pass; API-test provider separation
- [x] Correct AD-07's omitted hidden-if-desired clause and its derived fit-gap text; retain the other matrix analysis
- [x] Mark the detailed M0 PoC proposal provisional and re-baselining-required; do not schedule a specific draft source or implementation
- [x] Run documentation regression checks and close M0.1 handoff

## M1 (placeholder — only after a detailed plan is reviewed and approved)

- [ ] Produce and review a re-baselined PoC plan consistent with the confirmed constraints; implementation language, run shapes, schemas, synthesis, sequence, and budget remain open

## Later

- [ ] Decide final project name and implementation language
