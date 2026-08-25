---
updated_at: 2026-08-25T05:49:18Z
updated_by: cli
session_status: closed
branch: main
last_commit: 24c6079
---
# Handoff

## Now

**M1b is complete through G7 under approved Plan R6 (ADR 0044).** G0–G7
are closed and indexed in PLAN/VERIFY. Team contracts, the local provider,
the deterministic runner/lifecycle, and the optional ClawTeam provider are
implemented. The explicit close disposition is
`CLAWTEAM_DISPOSITION=parity-green`. Hosted run 32812856864 at full product
SHA `688fffa019a09ca21156d5e663bfd51f364b10db` was freshly read back as
completed/success and is 12/12 green across six core, three optional-provider,
and three credential-free vendor-smoke jobs on Ubuntu/macOS/Windows.

Final local evidence is also green: core **594 passed + 4 expected skips**;
optional compatibility **31 passed** and the full optional tree **625 passed +
3 expected Windows-only skips**. Lock, Ruff lint/format, strict mypy/120,
schemas plus export round-trip, build, workflow parse, Assistant/team
validation, direct/team render-only, version, package hash, and diff hygiene
pass. The venv is restored to core-only with ClawTeam confirmed absent. M1b
made zero live calls; M1a's ledger remains 25/30 spent, five remaining.

The M1c PoC B r0 at `docs/plans/m1c-dynamic-member-poc.md` is explicitly
**PROPOSED — NOT APPROVED**. It names a proposed (unapproved) new 18-call
ceiling, the pending ClawTeam accept/drop decision, and the live
`member-result-v1`/writable-deliverable handoff. No M1c implementation began.

## In flight

Nothing is in flight. The G7 documentation/steward changes and r0 draft belong
to the semantic commit carrying this handoff. After that commit, expected git
state is `main` three commits ahead of `origin/main` (origin remains
`688fffa`) with only the pre-existing untracked `.codex/`; it was deliberately
untouched and excluded. No G7 push is needed because the final product tree is
already the exact 12/12 hosted SHA and G7 changes documentation only.

## Next steps

1. Do not implement M1c from r0. If the owner wants to continue, expand the r0
   into a detailed revision, independently review it, freeze the resolved SHA,
   and obtain an explicit owner G0 approval before source work.
2. During that review, ask the owner to choose the prepared ClawTeam packet:
   accept optional support plus all four caveats, or drop it without
   replacement. Record the answer in DECISIONS/QUESTIONS before PoC B starts.
3. Ask the owner to accept, change, or reject the draft's separate 18-call
   ceiling. No live call follows merely from accepting a plan: each live cycle
   still needs its own green no-call gate and fresh owner go.
4. Preserve the M1c handoff: freshly probe each candidate supported harness,
   then require full live `member-result-v1` acceptance and one writable
   declared-deliverable smoke per supported harness before making live-support
   claims.

## Blockers

No blocker remains for M1b; it is complete. M1c implementation is intentionally
blocked on its own detailed reviewed plan and owner G0. Two owner judgments are
also pending before PoC B: the ClawTeam accept/drop packet and the exact M1c
live-call ceiling. HB-03 constraint precedence remains open; the detailed plan
must get an answer or keep constraints out of scope.

## Key files

- `docs/plans/m1b-team-foundation.md` — approved normative R6, frozen approval
  source `760a8ae`; section 18 defines later-milestone handoffs.
- `docs/plans/m1c-dynamic-member-poc.md` — proposed-not-approved M1c r0; the
  next planning input, never implementation authorization.
- `.project-steward/VERIFY.md` — G7 close table, exact disposition, gate SHA
  index, hosted run, local matrices, ledger, and M1c handoff.
- `.project-steward/PLAN.md` — all M1b gates closed; M1c roadmap still open.
- `.project-steward/QUESTIONS.md` — exact ClawTeam accept/drop packet and draft
  M1c budget question.
- `.project-steward/RISKS.md` — R11/R12/R18/R31/R36 carry M1c limits; R37 is
  mitigated by the implemented fault matrix.
- `src/agentteam/domain/team.py` / `domain/run.py` — M1b contracts and reserved
  M1c/M2/M3 fields.
- `src/agentteam/coordination/protocol.py` / `local.py` / `clawteam.py` — seam,
  product provider, and optional provider.
- `src/agentteam/run/team.py` and `tests/acceptance/test_team_lifecycle.py` —
  deterministic lifecycle and public-CLI acceptance baseline M1c must retain.
- `.github/workflows/ci.yml` — final 12-job deterministic matrix shape.

## Tried and rejected

- Rejected treating the passing LOC ratio as the owner's caveat acceptance;
  the decision remains explicit and owner-owned.
- Rejected spending or reallocating M1a's five remaining calls; M1b's budget
  was zero and M1c's 18-call figure is only a proposal.
- Rejected starting dynamic-member implementation under M1b or describing
  hidden as a security boundary; r0 defines it as a presentation projection.
- Rejected a docs-only G7 push solely to manufacture a newer CI run. The final
  product SHA already has the required full 12/12 matrix, and all G7-local
  documentation/package checks pass.
- Preserved M1b design rejections: providers never launch/stop harnesses,
  `HarnessAdapter.parse()` remains untouched, declared files alone propagate,
  and direct/synthesis behavior remains unchanged.

## Warnings

- **M1c is not approved.** Planning/review is the only next milestone action.
- `18` is a draft live-budget ask, not permission. M1a's five remaining calls
  do not transfer. Never make an unattended/automatic live retry.
- The no-call mapping evidence is version-bound to Claude Code 2.1.243, Codex
  CLI 0.149.1, and Grok 1.0.5; M1c must probe current versions and keep Grok's
  task-scale/Windows evidence boundaries explicit.
- Optional ClawTeam support remains `parity-green` only under the exact pin and
  recorded caveats. Do not infer the pending keep/drop judgment.
- Local pytest should unset the host `PYTHONPATH` and use a task-local uv cache;
  the ROS-Foxy/rich-terminal host environment is not project evidence.
- The pre-existing untracked `.codex/` is user state. Do not stage, edit, or
  remove it.
- Never force-push. M1c requires its own approved plan/scope before treating
  the earlier M1b CI push authorization as applicable.
