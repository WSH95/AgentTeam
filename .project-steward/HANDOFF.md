---
updated_at: 2026-08-24T01:32:50Z
updated_by: cli
session_status: closed
branch: main
last_commit: e699c91
---
# Handoff

## Now

**M1a G3 is COMPLETE and closed (2026-08-23).** G1, G2, and G3 all closed
today. Public repository https://github.com/WSH95/AgentTeam, `main @ 37219bb`,
local == origin, tree clean (except the wrap commit that carries this file).

G3 (per the owner-approved per-gate execution plan; every coding gate needs
such a plan first — standing working agreement):
- `4d6e082` feat(harness): V1 archive hasher; package loader + prohibited-
  content heuristics; §11 selection with `decided_by`; model/effort
  precedence; env builder (conflict names as profile data, fail closed);
  launcher policy (npm `.cmd` shim parser, allowlist, refused,
  `python-script` for fakes); async process runner (tree kill, cancel, 130);
  Claude/Codex/Grok adapters (verified argv recipes, Skill channels,
  injection records, argv guard, redaction by construction); parser fixtures
  (promotion-only after G5); deterministic fakes + `examples/profiles/
  ci-fake.yaml`; example `code-reviewer` package (three Skills).
- `f5e7cbb` feat(cli): exit codes 0/1/2/3/130; `atm assistant validate
  [--strict-content]`; `atm profile init/validate/doctor` (no `--probe`);
  `atm run --render-only` (+ `claude` alias); CI smoke step.
- Fixes on their own push approvals: `42c43be` (bare-dot ruff over the
  fakes), `37219bb` (platform-naive test assertion).
- **Evidence:** all six CI legs green at `37219bb` — run
  https://github.com/WSH95/AgentTeam/actions/runs/32674468887 — including
  the Windows-only `.cmd` shim suite on real runners. 213 tests; no model
  call anywhere. VERIFY "G3 evidence" + "G3 local verification" (deviations
  recorded there; G5 probe items listed).

## In flight

Nothing.

## Next steps

1. **G4 needs its own per-gate execution plan first** (plan mode → review →
   owner approval). Scope per plan §3/§10/§12/§14/§15: the direct ensemble
   state machine (§12 steps 1–12: pending archive before side effects, leg
   workspace copies + target hashes, parallel fan-out, one transient retry,
   synthesis over labelled leg reports only, atomic finalize, stable exit
   codes incl. 3), run archive + `RunRecordV1`/`HarnessInvocationV1`/
   `EnsembleRecordV1` writers, solo mode, `fixtures/review-target/` (three
   labelled defects) + oracle outside the workspace + the deterministic §14
   matcher, example run-requests, cross-OS example-package hash identity in
   CI, deterministic acceptance jobs, and the optional exact-pinned ClawTeam
   seam qualification (separate uv extra install in CI; `src/agentteam/
   compat/clawteam.py`; report under `docs/`; failure never contaminates the
   direct core). Synthesis instruction file `src/agentteam/synthesis/
   instructions.md` (hash carried by `EnsembleRecordV1`).
2. The wrap commit after this handoff is local; push only on explicit
   approval.
3. Still parked: HB-03 register amendment (owner answer pending); AGENTS.md
   `Live PoC` row at G4 (own shown diff); G5 probe items (Claude skill
   channel + `--append-system-prompt-file`, Codex final event, Grok
   structured-output location + auth).

## Blockers

- None for planning G4. Live calls stay behind G5/G6 (probes ≤ 2/harness,
  ceiling 30 calls, owner-attended).

## Key files

- `src/agentteam/{harness,resolution,commands}/` — the G3 core; `tests/`
  213 tests; `fixtures/fake-harness/` + `examples/profiles/ci-fake.yaml`;
  `examples/assistants/code-reviewer/`.
- `docs/plans/m1a-direct-harness-poc.md` §10/§12/§13/§14/§15 — the G4 spec.
- `.project-steward/VERIFY.md` — G3 evidence + deviations; DECISIONS 0023/
  0024; PLAN (G4 next).
- Run everything locally as `env -u PYTHONPATH uv run …` (ROS quirk); lint
  is bare-dot (`ruff check .`) exactly as CI runs it.

## Tried and rejected

- Never push without explicit approval; each push its own gate.
- No model call in tests/CI; fakes only until G5/G6.
- Do not use `grok agent headless` (WebSocket relay); headless Grok is
  `grok -p`. Codex `exec` has no `-a` flag — approval via
  `-c approval_policy="never"`.
- Skills only into `.agentteam-managed`-marked dirs; never unmarked ones.
- `Path("/abs/x")` is not absolute on Windows — never assert on it.

## Warnings

- Vendor-facing schema/channel choices are probe-verified at G5; the parser
  tolerates both Grok structured-output locations until then.
- The example package hash is content-derived; editing
  `examples/assistants/code-reviewer/` changes bundle hashes G4 will pin.
- ClawTeam qualification (G4) uses the optional extra in a separate CI job
  only; never `--all-extras` on the core legs.
