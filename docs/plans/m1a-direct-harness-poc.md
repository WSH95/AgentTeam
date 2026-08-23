# AgentTeam M1a direct-harness PoC implementation plan

- Status: **proposed for review — not approved for product implementation**
- Plan revision date: 2026-08-23
- Revision baseline: `9aff78f` (`docs(plan): propose AgentTeam M1a direct harness PoC`)
- Product name: **AgentTeam**
- Planned repository: `WSH95/AgentTeam`
- CLI: `atm`

This is the implementation plan to execute only after a separate explicit
product-implementation approval. The 2026-08-23 documentation rebaseline
changed the proposed core from TypeScript/Node to Python/uv and made ClawTeam
an optional provider. It did not authorize the directory/repository rename,
source code, dependency installation, credential setup, live harness calls,
GitHub repository creation, or a push.

## 1. Outcome and milestone boundary

M1a proves that one portable Assistant definition can be resolved without
mutation, rendered into three installed coding harnesses, executed as fresh
independent review legs, and synthesized with attributable evidence. The
first-pass harnesses are Claude Code, Codex CLI, and Grok Build CLI.

The three review legs run concurrently. After all three finish successfully,
a separate fresh Claude Code invocation synthesizes their normalized reports.
There is no cross-harness fallback: a failed required leg makes the ensemble
fail. One retry is allowed only for a classified transient failure.

M1a ships the direct subprocess path. It also performs a bounded compatibility
qualification of the optional, exactly pinned ClawTeam Python seam. That check
does not expose TeamTemplate, TeamRun, dynamic-member, task, inbox, or nesting
commands to users and does not make ClawTeam a core dependency.

## 2. Product and architecture decisions

- The core is Python `>=3.11`, packaged with `pyproject.toml`, built with
  Hatchling, and developed/locked with `uv`.
- JSON Schema records, the `atm` CLI, and a later MCP server are the
  language-neutral integration boundary. Python objects never become the
  portable interchange format.
- AgentTeam includes its direct runner. Coordination substrates are optional
  providers; a normal direct installation neither installs nor imports
  ClawTeam.
- The first optional provider is ClawTeam from upstream commit
  `01198332ef9270c32c5460b8a178f964fc0df451` (package version `0.3.0`) with
  `mcp>=1,<2`. The full revision is recorded in `uv.lock`.
- ClawTeam imports are confined to one AgentTeam-owned compatibility/provider
  module. No other domain, harness, CLI, or archive module imports it.
- M1a accepts one process-scoped ClawTeam data root with opaque per-run team
  namespaces. This is recorded as `namespace` isolation, never as mechanical
  security isolation.
- ClawTeam's built-in `SubprocessBackend` is not used: it launches through
  `shell=True`, discards output, and is not the AgentTeam harness boundary.
- The final product name is AgentTeam; the future repository is
  `WSH95/AgentTeam`; the CLI is `atm`; and the eventual local directory is
  `/home/wsh/Documents/AgentTeam`.
- Canonical product documentation is English. The public license is MIT with
  `Copyright (c) 2026 ShuhanWang`. No package is published in M1a.
- Native unattended runs use the owner's subscription login in each installed
  vendor CLI. AgentTeam does not copy, read, export, broker, or upload
  credentials.
- Windows and macOS evidence comes from credential-free GitHub-hosted CI.
  Live subscription-backed acceptance remains on the owner's Ubuntu host.
- The deferred API-test provider is replaceable. Provider URL, model, and
  credential environment-variable name belong in local profile data; M1a does
  not request or use an API key.

## 3. Delivery sequence and gates

Implementation follows these gates in order. A failed gate stops the later
work named in its stop rule.

| Gate | Work | Evidence required |
| --- | --- | --- |
| G0 | Approve this plan | Owner explicitly approves the final reviewed plan and that approval is committed before product source work |
| G1 | Rename and re-baseline | Clean worktree; target absent; directory becomes `/home/wsh/Documents/AgentTeam`; historical evidence remains attributable; guarded instructions updated as approved |
| G2 | Python foundation | Frozen `uv.lock`; Python package builds; checked-in schemas reproduce; `atm --help` and `atm --version` pass |
| G3 | Direct harness core | Claude, Codex, and Grok adapters pass argv/env/parser tests against deterministic fake executables; no model call |
| G4 | Deterministic PoC | Complete fan-out/synthesis state machine passes locally; optional ClawTeam seam passes its local compatibility suite |
| G5 | Native-auth preflight | Owner completes one interactive login per dedicated vendor config home; `atm profile doctor` reports sanitized status only |
| G6 | Ubuntu live PoC | Three subscription-backed legs plus fresh Claude synthesis meet section 14 without exceeding the call/time bounds |
| G7 | Public CI | After separate repository/push approval, core jobs pass on Ubuntu/Windows/macOS with Python 3.11 and 3.13; optional ClawTeam jobs pass on all three OSes with Python 3.11 |
| G8 | M1a close | Verification and sanitized summary are current; no secret/raw evidence is tracked; M1b remains separately planned |

An optional ClawTeam failure does not alter or contaminate direct execution.
It blocks describing that provider as qualified and blocks M1b until the
failure is fixed, explicitly platform-scoped, or the provider decision is
reviewed. M1a must not silently fork ClawTeam to make a job green.

## 4. Rename and repository re-baseline

G1 is one controlled semantic change from a clean committed tree:

1. Recheck that `/home/wsh/Documents/AgentTeam` is absent and no `atm`
   executable collision exists.
2. Move the existing repository; do not copy it or initialize another Git
   repository. Verify the same HEAD, branch, and clean status afterward.
3. Update current identity in Project Steward state, the discovery landing
   page, and new product docs. Preserve panel, critic, evidence, decision, and
   progress text as dated records; use amendment notes instead of global
   `ats`/`ATM` replacement.
4. Add a root `README.md`, `LICENSE`, and implementation `.gitignore`.
5. Keep `CLAUDE.md` as the thin `@AGENTS.md` adapter.

Once the Python scaffold exists, update the managed command table to:

| Task | Command |
| --- | --- |
| Build | `uv build` |
| Test | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Typecheck | `uv run mypy src tests` |
| Live PoC | `uv run atm run examples/run-requests/live-review.yaml` |

## 5. Runtime and dependency baseline

M1a is one Python distribution at the repository root:

- distribution/import package: `agentteam`;
- version: `0.1.0a0`;
- `requires-python = ">=3.11"`;
- build backend: Hatchling;
- environment and lock manager: `uv` with committed `uv.lock`;
- console script: `atm = "agentteam.cli:main"`;
- source layout: `src/agentteam/`;
- no wheel, sdist, or PyPI publication during M1a.

Runtime dependencies are limited to Typer for the CLI, Pydantic v2 for closed
models and JSON Schema generation, and PyYAML for human-authored YAML inputs.

The optional `clawteam` extra contains the exact Git revision above and the
`mcp>=1,<2` compatibility bound. Development dependencies include pytest,
pytest-asyncio, jsonschema, Ruff, mypy, and required type stubs. All resolved
versions are locked; adding a dependency requires a documented reason.

## 6. Planned repository layout

```text
src/agentteam/
  cli.py
  commands/
  domain/
  resolution/
  harness/
  run/
  schema/
  compat/clawteam.py
schemas/
  assistant-definition-v1.schema.json
  overlay-v1.schema.json
  harness-profile-set-v1.schema.json
  run-request-v1.schema.json
  harness-invocation-v1.schema.json
  ensemble-record-v1.schema.json
examples/
  assistants/code-reviewer/
  run-requests/direct-review.yaml
fixtures/
  review-target/
  fake-harness/
tests/
  unit/
  integration/
  acceptance/
  compatibility/
docs/
  plans/
  provenance.md
.github/workflows/ci.yml
```

Generated JSON Schemas are checked in and reproduced deterministically from
Pydantic models. External consumers need neither Python nor AgentTeam to read
or validate them.

## 7. Data contracts

Every persistent record is closed (`additionalProperties: false`), carries
`schema_version: 1` and a fixed `kind`, and serializes to canonical snake_case
JSON. Human-authored inputs accept YAML or JSON; runtime records are JSON.
Unknown fields fail validation.

`AssistantDefinitionV1` contains stable metadata, separate persona/principle/
method instruction files, semantic capability requirements, explicit artifact
references, portable permission intent, abstract harness hints, optional
substrate-neutral collaboration guidance, and prohibited-content checks. It
never contains a concrete project, session, credential, provider endpoint, or
permanent harness binding.

`OverlayV1` supports Base plus User Overlay with target/version constraints,
an allowed patch surface, provenance, deterministic precedence, and a
resolution report. Reviewed Evolution proposals remain a committed later
milestone; M1a never silently persists run output into a definition.

`HarnessProfileSetV1` is local and gitignored. Each Claude, Codex, and Grok
entry records the executable, expected version/capabilities, dedicated vendor
config home, native-subscription auth mode, optional local model/effort
defaults and mappings, timeouts, proxy policy, and environment-variable names
only. A later `api_test` profile kind remains structurally possible but is
rejected by the M1a runner.

`RunRequestV1` contains the Assistant/Overlay paths, workspace/task paths,
`mode: direct`, unique harnesses, optional synthesis, local model/effort
overrides, output path, timeout, evidence, and bounded retry settings. Runtime
IDs, timestamps, results, and subprocess state belong only in the archive.

`HarnessInvocationV1` records run/ensemble/attempt IDs; requested and observed
harness/model/effort; bundle hash; redacted argv; environment names and policy
decisions; path placeholders; timing; artifact references and hashes; reported
usage; retry classification; exit/signal; schema outcome; and terminal status.
Cost is never fabricated. Codex remains `cost_source: unavailable`.

`EnsembleRecordV1` names every leg and synthesis invocation, synthesis input
IDs, attribution links, aggregate status, and separate mechanical and semantic
acceptance results.

Before and after a run, AgentTeam hashes all resolved definition files and
fails if any changed.

## 8. Public CLI contract

```text
atm assistant validate <package> [--strict-content] [--json]
atm profile init [--config <path>] [--json]
atm profile validate [--config <path>] [--json]
atm profile doctor [--config <path>] [--json]
atm run <request.yaml|request.json>
  [--assistant <package>]
  [--workspace <path>]
  [--task-file <path>]
  [--harness <claude|codex|grok>]...
  [--model <harness>=<model>]...
  [--effort <harness>=<effort>]...
  [--output-dir <path>]
  [--config <path>]
  [--json]
atm --help
atm --version
```

Multiline/user-controlled content travels by file or stdin, never a shell
command string. Stable exit codes are `0` success, `1` runtime/harness failure,
`2` invalid/unsafe input, `3` semantic acceptance failure, and `130` owner
cancellation.

No team or ClawTeam command is public in M1a. If the optional extra is absent,
direct commands behave identically and never attempt a fallback installation.

## 9. Python interfaces and process contract

The internal harness seam is an async typed `Protocol`:

```python
class HarnessAdapter(Protocol):
    async def probe(self, context: ProbeContext) -> HarnessCapabilityReportV1: ...
    def render(self, context: RenderContext) -> RenderedInvocationV1: ...
    async def invoke(
        self, rendered: RenderedInvocationV1, cancellation: CancellationToken
    ) -> RawInvocationV1: ...
    def parse(self, raw: RawInvocationV1) -> NormalizedReviewV1: ...
```

`render` is pure with respect to portable definitions and writes only
run-scoped files. `invoke` delegates to one shared process runner. `parse`
validates vendor output into the same normalized review model.

The process runner uses `asyncio.create_subprocess_exec`, never
`create_subprocess_shell`; concurrently drains stdout/stderr; preserves raw
bytes in access-restricted local evidence; creates a pending record before
spawn; atomically finalizes it; enforces a 15-minute attempt limit; terminates
the process tree on cancellation/timeout; and finalizes every started attempt.
POSIX uses a new process session/group; Windows uses a new process group and
`taskkill.exe` as an argv array when tree termination is needed.

The later `CoordinationSubstrate` protocol retains create-space, member, task,
wait, message, snapshot, stop, and cleanup operations. It is documented but
not exposed or completed in M1a.

## 10. Optional ClawTeam compatibility qualification

The compatibility module is an anti-corruption boundary, not a second public
runtime:

1. It is importable only when `agentteam[clawteam]` is installed.
2. It fixes one data root before the first coordination operation and rejects
   attempts to switch roots in the same process.
3. It uses opaque AgentTeam-generated team names and explicit file task store
   and file transport primitives.
4. It initializes and clears ClawTeam's global event bus before any operation,
   so user-configured ClawTeam shell/Python hooks cannot execute through the
   compatibility check.
5. It never calls ClawTeam's built-in subprocess/tmux/wsh backends, template
   launcher, keepalive wrapper, or CLI adapter chain.
6. It records the exact package version/revision and achieved isolation level
   (`namespace`).

Qualification exercises team/member lifecycle, task dependency auto-unblock,
mailbox send/receive, snapshot create/read/restore, cleanup, and two namespaces
with no API-level task/message crossover. A hostile hook fixture proves no
hook callback executes. Tests must not read or mutate the owner's actual
`~/.clawteam` state.

## 11. Model, authentication, and environment policy

Concrete model/effort precedence is CLI override, RunRequest override, local
HarnessProfile mapping from a portable hint, local profile default, then vendor
default. An unspecified value stays unspecified unless local profile data
supplies it. Unsupported values fail before a model call when possible;
otherwise the vendor error is recorded with no harness fallback.

The owner performs interactive login in dedicated AgentTeam config homes.
`atm profile init` creates non-secret directories/config and prints login
instructions; it never automates a browser or copies a credential store.
`profile doctor` exposes only allowlisted status fields.

Each native run starts from a minimal cross-platform environment allowlist,
sets the selected config-home variable, records names only, and fails closed
when API-key/base-URL/alternate-provider or unapproved proxy variables could
redirect subscription authentication. API mode is never an auth fallback.

Harness isolation remains:

- Claude Code: `-p`, `--safe-mode`, `--no-session-persistence`, isolated
  `CLAUDE_CONFIG_DIR`, file/stdin instructions, structured output, read-only
  review tools; never `--bare`.
- Codex: `codex exec`, `--ephemeral`, `--ignore-user-config`, `--ignore-rules`,
  isolated `CODEX_HOME`, `model_instructions_file`, read-only sandbox,
  approval `never`, JSONL plus output schema.
- Grok Build: isolated `GROK_HOME`, memory/subagents disabled, leader mode and
  web search disabled, read-only sandbox, file-delivered definition, and
  structured output.

## 12. Direct ensemble state machine

1. Validate profile, Assistant, Overlay, and RunRequest.
2. Resolve paths, overlays, portable hints, and local overrides.
3. Build one immutable definition bundle and canonical SHA-256 hash.
4. Create a pending run archive before any harness side effect.
5. Copy the fixture into three isolated leg workspaces; no leg receives another
   leg's outputs; target hashes detect mutation.
6. Render all three invocations from the same bundle.
7. Start Claude, Codex, and Grok concurrently in fresh-session mode.
8. Retry the same harness once only for network interruption, rate limit,
   service unavailability, or timeout.
9. Never retry auth, permission, invalid input, schema, semantic, or unknown
   failures; never substitute another harness.
10. Require all three normalized reports before synthesis.
11. Give a fresh Claude invocation only the three labelled reports, not the
    target or hidden oracle.
12. Validate synthesis schema/attribution, evaluate semantic predicates,
    re-hash definitions, finalize the archive, and return the stable exit code.

One acceptance cycle uses at most eight model calls: three legs, up to three
one-time leg retries, synthesis, and at most one transient synthesis retry.
AgentTeam never starts another cycle automatically.

## 13. Evidence and privacy

Gitignored local run state contains `run.json`, resolved request and bundle
manifest, per-invocation records/raw streams/normalized result, ensemble
record, event log, and SHA-256 manifest. Raw output remains local for parser
and attribution diagnosis.

POSIX evidence uses owner-only permissions. Windows relies on the user's
profile ACL and warns for paths outside it. Recorded argv uses typed
placeholders; environment records contain names and policy outcomes only.
Credential files and values are never read as evidence.

M1a performs no automatic `git add`, publication, upload, or raw-evidence
export. Only a separately reviewed sanitized summary may be committed.

## 14. PoC fixture and live semantic acceptance

The committed review target is a small TypeScript module with three labelled,
non-production defects: shell command injection, an off-by-one boundary error,
and caller-input mutation. Using a TypeScript review target does not couple the
Python runner to Node; it deliberately tests language-independent review.

All conditions must pass in one live cycle:

1. Claude, Codex, and Grok finish independent fresh legs with the same bundle
   and target hashes.
2. Each identifies command injection and at least one other seeded defect with
   an actionable explanation.
3. Their union identifies all three defects.
4. No leg invents a critical finding outside the oracle.
5. Synthesis lists all defects, attributes each to real invocation IDs, and
   distinguishes agreement from disagreement.
6. The Assistant package remains byte-identical.
7. Every attempt reaches a terminal record and archive hashes reconstruct.
8. No credential value or raw evidence is tracked.
9. Mechanical and semantic outcomes remain separate; semantically inadequate
   valid output exits `3`.

## 15. Deterministic test plan

Normal tests never invoke a vendor model. Cross-platform fake harnesses are
Python modules launched through the same process runner and record argv,
stdin, cwd, and environment names.

Coverage includes schema parity; exclusion/path traversal; bundle immutability;
overlay/model precedence; exact vendor rendering; spaces/Unicode/backslashes/
long paths/CRLF; concurrent and malformed streams; schema/vendor failures;
retry classification; timeout/cancellation/process-tree cleanup; atomic
archive recovery; redaction; solo mode; parallel fan-out then synthesis;
required-leg failure; attribution; semantic predicates; CLI JSON/help/version;
and the optional ClawTeam scenarios in section 10.

Local deterministic verification is:

```text
uv sync --frozen --all-groups --extra clawteam
uv run ruff check .
uv run mypy src tests
uv run pytest
uv build
```

Live execution is never part of pytest, the default verification command, or
hosted CI.

## 16. GitHub CI and publication

Core matrix:

- OS: `ubuntu-latest`, `windows-latest`, `macos-latest`;
- Python: 3.11 and 3.13;
- install: official `uv` action followed by `uv sync --frozen --all-groups`;
- checks: lock consistency, Ruff, mypy, pytest, build, schema reproduction, and
  deterministic acceptance.

Optional provider matrix:

- the same three OSes on Python 3.11;
- `uv sync --frozen --all-groups --extra clawteam`;
- ClawTeam compatibility tests only, with temporary data/config fixtures.

CI has no vendor login, model call, API key, API-test route, or secret
permission. Passing proves deterministic Python/path/process/archive/schema
and optional-provider plumbing only.

Before G7, run local deterministic and Ubuntu live gates, inspect history for
secrets/raw evidence, verify MIT and third-party notices, recheck the remote
name, ask for explicit repository/push approval, and have the owner repair
`gh` authentication without sharing a token. No release, tag, package
registry, installer, or signed artifact is in M1a.

## 17. Commit boundaries during product implementation

1. `chore(project): rename project to AgentTeam`
2. `chore(core): scaffold Python CLI package with uv`
3. `feat(domain): add portable definition and run schemas`
4. `test(substrate): qualify optional ClawTeam seam`
5. `feat(harness): add isolated direct CLI adapters`
6. `feat(run): add invocation ledger and parallel ensemble runner`
7. `test(poc): add deterministic direct-harness acceptance`
8. `docs(poc): record subscription-backed Ubuntu acceptance`
9. `ci: verify direct and optional-provider plumbing`

Include Project Steward state with its semantic change. Never push without the
separate approval.

## 18. Stop rules

- Stop on any mutation of a portable Assistant package.
- Stop rather than insert API mode if native subscription execution fails.
- Stop if an adapter needs credential-file parsing or copying.
- Fix deterministic Windows/macOS direct plumbing before live/product claims.
- A ClawTeam compatibility failure blocks provider qualification and M1b; do
  not silently fork, vendor, or make it mandatory.
- Record vendor flag drift in dated profile data/tests rather than hidden
  branching.
- Stop at the eight-call or 15-minute attempt bound.
- If output exposes a secret, keep it local, rotate outside AgentTeam, and do
  not commit/upload it.
- After two failures for the same live semantic reason, return to review rather
  than tune prompts indefinitely.
- G8 ends M1a. Do not begin M1b in the same approval scope.

## 19. Committed later milestones

These are product obligations from the original brief, not optional ideas.
Each receives a separate detailed plan and approval:

1. **M1b — Team foundation:** substrate-neutral TeamTemplate, TeamRun, Member,
   and CoordinationSubstrate contracts; optional ClawTeam provider.
2. **M1c — dynamic-member PoC B:** reusable Lead/Implementer/Reviewer team,
   mixed harnesses, one hidden auditable temporary specialist, enforced policy
   decision, and complete archive.
3. **M2 — nested-team PoC C:** temporary inner TeamRun, isolated namespace,
   result return, archive, outer continuation, explicit achieved isolation,
   recovery, and the `atm` MCP server.
4. **M3 — evolution and artifacts:** Reviewed Evolution proposals/review,
   artifact manifest/lock, per-host resolution, credential-free export/import,
   and modification detection.
5. **M4 — operations:** deterministic process/metric/checkpoint/log monitors,
   schedulers, triggers, health/restart policy, and fresh Assistant invocation
   for interpretation/decisions/escalation.
6. **Optional adapters/surfaces:** native DSH package, OpenClaw, Hermes,
   Telegram/Discord, and replaceable API-test profiles enter only through the
   stable schema/CLI/MCP boundaries.

## 20. Explicitly outside M1a

- Public TeamTemplate/TeamRun/dynamic/nested team behavior;
- a production CoordinationSubstrate or mechanical isolation claim;
- ClawTeam process spawning, keepalive, tmux, worktrees, or upstream/fork work;
- ACP, WebSocket, daemon, persistent leader transport, or surfaces;
- reviewed evolution generation, artifact installation, or auto-updates;
- Hermes/OpenClaw/Telegram/DSH native integration, scheduling, or UI;
- API-test execution/key handling/base-URL canary;
- releases, installers, hosted credential services, or package publication.

## 21. Approval checklist and traceability

Review must confirm direct-first scope, Python/uv packaging, versioned schemas,
optional-not-mandatory ClawTeam, namespace-only isolation claim, three-harness
auth/evidence rules, semantic thresholds, retry/time/call limits, hosted-CI
boundary, later milestone obligations, AgentTeam/`atm` identity, English docs,
and MIT holder line.

Implementation begins only after review comments are resolved and the owner
explicitly marks this plan approved.

Project-local sources remain the M0.1 review, harness capability evidence,
architecture synthesis, historical PoC proposal, and product requirements.
Volatile vendor CLI/auth facts must be rechecked at their execution gate.
ClawTeam compatibility is anchored to the full Git revision above; uv behavior
is anchored to the installed `uv 0.11.26` help captured during planning.
