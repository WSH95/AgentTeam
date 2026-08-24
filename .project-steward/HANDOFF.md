---
updated_at: 2026-08-24T13:40:07Z
updated_by: codex
session_status: active
branch: main
last_commit: 2f87517
---
# Handoff

## Now

**M1a G5.R is implemented and locally verified; G6 has not started.** R3–R6
and H9 are checked off in PLAN. Core mode passes 417 tests + 4 expected
skips; the pinned optional-ClawTeam mode passes 429 + 3 skips and its focused
compatibility suite passes 12. Both modes pass the complete local CI-parity
path, including deterministic acceptance with both tiers green. The owner
approved the complete G5.R semantic commit; the commit containing this
handoff is that boundary. G6 remains separate and unstarted.

## In flight

Nothing. No process is running; implementation, two-mode validation, steward
bookkeeping, and the owner-approved semantic commit are complete. The local
environment was restored to core mode after the optional-extra verification.

## Next steps

1. Before G6, review the exact attended command
   `uv run atm run examples/run-requests/live-review.yaml`, the normal proxy
   environment, output/workspace targets, four-call normal path, retry ceiling,
   stop rules, and remaining 21-call M1a budget; obtain explicit owner
   confirmation immediately before execution.
2. After any G6 run, inspect the owner-only archive and promote only manually
   sanitized evidence; close G6 only if both acceptance tiers pass.
3. Commit permission does not imply push permission. Push or hosted-CI work
   requires its own explicit owner approval.

## Blockers

No G5.R blocker. G6 remains intentionally gated on the pre-run review and a
fresh attended-execution confirmation.

## Key files

- `src/agentteam/run/runner.py`, `profile/probe.py`, and
  `harness/capabilities.py` — R3/R4/R5 runtime fixes.
- `src/agentteam/domain/run.py`, `harness/codex.py`, and
  `schemas/harness-invocation-v1.schema.json` — R6 evidence contract.
- `tests/integration/test_{run_execute,profile_probe}.py` and
  `tests/unit/test_{preflight,render_claude,render_codex,render_grok}.py` —
  primary regressions and H9 coverage.
- `.project-steward/VERIFY.md` — exact two-mode validation evidence.

## Tried and rejected

- A hard-coded `test-version` in the shared render-context builder made 22
  fake-profile tests correctly fail the new currency guard. The builder now
  derives one consistent current verified version from the supplied profile
  and fails closed on inconsistent versions.
- Sandboxed `uv build`/acceptance initially could not create uv cache lock
  files outside the workspace. Approved cache access (or a task-local
  `UV_CACHE_DIR` for the second acceptance run) completed the same commands.

## Warnings

- No owner credential file or `~/.agentteam/vendors/` content was read. No
  live vendor/model call, G6 run, push, or remote mutation occurred.
- `select_verified(..., cli_version=None)` is render-only behavior;
  `execute_run` rejects non-live plans and missing observed versions before
  archive creation.
- Ignored fake homes under `examples/profiles/.agentteam-local/` may remain
  from deterministic acceptance; they are disposable test state, not owner
  vendor homes.
