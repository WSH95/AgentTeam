---
updated_at: 2026-08-24T19:11:54Z
updated_by: cli
session_status: closed
branch: main
last_commit: 856d525
---
# Handoff

## Now

**M1a IS COMPLETE — closed as a semantic PASS (ADR 0038, 2026-08-24).** All
eight gates are done. The live PoC passed both acceptance tiers under the
ADR 0036 amended gate (Claude Code + Codex legs + Claude synthesis;
`run-20260824-170359-58d9`); the final credential-free matrices plus the
new vendor-smoke job are **12/12 green** at `0864742` (run 32765672784) —
the vendor-smoke job caught and drove fixes for two real Windows product
bugs on its first day (bare-name launcher resolution `1555c5d`;
case-insensitive env baseline `0864742`), giving R30 its first real
`.cmd`-shim evidence; the pinned history secret scan sits at the 3-hit
enumerated benign baseline; the owner-reviewed sanitized evidence bundle is
committed at `docs/evidence/m1a-live-2026-08-24/` with its sibling G8
record; and the M1b draft (`docs/plans/m1b-team-foundation.md`, r0) is
proposed and NOT approved. 25 of the 30-call live ceiling are spent; **5
remain, each a future individual owner ceiling decision**.

## In flight

Nothing. The closure commit carrying this handoff is the last local work;
after its push the tree and origin are identical.

## Next steps (a NEW approval scope — nothing starts automatically)

1. **M1b planning**: expand `docs/plans/m1b-team-foundation.md` in its own
   session (contracts, gates, test matrix, budget, stop rules), run an
   independent review (the `3407ec9`/`317bb52` precedent), and record owner
   approval as a DECISIONS entry naming the file + SHA. The draft ClawTeam
   exit criterion (≤1.5× local-provider LOC + caveats accepted in writing)
   finalizes there. Local deterministic provider first (ADR 0018).
2. Open questions that may ride along: Q4 (bounded ClawTeam upstream PRs),
   Q6 (Hermes expansion trigger), HB-03 register amendment, R15/overlay
   question before M3.
3. Grok re-entry: on a new Grok CLI release, fresh probes + an owner
   decision may restore the all-three live gate (ADR 0036; RISKS R27/R33).
4. Follow-ups noted in reviews, none blocking: exec-bit flattening (R34),
   owner-only sweep-helper extraction, chmod-failure reporting, npm-channel
   drift watch on the vendor-smoke job.

## Blockers

None. M1b needs its own reviewed plan and explicit owner approval before
any implementation (PROJECT.md; plan §18).

## Key files

- `docs/evidence/m1a-live-2026-08-24/` + `docs/evidence/m1a-live-2026-08-24.md`
  — the committed acceptance evidence and its G8 record.
- `docs/plans/m1b-team-foundation.md` — the unapproved M1b draft r0.
- `.project-steward/DECISIONS.md` ADRs 0034–0038 — the complete G6→G8
  decision trail (steering scope, §18 ruling, gate amendment,
  build-vs-reuse reaffirmation, M1a closure).
- `.project-steward/VERIFY.md` — gate-by-gate evidence, newest first (G8,
  G7 incl. the pinned secret-scan command, five G6 cycles, G6.R sections).
- `~/.agentteam/runs/` — raw archives, local-only forever.

## Tried and rejected (session highlights for a successor)

- Grok text-channel fallback and `--max-turns`: both investigated and
  falsified live; fail-hard held; the gate amendment was the evidence-based
  outcome.
- Weakening validators (attribution pairs, oracle categories) instead of
  fixing steering: rejected each time; cycle 5 proved the steering live.
- Building on ClawTeam/OpenClaw/Hermes instead of the thin layer: examined
  end-to-end under an owner challenge (ADR 0037) — reuse is staged where it
  belongs (M1b provider, later surfaces), not rebuilt.

## Warnings

- **5 of 30 live calls remain**; ADR 0033 discipline binds every one.
- Capability evidence is version-bound (Claude 2.1.241 / Codex 0.149.1 /
  Grok 1.0.5); any CLI drift forces doctor/probe reassessment first.
- Test counts moved this session: core 453+4 / extra ~465+3 + compat 12
  (state the mode). Pinned package hash: `fd54eae7dbaa…`.
- The vendor-smoke job installs npm CLIs at latest: vendor flag/channel
  drift will surface there by design — treat a red as dated capability
  evidence, not noise.
- Raw run archives never leave `~/.agentteam/runs/`; promotion only via the
  reviewed sanitizer path.
