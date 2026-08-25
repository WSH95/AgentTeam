---
updated_at: 2026-08-25T03:31:12Z
updated_by: codex
session_status: active
branch: main
last_commit: 9f52dc1
---
# Handoff

## Now

**M1b G2 is complete and fully green locally.** The approved r6 source remains
`760a8ae8c7021b0427bf29c84f005bebdd453bf6` (ADR 0044); G1 is committed at
`9f52dc1`. G2 adds the synchronous provider-neutral protocol/DTO/error/wait
seam, deterministic file-backed local provider, reusable provider conformance
base, local-only file-semantics tests, and frozen optional-provider
containment scan.

The G2 block passed: focused 29; full 538 passed + 4 expected skips; Ruff
lint/format, strict mypy over 111 source files, schemas, lock, build, and diff
check clean. The local provider uses the canonical first `coordination/space`,
atomic owner-only state, deterministic ids/order, retained consumed mail and
snapshots, and non-deleting tombstone cleanup. Zero live calls were spent.

## In flight

G2 is prepared for its semantic commit from parent `9f52dc1`. The pre-existing
untracked `.codex/` remains untouched. G3 has not started; its first action is
a gate-specific plan against the approved team lifecycle and fault taxonomy.

## Next steps

1. Commit G2 as `feat(coordination): add local provider`, including this
   steward state and excluding `.codex/`.
2. Plan G3 before implementation: team request dispatch/resolution/selection,
   scope-aware rendering, team archive/runner, member results, canonical
   deliverables/handoffs/ledger, lifecycle finalization, binding verifier, and
   the full injected-fault taxonomy.
3. Implement/test/debug G3 to green and commit, then continue through G4–G7;
   fast-forward push when hosted CI
   evidence is needed under the owner's standing approval.

## Blockers

No mechanical blocker or open G3 product decision. Live writable-member claims remain deferred to M1c,
which must re-probe
then-supported clients and run one declared-deliverable acceptance per
supported harness. Team Grok is unsupported on Windows under the r6
evidence boundary.

## Key files

- `docs/plans/m1b-team-foundation.md` — **approved r6**, frozen approval
  source `760a8ae`.
- `src/agentteam/domain/team.py` / `domain/run.py` — G1 public contracts and
  the direct/team run-record union.
- `src/agentteam/resolution/team.py` / `commands/team.py` — template loading,
  hashing, transitive validation, and CLI.
- `examples/teams/development.yaml` — committed three-member acceptance shape.
- `src/agentteam/coordination/protocol.py` / `local.py` — G2 seam and product
  provider; `tests/coordination_suite.py` is the G5-reusable contract.
- `tests/unit/test_import_containment.py` — frozen optional-provider boundary.
- `docs/reviews/2026-08-24-m1b-plan-review-at-760a8ae.md` — immutable sixth
  review (confirmation). Prior records through
  `docs/reviews/2026-08-24-m1b-plan-review-at-12ca6c7.md` remain unchanged.
- `.project-steward/DECISIONS.md` ADR 0044 — G0 approval; ADR 0043 — r6 design.
- `.project-steward/RISKS.md` R36/R37 — adapter-enforcement and terminal-
  pairing boundaries.

## Tried and rejected

- Rejected `output_contract` or workspace access as a team/direct side
  channel; scope is explicit.
- Rejected writes to persistent `GROK_HOME`, fixed globally collidable
  profile names, pre-existing project-profile overwrite, and Windows
  unsandboxed continuation.
- Rejected step-5 copy hashes as invocation baselines; target baselines are
  launch-time facts after handoff materialization.
- Rejected a blanket abandoned sweep; succeeded work is never rewritten,
  interrupted allocated work is cancelled, and abandonment means no
  durable allocation.
- Preserved prior decisions: `HarnessAdapter.parse()` stays untouched;
  team mutation propagates declared files only; direct/synthesis rendering
  and direct immutability stay unchanged.

## Warnings

- **M1b's live-call budget is ZERO.** Five calls remain from M1a and are
  not an M1b allowance.
- Product work follows G1–G7 only; do not begin M1c in this approval scope.
- The no-call mapping evidence is version-bound to Claude Code 2.1.243,
  Codex CLI 0.149.1, and Grok 1.0.5; help/guide inspection did not upgrade
  live capability evidence.
- The first parallel `uv` mypy/schema attempt contended on a read-only host
  cache; sequential reruns with a task-local `/tmp` cache passed. This was
  an environment failure, not a tree defect.
- Local pytest needs
  `env -u PYTHONPATH NO_COLOR=1 TERM=dumb uv run pytest` because of the
  host's rich-terminal/ROS-Foxy environment, not a tree defect.
- The pre-existing untracked `.codex/` remains untouched and must not be
  staged accidentally.
