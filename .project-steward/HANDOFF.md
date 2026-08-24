---
updated_at: 2026-08-24T14:00:41Z
updated_by: codex
session_status: active
branch: main
last_commit: e722c15
---
# Handoff

## Now

**G5.R is closed and pushed through corrective commit `e722c15`; G6 has not
started.** The first hosted run retained its 7/9 failure history. Corrective
run 32735583747 is 9/9 green: all six Ubuntu/Windows/macOS × Python 3.11/3.13
scaffold jobs and all three OS-specific optional-ClawTeam jobs passed,
including every deterministic acceptance step. The owner approved the
evidence-only commit containing this handoff; it remains local until any
separate push approval.

## In flight

Nothing. No process is running; product/test changes are pushed and hosted
evidence is captured in the local commit containing this handoff. The local
environment remains in core mode.

## Next steps

1. Push the evidence-only steward commit only on its own explicit owner
   approval; a push will trigger another credential-free CI run.
2. Before G6, review the exact attended command
   `uv run atm run examples/run-requests/live-review.yaml`, the normal proxy
   environment, output/workspace targets, four-call normal path, retry ceiling,
   stop rules, and remaining 21-call M1a budget; obtain explicit owner
   confirmation immediately before execution.
3. After any G6 run, inspect the owner-only archive and promote only manually
   sanitized evidence; close G6 only if both acceptance tiers pass.

## Blockers

No G5.R blocker. G6 remains gated on its separate pre-run review and fresh
attended-execution confirmation.

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
- CI run 32734735405 proved the mocked stuck-pipe test itself was POSIX-only:
  Windows has no `os.killpg`. Testing the platform-independent drain helper
  directly retains the bounded 10s/5s assertions; the separate real POSIX
  descendant test retains group TERM/KILL coverage. Corrective run
  32735583747 passed all nine jobs.

## Warnings

- No owner credential file or `~/.agentteam/vendors/` content was read. No
  live vendor/model call or G6 run occurred. The only remote mutations were
  the explicitly approved fast-forward pushes through `30c17b5` and
  `e722c15`.
- `select_verified(..., cli_version=None)` is render-only behavior;
  `execute_run` rejects non-live plans and missing observed versions before
  archive creation.
- Ignored fake homes under `examples/profiles/.agentteam-local/` may remain
  from deterministic acceptance; they are disposable test state, not owner
  vendor homes.
