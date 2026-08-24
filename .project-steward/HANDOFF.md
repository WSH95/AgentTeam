---
updated_at: 2026-08-24T19:57:15Z
updated_by: claude
session_status: active
branch: main
last_commit: d40cb82
---
# Handoff

## Now

**The M1b plan is EXPANDED to draft r1 — proposed, NOT approved.** This
session executed the r0 approval checklist's item 1 ("expand this draft to
a full plan … in its own session"): `docs/plans/m1b-team-foundation.md`
grew from the 77-line r0 skeleton (`856d525`) to a full 874-line,
21-section plan in the M1a house style — field-level team contracts
(`TeamTemplateV1`, `TeamRunRequestV1`, the run-record team-mode extension;
no second run kind), gates M1b G0–G7 with mechanically checkable evidence,
the `CoordinationSubstrate` protocol plus the local-deterministic (first)
and ClawTeam (second, extra-only) providers, the pinned ClawTeam
exit-criterion measurement rule, a **zero-live-call budget**, the
deterministic test plan and CI mapping (12-job shape unchanged), stop
rules with falsification routing, and a §20 approval checklist that
doubles as the independent review's charter. The claim audit is green:
the r0 exit-criterion blockquote is carried byte-identical, the 233/281
LOC baseline re-derives exactly, and every cited SHA/ADR/path resolves.
Full suite green: 453 passed + 4 skipped (matches the M1a-close counts;
one `doctor --help` assertion is terminal-sensitive — see Warnings).

## In flight

The commit carrying this handoff holds r1 plus this steward state. The
owner said they will review r1 after the commit — that owner read is the
immediate next event, before the independent review session.

## Next steps (r0 checklist items 2–3; a NEW approval scope — nothing starts automatically)

1. **Owner reads r1.** Owner answers may land for the §20 decision items —
   HB-03 disposition (options A/B/C/defer; A recommended), the
   exit-criterion measurement rule (§10), the CLI verb set (§7), the
   zero-live budget (§11), reserved-field sets (§6). Edits fold in as r1
   amendments (small) or r2 (structural).
2. **Independent review in a FRESH session** against the frozen r1 commit
   SHA (the `3407ec9`/`317bb52` precedent): read exclusively via
   `git show <sha>:docs/plans/m1b-team-foundation.md` (+ the repo at that
   SHA), write an immutable dated record
   `docs/reviews/2026-08-<dd>-m1b-plan-review-at-<short-sha>.md` with the
   house front matter, findings `Rn`/`Hn`; plan §20 lists what review must
   confirm. Do NOT run the review in this session — independence needs a
   fresh context.
3. Resolve findings (revision r2 if needed) → **owner approval** as a
   DECISIONS entry naming the plan file + approved commit SHA (G0) →
   status line flips to `approved` in the following commit → only then
   does implementation begin (plan §3 gates, §16 commit boundaries).
4. Nothing is pushed. Every push needs its own explicit owner approval
   (`never_push = true`).

## Blockers

None mechanical. M1b implementation is blocked by design on the
independent review and the G0 owner approval. The §20 owner decisions
(HB-03, exit-criterion rule, verb set, field sets, budget) ride with the
approval — the plan is written so A/B/defer on HB-03 land without
contract churn.

## Key files

- `docs/plans/m1b-team-foundation.md` — **r1, the review target.**
- `docs/plans/m1a-direct-harness-poc.md` — house style; every "M1a §N"
  pointer in r1 targets it.
- `docs/evidence/clawteam-qualification-2026-08-23.md` — the 233/281 LOC
  baseline and the four caveats the exit criterion needs accepted in
  writing.
- `docs/discovery/team-execution-model.md` + `docs/discovery/evidence/glossary.md`
  — the normative TC/TE content and vocabulary behind r1 §6/§8/§11.
- `.project-steward/QUESTIONS.md` — the exit-criterion and HB-03 items now
  point at plan §10/§20; both stay open until approval.
- `.project-steward/PLAN.md` — M1b section carries the r1 sub-bullet;
  gate rows are added only at/after G0.

## Tried and rejected (session highlights for a successor)

- Running the independent review in this same session: rejected —
  independence requires a fresh context reviewing the frozen SHA
  (precedent, and the plan's own §3 G0 row).
- A separate `team-run-v1` schema/record kind: rejected up front — the
  run record is extended in place (M1a §7 constraint; r1 §2 decision 3).
- Counting test LOC inside the exit-criterion ratio: rejected in the
  proposed rule (it would penalize writing tests); reported as context
  instead (r1 §10).

## Warnings

- **5 of 30 live calls remain from M1a; r1 sets the M1b budget to ZERO.**
  Any live urge during M1b routes to the M1c plan (r1 §11/§17), and every
  live call stays an individual owner ceiling decision (ADR 0038).
- r1 is NOT approved: no product code, no schema files, no register (v3.4)
  amendment until G0. The HB-03 register amendment stays a docs-only
  follow-up after the owner answers.
- Local pytest on this host needs a plain terminal:
  `env -u PYTHONPATH NO_COLOR=1 TERM=dumb uv run pytest` — a rich
  terminal makes one `doctor --help` assertion fail on ANSI codes, and a
  ROS-Foxy `PYTHONPATH` leak breaks collection outright. Neither is a
  tree problem (CI 12/12 at `0864742` stands).
- Capability evidence remains version-bound (Claude 2.1.241 /
  Codex 0.149.1 / Grok 1.0.5); Grok re-entry still needs fresh probes +
  an owner decision (ADR 0036).
