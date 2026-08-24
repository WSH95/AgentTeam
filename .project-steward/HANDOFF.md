---
updated_at: 2026-08-24T01:58:50Z
updated_by: cli
session_status: closed
branch: main
last_commit: b8d5f9d
---
# Handoff

## Now

**M1a G4 is COMPLETE and closed (2026-08-23).** G1–G4 all closed. Public
repository https://github.com/WSH95/AgentTeam, origin `main @ b8d5f9d`
(**all nine CI checks green on the first push** — run 32681299831: six
scaffold legs ubuntu/windows/macos × 3.11/3.13 plus the three-OS `clawteam`
job). The tree carries only the G4 closure commit after this handoff.

G4 (per the owner-approved per-gate execution plan; every coding gate needs
such a plan first — standing working agreement):
- `e699c91` feat(run): the §12 state machine — pending archive before any
  side effect (atomic writes, POSIX 0700/0600, Windows profile warn, SHA-256
  manifest), per-leg isolated workspace copies + raw-bytes target hashing
  with injection-derived exclusions, concurrent legs, one same-harness
  transient-only retry, synthesis over labelled leg reports only
  (`src/agentteam/synthesis/instructions.md`, LF-normalised instruction
  hash, attribution validated), §14 matcher + mechanical/semantic tier
  evaluators, the tested archive sanitizer, the live `atm run` path (exit
  0/1/2/3/130), `RunRequestV1.acceptance.oracle` (additive, schema regen).
- `48cac73` test(poc): `fixtures/review-target/` (3 seeded defects; labels
  only in `fixtures/review-target.oracle.json`), example run requests
  (direct-review / live-review), the acceptance suite (both tiers PASS
  deterministically; exit-3 and exit-1 paths; ≤8-call budget; SIGINT→130),
  pinned cross-OS package hash `fb9e98a3…`, two named CI steps. Plus a
  redaction hardening the sanitizer caught: launcher argv prefixes are now
  placeholdered in every command record.
- `b8d5f9d` test(substrate): the §10 ClawTeam anti-corruption seam
  (`src/agentteam/compat/clawteam.py`, pinned 0119833…): one data root per
  process, opaque names, explicit file primitives, global bus replaced +
  hook loader spent — hostile-hook fixture proves no user hook executes; 12
  scenarios green on 3 OSes; report
  `docs/evidence/clawteam-qualification-2026-08-23.md`; `clawteam` CI job;
  core legs never install the extra (skip-clean proven).
- **354 tests with the extra / 342 + clean skip without.** Deviations and
  the full local block: VERIFY "G4 local verification" + "G4 evidence".
- AGENTS.md carries the owner-approved `Live PoC` row + stack-line cleanup
  (DECISIONS 0025).

## In flight

Nothing. The G4 closure commit (steward files + AGENTS.md diffs) is local
until the owner approves its push.

## Next steps

1. **G5 — native-auth preflight and probes (owner-attended).** The owner
   runs `atm profile init` (writes `~/.agentteam/profiles.yaml` + vendor
   config homes) and performs one interactive login per vendor home
   (`claude /login`, `codex login`, `grok` auth — each pointed at its
   `~/.agentteam/vendors/<harness>` via the config-home env var; init
   prints the instructions). Then implement `atm profile doctor --probe`:
   at most **two calls per harness**, outside the acceptance cycle, writing
   capability verification levels + `cli_version`/`verified_at` into the
   profile. The probes settle the parked items: Claude Skill channel
   (config-home skills vs `--plugin-dir` vs workspace) and
   `--append-system-prompt-file`; Codex final-event shape; Grok
   structured-output location and auth (Grok stays `unverified` until its
   first live leg). Raw captures land in gitignored `~/.agentteam/probes/`.
   G5 needs its own small per-gate plan first (working agreement).
2. **G6 — Ubuntu live PoC** after G5: `uv run atm run
   examples/run-requests/live-review.yaml` (the AGENTS.md Live PoC row);
   one cycle ≤ 8 calls; reruns only with separate owner confirmation (≤2);
   hard ceiling 30 calls. Exit 3 routes to definition/prompt work; the
   sanitizer (`agentteam.run.sanitize`) is already tested for the G8
   evidence bundle.
3. Housekeeping: the G4 closure commit is unpushed (own approval); HB-03
   register amendment still awaits the owner's QUESTIONS answer.

## Blockers

- G5/G6 need the owner present for logins and live calls. Nothing blocks
  planning G5.

## Key files

- `src/agentteam/run/` — the runner (preflight/archive/workspace/runner/
  synthesis/acceptance/sanitize); `src/agentteam/compat/clawteam.py`;
  `tests/{acceptance,compatibility}/`; `fixtures/review-target*`;
  `examples/run-requests/`.
- `docs/plans/m1a-direct-harness-poc.md` §11 (probes), §14 (live
  conditions), §13 (evidence privacy) — the G5/G6 spec.
- VERIFY "G4 evidence"/"G4 local verification" (deviations 1–16);
  DECISIONS 0025; `docs/evidence/clawteam-qualification-2026-08-23.md`.
- Run everything locally as `env -u PYTHONPATH uv run …` (ROS quirk); lint
  is bare-dot exactly as CI; extra installed locally right now
  (`uv sync --frozen --all-groups --extra clawteam`).

## Tried and rejected

- Never push without explicit approval; each push its own gate.
- No model call in tests/CI; fakes only until G5/G6. Probes ≤2/harness.
- Exit 3 is semantic-only; mechanical failures (incl. target mutation and
  package re-hash) exit 1 with the stop-rule reason.
- ClawTeam: never `--all-extras` on core legs; teams with empty `user`
  (a user name prefixes inbox dirs and desynchronises send/receive); the
  owner's `~/.clawteam` is refused by the seam and untouched by tests.
- `Path("/abs/x")` is not absolute on Windows — never assert on it.

## Warnings

- Editing `examples/assistants/code-reviewer/` changes the pinned package
  hash (`tests/acceptance/test_hash_identity.py` documents regeneration).
- The fakes' finding lines are coupled to `fixtures/review-target/` line
  numbers and the oracle windows; `tests/acceptance/test_fixture_consistency.py`
  is the net that catches drift.
- Vendor-facing schema/channel choices remain probe-verified at G5; the
  Grok parser tolerates both structured-output locations until then.
