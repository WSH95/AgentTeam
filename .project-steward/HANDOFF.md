---
updated_at: 2026-08-25T01:45:13Z
updated_by: codex
session_status: active
branch: main
last_commit: a140829
---
# Handoff

## Now

**The M1b plan is at draft r6 after five independent review rounds; r6 is
NOT approved.** The fifth review froze r5 at full commit
`12ca6c730f99816ed79c6e0537de021d25dd24b2` and plan SHA-256
`95ff6ab3816efd61db845216b34aecb64b8d22efde3f13a727027c612a44acf4`.
Its immutable adjudicated record is
`docs/reviews/2026-08-24-m1b-plan-review-at-12ca6c7.md` (`a140829`).

r6 (plan §21 r5→r6 table; ADR 0043) closes the fifth-round gaps with:

- complete disjoint Claude allow/deny sets for both grants;
- an explicit `standalone | team-member` render discriminator;
- collision-safe, per-render project `.grok/sandbox.toml` profiles that
  never rewrite persistent `GROK_HOME`, plus fail-closed Windows refusal;
- team Codex workspace-write with network explicitly disabled;
- step-5 copy verification separated from the handoff-inclusive,
  launch-time `target.before`;
- a shared `SubstrateKind` leaving `domain/run.py` at zero `clawteam`
  occurrences; and
- a run-only task `cancelled` state and exhaustive terminal sweep: causal
  task failure, non-causal allocated cancellation, never-allocated
  abandonment, completed preservation, and explicit pre-/post-commit
  provider-completion ambiguity.

## In flight

The immutable fifth-review record is committed separately at `a140829`.
The r6 docs/steward change is complete and lands in the commit carrying this
handoff. Product implementation has not started. Validation is green: frozen
r5 hash exact; 453 passed + 4 skipped; Ruff clean; mypy clean across 98 source
files; schemas current; Markdown fences balanced; diff check clean. Zero live
calls were spent. The pre-existing untracked `.codex/` remains untouched.

## Next steps (a NEW approval scope — nothing starts automatically)

1. Treat the commit carrying this handoff as the proposed r6 revision. Either
   commission a frozen-SHA confirmation pass or approve G0 via a DECISIONS
   entry naming
   `docs/plans/m1b-team-foundation.md` and that commit SHA.
2. Only after G0: execute plan gates G1–G7 and §16 commit boundaries.
3. At G0, carry the glossary CoordinationSubstrate `stop` amendment listed
   in plan §20.
4. Push only on a separate explicit owner approval.

## Blockers

No mechanical blocker. Product implementation is intentionally blocked on
G0. Live writable-member claims remain deferred to M1c, which must re-probe
then-supported clients and run one declared-deliverable acceptance per
supported harness. Team Grok is unsupported on Windows under the r6
evidence boundary.

## Key files

- `docs/plans/m1b-team-foundation.md` — **draft r6, the current approval
  target**.
- `docs/reviews/2026-08-24-m1b-plan-review-at-12ca6c7.md` — immutable fifth
  review record (`a140829`); the prior four records remain unchanged.
- `.project-steward/DECISIONS.md` ADR 0043 — r6 design decisions.
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
- r6 is committed as a proposed draft but NOT approved: no product source,
  schemas, discovery/register text, or glossary amendment may begin before G0.
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
