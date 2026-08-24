---
updated_at: 2026-08-24T12:12:22Z
updated_by: cli
session_status: closed
branch: main
last_commit: 8cd9e38
---
# Handoff

## Now

**M1a G5 is closed (ADR 0031), independently reviewed (ADR 0032), and fully
published with all nine hosted CI checks green.** At wrap time local `main`
equals `origin/main` at `8cd9e38`; the wrap commit carrying this handoff is
the only unpushed commit afterwards.

What this session did (2026-08-24, on the owner's "resume and review G5"):

- Resumed after the codex session's benign unclosed exit (it checkpointed
  the G5 closure at `317bb52` and never ran wrap; no work was lost).
- Independent review at `317bb52`
  (`docs/reviews/2026-08-24-g5-review-at-317bb52.md`): the closure evidence
  is **genuine** — all five probe captures re-verified (45/45 recorded
  hashes recompute, 0700/0600, every cited timing/exit/row matches),
  profiles and the non-mutating no-call doctor exact, and all 9 attended
  calls (Claude 3 / Codex 2 / Grok 4) traced to explicit approvals.
  **21 of the 30-call M1a ceiling remain.**
- Found and fixed, each on explicit owner ruling and each pushed on its own
  approval: `739be1a` (undeclared `click` dependency — typer 0.27 vendors
  Click — broke every core-mode CI leg; also restores prompt Ctrl-C → 130),
  `83f2b3b` (CI acceptance step provisions the fake vendor homes the new
  preflight requires), `0dfbca9` (mypy `platform = "linux"` pin — win32
  analysis rejected the POSIX-only branches), `5d27d2f` (Windows redaction:
  JSON-escaped path spelling now redacted, with a cross-platform regression
  test; two login-command tests assert the platform-appropriate form).
- Plan amendment `cc81b51` (ADR 0033, owner-approved diff): §22 amendment
  record + budget reconciliation.
- Hosted evidence: run **32724844619 at `5d27d2f` — all nine checks green**
  (six scaffold legs ubuntu/windows/macos × 3.11/3.13 + the three-OS
  clawteam job); the three-run failure history is in VERIFY "G5 independent
  review".

Verification state: full CI-parity step list passes locally in both
dependency modes — core 392+4 skips, extra 405+3 skips (the +1 is the new
redaction regression test), compatibility 12. Test counts are
mode-dependent; always state the mode.

## In flight

Nothing. No process is running, the worktree is clean, and everything
through `8cd9e38` is pushed.

## Next steps

1. **Resolve the PLAN "G5.R" pre-G6 tasks** (review R3–R6 + the H9
   test-gap cluster; fix shapes in the review doc §2): close managed-skills
   leases on every `_run_body` exit path; bound the probe kill-escalation
   (unconditional group SIGKILL + timeout on the final drain); enforce
   channel currency at the consumption point; persist the live Codex
   `-o`/JSONL disagreement. G6 does not start before these.
2. **G6 pre-run review, then the live PoC**: review the exact command
   (`uv run atm run examples/run-requests/live-review.yaml`, normal proxy
   environment), the four-call normal path (three legs + fresh Claude
   synthesis), retry ceiling, stop rules, workspace/output targets, and
   expected evidence; obtain explicit owner confirmation immediately before
   execution. Budget: one 8-call cycle plus one confirmed rerun fit the
   remaining 21 calls; a **second** rerun would exceed the 30-call ceiling
   and needs an explicit owner ceiling decision (ADR 0033).
3. After a G6 run: review the owner-only archive, promote only manually
   sanitized evidence, rerun the credential-free block, and close G6 only
   if both mechanical and semantic acceptance tiers pass; otherwise retain
   the failure and stop.
4. Push the wrap commit (and anything later) only on its own explicit
   owner approval.

## Blockers

- None. G6 is gated on the G5.R tasks and its own attended execution
  confirmation.

## Key files

- `docs/reviews/2026-08-24-g5-review-at-317bb52.md` — review record: claims
  matrix A–N, findings R1–R8 (fix shapes for the G5.R tasks live in §2),
  hygiene H1–H13, owner rulings.
- PLAN "G5.R" block; DECISIONS 0032/0033; VERIFY "G5 independent review"
  (incl. the three-run hosted history); RISKS R24/R32 notes.
- `src/agentteam/harness/rendering.py` (JSON-escaped redaction),
  `src/agentteam/commands/profile.py` (typer Abort), `.github/workflows/
  ci.yml` (acceptance-step home provisioning), `pyproject.toml`
  ([tool.mypy] platform pin).
- `src/agentteam/profile/{probe,doctor,capture,setup}.py`, `run/
  {preflight,runner}.py`, `harness/{environment,skills,claude,codex,
  grok}.py` — the reviewed G5 machinery.

## Tried and rejected

- Do not re-argue ADR 0026–0031: the review verified traceability and
  implementation and recorded no dissents; the closure stands.
- Do not treat VERIFY's six-command "credential-free block" as CI parity:
  it omits the CI-only steps and its with-extra pytest mode hides core-mode
  breakage (exactly how the `click` regression hid). Run the full
  `.github/workflows/ci.yml` step list in **both** dependency modes before
  any push claim.
- Fake-home provisioning belongs in the CI step (mirroring
  tests/conftest.py), not in a weakened preflight — the home-existence gate
  is doing its job.
- Never assert POSIX-form login commands unconditionally in tests; win32
  intentionally prints PowerShell-quoted commands.

## Warnings

- Raw probe captures stay owner-only under `~/.agentteam/`; never track or
  publish them; never read `~/.agentteam/vendors/` (credential homes).
- Capability evidence is version-bound (Claude Code 2.1.241, Codex 0.149.1,
  Grok 1.0.5): any vendor CLI upgrade makes readiness stale and forces
  doctor/probe reassessment before another live run.
- mypy analysis is pinned to `platform = "linux"`: Windows *typing* is not
  analyzed; Windows runtime behavior is proven by pytest on the Windows CI
  legs.
- Commit permission never implies push permission; every push is its own
  explicit owner decision. G6 never starts automatically.
