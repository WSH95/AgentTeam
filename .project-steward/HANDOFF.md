---
updated_at: 2026-08-24T21:08:16Z
updated_by: claude
session_status: active
branch: main
last_commit: 9802775
---
# Handoff

## Now

**The M1b plan is at draft r2 — reviewed once, findings resolved, NOT
approved.** Sequence this session: r1 (expanded plan, `14dc218`) → the
owner delivered the independent review (verdict "do not approve yet": 7
approval-blocking findings + 3 hygiene items — every one re-verified
against the tree and confirmed real) → the review is recorded verbatim as
an immutable dated record `docs/reviews/2026-08-24-m1b-plan-review-at-14dc218.md`
(`9802775`) → **r2 resolves all ten findings** (the commit carrying this
handoff; resolution table in plan §21; ADR 0039). Highlights of r2:
explicit ClawTeam disposition at close (`parity-green | failed-routed |
dropped-by-owner`); run record as a mode-discriminated `oneOf` union with
jsonschema-level negative tests (2 new + 2 regenerated schema files);
HB-03 constraints **deferred out of M1b entirely** (owner decision, ADR
0039 — preference layer only); a new minimal `implementer` example
Assistant so `decided_by: team` and mixed harnesses are real acceptance
evidence; a decision-complete task data flow (skeleton ids, required
`goal`, owner bijection, launch-on-ready with staged 7a/7b rendering,
HandoffPayload claim-and-embed transport, failure-cascade vs fault-abort);
`create_space(*, lead)` replacing the seam's hard-coded `atm-lead`; the
§11.4–11.6 finalization invariant, message ledger, and snapshot copy-out;
a fault-injection matrix as G3 evidence; and a static import-containment
scan enforcing the exit-criterion boundary.

## In flight

Nothing after the r2 commit. Zero live calls spent; tree green
(453 passed + 4 skipped under a plain terminal).

## Next steps (a NEW approval scope — nothing starts automatically)

1. **Owner G0 decision on r2** — either: approve (a DECISIONS entry
   naming `docs/plans/m1b-team-foundation.md` + r2's commit SHA; the
   status line flips to `approved` in the following commit), **or** send
   r2 for a confirmation re-review first (fresh session against r2's
   frozen SHA, same `docs/reviews/` record convention; plan §20 is the
   charter, §21 the r1→r2 resolution table to spot-check).
2. Only after G0: implementation per plan §3 gates G1–G7 and §16 commit
   boundaries. First code commit is `feat(domain): …` (G1).
3. At G0 the approval ADR also carries the glossary CoordinationSubstrate
   `stop` amendment (plan §20 follow-up; review hygiene item 1).
4. Pushes: `main` is now 3 ahead of origin (`14dc218`, `9802775`, the r2
   commit); **nothing pushed** — every push needs explicit owner approval
   (`never_push = true`).

## Blockers

None mechanical. Implementation is blocked by design on G0. The open
owner items are: G0 itself, the §20 finalize-at-approval list
(exit-criterion wording + measurement rule, zero-live budget, CLI verb
set, reserved-field sets), and — independent of M1b — the HB-03 semantic
question (open in QUESTIONS.md with recorded options).

## Key files

- `docs/plans/m1b-team-foundation.md` — **r2, the approval target** (§21
  maps every review finding to its resolution).
- `docs/reviews/2026-08-24-m1b-plan-review-at-14dc218.md` — the r1 review,
  immutable, valid for `14dc218` only.
- `.project-steward/DECISIONS.md` ADR 0039 — review recorded; HB-03
  deferred; next-step contract.
- `docs/plans/m1a-direct-harness-poc.md` — house style; every "M1a §N"
  pointer targets it.
- `docs/evidence/clawteam-qualification-2026-08-23.md` — 233/281 LOC
  baseline + the four caveats; `src/agentteam/compat/clawteam.py` — the
  seam whose `create_space` gains the `leader` parameter at G5.

## Tried and rejected (session highlights for a successor)

- Every review finding was verified against the tree BEFORE resolution;
  none was taken on faith (per-finding anchors in ADR 0039/PROGRESS).
- Rejected: treating the review's finding 3 by fully specifying HB-03
  option A in r2 — the owner chose Defer (smallest M1b, review's own
  recommendation).
- Rejected: putting message bodies in `events.jsonl` (violates the events
  contract "ids, names, short details only") — the ledger
  `coordination/messages.jsonl` with hash-linked `message-sent` events is
  the durable history instead.
- Rejected: a new `aborted` run status (`RunStatus` has `cancelled`;
  no new status value ships) and sibling-termination on task failure
  (M1a terminates trees only for that invocation's cancel/timeout —
  hence the cascade/abort split).

## Warnings

- **5 of 30 live calls remain from M1a; M1b's budget is ZERO live calls**
  (plan §11/§17); any live urge routes to the M1c plan.
- r2 is NOT approved: no product code, no schema files, no register or
  glossary amendments until G0.
- Local pytest on this host needs a plain terminal:
  `env -u PYTHONPATH NO_COLOR=1 TERM=dumb uv run pytest` (rich ANSI breaks
  one doctor --help assertion; a ROS-Foxy PYTHONPATH leak breaks
  collection). Neither is a tree problem.
- Capability evidence stays version-bound (Claude 2.1.241 / Codex 0.149.1
  / Grok 1.0.5); Grok re-entry needs fresh probes + an owner decision
  (ADR 0036).
