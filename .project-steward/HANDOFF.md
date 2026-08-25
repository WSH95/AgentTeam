---
updated_at: 2026-08-25T05:32:34Z
updated_by: codex
session_status: active
branch: main
last_commit: 17b2c4f
---
# Handoff

## Now

**M1b G6 is measured and its owner decision packet is ready.** The approved
r6 source remains `760a8ae8c7021b0427bf29c84f005bebdd453bf6` (ADR 0044).
The thin optional provider now sits behind the generic registry and qualified
seam, with the logical lead, stable `AGENTTEAM_HOME`-relative process root,
opaque namespaces, full-roster reconciliation, status/error/message mapping,
and verified-copy-out snapshot deletion implemented. The full section-13
three-member lifecycle runs through the public CLI over this provider.

G5 remains `parity-green`. Hosted run 32812856864 at full SHA
`688fffa019a09ca21156d5e663bfd51f364b10db` is 12/12 green: all three
optional-provider legs passed the qualification, conformance, and complete
lifecycle suite on Ubuntu/macOS/Windows; all six scaffold and three
credential-free vendor-smoke legs also passed. Local evidence is green:
optional compatibility **31 passed**; the full tree
with the extra **625 passed + 3 platform skips**; the clean core environment
with the dependency absent **594 passed + 4 expected skips**. Ruff lint/format,
strict mypy over 120 source files, schemas, lock, workflow parse, build, and
diff hygiene all pass. The only initial conformance mismatch was upstream
`restore()` returning a summary; the adapter now returns the preserved opaque
bundle required by the shared protocol. Zero live calls were spent.

G6's pinned physical-LOC command reports **516 optional production LOC / 486
local-provider LOC = 86/81 = 1.061728395×**, below the `1.5×` ceiling of 729
with 213 LOC headroom. The original compatibility baseline remains exactly
233 LOC; the provider adds 283. Test context is 558 optional vs 163 local and
is excluded by the approved rule. The containment inventory is 2/2 green.
QUESTIONS carries the explicit accept-all-four-caveats vs drop-without-
replacement packet.

## In flight

G6's steward measurement/packet is uncommitted on top of G5 closure commit
`17b2c4f`; the branch is one commit ahead of `origin/main` before the G6
commit, and the pre-existing untracked `.codex/` remains untouched. G7 has
not started; its first action is a fresh closeout plan.

## Next steps

1. Validate and commit the G6 measurement/packet, excluding `.codex/`.
2. Plan G7 before closeout: reconcile every G1–G6 SHA/run/evidence row, prove
   the live-call ledger stayed at five remaining, record the explicit
   `parity-green` disposition, and draft M1c PoC B as proposed-not-approved.
3. Run the final required matrices/consistency checks, debug to green, commit
   M1b closure, and stop before any M1c implementation.

## Blockers

No mechanical blocker to G7 or M1b closure. The measured ratio passes, but the
owner's accept/drop judgment is genuinely required **before M1c PoC B**, not
before G7; agents must not infer it. Live writable-member claims remain
deferred to M1c, which must re-probe then-supported clients and run one
declared-deliverable acceptance per supported harness. Team Grok is
unsupported on Windows under the r6 evidence boundary.

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
