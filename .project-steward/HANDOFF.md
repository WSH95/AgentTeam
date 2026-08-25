---
updated_at: 2026-08-25T04:31:52Z
updated_by: codex
session_status: active
branch: main
last_commit: 8d3f998
---
# Handoff

## Now

**M1b G3 is committed and M1b G4 is locally green, pending hosted core
evidence.** The approved r6 source remains
`760a8ae8c7021b0427bf29c84f005bebdd453bf6` (ADR 0044); G3 is committed at
`8d3f998`. G4 adds the dedicated public-CLI lifecycle acceptance and extends
the named scaffold acceptance step to execute both direct and three-member
team requests on all six core legs.

The G4 local block passed: new acceptance 2; targeted acceptance/render/hash
59; exact CI shell path; full 594 passed + 4 expected skips; Ruff lint/format,
strict mypy over 117 source files, schemas, lock, workflow parse, build, and
diff check clean. Acceptance found and fixed an undeclared Skill-free Codex
workspace marker and made the fake deliverable byte-stable across platforms.
Zero live calls were spent.

## In flight

G4 is prepared for its semantic CI-candidate commit from parent `8d3f998`.
The pre-existing untracked `.codex/` remains untouched. G4 stays open until a
fast-forward push proves all six hosted scaffold legs green.

## Next steps

1. Commit the locally green G4 candidate as
   `test(poc): add deterministic team-lifecycle acceptance`, including this
   steward state and excluding `.codex/`.
2. Fast-forward push `main` under the owner's standing approval and monitor the
   hosted workflow, requiring all six scaffold OS/Python legs green.
3. Record the run id/results, mark G4 complete, commit its hosted-evidence
   checkpoint, then begin G5 with a fresh gate-specific plan.

## Blockers

No mechanical blocker or open G4 product decision. Hosted core evidence is
the remaining gate condition, not a blocker. Live writable-member claims remain deferred to M1c,
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
- `src/agentteam/run/team_preflight.py` / `team.py` — G3 preflight and
  deterministic lifecycle implementation.
- `tests/integration/test_team_run_execute.py` / `test_team_run_faults.py` —
  G3 end-to-end and injected-fault evidence.
- `tests/acceptance/test_team_lifecycle.py` — G4's complete section-13
  public-CLI acceptance.
- `.github/workflows/ci.yml` — named direct + team deterministic acceptance on
  every scaffold leg.
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
