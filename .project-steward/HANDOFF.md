---
updated_at: 2026-08-23T04:30:00Z
updated_by: claude (session 01HY9w7nNFHeMiAX7ZeUdVY2)
session_status: closed
branch: main
last_commit: (HEAD) docs(discovery): M0 discovery documents (9) + evidence — STOP for review
---

# Handoff

## Now

**M0 discovery is complete and STOPPED for product/architecture review.** All nine documents are in `docs/discovery/` (index: `docs/discovery/README.md`), adversarially reviewed, fixed, re-checked (all PASS) and read through by the owner. No production code, no PoC code exists; nothing is pushed.

The answer (`architecture-options.md` §5, verbatim in README and `minimal-poc-plan.md` §1): a thin, format-independent Assistant/Team layer (working name `ats`) that owns only the data no existing system has (Assistant definitions + exclusion validator; TeamTemplates by reference; Base/User/Reviewed-Evolution overlays + Proposal/review record; HarnessProfiles + selection policy; invocation ledger + ensemble record; artifact manifest/lock/resolution report; TeamRun record, rosters, nesting contract, archive) behind two seams — HarnessAdapter and CoordinationSubstrate — with one implementation each today (five harness adapters planned, claude-code + codex in the PoC-A slice; ClawTeam 0.3.0@0119833 over its CLI, subprocess backend, no tmux; plus a trivial `direct` launcher). M ≈4–6k LOC incl. data; PoC-A slice ≈2–3k. Not built: a second team substrate, a ClawTeam fork, library-seam coupling, Surface adapters, an artifact installer, a UI, any DAG/mailbox/liveness of our own.

## In flight

- Nothing. Background workflows are all complete. Scratchpad (under /tmp) holds only working copies; every durable artifact is in the repo.

## Next steps (for the owner, then for the next session)

1. Owner reviews `docs/discovery/README.md` → `architecture-options.md` (§5 answer, §5.0 assumptions, §5.1 M-row coverage, §7 questions) → `minimal-poc-plan.md`; skims the three model documents, the fit-gap matrix, reuse-vs-build and the ATM disposition.
2. Owner answers `.project-steward/QUESTIONS.md` Q1–Q10 (language; Windows/macOS probe host + precondition?; acceptable enforcement levels; file ClawTeam PRs?; unattended-run credentials; Hermes Member in PoC B?; ATM licence statement; PoC budget + no-op tier; ensemble synthesis harness; Member coordination protocol per substrate?).
3. Only after that: a new phase. If the answer is accepted, the next session runs the brainstorming → writing-plans path for the PoC-A slice as defined in `minimal-poc-plan.md` §3 (day-one probes (a)–(d) first). If rejected or amended, revise `architecture-options.md` §5 and re-run the affected critics.

## Blockers

- None technical. Decisions Q1–Q10 are the owner's.

## Key files

- `docs/discovery/README.md` (index, answer, STOP) · `product-intent.md` (register v3.2, frozen) · `architecture-options.md` · `minimal-poc-plan.md` · `existing-systems-fit-gap.md` · `reuse-vs-build-analysis.md` · `assistant-domain-model.md` · `team-execution-model.md` · `harness-broker-model.md` · `legacy-atm-disposition.md` · `evidence/` (glossary, 10 evidence files, `panel/`, `critics/`).
- `.project-steward/{PLAN,DECISIONS (0001–0009),QUESTIONS (Q1–Q10),RISKS,VERIFY}.md`.

## Tried and rejected

- Opus model override for fit-gap agents (stopped; consistency preferred). AGENTS.md update at end of M0 (owner chose to keep it untouched — DECISIONS 0008).

## Warnings

- Discovery only; do not start implementation until the owner closes the review gate. Reference repos under `/home/wsh/Documents/00000/` stay read-only. Evidence is version-pinned (Claude Code 2.1.239, Codex 0.148.0, Grok 1.0.5, OpenClaw 2026.7.1-2, Hermes 0.20.4, ClawTeam 0.3.0@0119833) — re-verify flags before PoCs if versions change.
