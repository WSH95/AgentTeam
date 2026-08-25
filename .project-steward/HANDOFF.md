---
updated_at: 2026-08-25T00:21:44Z
updated_by: codex
session_status: active
branch: main
last_commit: 84c7919
---
# Handoff

## Now

**The M1b plan is at draft r5 after four independent review rounds; all
current findings are resolved in the plan, but r5 is NOT approved.** The
fourth review froze r4 at full commit
`3d0211a456cedb356aa512cb5f257b448dbb70e1` and plan SHA-256
`e1c7f222ce22785b37eb22fca553281d0936b5367313a3a7b9a1d38c587200c9`;
its immutable record is
`docs/reviews/2026-08-24-m1b-plan-review-at-3d0211a.md` (`84c7919`).
It found 3 high contract gaps, 3 medium implementation gaps, and 4
consistency corrections.

r5 (the commit carrying this handoff; §21 r4→r5 table; ADR 0042)
resolves them with:

- explicit per-task `workspace_access`, read-only by default and audited
  in `tasks[]`; only the fixture's implement task is writable;
- exact least-privilege mappings for Claude/Codex/Grok, with fail-closed
  custom Grok profiles for both team grants; direct/synthesis rendering
  remains unchanged;
- null execution = no durable invocation allocation, with final render →
  pending invocation → run binding → provider running → spawn, and a
  cross-file archive verifier;
- a state-free render-only branch and disposable normal preflight roots;
- `cleanup(space, copy_out_verified=...) -> CleanupOutcome`, so
  ClawTeam deletes only a verified snapshot and events never expose its
  stable root;
- one completion publication barrier before provider auto-unblock;
- NFC/casefold/component-safe deliverables that cannot re-export
  renderer-owned AGENTS/Skill paths; and
- exact occurrence-level ClawTeam containment plus a failed-routed
  reproduction that remains collected outside the skipped success suite.

## In flight

Nothing after the r5 planning commit. Product implementation has not
started. Planning-only validation is green: frozen r4 hash exact; 453
passed + 4 skipped; Ruff clean; mypy clean across 98 source files;
schemas current; diff check clean. Zero live calls were spent.

## Next steps (a NEW approval scope — nothing starts automatically)

1. **Owner G0 decision on r5** — approve via a DECISIONS entry naming
   `docs/plans/m1b-team-foundation.md` and r5's commit SHA, or commission
   another independent review against r5's frozen SHA.
2. Only after G0: execute plan gates G1–G7 and §16 commit boundaries.
3. At G0, carry the glossary CoordinationSubstrate `stop` amendment
   listed in plan §20.
4. Push only on a separate explicit owner approval; the two r5-session
   commits are local.

## Blockers

No mechanical blocker. Product implementation is intentionally blocked
on G0. Live writable-member claims are additionally deferred to M1c,
which must re-probe then-supported clients and run one declared-deliverable
acceptance per supported harness.

## Key files

- `docs/plans/m1b-team-foundation.md` — **r5, the approval target**.
- `docs/reviews/2026-08-24-m1b-plan-review-at-{14dc218,54728c8,6d3f329,3d0211a}.md`
  — four immutable review records.
- `.project-steward/DECISIONS.md` ADRs 0039–0042 — the review/resolution
  trail.
- `.project-steward/RISKS.md` R36 — writable-client evidence boundary.

## Tried and rejected

- Rejected implicit writable behavior: every task grant is explicit,
  defaults read-only, and is audited.
- Rejected model validators that infer task history absent from the
  record: the archive verifier owns cross-file execution integrity.
- Rejected provider-side guessing about verified copy-out: the cleanup
  handshake carries the fact directly.
- Rejected file-level containment exceptions: declarative occurrences
  are frozen individually and the CLI remains generic.
- Preserved prior decisions: `HarnessAdapter.parse()` stays untouched;
  team mutation propagates declared files only; direct immutability stays
  unchanged.

## Warnings

- **M1b's live-call budget is ZERO.** Five calls remain from M1a and are
  not an M1b allowance.
- r5 is NOT approved: no product source, schemas, register, or glossary
  amendment may begin before G0.
- The no-call mapping check saw Claude 2.1.243, Codex 0.149.1, and Grok
  1.0.5. Existing live capability evidence remains version-bound
  (Claude 2.1.241 / Codex 0.149.1 / Grok 1.0.5); help inspection did not
  upgrade it.
- Local pytest needs
  `env -u PYTHONPATH NO_COLOR=1 TERM=dumb uv run pytest` because of the
  host's rich-terminal/ROS-Foxy environment, not a tree defect.
- The pre-existing untracked `.codex/` remains untouched.
