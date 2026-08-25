---
updated_at: 2026-08-25T03:14:42Z
updated_by: codex
session_status: active
branch: main
last_commit: 84a60e3
---
# Handoff

## Now

**M1b G1 is complete and fully green locally.** The frozen/approved r6 source
remains `760a8ae8c7021b0427bf29c84f005bebdd453bf6` (ADR 0044). G1 adds the
three approved public contracts/schemas, the schema-level direct/team
run-record union, shared substrate/task contract types, reference-aware
`atm team validate`, and the committed implementer/development/team-request
fixtures. The direct variant body and serialization order remain exactly the
pre-M1b contract.

The gate block passed: focused 154; full 509 passed + 4 expected skips;
Ruff lint/format, strict mypy over 104 source files, schemas, lock, build, and
diff check clean. Exactly three schemas are new and only run-record plus
harness-invocation changed. Zero live calls were spent.

## In flight

G1 is prepared for its semantic commit from parent `84a60e3`. The pre-existing
untracked `.codex/` remains untouched. G2 has not started; its first action is
a gate-specific plan against the approved protocol/local-provider contract.

## Next steps

1. Commit G1 as `feat(team): add foundational contracts and schemas`, including
   this steward state and excluding `.codex/`.
2. Plan G2 before implementation: generic async protocol/DTO/errors, local
   provider storage semantics, shared conformance suite, containment scan.
3. Implement/test/debug G2 to green and commit, then continue through G3–G7;
   fast-forward push when hosted CI
   evidence is needed under the owner's standing approval.

## Blockers

No mechanical blocker or open G2 product decision. Live writable-member claims remain deferred to M1c,
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
