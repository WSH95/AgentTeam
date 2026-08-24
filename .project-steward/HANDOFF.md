---
updated_at: 2026-08-24T08:28:46Z
updated_by: codex
session_status: active
branch: main
last_commit: 695a4a4
---
# Handoff

## Now

**M1a G5 is closed; G6 is the next gate and has not started.** G1–G4 were
already closed. The commit carrying this handoff records the complete G5
boundary locally; nothing has been pushed.

The owner profiles use dedicated persistent native-auth homes and inherit the
normal terminal/Sing-box proxy variables unchanged. Actual versions are Claude
Code 2.1.241, Codex 0.149.1, and Grok 1.0.5. Final authoritative capture
`probe-20260824T075919Z-1edf636a` contains exactly one successful call per
harness and no fallback calls:

- Claude passed in 10.363 seconds with five verified primary rows.
- Codex passed in 20.490 seconds with seven verified rows, including
  authoritative output-file and matching final JSONL telemetry.
- Grok passed in 17.195 seconds with eight required verified rows, both Skill
  body markers, and the field structured-output location.

All artifact hashes recompute with zero mismatches; capture directories are
0700 and files 0600. Sanitized no-call doctor exits 0 with all three profiles
ready, no conflicts, no missing flags, no version mismatch or staleness, and
no readiness problems. Capability inventory still includes unused fallbacks:
Claude has 3 `observed`, Codex 2, and Grok 1 `observed` plus the unselected
JSON-in-`text` alternative `unverified`. This is intentional: readiness needs
the required base plus one current verified channel per ladder, not exhaustive
proof of every fallback (ADR 0031).

The implementation includes secure/atomic profile initialization, terminal
proxy inheritance with explicit-deny support, sanitized diagnostics,
TTY-gated sequential bounded probes, owner-only captures, partial atomic
evidence updates, persistent authenticated homes for live runs, verified-only
adapter ladders, a safe exclusive Claude Skill lease, corrected Grok argv and
output parsing, and selectable authoritative `--reprobe-ready`.

Credential-free verification is green: Ruff lint/format, strict mypy (97
files), schema reproduction, **404 passed + 3 expected Windows-only skips**,
wheel/sdist build, and `git diff --check`. Reviewed sanitized vendor envelope
fixtures are tracked; raw captures remain outside git. No credential file or
proxy value was read/copied, and no API-key/CI model call, G6 run, push, or
package publication occurred.

## In flight

No process is running. G5 has no remaining item. G6 requires a fresh explicit
owner-attended execution decision; closing G5 does not start it automatically.

## Next steps

1. Review the local G5 closure commit and worktree status. Do not push unless
   the owner separately approves that push.
2. Before G6, review the exact live-PoC command, four-call normal path (three
   independent legs plus fresh Claude synthesis), retry ceiling, stop rules,
   workspace/output targets, and expected evidence. Obtain explicit owner
   confirmation immediately before execution.
3. Only after that confirmation, run `uv run atm run
   examples/run-requests/live-review.yaml` from the repository in the normal
   proxy environment. G6 remains bounded by the approved M1a call/time budget
   and never starts a second cycle automatically.
4. Review the owner-only G6 archive, promote only manually sanitized evidence,
   rerun the credential-free block, and close G6 only if both mechanical and
   semantic acceptance tiers pass. Otherwise retain the failure and stop.

## Blockers

- None for G5. G6 is intentionally waiting for its explicit owner-attended
  execution confirmation and pre-run review.

## Key files

- `src/agentteam/commands/profile.py` and
  `src/agentteam/profile/{setup,doctor,probe,capture}.py` — G5 lifecycle and
  authoritative reassessment.
- `src/agentteam/harness/{environment,skills,claude,codex,grok}.py` — native
  environment and verified channel selection.
- `src/agentteam/run/` and `examples/run-requests/live-review.yaml` — the
  already implemented but not-yet-executed G6 path.
- PLAN G5/G6, VERIFY G5, DECISIONS 0026–0031, and RISKS R21/R27/R31/R33.

## Tried and rejected

- Never unset the owner's proxy variables; Sing-box is intentional network
  infrastructure. Explicit `proxy_policy: deny` remains opt-in.
- Help flags or Skill discovery alone do not verify behavior; only exact
  random markers under the AgentTeam runner upgrade a row.
- Bare Grok `-p` plus `--prompt-file` is invalid in 1.0.5; use the corrected
  prompt-file recipe and explicit Skill slash names.
- Do not require every fallback capability to become verified. Doing so would
  spend calls without improving current-path readiness and would confuse
  advertised alternatives with the selected runtime contract.
- No automatic login/browser launch, API-key fallback, hidden retry, model
  substitution, or raw-capture promotion is allowed.

## Warnings

- Raw probe/run streams can contain vendor/workspace material. Keep
  `~/.agentteam/` owner-only and never add or publish raw captures.
- Capability evidence is version-bound. Any CLI version change makes current
  readiness stale and requires doctor/probe reassessment before another live
  run.
- G5 claims are Ubuntu owner-host claims only. Hosted CI remains fake and
  credential-free; Windows/macOS prove deterministic plumbing only.
- Commit permission does not imply push permission. Every push remains a
  separate explicit owner decision.
