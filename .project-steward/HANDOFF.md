---
updated_at: 2026-08-22T16:05:00Z
updated_by: claude (session 01HY9w7nNFHeMiAX7ZeUdVY2)
session_status: closed
branch: main
last_commit: (see git log — "docs(discovery): fit-gap matrix (W2a-1)" expected as HEAD)
---

# Handoff

## Now

M0 discovery phase. **Paused by user request after W2a-1.** Done and committed: Phase 0 (steward init, glossary, requirement register frozen at 54 rows, PoC acceptance criteria, intent prose), W1 (10 evidence files, ≈48k words, 288 findings), W2a-1 (`docs/discovery/existing-systems-fit-gap.md`: 54 requirements × 11 systems, 8 layers + XC, per-layer roll-ups, 54 gaps, 55 evidence gaps; lint clean; owner-reviewed for cross-layer consistency).

Headline fit-gap verdicts (see the doc's layer summaries): AD and TC layers are genuinely new relative to every substrate; TE, HB, AR, MS, LO are reachable at reuse rungs 1–3 on ClawTeam / OpenClaw / Hermes but with recurring new pieces — a nested-TeamRun *object* (parent link + inner coordination + result contract + archive), archive completeness for generic CLIs, a HarnessProfile data model + user>role>default selection policy, ensemble+synthesis, a harness-neutral Assistant with capability/artifact vocabulary, the reviewed-evolution overlay + Proposal object. Hermes (profiles/distributions, delegate_task, kanban) is a stronger substrate/backend candidate than the original recon assumed.

## In flight

- Nothing running. All workflow scripts for the remaining phases are pre-written in the session scratchpad (`/tmp/claude-1000/-home-wsh-Documents-assistant-team-system-dev/17fd77ac-75ce-402b-a1a9-5d1eebba9843/scratchpad/`): `w2a2-drafters.js` (reuse-vs-build, legacy-atm-disposition, assistant-domain-model, team-execution-model, harness-broker-model), `w2b1-panel.js` (3 biased architects → 2 judges), `w3-critics.js` (9 critics + completeness). **/tmp may not survive a reboot** — if missing, reconstruct from the approved plan `~/.claude/plans/i-am-starting-a-lucky-coral.md` (Phases 2–3 describe each agent's brief; ownership table + guardrails are in the plan's "Guardrails" section).
- Fit-gap source sections (merge inputs) also live in the scratchpad (`fitgap/{AD-EV,TC-TE,HB-AR,MS-LO}.md`); the merged document in the repo is the durable artifact.

## Next steps

1. Resume: `Workflow({scriptPath: "<scratchpad>/w2a2-drafters.js"})` → 5 documents. Then owner skim of "Inconsistencies noted" sections.
2. `Workflow({scriptPath: "<scratchpad>/w2b1-panel.js"})` → `scratchpad/arch/proposal-{A,B,C}.md` + `judge-{1,2}.md`. Owner reads both judge files, writes a tiebreak note, then a small synthesis agent writes `docs/discovery/architecture-options.md` (options compared on the shared rubric; panel + dissent; THE "smallest new layer" answer as one paragraph + one table), followed by a `minimal-poc-plan.md` drafter (PoC A/B/C on this host: Codex 0.148 / Claude Code 2.1.239 / ClawTeam subprocess backend (no tmux) / optional Hermes-OpenClaw; platform matrix; no Telegram).
3. `Workflow({scriptPath: "<scratchpad>/w3-critics.js"})` → `scratchpad/critics/*.findings.md`; fix pass (small fixes by owner; larger rewrites via fixer agents); re-run critics for docs with BLOCKER/MAJOR.
4. Owner full read-through of all 9 docs; fill the answer paragraph in `docs/discovery/README.md`; update PLAN/PROGRESS/DECISIONS/QUESTIONS/RISKS; commit `docs(discovery): M0 discovery documents (9) + evidence`; **STOP for product/architecture review** (no writing-plans, no code).

## Blockers

- None technical. Two usage cuts happened (session limit; Fable 5 limit — user upgraded). If an agent fails with a limit message, re-run only the missing outputs (pattern used in W1b/W2a-1b/d).

## Key files

- `docs/discovery/README.md` (index/status) · `product-intent.md` (register v3, frozen) · `evidence/glossary.md` · `evidence/*.md` (10) · `existing-systems-fit-gap.md` · `.project-steward/{PLAN,DECISIONS,QUESTIONS,RISKS}.md`.

## Tried and rejected

- Opus model override for fit-gap agents (W2a-1c): stopped after ~2 min once Fable was available again; no output kept (consistency of classification across layer pairs preferred).

## Warnings

- Discovery only: no production code, no PoC code; nothing pushed. Reference repos under `/home/wsh/Documents/00000/` are read-only. Probe venv under the scratchpad only.
- Evidence files carry `date: 2026-08-21/22` and pinned CLI versions; re-verify before PoCs if harness versions change.
