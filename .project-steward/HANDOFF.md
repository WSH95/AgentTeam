---
updated_at: 2026-08-24T22:39:44Z
updated_by: claude
session_status: active
branch: main
last_commit: e89a75f
---
# Handoff

## Now

**The M1b plan is at draft r3 — two review rounds survived, all findings
resolved, NOT approved.** Full chain this session: r1 (expanded plan,
`14dc218`) → first independent review (7 blocking + 3 hygiene; recorded
`docs/reviews/2026-08-24-m1b-plan-review-at-14dc218.md`, `9802775`) → r2
resolves all ten (`54728c8`; ADR 0039 — HB-03 deferred out of M1b) →
second independent review of r2 (6 implementation-blocking + 3 medium;
recorded `docs/reviews/2026-08-24-m1b-plan-review-at-54728c8.md`,
`e89a75f`) → **r3 resolves all nine** (the commit carrying this handoff;
§21 r2→r3 table; ADR 0040). Every finding in both rounds was re-verified
against the tree before resolution. r3's substance: lifecycle nullability
for the team record; the complete provider task semantics
(`SubstrateTaskStatus`, DTOs with the remaining-vs-declared `blocked_by`
split, `TaskClaimError`/`UnknownTaskError`, `running ↔ in_progress` in
the adapter, run-only `failed`/`abandoned` with the auto-unblock-safety
rationale, Kahn-with-declaration-order registration); **`MemberResultV1`
introduced now** (owner decision — third new vendor-facing schema;
additive harness dispatch, review path untouched; deliverables declared →
validated → archived → materialized; live vendor acceptance is a named
M1c handoff); **blinded handoffs** on declared-independence edges; the
`failed-routed` green-CI branch (registry-unsupported + dated
strict-xfail); unified finalization (abandon sweep; terminal record then
manifest; `processes-stopped` unconditional; an 11-op fault matrix with a
parallel-branch template); the parity-fixture split; the AST +
token-allowlist containment scan; and the **stable
`~/.agentteam/clawteam/` process root restored per ADR 0015**.

## In flight

Nothing after the r3 commit. Zero live calls spent; tree green
(453 passed + 4 skipped under a plain terminal).

## Next steps (a NEW approval scope — nothing starts automatically)

1. **Owner G0 decision on r3** — either: approve (a DECISIONS entry
   naming `docs/plans/m1b-team-foundation.md` + r3's commit SHA; the
   status line flips to `approved` in the following commit), **or**
   another confirmation pass in a fresh session against r3's frozen SHA
   (same `docs/reviews/` convention; plan §20 is the charter, §21 the
   two-round resolution history).
2. Only after G0: implementation per plan §3 gates G1–G7 and §16 commit
   boundaries. First code commit is `feat(domain): …` (G1, now including
   `MemberResultV1`).
3. At G0 the approval ADR also carries the glossary CoordinationSubstrate
   `stop` amendment (plan §20 follow-up).
4. Pushes: `main` is now 5 ahead of origin (`14dc218`, `9802775`,
   `54728c8`, `e89a75f`, the r3 commit); **nothing pushed** — every push
   needs explicit owner approval (`never_push = true`).

## Blockers

None mechanical. Implementation is blocked by design on G0. Open owner
items: G0 itself; the §20 finalize-at-approval list (exit-criterion
wording + measurement rule, zero-live budget, CLI verb set,
reserved-field sets, the MemberResultV1 field set); and — independent of
M1b — the HB-03 semantic question (open in QUESTIONS.md with recorded
options).

## Key files

- `docs/plans/m1b-team-foundation.md` — **r3, the approval target** (§21
  maps both review rounds to their resolutions).
- `docs/reviews/2026-08-24-m1b-plan-review-at-14dc218.md` and
  `docs/reviews/2026-08-24-m1b-plan-review-at-54728c8.md` — the two
  immutable review records.
- `.project-steward/DECISIONS.md` ADRs 0039–0040 — the review/resolution
  trail and the owner decisions (HB-03 defer; MemberResultV1; stable
  ClawTeam root).
- `docs/plans/m1a-direct-harness-poc.md` — house style; every "M1a §N"
  pointer targets it.
- `docs/evidence/clawteam-qualification-2026-08-23.md` +
  `src/agentteam/compat/clawteam.py` — the 233/281 baseline, the four
  caveats, and the seam whose `create_space` gains `leader` at G5.

## Tried and rejected (session highlights for a successor)

- Every review finding in both rounds was verified against the tree
  BEFORE resolution; none was taken on faith (anchors in ADRs 0039/0040
  and PROGRESS).
- Rejected: constraining M1b to review-shaped member results — the owner
  chose the provider-neutral `MemberResultV1` path instead (ADR 0040).
- Rejected: a `receive`-failure cascade (provider raise = infrastructure
  → fault abort; the failure taxonomy stays exhaustive by cause).
- Rejected: neutralizing snapshot bundles (provider-shaped opaque dicts
  preserve forensic fidelity; translation lives in test-side readers).
- Rejected: keeping the per-run ClawTeam data root (breaks the seam's
  one-root rule for multi-run processes; the stable root restores ADR
  0015).

## Warnings

- **5 of 30 live calls remain from M1a; M1b's budget is ZERO live calls**
  (plan §11/§17). `member-result-v1`'s live vendor acceptance is
  explicitly M1c evidence — deterministic-only until then.
- r3 is NOT approved: no product code, no schema files, no register or
  glossary amendments until G0.
- Local pytest on this host needs a plain terminal:
  `env -u PYTHONPATH NO_COLOR=1 TERM=dumb uv run pytest` (rich ANSI breaks
  one doctor --help assertion; a ROS-Foxy PYTHONPATH leak breaks
  collection). Neither is a tree problem.
- An untracked `.codex/` directory exists at the repo root (not created by
  this session; left untouched; owner to decide whether to gitignore).
- Capability evidence stays version-bound (Claude 2.1.241 / Codex 0.149.1
  / Grok 1.0.5); Grok re-entry needs fresh probes + an owner decision
  (ADR 0036).
