---
updated_at: 2026-08-26T02:43:14Z
updated_by: codex
session_status: active
branch: main
last_commit: bc98735
---
# Handoff

## Now

M1c G0–G6.R remain closed. Under ADR 0049, the complete deterministic G7
candidate is implemented and locally green with zero live calls. It adds the
internal attended 19-call driver, exact Codex/Claude/Grok workflow fixtures,
atomic sanitized audit export, exact permission inspection, and default
Ubuntu/macOS-only CI with Windows retained as manual opt-in.

## In flight

- Full local acceptance is green: 774 passed + 4 expected skips, Ruff lint and
  format, strict mypy over 152 source files, 26 schemas, lock, wheel/sdist,
  Node syntax, exact fixture hashes, wheel scope, and diff hygiene.
- A deterministic seven-bundle evidence rehearsal is scanner-clean and
  reconciles exactly 19/23 prompts with diagnostics 0.
- The adversarial critique found and closed source-drift, hosted-run binding,
  exact-path display/correlation, partial-ledger, blocked-abort/process-group,
  launch-binding, manifest, path-scanner, ambiguous-run-store, and implicit
  permission-deadline gaps. The final synthesis for product tree `bc98735` is
  tracked at `docs/reviews/2026-08-26-m1c-g7-candidate-review.md` with no open
  high/medium finding.
- Product commits `dec83e0` and `bc98735` are local. The pre-existing `.codex/`
  remains untouched and out of scope.

## Next steps

1. Commit the review artifact and this checkpoint, then fast-forward push the
   resulting exact candidate.
2. Require the candidate-bound GitHub Actions run to contain exactly eight
   completed/success Ubuntu/macOS jobs and no Windows job.
3. Only then start the attended Claude → Codex → Grok five-prompt lifecycles
   and Codex → Claude → Grok → Grok workflow. Every gate remains default-no;
   stop at the first failure and spend no diagnostic prompt.
4. Review/commit sanitized evidence and close G7/G8 before beginning M1d D0.

## Blockers

There is no deterministic blocker. Live execution is intentionally blocked on
the exact candidate commit, its eight-job hosted success, process/run
exclusivity, and the fresh default-no confirmations embedded in the driver.
Windows development/testing remains paused.

## Warnings

- No live/provider call has occurred in this G7 attempt.
- Never edit source after calls begin; a failure returns to the owner instead
  of retrying or spending the four-call diagnostic reserve.
- Do not run the manual Windows input, alter dependency pins/contracts, touch
  `.codex/`, force-push, or mutate unrelated remote state.
