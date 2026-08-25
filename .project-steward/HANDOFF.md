---
updated_at: 2026-08-25T22:07:49Z
updated_by: cli
session_status: active
branch: main
last_commit: df6077a
---
# Handoff

## Now

M1a and M1b remain complete. M1c interactive TeamRun r2 is implemented in the
uncommitted working tree through the G6 no-call qualification machinery. G0–G4
are locally closed. The G5 deterministic/adversarial audit is green: 76 focused
tests and the final full regression of 735 passed + 4 expected skips, with the
static/schema/lock/package block clean. G5 remains open for hosted
Ubuntu/Windows/macOS evidence. No runtime install, credential read, model/live
call, commit, or push occurred.

## In flight

- The implementation is review-ready but intentionally uncommitted. It
  includes the V2 catalog/contracts, interactive controller and protocols,
  provider SPI/fakes, pinned thin direct-ACP reference provider, workspace and
  permission controls, archive/export, CLI surfaces, tests, docs, and CI step.
- G6's installer, installed-tree integrity, exact-profile qualification cache,
  no-call bridge lifecycle, and fail-closed capability resolution are complete.
  The direct-ACP runtime itself remains absent, so no current-version provider
  is qualified.
- The final adversarial review has no unresolved high-severity implementation
  finding. RISKS R38 records the bounded M3 follow-up for Skill supporting
  scripts/assets; M1c projects `SKILL.md` instructions only.
- The pre-existing untracked `.codex/` is user state and remains untouched.

## Next steps

1. Owner reviews the M1c r2 implementation and local evidence.
2. If approved, obtain separate approval for the proposed semantic commit
   `feat(interactive): implement M1c TeamRun foundation`; obtain explicit push
   approval before using hosted CI to close G5.
3. Separately decide whether to install the exact pinned direct-ACP runtime.
   If approved, run fresh per-harness no-call qualification and record the
   supported/excluded capability result to close G6.
4. Stop before G7 and request its fresh attended live-call go. Do not infer
   authorization from the approved plan or implementation review.
5. Close M1c G8 before starting M1d D0; M1d also needs the ClawTeam/native-spawn
   owner ruling and has a zero-call budget.

## Blockers

G5 hosted evidence needs a semantic commit and explicit push approval. G6
current-version evidence needs separate runtime install/download approval.
G7 is blocked by design on a fresh attended owner go. M1d remains blocked on
M1c G8 and its D0 decisions. HB-03 remains deferred.

## Key files

- `docs/plans/m1c-interactive-teamrun-foundation.md` — approved r2,
  `51dfebd9…0155`.
- `docs/plans/m1d-dynamic-member-poc.md` — approved r2,
  `bcffbc65…144d`.
- `docs/interactive-teamruns.md` — operator, lifecycle, permission, and
  provider-ownership guide.
- `.project-steward/VERIFY.md` — final local audit and exact validation block.
- `.project-steward/PLAN.md` — G5/G6 remain unchecked with their missing
  external evidence stated explicitly.
- `/tmp/agentteam-m1c-g5-review/review_results.md` — local adversarial review
  synthesis (not a committed project artifact).

## Warnings

- Never make a G7 model call without a fresh attended owner go.
- Never install/update direct-ACP pins without separate approval; chat itself
  never installs.
- Do not edit, stage, remove, or otherwise touch `.codex/`.
- Never commit or push without explicit approval. Preserve all V1
  schema/archive bytes and the existing dirty planning work.
