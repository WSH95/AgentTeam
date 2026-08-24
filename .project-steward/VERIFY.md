# Verification

How to check the project is healthy. The commands in `AGENTS.md` are the
current credential-free local block; live model calls are always separate,
owner-attended gates.

## G5.R pre-G6 remediation — 2026-08-24 (implemented locally)

| Check | Result |
| --- | --- |
| R3 managed-Skills lifetime | PASS — preparation and concurrent execution share one outer `try/finally`; both a later-leg workspace-copy mismatch and an unexpected archive-write exception prove an already-acquired Claude lease is closed |
| R4 bounded probe termination | PASS — POSIX always sends group SIGKILL after the SIGTERM grace; drains are bounded at 10s then 5s with direct-kill and abandoned-pipes fallback. A real parent-exits/descendant-ignores-SIGTERM case completes in under 5s and stops the descendant; a stuck-process double proves no unbounded `communicate()` remains |
| R5 channel currency | PASS — live preflight carries each observed CLI version into every leg and synthesis plan; adapters select only rows verified at that exact version, mixed-currency ladders fall back correctly, and `execute_run` rejects non-live plans or a missing observed version before archive creation. Render-only remains explicitly versionless |
| R6 problem persistence | PASS — invocation records and the regenerated V1 schema carry optional-default `problems`; normal and synthesis paths persist extractor/parser problems; Codex agreement is quiet while a deterministic live-shaped `-o`/JSONL mismatch remains telemetry on a succeeded invocation and survives sanitization |
| H9 named gaps | PASS — exact Claude allowed/disallowed tool sets and forbidden flags, ADR 0028's negative fake branch, Grok snake-case `structured_output`, all adapter channel-error ladders, live-preflight missing/failed-version/symlink/synthesis branches, and real `typer.confirm` EOF→130 are covered |
| Full local CI parity | PASS — core mode: `uv lock --check`, frozen sync, Ruff lint + format (101 files), strict mypy (97 files), **pytest 417 passed + 4 skips**, schema check + stable export, wheel/sdist build, CLI help/version, strict Assistant validation, three-harness render-only smoke, pinned hash `fb9e98a3…`, and deterministic acceptance both tiers. Optional-extra mode: the same checks, **pytest 429 passed + 3 skips**, and `tests/compatibility` **12 passed**. `git diff --check` is clean; the environment was restored to core mode |
| Hosted CI at `30c17b5` | **FAIL, local fix pending commit/push** — run [32734735405](https://github.com/WSH95/AgentTeam/actions/runs/32734735405) finished 7/9 green: all three optional-ClawTeam jobs and all four Linux/macOS scaffold jobs passed; both Windows scaffold jobs reached Tests and failed the same single test. `test_probe_final_pipe_drain_is_bounded` forced the POSIX path and attempted to monkeypatch absent `os.killpg`; production Windows code was not implicated. The local follow-up tests `_drain_terminated_probe_process` directly on every platform; focused 29 passed, full core 417+4, Ruff/format, and mypy/97 are green. A fresh 9/9 hosted run is required before G5.R re-closes |
| Boundary | PASS — deterministic local fakes and credential-free hosted CI only; no owner credential/vendor-home read, live vendor/model call, or G6 run. Commit `30c17b5` was pushed to `origin/main` on explicit approval solely to run CI; no other remote mutation occurred. `AGENTS.md` and `CLAUDE.md` are untouched |

Last verified: 2026-08-24 by Codex (G5.R deterministic remediation, two-mode
local CI parity, and hosted run 32734735405 diagnosis; no vendor/model call or
credential read).

## G5 independent review — 2026-08-24 (closure verified; two CI regressions fixed)

Review record: `docs/reviews/2026-08-24-g5-review-at-317bb52.md` (ADR 0032);
scope `549804f..317bb52`; owner-host evidence audited by the reviewer only,
`~/.agentteam/vendors/` never read, no vendor model call.

| Check | Result |
| --- | --- |
| Owner-host evidence | PASS — all five captures: 45/45 manifest-recorded artifact SHA-256s recompute, every dir 0700 / file 0600, statuses/durations match every cited number (180640 ms SIGKILL timeout; 44 ms exit-2 reject; 12362 ms exit-0/assessment-failed; 16562 ms; final 10363/20490/17195 ms); final capture exactly one call per harness; 9 call dirs total = Claude 3 / Codex 2 / Grok 4, each traced to ADR 0028/0029/0030 + Q12; 21 of the 30-call ceiling remain |
| Installed CLIs | PASS — `2.1.241 (Claude Code)`, `codex-cli 0.149.1`, `grok 1.0.5 (5115b46bc9)` byte-match the claims and the profile rows; every adapter/probe flag present in `--help` |
| Profiles + doctor | PASS — rows Claude 5v/3o, Codex 7v/2o, Grok 8v/1o/1u, version-bound, `proxy_policy: inherit`, names only; no-call doctor exit 0, all ready, `conflicts_set: []`, six inherited proxy names, provably non-mutating (before/after content hash) |
| Fixture promotion | PASS — zero distinctive fixture literals appear in the raw captures (only shared vendor protocol vocabulary); hygiene caveats H1/H2 recorded in the review |
| CI parity at `317bb52` | **FAIL, now fixed** — R1: `from click import Abort` was an undeclared dependency (typer 0.27.1 vendors Click; external click arrives only via the clawteam extra): core-mode mypy 2 errors, pytest 7 collection errors, every `atm` command dead — all six scaffold legs would have failed; fixed in `739be1a` (also restores prompt Ctrl-C → exit 130, review R2). R8: the deterministic-acceptance step lacked the fake vendor homes the new live preflight requires — fixed in `83f2b3b` |
| Post-fix full CI step list (local) | PASS, 0 failures — core mode: lock check, frozen sync, bare-dot Ruff + format, strict mypy, **pytest 392 passed + 4 skips**, schema check + export round-trip, `uv build`, `atm --help/--version`, `assistant validate --strict-content`, three-harness render-only smoke, pinned hash `fb9e98a3…`, deterministic acceptance both tiers; extra mode: **pytest 404 passed + 3 skips** and `tests/compatibility` 12 passed; `git diff --check` clean; owner `profiles.yaml` hash unchanged across the whole suite |
| Code vs ADR 0026–0030 contracts | PASS with recorded findings — ceilings, evidence semantics (call-2 unresolved-only vs authoritative downgrade), capture lifecycle, redaction (value-absence sweep), atomic locked profile updates, proxy inherit/deny, Claude/Grok argv all verified at cited lines; R3–R6 (lease leak on early-return paths, unbounded kill-escalation branch, stale-verified channel selection, discarded live Codex `-o`/JSONL disagreement) filed as PLAN G5.R pre-G6 tasks |
| Boundary | PASS — nothing pushed at review time; no tracked capture/secret/proxy-value/absolute path in the range; no G6 run; AGENTS.md/CLAUDE.md untouched; review wrote only `docs/reviews/`, steward records, and the two owner-ruled fixes |

Hosted evidence (failure history recorded, not hidden; each fix push
separately owner-approved):

- Run 32722979375 at `cc81b51` (the approved `03635e7..cc81b51` push):
  **7 of 9 green**; both Windows scaffold legs failed at **Typecheck** —
  mypy analyzing under the runner's native `platform=win32` rejects the G5
  POSIX-only branches (`fcntl.flock`, `os.killpg`, `os.fchmod`, `SIGKILL`),
  flips the win32 type-ignores to unused, and marks POSIX statements
  unreachable (~20 analysis errors; no Windows test ran). Fix `0dfbca9`:
  `[tool.mypy] platform = "linux"` so all nine legs type-check the identical
  code view as the green local runs; Windows runtime behavior stays proven
  by pytest on the Windows legs.
- Run 32723369374 at `0dfbca9`: Typecheck green everywhere; the Windows
  legs reached **Tests** — the first real-Windows execution of the G5
  paths — and failed 3 of 384: the sanitized-bundle round trip
  **fail-closed correctly** on `inv-codex.json` (the Codex
  `model_instructions_file` path is embedded via `json.dumps`, so its
  Windows spelling carries doubled backslashes and the raw-path redaction
  needle missed it), and two profile-init tests asserted the POSIX
  login-command form while win32 intentionally prints PowerShell-quoted
  commands. Fix `5d27d2f`: the redaction also replaces each needle's
  JSON-escaped spelling (identical on POSIX) with a Windows-shaped
  regression test that runs on every OS, and the two tests assert the
  platform-appropriate form. Local suite after: 405 passed + 3 skips.
- Run 32724844619 at `5d27d2f`: **all nine checks green** — six scaffold
  legs (ubuntu/windows/macos × 3.11/3.13) and the three-OS `clawteam` job.
  First complete hosted evidence for the G5 work.

Last verified: 2026-08-24 by Claude (Fable 5) independent review session
(read-only evidence audit + credential-free local execution; no vendor model
call; no credential or proxy value read).

## G5 deterministic and owner-host verification — 2026-08-24 (gate closed)

| Check | Result |
| --- | --- |
| Credential-free block | PASS — `ruff check .`; `ruff format --check .` (101 files); strict `mypy src tests` (97 files); `pytest -q --tb=short` (**404 passed, 3 Windows-only skips on Ubuntu**); `python -m agentteam.schema check`; `uv build` produced `agentteam-0.1.0a0` wheel + sdist; `git diff --check` clean |
| Profile initialization | PASS deterministically — refuses overwrite/symlinked homes/unmarked nonempty Claude Skill roots and existing vendor configs; creates profile/vendor/Skill directories 0700 and files 0600 on POSIX; profile writes are atomic; Codex is seeded for file-backed ChatGPT-only login, Grok compatibility discovery is disabled, and POSIX/PowerShell login commands are tested |
| No-call doctor | PASS deterministically — executable/version/home/expected-version/help-flag/conflict checks, sanitized Claude/Codex auth status parsing, Grok probe-only auth, names-only JSON, no profile mutation, and exit 1 vs 2 paths are covered |
| Attended probes | PASS against stdlib-only fakes — all harnesses preflight before any call; TTY required; confirmation immediately precedes each invocation; profile order and ≤2 calls/harness enforced; prompt decline/Ctrl-C → 130; primary/fallback markers, signed-out/missing flags, malformed output, timeout, Codex `-o` vs JSONL disagreement, Grok camel/snake structured fields and JSON-in-`text`, bare-`-p` rejection, explicit Skill references, partial evidence, and two-call exhaustion are covered. Selectable authoritative re-probes additionally cover aliases/duplicates, invalid option combinations, `not-selected`/`already-ready`, all-three/default selection, forced evidence downgrade, partial cancellation, and profile-order execution independent of flag order |
| Persistence and runtime integration | PASS — captures are pending-first then terminal under owner-only `probes/YYYY-MM-DD/<id>/...`, with redacted command, raw streams/output, hashes, and sanitized result; assessed rows update atomically without disturbing owner settings or never-assessed rows; live runs require current version-bound verified native-auth/channels and persistent homes; render-only remains synthetic; Claude config-home Skills hold an exclusive managed lease through invocation, immediately mark an accepted empty root, preserve unmanaged content, and clean managed payload in `finally` |
| Terminal proxy correction | PASS — `profile init` seeds explicit `inherit`; all present standard uppercase/lowercase proxy names pass unchanged through diagnostics, probes, and live environments independently of custom conflict lists; explicit `deny` rejects them; API/base/provider conflicts stay fail-closed; doctor and captures report names only. Regression coverage includes `NO_PROXY`, doctor exit paths, probe capture redaction, and live preflight. |
| Build note | PASS after the sandboxed isolated build could not fetch a missing Hatchling requirement; the explicitly approved `uv build` rerun with dependency-network access succeeded. No package was published. |
| Boundary | PASS — deterministic tests invoke local fakes only; owner-host calls were separately attended and captured. No credential file or proxy value was read/copied, no API-key/CI call or G6 run occurred, and nothing was pushed. The final all-three reassessment passed and closes G5; G6 remains a separate owner-attended gate. |

The runtime/profile boundary is committed as `549804f`; the profile lifecycle
and bounded probe boundary is committed as `695a4a4`. The commit carrying this
verification records the proxy correction, live-found recipe fixes, and
authoritative re-probe extension. None has been pushed in this session.

Owner-host pre-login checkpoint (2026-08-24): PASS for profile schema and
0700/0600 permissions; actual versions Claude 2.1.241, Codex 0.149.1, Grok
1.0.5 (5115b46bc9); sanitized doctor found no binary/home/flag issue and the
expected signed-out/unverified state when proxy names were omitted. This does
**not** validate the live network policy: the owner uses Sing-box intentionally,
so authentication is paused until proxy inheritance is decided and doctor
honors that policy. The Claude login command was cancelled with exit 130; no
probe/model call or credential-file inspection occurred.

Owner-host proxy-correction checkpoint (2026-08-24): PASS. The owner selected
trusted terminal/Sing-box inheritance (ADR 0027); the three existing profile
rows were changed atomically from `deny` to `inherit` with all other fields
asserted unchanged and mode retained as 0600. No-call doctor ran in the normal
environment and reported the six present standard uppercase/lowercase proxy
names (including `NO_PROXY`/`no_proxy`) as inherited, `conflicts_set: []` for
all three harnesses, healthy executable/version/home/flag checks, Claude/Codex
signed out, and Grok unverified. Exit 1 is expected until login/probes; no
credential file, proxy value, vendor model, or probe call was read or invoked.

Owner-host login checkpoint (2026-08-24): PASS. The owner completed the
printed Claude, Codex, and Grok native-login commands sequentially in their
dedicated config homes with the normal proxy environment intact. Sanitized
post-login doctor reports Claude and Codex `signed-in`, Grok `unverified` as
designed until a structured probe, `conflicts_set: []`, and the same six
inherited proxy names for every harness. Exit 1 is readiness-only. AgentTeam
did not inspect credential files; no probe/model call occurred at this
checkpoint.

Owner-host Claude probe checkpoint (2026-08-24): FAIL, safely bounded. Call 1
under capture `probe-20260824T061711Z-971ee2af` ran for 180.64 seconds, emitted
zero-byte stdout/stderr/output, timed out, and was tree-killed (`SIGKILL`). Its
five assessed capability rows are current-version `unverified`; call 2 was
declined during diagnosis and the command exited 130, so Codex/Grok made zero
calls. Sanitized evidence showed `Skill` missing from Claude's `allowedTools`
despite a prompt requiring Skill invocation under `dontAsk`. ADR 0028 fixes
this in probe/live recipes and makes the fake withhold Skill markers unless
permission is present. Post-fix full block: Ruff/format, strict mypy, schemas,
build, **392 passed + 3 skips**. Anthropic `/v1/messages` credential-free GET
through the inherited proxy returned HTTP 405 in 1.13s, ruling out a generally
broken HTTPS route; no response body or proxy/credential value was captured.
The one remaining Claude invocation was reserved until the fix passed the full
credential-free block.

Owner-host attended continuation checkpoint (2026-08-24): PARTIAL PASS; G5
remains open. Capture `probe-20260824T063407Z-53c52838` used Claude's second
and final actual invocation: exit 0 in 174.77s and all five rows verified
(`headless-json`, `structured-output`, `native-auth`,
`append-system-prompt-file`, `skills-config-home`). Codex call 1 exited 0 in
25.79s and verified all seven rows, including authoritative `-o`, schema,
workspace Skill, JSONL, and matching final agent-message telemetry. Grok's
first confirmed invocation exited 2 in 44ms before model dispatch because the
recipe supplied bare `-p` before `--prompt-file`; the captured stderr states
that `--single <PROMPT>` requires a value. The owner declined the offered
fallback, preserving prior results and exit 130.

After removing bare `-p` from probe and live argv, Grok's second/final
confirmed invocation under `probe-20260824T064233Z-139f93bd` exited 0 in
12.36s. It verified native auth, prompt-file headless mode, `--rules`,
structured output, and JSON encoded in `text` (six current rows total). The
response reproduced the random instruction marker but supplied two invented,
wrong-length Skill-like values. A credential-free `grok inspect --json` in the
preserved probe workspace independently listed both intended Skills as enabled,
user-invocable project sources at `.grok/skills/.../SKILL.md` and
`.agents/skills/.../SKILL.md`; discovery therefore worked, but body delivery
did not. The owner declined the next displayed prompt because it would have
been Grok's third confirmed invocation. Final no-call doctor: Claude ready
(5 verified), Codex ready (7), Grok auth `verified-by-probe` with 6 verified / 3
unverified and exactly one readiness problem — no verified Skill channel.

Capture review and fixture promotion (2026-08-24): PASS with sanitization.
All three capture roots are 0700, manifests are 0600, and every recorded
artifact SHA-256 recomputes. The Claude result envelope, Codex command-event +
final-message JSONL shape, and Grok camelCase `structuredOutput` envelope were
manually reconciled into parser fixtures. Identifiers, prompts, random markers,
commands, reasoning, model names, and usage/cost values are synthetic; raw
captures remain outside git. Post-promotion parser tests pass, and the full
credential-free block remains 392 passed + 3 expected skips. ADR 0029 records
the stop decision and the implementation correction. G6 is prohibited.

Owner-approved corrected Grok checkpoint (2026-08-24): PASS. Capture
`probe-20260824T070542Z-60bf6738` call 1 exited 0 in 16.562 seconds. Its
sanitized result assessed nine rows and verified eight required rows:
headless JSON, native auth, prompt file, rules instructions, both independent
workspace Skill paths, structured output, and the field output location.
JSON-in-`text` is the sole unverified alternative. Manifest/artifact files are
0600 and the result is terminal; raw streams remain owner-only and unpromoted.
No-call readiness is now Claude 5, Codex 7, and Grok 8 verified required rows.

Selectable authoritative re-probe checkpoint (2026-08-24): PASS
deterministically. Normal `--probe` still performs zero calls for ready
profiles. `--reprobe-ready` plus repeatable `--harness` can reassess selected
ready profiles in profile order; nonselected rows remain explicit, all three
still preflight, and assessed failure replaces current evidence atomically.
Focused suites passed 37 tests; the final full block passed Ruff/format, strict
mypy, schema reproduction, **404 tests + 3 expected Windows skips**, wheel and
sdist build, and `git diff --check`. At that checkpoint, the owner-attended
all-three capture was the only remaining G5 item; no G6 run had occurred.

Final authoritative all-three checkpoint (2026-08-24): PASS; **G5 closed**.
Capture `probe-20260824T075919Z-1edf636a` used one call per harness and no
fallback calls. Claude Code 2.1.241 passed in 10.363 seconds and verified its
five primary rows; Codex 0.149.1 passed in 20.490 seconds and verified seven
rows, including authoritative `-o` and matching JSONL telemetry; Grok 1.0.5
passed in 17.195 seconds and verified eight required rows, both Skill bodies,
and field structured output. All three manifests are terminal with exit 0;
all recorded artifact hashes recompute (`0` mismatches); every capture
directory is 0700 and file 0600. Sanitized no-call doctor exits 0: Claude
5 verified / 3 observed, Codex 7 / 2, Grok 8 / 1 observed / 1 unverified;
all are ready with no conflicts, missing flags, version mismatch, staleness, or
readiness problem. The non-verified rows are unused fallback inventory and do
not weaken the proven primary paths. No raw capture was tracked, no credential
or proxy value was read, and G6 was not invoked (ADR 0031).

Last verified: 2026-08-24 by Codex (credential-free fakes + attended owner-host G5 probes).

## G4 evidence — 2026-08-23 (gate closed)

| Check | Result |
| --- | --- |
| Core matrix with the G4 suites | PASS — run 32681299831 (https://github.com/WSH95/AgentTeam/actions/runs/32681299831) at `b8d5f9d`: **all six scaffold legs green** (ubuntu/windows/macos × 3.11/3.13) on the first push — full pytest (incl. `tests/acceptance`), the pinned example-package hash identity step (cross-OS identity `fb9e98a3…`), and the deterministic-acceptance step (full fake ensemble via the CLI; run succeeded, both tiers PASS) |
| Optional ClawTeam matrix | PASS — the **`clawteam` job green on all three OSes** (py3.11, `uv sync --frozen --all-groups --extra clawteam`, `tests/compatibility` only): the seam's 12 qualification scenarios incl. hostile-hook containment passed on real ubuntu/windows/macos runners; the core legs never install the extra and their pytest shows the suite skipping cleanly |
| Failure history (evidence, not hidden) | none — first push green on all nine checks |
| Boundaries | PASS — no model call, no vendor login, no credential; ClawTeam exercised in-process against temporary data roots only |

G4 of the approved M1a plan is complete: the fan-out/synthesis state machine
passes locally and in CI incl. solo mode, selection precedence, three Skills
per harness, and example-package hash identity; the optional ClawTeam seam
passes its compatibility suite on three OSes and its qualification report is
committed; the deterministic-acceptance, hash-identity, and ClawTeam jobs are
in CI.

Last verified: 2026-08-23 by Claude (Fable 5) session.

## G4 local verification — 2026-08-23 (pre-push)

Execution followed the owner-approved G4 per-gate execution plan (design
decisions D1–D12; strict red-first TDD throughout). Commits: `e699c91`
feat(run), `48cac73` test(poc), `b8d5f9d` test(substrate).

| Check | Result |
| --- | --- |
| Local block | PASS — `uv lock --check`; frozen sync; bare-dot `ruff check`/`format --check`; `mypy` strict (86 files, incl. the compat seam and both conftests); `pytest` **354 passed + 3 Windows-only skips** with the clawteam extra, **342 passed + 4 skips** in core mode (the compatibility suite skips cleanly); `uv build` (wheel ships `agentteam/synthesis/instructions.md`); `python -m agentteam.schema check` + export round-trip clean; both new CI steps executed locally verbatim (pinned hash assert; full fake ensemble via the CLI → both tiers PASS) |
| G4 gate items (plan §3) | Complete fan-out/synthesis state machine green locally: §12 steps 4–12 (pending archive before side effects; per-leg isolated copies with verified hashes; all renders before any launch; concurrent legs; one same-harness transient-only retry; synthesis over labelled reports only; attribution validated; package re-hash; atomic finalize; stable exit codes 0/1/2/3/130); solo mode (`decided_by: assistant`, `kind: invocation`, synthesis skipped unless explicit); selection precedence; three Skills rendered per harness (injection records assert all `skill:*` parts); example-package hash identity pinned (`fb9e98a3…`); ClawTeam seam passes its 12-scenario local suite (hostile hooks contained) and the qualification report is written (`docs/evidence/clawteam-qualification-2026-08-23.md`); deterministic-acceptance + hash-identity steps and the `clawteam` job added to CI |
| §14 acceptance (deterministic) | Both tiers PASS end-to-end over the committed fixture/oracle via the real CLI; `semantic-miss` and `invent-critical` exit 3 with mechanics green; target mutation and the package-mutation stop rule exit 1; the retried cycle stays at 6 ≤ 8 calls; oracle never copied into a leg workspace or synthesis input |
| Safety asserts (tests) | no `env_values` key in any archived record; events carry no absolute paths; the sanitized bundle scans clean (no value, no source path, no raw stream) and every emitted record re-validates; POSIX archives 0o700/0o600; SIGINT finalizes cancelled records and exits 130; the compatibility suite never touches the owner's real `~/.clawteam` (session-scoped guard) and the seam refuses it outright |
| Deviations (recorded per the G4 plan, D1–D12 + execution) | (1) `RunRequestV1.acceptance.oracle` additive optional field, schema regenerated; (2) request-file paths resolve request-relative, flag paths CWD-relative; (3) target hashing is a raw-bytes tree hasher with `files_written`-derived exclusions — not the V1 package contract; (4) mechanical failures (leg failure, target mutation, package re-hash mismatch) exit 1 — exit 3 is semantic-only, and the run record then stays `succeeded` with the verdict in the ensemble's semantic tier; (5) oracle carries `aliases`; oracle + archive manifest are internal models (schema set stays nine); (6) `instruction_hash` = LF-normalised SHA-256 of `synthesis/instructions.md`; (7) cond-7/cond-8 are structural in-record checks (artifact re-hash; `env_values`-key scan) — full disk reconstruction and value-absence are proven by tests and the sanitizer; (8) single-leg runs skip synthesis unless the request sets `synthesis` explicitly, and solo runs carry no acceptance tiers; (9) `extract_structured` is an internal adapter helper beyond the §9 four-method protocol; (10) fake `target_sha256` is informational, never compared to the computed tree hash; (11) §16 CI reading: acceptance + hash-identity as named core-matrix steps/tests, one new `clawteam` job, `scaffold` job id kept; (12) `ClawTeamCompat._reset_for_tests` escape hatch; no clawteam `filterwarnings` ignores were needed on py3.11; (13) `test_without_render_only_exits_2_until_g4` replaced by the live launch-path test; (14) launcher argv prefix (interpreter/executable paths) now redacted to the launcher token in every command record — a G3 gap the sanitizer's own scan caught; (15) ClawTeam teams are created with an empty `user` (a user name prefixes inbox directories and desynchronises send/receive); (16) mypy gains `explicit_package_bases` for the second conftest |
| Probe items left for G5 (unchanged) | Claude skill-channel #1 + `--append-system-prompt-file`; Codex final-event shape (adapter uses `-o`); Grok structured-output location (parser tolerates both) + auth |

Last verified: 2026-08-23 by Claude (Fable 5) session (fakes only; no vendor
binary executed by tests; ClawTeam exercised in-process against temp roots).

## G3 evidence — 2026-08-23 (gate closed)

| Check | Result |
| --- | --- |
| Scaffold matrix with the G3 suites | PASS — run 32674468887 (https://github.com/WSH95/AgentTeam/actions/runs/32674468887) at `37219bb`: **all six legs green** (ubuntu/windows/macos x 3.11/3.13). The Windows legs executed the Windows-only `.cmd` shim suite against real runners (resolved-shim branch through real `node`, allowlisted branch through `cmd.exe`, refused branch pre-launch) — first real-shim-environment evidence |
| CI smoke | PASS on every leg — `atm assistant validate examples/assistants/code-reviewer --strict-content` and the three-harness `atm run --render-only` against `ci-fake.yaml` |
| Failure history (evidence, not hidden) | run 32672319094: all legs at Lint (fakes' one-line constants; CI lints bare `.`, local block had been scoped to src/tests) → `42c43be`; run 32673977915: ubuntu+macos green, Windows failed one platform-naive test assertion (`Path("/abs/x")` is drive-relative on Windows) → `37219bb`. Each fix pushed on its own owner approval |
| Boundaries | PASS — no model call, no vendor login, no credential; the only vendor-binary execution in CI is `node` running the synthetic test shim |

G3 of the approved M1a plan is complete: adapters pass argv/env/parser tests
against deterministic fakes incl. Skill-channel rendering, selection with
`decided_by`, and the Windows-only `.cmd` shim fake; the tests are in CI; no
model call.

Last verified: 2026-08-23 by Claude (Fable 5) session.

## G3 local verification — 2026-08-23 (pre-push)

Execution followed the owner-approved G3 execution plan (fact sheet verified
against installed CLIs; design agent + my pass; strict red-first TDD).
Commits: `4d6e082` feat(harness), `f5e7cbb` feat(cli) — local only.

| Check | Result |
| --- | --- |
| Local block (3.11 + fresh 3.13 env) | PASS — `uv lock --check`, frozen sync, `ruff check`/`format --check`, `mypy` strict, `pytest` 212 passed + 3 Windows-only skips, `uv build`, `python -m agentteam.schema check`, `atm --help/--version`, and the two CI smoke lines run locally (validate --strict-content; three-harness render-only against `ci-fake.yaml`) |
| G3 gate items (plan §3) | adapters pass argv/env/parser tests against deterministic fakes (golden argv per harness; fakes observe argv/env/stdin; round trips valid); Skill-channel rendering per harness (config-home / .agents / .grok channels, `.agentteam-managed` marker, required-skill failure before launch); selection with `decided_by` incl. hard exit-2 failures; the Windows-only `.cmd` suite is in the tree and runs on the windows CI legs; all tests ride the CI pytest step; **no model call anywhere** |
| Safety asserts (tests) | render-only writes only under the output dir (package/workspace digests unchanged); `invocation.render.json` has no `env_values` (excluded at the model level); doctor output is names-only (value-leak test); conflict env vars fail closed |
| Deviations (recorded per the G3 plan) | `python-script` launcher-policy enum (additive schema regen); `parse() -> ParsedLegV1`; extra `feat(cli)` commit; Codex `-c approval_policy="never"` (no `-a` on `exec` 0.149.0); Codex pre-probe instruction channel = workspace `AGENTS.md`; Grok prompt-file preamble (`--rules` is inline-only); minified inline schema for Claude/Grok, file schema for Codex; conflict env lists as seeded profile data; Claude inline `--append-system-prompt` fallback until the G5 probe |
| Probe items left for G5 (by design) | Claude skill-channel #1 + `--append-system-prompt-file`; Codex final-event shape (adapter uses `-o`); Grok structured-output location (parser tolerates both) + auth |

Last verified: 2026-08-23 by Claude (Fable 5) session (fakes only; no vendor
binary executed by tests).

## G2 evidence — 2026-08-23 (gate closed)

| Check | Result |
| --- | --- |
| Repository | PASS — https://github.com/WSH95/AgentTeam is PUBLIC with license `mit`, default branch `main` (`gh repo view --json visibility,licenseInfo,defaultBranchRef`); created and first pushed on the owner's explicit approvals (DECISIONS 0024) |
| Pushed history | `main @ d9440f8`; first push was `8660e6a` (the secret-scanned SHA, 0 hits); `671c2d9` and `d9440f8` are CI fixes, each pushed on its own owner approval |
| Scaffold smoke matrix | PASS — run 32667607711 (https://github.com/WSH95/AgentTeam/actions/runs/32667607711) at `d9440f8`: **all six legs green** — ubuntu-latest/windows-latest/macos-latest x Python 3.11/3.13 (lock check, frozen sync, interpreter assert, ruff, ruff format, mypy, pytest 91, uv build, schema check, export round-trip `git diff --exit-code -- schemas`, `atm --help/--version`) |
| CI failure history (evidence, not hidden) | run 32667232109 at `8660e6a`: all legs failed at job setup — `astral-sh/setup-uv` has no floating `v10` tag → pinned to the v10.0.1 commit (`671c2d9`); run 32667352498 at `671c2d9`: macOS+Windows green, Ubuntu legs failed at the argument-less `uv python find` diagnostic (resolves `.python-version` 3.11; never auto-installs; image ships no 3.11/3.13) → explicit `uv python install <matrix>` + versioned `find` (`d9440f8`) |
| Boundaries | PASS — CI ran with `contents: read` only; no credential, vendor login, or model call anywhere; no package published |

G2 of the approved M1a plan is complete. Gate evidence per plan §3: frozen
`uv.lock`; package builds; checked-in schemas reproduce (all six legs);
`atm --help`/`--version` pass; pre-first-push checklist passed; public
repository created with MIT and pushed after explicit approval; scaffold
smoke matrix green on three OSes.

Last verified: 2026-08-23 by Claude (Fable 5) session.

## G2 local verification — 2026-08-23 (pre-push)

Execution followed the owner-approved G2 plan (drafted, independently reviewed
twice, critiqued, then approved 2026-08-23 in-session). Commits: `cc0cc5f`
chore(core) scaffold, `be5ce15` feat(domain) records+schemas; both local only.

| Check | Result |
| --- | --- |
| Local verification block (3.11) | PASS — `uv lock --check`; `uv sync --frozen --all-groups`; `ruff check .`; `ruff format --check .`; `mypy` (strict + pydantic plugin) clean; `pytest` 91 passed; `uv build`; `python -m agentteam.schema check` current; `export` round-trip leaves `git diff -- schemas` empty; `atm --help`/`--version` |
| Fresh 3.13 environment | PASS — same block (pytest 91, mypy, ruff, schema check, `atm --version`) on CPython 3.13.14 in a scratch `UV_PROJECT_ENVIRONMENT` |
| Commit 3 standalone | PASS — scratch `git worktree` at `cc0cc5f`: sync, pytest (6), ruff, mypy, `atm --version` |
| Package contents | PASS — wheel: `agentteam/py.typed` present, no `tests/`; sdist: `/src/agentteam`, `/schemas` (+README), `/README.md`, `/LICENSE`, `/pyproject.toml` only (anchored includes); wheel smoke `uv run --isolated --no-project --with <wheel> atm --version` prints `atm 0.1.0a0` |
| Schema parity | PASS — nine files reproduce byte-for-byte and are LF on disk (`git ls-files --eol`: all new tracked files `i/lf`); Draft 2020-12 metaschema valid; minimal instances of all nine records validate via `jsonschema` and unknown fields fail both sides; no pattern uses look-around; vendor-facing files have `$defs` inlined, enum-not-const, all properties required |
| Contract fixes vs approved plan | PASS — severity `critical..info` + finding `category` (§14); `default_harness` + tier/reasoning mappings (§11); target hashes (§12/§14); `undeliverable_required_parts`, observed harness, `refused` launcher branch (§9/§11); overrides keyed by harness id (§2/§8); archive-contract manifest validator (§7); terminal ⇒ `finished_at`; execution `ref`↔`kind`; AwareDatetime everywhere |
| Deviations recorded | `api-test` spelling; `clawteam` extra with direct git ref (owner choice; not PyPI-uploadable, nothing published); AGENTS.md table: `Live PoC` deferred to G4, `Schemas` row added (ADR 0023); finding `category` extends §7's field list; invocation attempt identity = `invocation_id` + `retry.attempt`; §7 "bundle hash" = `effective_definition_hash` (+ Member `package_hash`); vendor-envelope fallback decided by G5 probes |
| Pre-first-push checklist (§16) | LICENSE (MIT) + `docs/provenance.md` (no ATM code copied; dependency + ClawTeam MIT notices) PASS; name checks 2026-08-23: GitHub `WSH95/AgentTeam` 404, PyPI `agentteam` 404, local `atm` absent — re-run immediately before creation; history secret scan: see the line below |
| History secret scan | recorded at the STOP question: `git log -p --all` at the final local HEAD through the key-shaped regex set + private-key headers; result and scanned SHA quoted in the push approval; pushed HEAD must equal that SHA |
| Public-visibility facts (not secrets) | commit author e-mail; `Claude-Session:` trailers; 43 `/home/wsh/...` paths in dated docs; tracked `.project-steward/{state.json,config.toml,backend.json}`; candidate-context wording in history — accepted with ADR 0019 (public at G2) |

Last verified: 2026-08-23 by Claude (Fable 5) session (no model call, no
credential read, no ClawTeam install, no push).

## G1 rename and documentation-hygiene verification — 2026-08-23

| Check | Result |
| --- | --- |
| Move (plan §4 items 1–2) | PASS — the owner moved the repository between sessions; at session start the working directory was `/home/wsh/Documents/AgentTeam`, `/home/wsh/Documents/assistant-team-system-dev` no longer existed, `main @ 025d02a` matched the handoff, the tree was clean, no merge/rebase was in progress, and `command -v atm` found no executable on `PATH` |
| Root files (plan §4 item 4) | PASS — `README.md` states alpha/pre-implementation status and links the steward files including QUESTIONS; `LICENSE` is MIT with `Copyright (c) 2026 ShuhanWang`; `.gitattributes` is `* text=auto eol=lf`; `git ls-files --eol` showed all 56 tracked files `i/lf w/lf`, so no renormalisation occurred; `.gitignore` adds Python/`uv` build and cache paths plus `.agentteam/` and `.env*` outside the steward-managed block |
| Identity amendments (plan §4 item 3) | PASS — only living documents changed (discovery landing page, `product-intent.md` frontmatter, one `legacy-atm-disposition.md` question note, PROJECT.md); panel, critic, evidence, decision, and progress text was not rewritten — `git grep -w ats` still lists the same historical files; `CLAUDE.md` remains the thin `@AGENTS.md` adapter; `AGENTS.md` untouched |
| Hygiene list (plan §4 item 6; review H3, H6, H8–H12, R7, R19) | PASS except the deferred item — PROJECT.md success criteria + volatile pins/scope decision moved out (H3); glossary defines HarnessAdapter, CoordinationSubstrate, Run/direct run, `atm`, legacy ATM, `independence {declared, achieved}` (H10/R10/R16); DECISIONS 0022 adds append-only amendment markers for 0007/0009/0012 (R19); VERIFY M0.1 counts corrected and PROGRESS re-sorted newest-first (H9); RISKS has ID/Owner/Status columns, 33 rows R01–R33 (H12); 10 critic files carry closure notes and the fix-pass file a provenance note, the three FAIL blockers spot-checked (H8); `minimal-poc-plan.md` banner confirmed and its pre-r3 Claude bullet amended (H6); both READMEs link QUESTIONS and `config.toml` names where its pointer lives (H11). **Deferred by design:** the HB-03 register amendment (R7) waits for the owner's QUESTIONS answer |
| Local toolchain baseline (moved here from PROJECT.md) | PASS — read-only `--version` checks, no model call: Claude Code 2.1.241, Codex 0.149.0, Grok Build 1.0.5, OpenClaw 2026.7.1-2, Hermes 0.20.4, `uv` 0.11.26 with uv-managed CPython 3.11.16 and 3.13.14, system `python3` 3.8.10; Ubuntu host without tmux |
| Local Markdown targets | PASS — 53 tracked Markdown files scanned, 30 local links checked, 0 broken |
| Markdown fences | PASS — 60 fence markers across 53 files, 0 unbalanced |
| Secret-pattern scan | PASS — 0 API-key-shaped values and 0 private-key headers across tracked files |
| Scope | PASS — commit 1 touched root files, living docs, and steward state; commit 2 is docs/steward only (`.md` plus `config.toml`); no source, dependency, CI workflow, repository, AGENTS.md, credential, model call, or push |
| Patch hygiene | PASS — `git diff --check` exits 0 for both commits |

Last verified: 2026-08-23 by Claude (Fable 5) session (documentation-only; no
credential values or model prompts used).

## G0 approval record — 2026-08-23

| Check | Result |
| --- | --- |
| Approval artefact | PASS — DECISIONS 0021 names `docs/plans/m1a-direct-harness-poc.md` r3 and commit `0f3e478`; the status line was flipped in the following commit |
| Steward consistency | PASS — PLAN M1a marked approved; QUESTIONS current gate = G1; HANDOFF carries the exact G1 move commands and the fresh-session instruction |
| Scope | PASS — documentation/steward only; no move, code, dependency, repository, or push |
| Patch hygiene | PASS — `git diff --check` exits 0 |

Last verified: 2026-08-23 by Claude (Fable 5) session.

## Current M1a r3 review-resolution verification — 2026-08-23

| Check | Result |
| --- | --- |
| Documentation-only scope | PASS — `docs/plans/m1a-direct-harness-poc.md` (r3), one sentence in `docs/discovery/team-execution-model.md` §4 (v2.3), Project Steward records; no code, rename, dependency, credential, model call, CI, remote change, or push |
| Review claims verified read-only | PASS — `claude --help` (2.1.241): `--safe-mode` disables skills/plugins/hooks/MCP, `--bare` never reads OAuth; `codex exec --help` (0.149.0): `--ignore-rules` = execpolicy `.rules` only; `grok inspect` (1.0.5) in a scratch dir lists `.grok/skills/` and `.agents/skills/` as project skill roots; scratch dir removed |
| r3 edit coverage | PASS — header/§1/§2/§3/§6.1/§7/§9/§11/§12/§14/§15/§16/§17/§18/§19/§21/§22 updated; gate names unchanged; status still *proposed* |
| Decision consistency | PASS — ADR 0020 ↔ QUESTIONS (budget, Claude channel) ↔ PLAN gate lines ↔ RISKS rows ↔ HANDOFF next steps |
| Patch hygiene | PASS — `git diff --check` exits 0 |

Last verified: 2026-08-23 by Claude (Fable 5) session (documentation-only).

## Current M1 plan-merge verification — 2026-08-23

| Check | Result |
| --- | --- |
| Documentation-only scope | PASS — `docs/plans/m1a-direct-harness-poc.md` (r2), a banner on `docs/plans/m1-agentteam-direct-slice.md`, and Project Steward records only; no code, rename, dependency, credential, model call, CI, remote change, or push |
| r2 edit coverage | PASS — every row of the approved edit list is present (header, §1–§4, §6–§19, §21, new §22); gate names G0–G8 unchanged; status still *proposed* |
| Decision consistency | PASS — ADR 0019 ↔ QUESTIONS closures ↔ PLAN M1a lines ↔ HANDOFF next steps; ADRs 0012–0018 not reopened |
| `gh` authentication | PASS — `gh auth status` read-only: account `WSH95`, `repo` scope, SSH; no token value recorded |
| Local Markdown targets | see the session's checks recorded in HANDOFF (links in touched documents resolve; future `schemas/`/`examples/` paths are named, not linked) |
| Patch hygiene | PASS — `git diff --check` exits 0 |

Last verified: 2026-08-23 by Claude (Fable 5) session (documentation-only).

## Current provider-neutral documentation verification — 2026-08-23

| Check | Result |
| --- | --- |
| Documentation-only scope | PASS — architecture, planning, evidence, and Project Steward records only; no product code, dependency, credential operation, model call, CI workflow, remote change, or push |
| Prospective-route neutrality | PASS — 0 candidate model, endpoint, credential-variable, or key-prefix identifiers; the provider-name inventory has exactly 1 occurrence, confined to the factual ClawTeam preset list |
| Generic contract retention | PASS — provider/profile/protocol/model fields remain conceptual; credentials remain environment-name-only; API mode remains separate from native auth with no fallback |
| CI and approval boundary | PASS — M1a hosted CI remains deterministic and credential-free; no API-test route is selected or approved and product implementation remains review-gated |
| Decision/history traceability | PASS — ADR 0017 records the neutrality rule; candidate-context history remains recoverable from Git while unrelated third-party capability evidence is preserved |
| Local Markdown targets | PASS — 50 tracked Markdown files scanned, 12 local links checked, 0 broken |
| Markdown fences | PASS — 60 fence markers across 50 tracked Markdown files, 0 unbalanced files |
| Secret-pattern scan | PASS — 0 common API-key-shaped values and 0 private-key headers |
| Patch hygiene | PASS — `git diff --check` exits 0 |

Validation removes tentative route selection from current tracked documentation;
it does not choose or test a provider/model, change CI, approve M1a, or run a
vendor harness.

Last verified: 2026-08-23 by Codex (documentation-only; no credential values or
model prompts used).

## Current Python/optional-provider rebaseline verification — 2026-08-23

| Check | Result |
| --- | --- |
| Documentation-only scope | PASS — only architecture/plan/Project Steward records changed (`state.json` metadata included); no product source, dependency install, rename, credential operation, model call, remote change, push, or generated product artifact |
| Architecture-decision coverage | PASS — Python `>=3.11`/`uv`/Hatchling; checked-in JSON Schema edge; `atm` then M2 MCP; built-in shell-free direct runner; optional exact-pinned in-process ClawTeam boundary; one data root/namespace-only claim; M1b–M4 obligations |
| ClawTeam boundary consistency | PASS — full revision `01198332ef9270c32c5460b8a178f964fc0df451` and `mcp>=1,<2` appear in the proposed plan/decision records; M1a excludes ClawTeam process backends and confines imports to one compatibility module |
| Guarded instruction change | PASS — the owner-approved `AGENTS.md` diff changes only the title, product description, and primary stack above managed blocks; command/task/session managed blocks are byte-unchanged |
| Historical/current-state separation | PASS — living landing/model/steward documents point to the re-baselined M1a proposal; former TypeScript/CLI-first mechanics remain only as explicitly superseded decisions or labelled M0 evidence |
| Frozen requirement matrix | PASS without re-judgment — `existing-systems-fit-gap.md` is untouched and the `product-intent.md` diff is below the frozen register; the prior 54×11 structural regression remains applicable |
| Local Markdown targets | PASS — 50 Markdown files scanned, 12 local links checked, 0 broken |
| Markdown fences | PASS — 60 fence markers across 50 Markdown files, 0 unbalanced files |
| Secret-pattern scan | PASS — 0 API-key-shaped values and 0 private-key headers in the documentation/steward scope |
| Patch hygiene | PASS — `git diff --check` exits 0 |

Validation establishes a coherent documentation and plan rebaseline. It does
not approve product implementation, install/test ClawTeam, execute a vendor
harness, or provide Windows/macOS/live-runtime evidence.

Last verified: 2026-08-23 by Codex (documentation-only; no credential values or
model prompts used).

## Previous M1a planning verification — 2026-08-23 (superseded stack baseline)

| Check | Result |
| --- | --- |
| M0.1 commit boundary | PASS — `3407ec9` contains the completed 22-file documentation review; the worktree was clean immediately afterward |
| Planning-only scope | PASS — proposed implementation plan plus Project Steward plan/decision/question/risk/handoff/verification state only; no product code, dependency, rename, AGENTS/CLAUDE edit, credential operation, model call, remote change, or push |
| Required decision coverage | PASS — AgentTeam/`atm`; TypeScript/Node; Claude + Codex + Grok direct-first; native subscription profiles; model/effort precedence; full local evidence; deterministic CI/live Ubuntu split; API-test and ClawTeam deferral |
| Current runtime baseline | PASS — local Node 24.16.0, npm 11.13.0, pnpm 11.22.0, Claude Code 2.1.241, Codex 0.149.0, and Grok Build 1.0.5 rechecked without a model call |
| Volatile primary-source check | PASS — Node 22/24 remain LTS; Claude auth/env precedence and Codex model/effort/profile configuration rechecked; Anthropic's Help Center says the separate Agent SDK/`claude -p` credit change is paused |
| Local Markdown targets | PASS — the five project-local plan sources and the PLAN-to-plan link resolve |
| Markdown fences | PASS — 14 fence markers (7 balanced blocks) in the proposed plan |
| Secret-pattern scan | PASS — 0 candidate-route-key-shaped values and 0 private-key headers in the planning/steward scope |
| Patch hygiene | PASS — `git diff --check` exits 0 |

The proposed plan is
`docs/plans/m1a-direct-harness-poc.md`. Validation establishes that it is a
complete, internally linked planning artifact; it does not approve the plan or
provide implementation/live-runtime evidence.

Last verified: 2026-08-23 by Codex (planning-only; no credential values or
model prompts used).

## Current M0.1 verification — 2026-08-22

| Check | Result |
| --- | --- |
| Current local CLI baseline | PASS — Claude Code 2.1.241, Codex 0.149.0, Grok Build 1.0.5, OpenClaw 2026.7.1-2 |
| Sanitized native-auth status | PASS for Claude subscription OAuth and Codex ChatGPT login; Grok active login not tested |
| Fit-gap structural regression | PASS — 54 register IDs map one-to-one to 54 matrix rows; 11 non-empty system cells per row; priorities and cell syntax valid; 0 errors |
| Canonical architecture answer | PASS — exactly 3 copies and 0 byte-level line mismatches across `architecture-options.md`, `minimal-poc-plan.md`, and discovery `README.md` |
| Local Markdown links | PASS — 47 Markdown files scanned, 12 local `.md` links checked, 0 broken. *Correction (2026-08-23, G1 hygiene, review H9; re-counted with `git ls-tree 3407ec9`): 49 tracked Markdown files existed at `3407ec9` — the scan silently excluded `AGENTS.md` and `CLAUDE.md`.* |
| Placeholder inventory | PASS with 3 intentional matches — all mark the still-open implementation-language decision (`PROJECT.md` once; `reuse-vs-build-analysis.md` twice). *Correction (2026-08-23, G1 hygiene, review H9; re-scanned at `3407ec9`): 5 `TBD` markers, not 3 — `AGENTS.md:5` and `evidence/panel/proposal-B-independent-layer.md:42` were missed; all five concerned the then-open implementation-language decision, so the PASS reading stands with the corrected count.* |
| Secret-pattern scan | PASS — 0 candidate-route-key-shaped values and 0 private-key headers |
| Patch hygiene | PASS — `git diff --check` exits 0 |

The fit-gap regression is deliberately **structural**, not a second semantic
review of all 594 system cells. It confirms that documentation edits did not
drop, duplicate, shift, or corrupt a requirement row. The M0 matrix is trusted
except for the targeted AD-07 semantic correction documented in
`docs/discovery/evidence/m0-product-architecture-review-2026-08-22.md` F9.

No model prompt, API-test-provider request, live ClawTeam run, live OpenClaw run, or
Windows/macOS execution was performed. Hosted CI coverage is a future
milestone requirement, not evidence already obtained. No credential value or
authentication file was inspected.

Last verified: 2026-08-22 by Codex (credential-free documentation review).

## Historical M0 note

The W3 critic/fix-pass artifacts remain historical evidence. Current project
state does not rely on the former future-dated owner-read-through claim or the
former claim that no placeholder markers existed.
