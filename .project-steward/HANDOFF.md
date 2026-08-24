---
updated_at: 2026-08-24T12:20:00Z
updated_by: claude
session_status: active
branch: main
last_commit: 5d27d2f
---
# Handoff

## Now

**G5 is closed (ADR 0031) and independently reviewed (ADR 0032).** The
2026-08-24 review at `317bb52`
(`docs/reviews/2026-08-24-g5-review-at-317bb52.md`) re-derived every
owner-host claim from disk and confirmed the closure evidence is genuine:
all five probe captures (45/45 recorded hashes recompute, 0700/0600
throughout, every cited timing/exit matches), profile rows (Claude 5v/3o,
Codex 7v/2o, Grok 8v/1o/1u, version-bound to the installed CLIs), a
non-mutating no-call doctor exit 0, and exactly 9 attended calls
(Claude 3 / Codex 2 / Grok 4), each traced to its owner approval — 21 of
the 30-call M1a ceiling remain.

The review also ran the **full CI step list locally in both dependency
modes** — something G5's own verification never did — and found two
CI-breaking regressions, both fixed on owner ruling in their own commits:

- `739be1a` — `from typer import Abort` (was `from click import Abort`, an
  undeclared dependency: typer 0.27.1 vendors Click, so core-mode installs
  had no `click` and every `atm` command, mypy, and pytest died; the wrong
  class also made a real prompt Ctrl-C exit 1 instead of the contractual
  130).
- `83f2b3b` — the CI deterministic-acceptance step now provisions the
  disposable fake vendor homes that the new G5 live preflight requires
  (green at G4 only because the gate predates it).

Post-fix the complete step list passes with **0 failures**: core mode 392
passed + 4 skips, extra mode 404 passed + 3 skips, compatibility 12,
acceptance both tiers, owner `profiles.yaml` untouched by the whole suite.

## In flight

- Nothing is running. The plan amendment was approved and committed
  (`cc81b51`, ADR 0033); `main` was pushed on the approved decisions
  (`03635e7..cc81b51`, then fix pushes `0dfbca9` and `5d27d2f`, each
  separately approved); **all nine CI checks are green at `5d27d2f`**
  (run 32724844619) — the first complete hosted evidence for the G5 work,
  including the first real-Windows execution of the G5 branches. The
  three-run failure history (Windows mypy platform analysis → `0dfbca9`;
  Windows-only redaction/test-form failures → `5d27d2f`) is in VERIFY.
- The hosted-evidence steward commit is **local only**; pushing it needs
  its own approval like every push.

## Next steps

1. Push the local hosted-evidence steward commit when the owner next
   approves a push (nothing else is unpushed).
2. (done) Plan amendment ADR 0033 committed; nine checks green at
   `5d27d2f`.
3. Resolve the PLAN "G5.R" pre-G6 tasks (review R3–R6 + the H9 test-gap
   cluster): lease cleanup on every `_run_body` exit path, bounded probe
   kill-escalation, channel-currency enforcement at consumption, persisted
   live Codex `-o`/JSONL disagreement.
4. Before G6: the existing pre-run review (exact live-PoC command,
   four-call normal path, retry ceiling, stop rules, workspace/output
   targets, expected evidence) plus explicit owner confirmation immediately
   before execution; then `uv run atm run
   examples/run-requests/live-review.yaml` in the normal proxy environment.
5. G6 budget note: 21 calls remain under the 30-call ceiling — one 8-call
   cycle plus one confirmed rerun fit; a second rerun would exceed the
   ceiling and needs an explicit owner decision at that point.

## Blockers

- None for the push. G6 is gated on the G5.R tasks and its own attended
  execution confirmation.

## Key files

- `docs/reviews/2026-08-24-g5-review-at-317bb52.md` — the review record
  (claims matrix A–N, findings R1–R8, hygiene H1–H13, owner rulings).
- `src/agentteam/commands/profile.py`, `.github/workflows/ci.yml` — the two
  fixes (`739be1a`, `83f2b3b`).
- PLAN "G5.R" block, DECISIONS 0032 (and 0033 once approved), VERIFY "G5
  independent review", RISKS R24/R32 notes.

## Tried and rejected

- Do not re-argue ADR 0026–0031: the review verified traceability and
  implementation, recorded no dissents, and the closure stands.
- Do not treat VERIFY's "credential-free block" as CI parity: it omits the
  CI-only steps (render smoke, hash pin, acceptance, export round-trip) and
  its pytest mode (with the clawteam extra) hides core-mode breakage. The
  review's two-mode full-step-list run is the pattern to keep.
- The fake-home provisioning belongs in the CI step (mirroring
  tests/conftest.py), not in a weakened preflight — the home-existence gate
  is doing its job.

## Warnings

- Raw probe captures stay owner-only under `~/.agentteam/`; never track or
  publish them. The review printed only hashes/metadata and never read
  `vendors/`.
- Capability evidence is version-bound: any vendor CLI upgrade makes
  readiness stale and forces reassessment before a live run.
- G5 claims are Ubuntu owner-host claims; hosted CI stays fake and
  credential-free; the nine-green run 32724844619 at `5d27d2f` is the
  hosted evidence for the G5 work.
- Commit permission never implies push permission. The one approved push is
  ADR 0032 item 5; every later push is a fresh owner decision.
