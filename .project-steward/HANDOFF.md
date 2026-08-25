---
updated_at: 2026-08-25T22:58:18Z
updated_by: codex
session_status: active
branch: main
last_commit: 35790ad
---
# Handoff

## Now

M1a and M1b remain complete. M1c G5 and G6 are closed. The final exact product
candidate `35790ad` passed hosted run 32908268851 **12/12** across all six
Ubuntu/macOS/Windows scaffold legs, all three optional ClawTeam jobs, and all
three credential-free vendor-smoke jobs. Both Windows scaffold legs passed the
full suite and named M1c acceptance, so the owner's conditional Windows hold
did not activate. The exact direct-ACP runtime is installed and the zero-call
qualification is honest: Grok 1.0.5 is supported; Claude Code 2.1.245 and Codex
0.149.1 are fail-closed excluded on real ACP resume errors. No credential value
was read or copied and no model/live call has occurred.

## In flight

- G5 product/fix commits and the G6 launcher-provenance correction are pushed;
  the final exact candidate is locally and hosted green.
- G6 exact runtime and owner-only qualification records are installed. Grok is
  supported; Claude/Codex remain fail-closed excluded.
- The final adversarial review has no unresolved high-severity implementation
  finding. RISKS R38 records the bounded M3 follow-up for Skill supporting
  scripts/assets; M1c projects `SKILL.md` instructions only.
- The pre-existing untracked `.codex/` is user state and remains untouched.

## Next steps

1. Obtain the fresh attended owner go required for G7. Do not infer it from the
   approved plan, implementation approval, or zero-call qualification.
2. If approved, execute only Grok's five bounded lifecycle calls and record the
   exact ledger; Claude/Codex remain ineligible unless a fresh no-call G6
   qualification first succeeds.
3. Close M1c G8 before starting M1d D0; M1d also needs the
   ClawTeam/native-spawn owner ruling and has a zero-call budget.

## Blockers

G5 and G6 have no remaining blocker. G7 is blocked by design on a fresh
attended owner go. Claude/Codex are ineligible under their current G6
exclusions; only Grok's five lifecycle calls may be proposed. M1d remains
blocked on M1c G8 and its D0 decisions. HB-03 remains deferred.

## Key files

- `docs/plans/m1c-interactive-teamrun-foundation.md` — approved r2,
  `51dfebd9…0155`.
- `docs/plans/m1d-dynamic-member-poc.md` — approved r2,
  `bcffbc65…144d`.
- `docs/interactive-teamruns.md` — operator, lifecycle, permission, and
  provider-ownership guide.
- `.project-steward/VERIFY.md` — final local audit and exact validation block.
- `.project-steward/PLAN.md` — G5/G6 are closed; G7/G8 remain open.
- `/tmp/agentteam-m1c-g5-review/review_results.md` — local adversarial review
  synthesis (not a committed project artifact).

## Warnings

- Never make a G7 model call without a fresh attended owner go.
- The approved runtime action installs only the checked-in exact pins; changing
  any pin still requires a new decision. Chat itself never installs.
- Do not edit, stage, remove, or otherwise touch `.codex/`.
- Commit/push authorization is scoped to closing the current M1c gates; never
  force-push or mutate unrelated remote state. Preserve all V1 schema/archive
  bytes.
