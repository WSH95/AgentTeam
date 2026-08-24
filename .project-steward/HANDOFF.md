---
updated_at: 2026-08-24T04:46:50Z
updated_by: codex
session_status: active
branch: main
last_commit: 549804f
---
# Handoff

## Now

**M1a G5's credential-free implementation is complete locally; G5 itself is
OPEN for owner-attended login/probe evidence.** G1–G4 are closed. The public
remote remains at the last approved G4 push; this session has not pushed.

Two local semantic boundaries implement the supplied G5 plan:

- `549804f fix(run): enforce authenticated homes and readiness` — live runs
  resolve the persistent profile vendor homes; render-only stays synthetic;
  current version-bound `verified` rows gate live calls; adapters use fixed
  verified-only channel ladders; Claude config-home Skills use an exclusive
  marked-directory lease held through invocation and cleaned in `finally`.
- The feature boundary carrying this handoff — secure/atomic owner-only
  `profile init`; correct Claude/Codex/Grok login commands and safe seed
  configs; sanitized no-call install/auth/readiness doctor; TTY-gated
  sequential `doctor --probe`; one confirmation per invocation, two-call
  ceiling, random instruction/Skill markers, primary/fallback recipes,
  owner-only pending/terminal captures, and atomic partial capability-row
  updates. The shared shell-free process runner now polls Popen pipes/process
  state rather than relying on a flaky sandbox child watcher.

Credential-free validation is green: Ruff lint/format, strict mypy (97 files),
schema reproduction, **385 passed + 3 Ubuntu-skipped Windows-only tests**, and
wheel/sdist build. Exact evidence is in VERIFY "G5 deterministic
implementation verification". No vendor login, credential read/copy, model
call, live fixture promotion, G6 run, or push occurred.

## In flight

Only the owner-attended portion of G5 remains. The feature boundary containing
this handoff is local; each push still requires its own explicit owner
approval. G6 is prohibited until all required probe rows are current and
verified.

## Next steps

1. Review the local G5 commits/diff. Do not push unless the owner separately
   approves that push.
2. On the owner host, run `uv run atm profile init` (default
   `~/.agentteam/profiles.yaml`; init refuses overwrite) and run each printed
   command yourself: `claude auth login`, `codex login`, and
   `grok login --oauth`, each with its dedicated config-home variable already
   rendered in the printed command. AgentTeam never opens a browser or reads
   credential files.
3. Run `uv run atm profile doctor`. An exit 1 for unprobed readiness rows is
   expected after successful login; exit 2 means invalid/unsafe config and
   must be fixed before any probe.
4. Run `uv run atm profile doctor --probe` from a TTY. Confirm each vendor call
   individually. Normal budget is three calls; fallbacks can raise the total
   to six, never more than two per harness. Decline/Ctrl-C exits 130 and keeps
   completed evidence.
5. Review raw owner-only captures under
   `~/.agentteam/probes/YYYY-MM-DD/<probe-id>/`. Promote only manually
   sanitized representative Claude/Codex/Grok parser fixtures, then rerun the
   credential-free block and record actual CLI versions, channels, output
   locations, call counts, and sanitization in PLAN/VERIFY/DECISIONS/PROGRESS.
   Close G5 only when every required readiness row passes.
6. Start G6 only after G5 closes: `uv run atm run
   examples/run-requests/live-review.yaml`, under the separately confirmed
   acceptance-cycle budget and stop rules.

## Blockers

- The dedicated vendor logins and 3–6 model calls require the owner at a TTY.
- No deterministic/code blocker remains for G5.

## Key files

- `src/agentteam/profile/{setup,doctor,probe,capture}.py` and
  `src/agentteam/commands/profile.py` — G5 lifecycle and CLI.
- `src/agentteam/run/preflight.py`, `src/agentteam/run/runner.py`,
  `src/agentteam/harness/{capabilities,skills,process}.py` — live readiness,
  persistent homes, lease, and process handling.
- `tests/integration/test_profile_probe.py`,
  `tests/integration/test_cli_profile.py`, `tests/unit/test_profile_setup.py`,
  `tests/unit/test_probe_capture.py`, and `fixtures/fake-harness/` —
  credential-free matrix.
- `docs/plans/m1a-direct-harness-poc.md` §11/§13/§14; VERIFY "G5
  deterministic implementation verification"; DECISIONS 0026.

## Tried and rejected

- No automatic login/browser launch, API-key fallback, credential copying,
  hidden retry, model substitution, synthesis, or automatic fixture promotion
  is allowed in probes.
- Do not use stale/observed/unverified capability rows for a live run; rerun
  doctor/probes after a CLI version change.
- Do not use an unmarked nonempty Claude Skill directory. The managed
  config-home channel is leased cross-process and only managed payload is
  cleaned.
- The original asyncio child-watcher path intermittently hung on short-lived
  fake children in this sandbox; Popen + nonblocking polling passed the full
  deterministic suite while preserving shell-free/tree-kill semantics.

## Warnings

- Raw probe stdout/stderr may contain sensitive workspace/vendor material even
  though directories are owner-only. Never add or publish raw captures.
- G5 live claims are Ubuntu owner-host claims only. Hosted CI stays fake and
  credential-free; the revised runner still needs the next pushed Windows CI
  evidence.
- The checked-in fake profile uses disposable persistent homes created by the
  pytest session fixture; run the test suite as one pytest process so parallel
  pytest sessions do not race that shared fixture root.
- Editing `examples/assistants/code-reviewer/` changes the pinned package hash;
  changing fake findings can invalidate fixture/oracle line coupling.
