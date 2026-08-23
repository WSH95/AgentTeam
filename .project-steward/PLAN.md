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

## M1a AgentTeam direct-harness PoC (approved — G0 done 2026-08-23)

Approved implementation plan (revision r3, approved text at `0f3e478`, DECISIONS 0021):
[`docs/plans/m1a-direct-harness-poc.md`](../docs/plans/m1a-direct-harness-poc.md).

- [x] Commit the completed M0.1 documentation review (`3407ec9`)
- [x] Record the owner-confirmed product identity, stack, auth, first-pass harness, model-policy, evidence, and live-test boundaries
- [x] Draft the exact direct-first implementation sequence, contracts, CLI, test matrix, live acceptance bar, publication gate, and stop rules
- [x] Commit the proposed plan and steward records as the multi-agent review baseline
- [x] Re-baseline the plan and current architecture documents for Python 3.11+/`uv`, a language-neutral edge, a built-in direct runner, and optional in-process coordination providers
- [x] Keep prospective API-test provider/model/endpoint selection unspecified across tracked documentation; preserve generic profile and secret-handling contracts
- [x] Independent review of the `3407ec9` baseline recorded (`docs/reviews/2026-08-23-m0-review-at-3407ec9.md`) with an independent M1 proposal for comparison (`docs/plans/m1-agentteam-direct-slice.md`); owner decisions in ADR 0018 — owner merges/selects before the approval step
- [x] Merge the independent proposal into M1a revision r2 (ADR 0019): selection precedence/`decided_by`, three Skills per harness, cross-OS hash identity, run record, probe levels, falsification routing, evidence bundle, docs-hygiene list, overlay deferred to M3, public repo at G2
- [x] Resolve the multi-agent review findings on r2 → revision r3 (ADR 0020): Claude recipe without `--safe-mode`, Grok `.grok/skills/`, pre-first-push checklist + gate-by-gate CI growth, Member execution binding (TEM §4 amended), Windows launcher policy + `.cmd` fake, computed hash only, required-Skill rule, promotion-only fixtures, waiver semantics, selection algorithm, V1 archive contract, budget ceiling 30
- [x] Incorporate multi-agent review findings without starting implementation (r3, ADR 0020)
- [x] Obtain explicit owner implementation approval, mark the reviewed plan `approved`, and commit any review resolutions (G0: DECISIONS 0021; status flipped)
- [x] G1 — rename/re-baseline the local project as AgentTeam (owner moved the repo 2026-08-23; root README/LICENSE/.gitattributes/.gitignore + identity amendments in `chore(project): rename project to AgentTeam`); documentation-hygiene docs-only commit (M1a §4 item 6; ADR 0022) — HB-03 register amendment deferred until the owner answers the QUESTIONS item; AGENTS command table waits for the G2 scaffold
- [ ] G2 — implement the Python 3.11+/`uv` foundation, Hatchling package, and checked-in V1 JSON Schemas; pass the pre-first-push checklist; create the public `WSH95/AgentTeam` repository (MIT) and push the scaffold after explicit approval; scaffold smoke matrix green on 3 OSes
- [ ] G3 — implement isolated Claude/Codex/Grok direct adapters (Skill channels, `decided_by`, Windows `.cmd` fake); adapter tests added to CI
- [ ] G4 — pass the deterministic direct-runner PoC locally (incl. solo mode, selection precedence, three Skills per harness, example-package hash identity) and qualify the optional, exactly pinned ClawTeam import/coordination seam without using its subprocess backend; write its qualification report
- [ ] G5 — complete owner-driven dedicated native-auth profile setup and the bounded day-one probes (verification levels recorded)
- [ ] G6 — pass the Ubuntu subscription-backed live PoC
- [ ] G7 — final CI matrices: credential-free core OS×Python matrix, optional ClawTeam compatibility matrix, and the vendor-smoke job; history secret scan repeated
- [ ] G8 — close M1a (reviewed sanitized evidence bundle committed; M1b draft names the local deterministic provider first and the ClawTeam exit criterion) and stop before TeamRun implementation

## M1b Team foundation (committed roadmap; outside the M1a approval scope)

- [ ] Prepare and approve a separate plan for TeamTemplate/TeamRun foundations, task/message/archive contracts, and the CoordinationSubstrate protocol
- [ ] Implement TeamRun orchestration and the optional ClawTeam provider behind the qualified compatibility boundary; keep harness launching on the built-in direct runner
- [ ] Preserve one AgentTeam-owned process data root with opaque team namespaces; claim namespace separation only

## M1c Dynamic-member PoC B (committed roadmap)

- [ ] Implement the product-owned dynamic-member policy gate and hidden/archive roster projections
- [ ] Prove the PoC B workflow with mechanical enforcement for every AgentTeam-mediated creation; record provider-bypass limits explicitly

## M2 Nested TeamRun PoC C + MCP (committed roadmap)

- [ ] Implement parent/child TeamRun lineage, result carrier, stop/cleanup, and isolation evidence
- [ ] Prove the PoC C nested-run acceptance contract
- [ ] Add an `atm` MCP server over the same versioned JSON contracts and core services

## M3 Evolution and artifacts (committed roadmap)

- [ ] Implement reviewed evolution overlays/proposals and portable artifact manifest/lock/resolution reporting

## M4 Long-running operations (committed roadmap)

- [ ] Implement deterministic watchers, RunStateSummary, decision log, and restart policy without requiring a resident LLM or gateway

## Optional later integrations and surfaces

- [ ] Reassess a small native TypeScript DSH adapter only if DSH becomes a primary daily harness; do not move the Python core for edge convenience
- [ ] Plan Hermes, OpenClaw, Telegram/surfaces, replaceable API-test providers, and any upstream ClawTeam changes independently when evidence and priority justify them
