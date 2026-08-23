# AgentTeam M1a direct-harness PoC implementation plan

- Status: **proposed for review — not approved for product implementation**
- Plan revision: **r3**, 2026-08-23 (r2 review findings resolved; r2 merged the
  independent proposal; see section 22)
- Revision baseline: `7ea1c0e` (r2 was `972aa95`; r1 was `9aff78f`,
  `docs(plan): propose AgentTeam M1a direct harness PoC`)
- Supersedes: `docs/plans/m1-agentteam-direct-slice.md` (independent proposal,
  merged here; kept as a dated record)
- Product name: **AgentTeam**
- Planned repository: `WSH95/AgentTeam` (public, MIT; created at G2 after the
  G1 rename)
- CLI: `atm`

This is the implementation plan to execute only after a separate explicit
product-implementation approval. The 2026-08-23 documentation rebaseline
changed the proposed core from TypeScript/Node to Python/uv and made ClawTeam
an optional provider; revision r2 merged the independent review
(`docs/reviews/2026-08-23-m0-review-at-3407ec9.md`), the independent proposal,
and the cross-check findings listed in section 22; revision r3 resolves the
multi-agent review findings on r2 (section 22). It did not authorize the
directory/repository rename, source code, dependency installation, credential
setup, live harness calls, GitHub repository creation, or a push.

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

M1a also establishes harness-selection precedence (user > Assistant > profile
default) with the deciding layer recorded on every invocation, renders the
example Assistant's three Skills into every harness, and proves that the
portable package hashes identically on the three CI operating systems. M1a
live runs are owner-attended as a milestone boundary; unattended native runs
belong to M4 and use subscription OAuth on the owner-operated persistent host
(Q5).

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
  `/home/wsh/Documents/AgentTeam`. The repository is created public with the
  MIT licence at G2, after the G1 directory rename and after the pre-first-push
  checklist of section 16; the first push is an explicit approval moment
  inside G2.
- Approval of this plan is recorded as a DECISIONS entry that names this file
  and the commit SHA holding the approved text; the status line flips to
  `approved` in the following commit because a commit cannot name its own SHA
  (ADR 0018).
- Harness identifiers in records and profiles are `claude-code`, `codex`, and
  `grok`; the CLI accepts `claude` as an alias.
- `run.json` is a `RunRecordV1`: a direct run is the one-Member case of the
  later TeamRun record, so M1b extends it instead of adding a second record
  kind. M1a implements no TeamTemplate or coordination behaviour.
- Overlays are deferred to M3. M1a reserves `overlay_refs: []` in the
  RunRequest and bundle manifest; the computed `effective_definition_hash`
  (equal to the Base hash in M1a) lives only in the bundle manifest, the run
  record, and the invocation records — never as client-supplied input.
  User-level choices travel through the CLI, the RunRequest, and the local
  HarnessProfile.
- Canonical product documentation is English. The public license is MIT with
  `Copyright (c) 2026 ShuhanWang`. No package is published in M1a.
- Native runs use the owner's subscription login in each installed vendor
  CLI; M1a runs are owner-attended and record `attendance` and `auth_mode` on
  every invocation. AgentTeam does not copy, read, export, broker, or upload
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
| G0 | Approve this plan | Owner explicitly approves the final reviewed plan; the approval is a DECISIONS entry naming this file and the commit SHA of the approved text, committed before product source work |
| G1 | Rename, re-baseline, documentation hygiene | Clean worktree; target absent; directory becomes `/home/wsh/Documents/AgentTeam`; historical evidence remains attributable; guarded instructions updated as approved; the documentation-hygiene list of section 4 item 6 lands as one docs-only commit |
| G2 | Python foundation and public repository | Frozen `uv.lock`; Python package builds; checked-in schemas reproduce; `atm --help` and `atm --version` pass; pre-first-push checklist passed (history secret scan, LICENSE and third-party notices, `docs/provenance.md`, repository/distribution-name checks); public `WSH95/AgentTeam` created with the MIT licence and the scaffold pushed after explicit approval; the **scaffold smoke matrix** (lock, Ruff, mypy, scaffold tests, build, schema reproduction, `--help`/`--version`) green on Ubuntu/Windows/macOS |
| G3 | Direct harness core | Claude, Codex, and Grok adapters pass argv/env/parser tests against deterministic fake executables, including Skill-channel rendering, harness-selection resolution with `decided_by`, and the Windows-only `.cmd` shim fake; these tests are added to CI; no model call |
| G4 | Deterministic PoC | Complete fan-out/synthesis state machine passes locally, including solo mode, selection/exclusion precedence, three Skills rendered per harness, and example-package hash identity; optional ClawTeam seam passes its local compatibility suite and writes its qualification report; the deterministic-acceptance, hash-identity, and optional ClawTeam jobs are added to CI |
| G5 | Native-auth preflight and probes | Owner completes one interactive login per dedicated vendor config home; `atm profile doctor` reports sanitized status only; bounded day-one probes (at most two calls per harness, outside the acceptance cycle) write capability verification levels into the profile; Grok authentication stays `unverified` until its first live leg if no status command exists |
| G6 | Ubuntu live PoC | Three subscription-backed legs plus fresh Claude synthesis meet section 14 — mechanical conditions (architecture gate) and semantic conditions (product-useful gate) recorded separately — within the call/time bounds |
| G7 | Final CI matrices | Core jobs pass on Ubuntu/Windows/macOS with Python 3.11 and 3.13; optional ClawTeam jobs pass on all three OSes with Python 3.11; the vendor-smoke job (npm-installed Claude Code and Codex `--version`/`--help` through the real launchers, no credentials) passes; the history secret scan is repeated |
| G8 | M1a close | Verification and the reviewed sanitized evidence bundle are current; no secret/raw evidence is tracked; semantic PASS recorded — or an owner-recorded waiver that closes M1a as failed/abandoned, never as PASS; the M1b draft names the local deterministic provider first and the ClawTeam exit criterion; M1b remains separately planned |

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
4. Add a root `README.md` (stating alpha status), `LICENSE` (MIT,
   `Copyright (c) 2026 ShuhanWang`), `.gitattributes` (`* text=auto eol=lf`,
   so hashes and schema reproduction agree on Windows checkouts), and an
   implementation `.gitignore`.
5. Keep `CLAUDE.md` as the thin `@AGENTS.md` adapter.
6. Documentation hygiene, as one docs-only commit in this gate (review H3, H6,
   H8–H12, R7, R19): PROJECT.md gains success criteria and loses volatile
   version pins and scope decisions (moved to PLAN/VERIFY); the glossary
   defines HarnessAdapter, CoordinationSubstrate, `atm`, "legacy ATM",
   `independence {declared, achieved}`, and the run-vs-TeamRun wording; an
   append-only DECISIONS entry adds amendment markers for 0007/0009/0012;
   VERIFY counts are corrected; RISKS gains ID/owner/status columns; each
   critic file gets a closure note; `minimal-poc-plan.md` carries a historical
   banner; README links QUESTIONS; `config.toml` loses its dangling pointer;
   the HB-03 register amendment is applied only after the owner answers the
   QUESTIONS item.

Once the Python scaffold exists, update the managed command table to (that
managed-block edit requires its own shown `AGENTS.md` diff and explicit
approval, ADR 0008/0014):

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
  synthesis/instructions.md
  compat/clawteam.py
schemas/
  assistant-definition-v1.schema.json
  harness-profile-set-v1.schema.json
  run-request-v1.schema.json
  run-record-v1.schema.json
  bundle-manifest-v1.schema.json
  harness-invocation-v1.schema.json
  ensemble-record-v1.schema.json
  normalized-review-v1.schema.json
  synthesis-report-v1.schema.json
examples/
  assistants/code-reviewer/
    skills/code-review/SKILL.md
    skills/security-review/SKILL.md
    skills/test-analysis/SKILL.md
  profiles/ci-fake.yaml
  run-requests/direct-review.yaml
  run-requests/live-review.yaml
fixtures/
  review-target/
  review-target.oracle.json
  vendor-output/
  fake-harness/
tests/
  unit/
  integration/
  acceptance/
  compatibility/
docs/
  plans/
  evidence/
  provenance.md
.gitattributes
.github/workflows/ci.yml
```

Generated JSON Schemas are checked in and reproduced deterministically from
Pydantic models (written with `\n` newlines and compared after LF
normalisation). External consumers need neither Python nor AgentTeam to read
or validate them. `examples/profiles/ci-fake.yaml` points every adapter at the
deterministic fakes so CI and local deterministic runs share one profile shape;
`fixtures/review-target.oracle.json` lives outside the copied workspace;
`fixtures/vendor-output/` holds sanitized vendor output samples for parser
tests; `src/agentteam/synthesis/instructions.md` is the committed synthesis
instruction whose hash the ensemble record carries.

### 6.1 Local state layout

The default state directory is `~/.agentteam/` (override with `AGENTTEAM_HOME`).
It holds `profiles.yaml` (the local, gitignored `HarnessProfileSetV1`, the
default target of `atm profile init`), one dedicated vendor config home per
harness under `vendors/<harness>/` (the `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, and
`GROK_HOME` the runs use), the archive root `runs/<run-id>/` unless a
RunRequest names an output path, and `probes/<date>/` for raw G5 probe
captures. Nothing under it is ever committed.

## 7. Data contracts

Every persistent record is closed (`additionalProperties: false`), carries
`schema_version: 1` and a fixed `kind`, and serializes to canonical snake_case
JSON. Human-authored inputs accept YAML or JSON; runtime records are JSON.
Unknown fields fail validation.

`AssistantDefinitionV1` contains stable metadata, separate persona/principle/
method instruction files, semantic capability requirements, explicit artifact
references (Skills are `agent-skill` artifacts with vendored sources; the
example `code-reviewer` carries three — `code-review`, `security-review`,
`test-analysis` — so Assistant ≠ Skill is visible in the definition itself),
portable permission intent, a portable `harness_policy` (preferred, allowed,
and forbidden harness identifiers, required capabilities, and abstract model
hints — never a concrete model or provider), optional substrate-neutral
collaboration guidance, and prohibited-content checks. It never contains a
concrete project, session, credential, provider endpoint, or permanent
harness binding.

Overlays (Base plus User Overlay, later Reviewed Evolution) are deferred to M3
(ADR 0016; recorded in DECISIONS 0019 after review item R15). M1a reserves
`overlay_refs: []` in the RunRequest and bundle manifest so the shape does not
change later; `effective_definition_hash` is computed state (equal to the Base
hash in M1a) recorded in the bundle manifest, `RunRecordV1`, and every
`HarnessInvocationV1`, never accepted from a request. M1a never silently
persists run output into a definition.

`HarnessProfileSetV1` is local and gitignored. Each Claude, Codex, and Grok
entry records the executable, expected version/capabilities, dedicated vendor
config home, native-subscription auth mode, optional local model/effort
defaults and mappings, timeouts, proxy policy, and environment-variable names
only. Each capability row carries `verification: verified|observed|unverified`
(verified = behaviour observed under the AgentTeam runner; observed = flag
present in `--help` or documentation only) plus `cli_version` and
`verified_at`; `atm profile doctor --probe` updates them. A later `api_test`
profile kind remains structurally possible but is rejected by the M1a runner.

`RunRequestV1` contains the Assistant path, the reserved `overlay_refs`,
workspace/task paths, `mode: direct`, the requested harnesses (unique; when
empty the Assistant's `harness_policy` decides and the run is solo), optional
synthesis, local model/effort overrides, output path, evidence settings, and
timeout/retry settings that may lower but never raise the section 9 caps.
Runtime IDs, timestamps, results, and subprocess state belong only in the
archive.

`RunRecordV1` (`run.json`) is the archive manifest: run id, `mode: direct`, the
single Member (Assistant reference, bundle hash, and one `execution` binding
`{kind: invocation | ensemble, ref}`), timing, and terminal status. In the
acceptance cycle the Member is bound to one `EnsembleRecordV1` that holds its
leg invocations and the synthesis invocation; in solo mode it is bound to one
`HarnessInvocationV1`. A Member is therefore bound to one *execution* at a time
(`team-execution-model.md` §4, amended for r3). `RunRecordV1` is the one-Member
subset of the later TeamRun record; M1b extends it with coordination fields
instead of introducing a second record kind.

`HarnessInvocationV1` records run/ensemble/attempt IDs; requested and observed
harness/version/model/effort; `selection {decided_by: user|assistant|default,
candidates}` (`team` and forced variants are reserved for M1b); bundle hash;
`injection.render` mapping each definition part to the channel used, plus
`degraded[]`; redacted argv; environment names and policy decisions; path
placeholders; `attendance` and `auth_mode` (`native-subscription` in M1a);
timing; artifact references and hashes; reported usage; retry classification;
exit code and nullable signal; schema outcome; and terminal status. Cost is
never fabricated. Codex remains `cost_source: unavailable`.

`EnsembleRecordV1` names every leg and synthesis invocation, synthesis input
IDs, the synthesis instruction hash, attribution links, aggregate status, and
separate mechanical and semantic acceptance results.

`NormalizedReviewV1` (per leg: `target_sha256`, `findings[]` with `id`,
`severity`, `file`, `line`, `title`, `rationale`; `summary`; `verdict`) and
`SynthesisReportV1` (`inputs[]`, `agreements[]` with `title` and `sources[]`,
`disagreements[]` with `title`, `asserted_by[]`, `not_asserted_by[]`,
`merged_findings[]`) are checked-in JSON Schemas consumed directly by Claude
`--json-schema`, Codex `--output-schema`, and Grok `--json-schema`. They are
authored in the intersection of the vendors' structured-output dialects (every
property required, `additionalProperties: false`, nullable-required
optionals), and the G5 probes confirm each vendor accepts them before any
acceptance cycle.

The V1 portable-archive contract that every canonical hash is computed over: a
package is a tree of regular files only (symlinks, devices, and empty
directories are rejected); every file must be valid UTF-8 text (binary
artifacts are outside V1); paths are relative, `/`-separated, UTF-8,
NFC-normalised, and sorted by code point; two paths that differ only by case
are rejected; file modes are excluded; CRLF and lone CR are normalised to LF;
the hash is SHA-256 over the ordered sequence of `(path, NUL, size, NUL,
bytes)` records. The same package therefore hashes identically on every
operating system, and every rejection names the offending path. Throughout
this plan a "call" is one CLI invocation of a vendor harness.

Before and after a run, AgentTeam hashes all resolved definition files and
fails if any changed.

## 8. Public CLI contract

```text
atm assistant validate <package> [--strict-content] [--json]
atm profile init [--config <path>] [--json]
atm profile validate [--config <path>] [--json]
atm profile doctor [--config <path>] [--probe] [--json]
atm run [<request.yaml|request.json>]
  [--assistant <package>]
  [--workspace <path>]
  [--task-file <path>]
  [--harness <claude-code|codex|grok>]...
  [--model <harness>=<model>]...
  [--effort <harness>=<effort>]...
  [--no-synthesis]
  [--render-only]
  [--output-dir <path>]
  [--config <path>]
  [--json]
atm --help
atm --version
```

The request file is optional when `--assistant`, `--workspace`, and
`--task-file` are given; flags override request fields. When neither the flags
nor the request name a harness, the Assistant's `harness_policy` decides and
the run is solo (`decided_by: assistant`); otherwise the user's choice wins
(`decided_by: user`). `claude` is accepted as an alias of `claude-code`.
`assistant validate --json` includes the package hash. `profile doctor --probe`
runs the bounded probes of section 11 and records verification levels; without
it, doctor reports sanitized status and flag presence only. `--render-only`
writes the rendered invocations for inspection without launching anything.

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
validates vendor output into the same normalized review model. `probe` returns
a `HarnessCapabilityReportV1` whose rows carry the verification level that is
written into the local profile.

The process runner uses `asyncio.create_subprocess_exec`, never
`create_subprocess_shell`; concurrently drains stdout/stderr; preserves raw
bytes in access-restricted local evidence; creates a pending record before
spawn; atomically finalizes it; enforces a 15-minute attempt limit; terminates
the process tree on cancellation/timeout; and finalizes every started attempt.
POSIX uses a new process session/group; Windows uses a new process group
(`CREATE_NEW_PROCESS_GROUP`) and `taskkill.exe /T /F /PID <pid>` as an argv
array when tree termination is needed. `signal` is nullable in records and exit
130 is mapped explicitly. A RunRequest may lower but never raise the 15-minute
attempt limit or the single transient retry.

Launcher policy. Python's `subprocess` documents that Windows batch files
(`.bat`/`.cmd`) may be launched through the system shell regardless of
`shell=False`, with no escaping added by Python. AgentTeam therefore never
hands user-controlled content to a batch file and applies one explicit policy:
a native `.exe` is launched directly; an npm `.cmd` shim (Claude Code, Codex)
is **resolved to its target** — the `node` entry script the shim wraps — and
`node.exe` is launched with that script as argv, so `cmd.exe` never parses
anything; if resolution fails, the `.cmd` is launched only when every argv
element matches a strict safe-character allowlist (no `&`, `|`, `<`, `>`, `^`,
`%`, `!`, `(`, `)`, or `"`; spaces are allowed and quoted), otherwise the
invocation exits `2` with the reason. All multi-line and user-controlled
content still travels by file or stdin. The resolved launcher and the policy
branch taken are recorded on the invocation.

Tests cover both branches with a Windows-only `.cmd` fake shim that receives
arguments containing spaces and metacharacters; CI fakes launched as
`python -m …` cover the rest. The minimal environment baseline is `PATH`,
`SystemRoot`, `SystemDrive`, `COMSPEC`, `PATHEXT`, `USERPROFILE`, `APPDATA`,
`LOCALAPPDATA`, and `TEMP`/`TMP` on Windows and `HOME`, `PATH`, `TMPDIR`, and
`LANG` on POSIX, plus the selected vendor config-home variable.

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
`~/.clawteam` state. Compatibility tests skip cleanly when the extra is absent,
and mypy ignores the untyped alpha package.

The qualification report records the compatibility module's LOC and test LOC,
the containments applied, global-state hazards found, the hook-containment
result, the two-namespace crossover result, and the per-OS outcome. These are
the inputs to the written ClawTeam exit criterion that M1b drafts before PoC B
(ADR 0018).

## 11. Model, authentication, and environment policy

Harness selection precedence is CLI `--harness` / RunRequest harnesses (user)
> Assistant `harness_policy` (assistant) > local HarnessProfile default
(default). The complete algorithm: (1) candidates are the harnesses with a
local profile and an installed executable; (2) harnesses forbidden by the user
request or by the Assistant's `forbidden` list are removed; (3) if the user
requested harnesses, every requested harness must be a candidate, allowed by
the Assistant, and eligible for the required capabilities — otherwise the run
fails before any launch (exit `2`); there is no implicit force mode in M1a;
`decided_by: user`; (4) otherwise the first entry of the Assistant's
`preferred` list that is a candidate and eligible is chosen, `decided_by:
assistant`; (5) if the Assistant expresses no preference, the profile default
is chosen, `decided_by: default`; (6) if nothing is eligible the run fails
with the reason recorded. A `team` layer is reserved for M1b.

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

Skills are rendered from the bundle into each harness's discovery channel.
Claude Code: `$CLAUDE_CONFIG_DIR/skills/<name>/SKILL.md` inside the isolated
config home (keeps the workspace clean), then `--plugin-dir <bundle-plugin>`
(verified in `--help`), then workspace `.claude/skills/` — the G5 probe picks
the first channel that demonstrably loads. Codex: workspace `.agents/skills/`.
Grok Build: workspace `.grok/skills/` (the documented project path) with
`.agents/skills/` as a fallback that `grok inspect` on 1.0.5 also lists as a
project root (verified locally 2026-08-23). Skills are **required** parts: if
a harness channel cannot deliver a required Skill, `render` fails before any
launch (exit `2`, `undeliverable_required_parts[]` recorded); `degraded[]`
covers optional parts only. The channel used is recorded per definition part.
Adapter-written injection directories are excluded from the target manifest so
they never count as target mutation.

Harness isolation remains:

- Claude Code: `-p`, `--no-session-persistence`, an isolated `CLAUDE_CONFIG_DIR`
  that contains only what AgentTeam writes, `--setting-sources user` (that
  isolated home only — no workspace settings), `--strict-mcp-config` with an
  AgentTeam-written empty `--mcp-config`, explicit tool restriction
  (`--tools`/`--allowedTools`/`--disallowedTools` with `--permission-mode`),
  instructions by file (`--append-system-prompt-file` — present in the binary
  but not in `--help`, so verified by the G5 probe; fallback
  `--append-system-prompt` with file-read text), structured output, read-only
  review tools. **Not** `--safe-mode`: it disables Skills, plugins, hooks, and
  MCP servers and would contradict the required Skill rendering; isolation
  rests on the fresh config home plus setting-sources and strict MCP instead.
  Never `--bare` (it never reads OAuth).
- Codex: `codex exec`, `--ephemeral`, `--ignore-user-config`, `--ignore-rules`
  (execpolicy `.rules` only; `AGENTS.md` discovery is unaffected), isolated
  `CODEX_HOME`, read-only sandbox, approval `never`, JSONL plus output schema.
  Instruction channel ladder, decided by the G5 probe and recorded in
  `degraded[]`: `model_instructions_file` (replaces Codex's built-in
  instructions — a quality risk), `developer_instructions` (appends, but is
  argv-inline or config), then workspace `AGENTS.md` (a valid fallback channel).
- Grok Build: isolated `GROK_HOME`, memory and subagents disabled, read-only
  sandbox, file-delivered definition (`--rules` appends;
  `--system-prompt-override` replaces the default system prompt and is used
  only if appending fails), `--json-schema` structured output; other controls
  (for example leader mode or web search) are disabled only if the probe shows
  they exist; active authentication stays `unverified` until the first live
  leg because Grok has no status command.

Day-one probes at G5: one trivial structured-output prompt per harness that
verifies the instruction channel, the Skills channel, schema acceptance, and
active authentication — at most two calls per harness, outside the acceptance
cycle. Results are written into the profile's verification levels; raw
captures land in the gitignored `~/.agentteam/probes/<date>/`. Tracked parser
fixtures under `fixtures/vendor-output/` change only through explicit,
reviewed promotion — a commit that names the probe and the sanitisation
applied — never by automatic replacement.

## 12. Direct ensemble state machine

1. Validate profile, Assistant, and RunRequest (reserved overlay fields must
   be empty in M1a); rendering fails before any launch if a required part —
   including each Skill — cannot be delivered to a selected harness.
2. Resolve paths, harness selection (`decided_by`), portable hints, and local
   overrides.
3. Build one immutable definition bundle and canonical SHA-256 hash.
4. Create a pending run archive before any harness side effect.
5. Copy the fixture into one isolated workspace per requested leg; no leg
   receives another leg's outputs; target hashes detect mutation.
6. Render all requested invocations from the same bundle, including the three
   Skills through each harness's skill channel.
7. Start all requested legs concurrently in fresh-session mode (Claude, Codex,
   and Grok in the acceptance cycle; one leg in solo mode, which skips
   synthesis unless requested).
8. Retry the same harness once only for network interruption, rate limit,
   service unavailability, or timeout.
9. Never retry auth, permission, invalid input, schema, semantic, or unknown
   failures; never substitute another harness.
10. Require every requested normalized report before synthesis.
11. Give a fresh Claude invocation only the labelled leg reports, not the
    target or hidden oracle.
12. Validate synthesis schema/attribution, evaluate semantic predicates,
    re-hash definitions, finalize the archive, and return the stable exit code.

One acceptance cycle uses at most eight calls (a call is one CLI invocation):
three legs, up to three one-time leg retries, synthesis, and at most one
transient synthesis retry. Across M1a the live budget is at most two probe
calls per harness, one initial acceptance cycle after G5, and at most two
reruns, each separately confirmed by the owner — a hard ceiling of 30 calls
(owner-approved 2026-08-23). AgentTeam never starts another cycle
automatically.

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
export. After owner review, a sanitized evidence bundle is committed under
`docs/evidence/m1a-live-<date>/`: the ensemble record, the redacted invocation
records (typed-placeholder argv, environment names only), the normalized
reviews, and a summary — all produced by the same tested redaction function.
Raw streams, workspace copies, absolute paths, and anything credential-shaped
stay local. This is the reviewed sanitized summary of ADR 0013 in its complete
form.

## 14. PoC fixture and live semantic acceptance

The committed review target is a small TypeScript module with three labelled,
non-production defects: shell command injection, an off-by-one boundary error,
and caller-input mutation. Using a TypeScript review target does not couple the
Python runner to Node; it deliberately tests language-independent review.

The labelled oracle (`fixtures/review-target.oracle.json`: file, line window,
and category per defect) lives outside the leg workspace and is never given to
a leg or to synthesis. A finding "identifies" a defect when file and category
match and the line falls inside the window; a "critical finding outside the
oracle" is any critical or high finding with no matching oracle entry. The
matcher is deterministic and unit-tested.

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

Conditions 1, 6, 7, and 8 — together with bundle/target hash identity, valid
attribution, and a recorded `decided_by` on every invocation — form the
**mechanical** tier and establish the architecture claims (AD-04, AD-08, AD-09,
HB-02, HB-03, HB-05, HB-07, TE-02, XC-04). Conditions 2–5 and 9 form the
**semantic** tier and establish product usefulness (product-intent §1.7, "the
same colleague"). The ensemble record stores both tiers separately. A semantic
miss routes to definition or prompt work, never to an architecture review. G8
closes on semantic PASS; an owner-recorded waiver may close M1a as
failed/abandoned — recorded as such in the evidence bundle, PLAN, and
DECISIONS — but never counts as semantic PASS. Condition 1's "same bundle"
includes the three Skills.

## 15. Deterministic test plan

Normal tests never invoke a vendor model. Cross-platform fake harnesses are
Python modules launched through the same process runner and record argv,
stdin, cwd, and environment names.

Coverage includes schema parity; exclusion/path traversal; bundle immutability;
harness-selection precedence and exclusion, including solo mode with
`decided_by: assistant`; model precedence; reserved overlay fields round-trip;
exact vendor rendering; Skill-channel rendering per harness and the
target-manifest exclusion; cross-OS hash identity of the committed example
package; `.gitattributes`/newline normalisation in schema reproduction;
vendor-output parser fixtures (hand-authored from documentation before G5,
updated only by reviewed promotion of sanitized G5 captures); the Windows-only
`.cmd` fake shim with adversarial spaces and metacharacters on both the
resolved-launcher and fail-closed branches; selection-algorithm cases including
hard failure for a user-requested forbidden or ineligible harness; an
undeliverable required Skill failing before launch; archive-contract
rejections (symlink, binary file, case-colliding paths); compatibility-suite
skip when the extra is absent; spaces/Unicode/backslashes/
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
- checks: lock consistency, Ruff, mypy, pytest, build, schema reproduction,
  deterministic acceptance, and example-package hash identity across the
  matrix.

The repository is public with the MIT licence from G2, created only after the
pre-first-push checklist passes: history secret scan, LICENSE and third-party
notices, `docs/provenance.md` (ATM provenance), and repository/distribution
name checks. CI grows with the gates: at G2 the scaffold smoke matrix (lock,
Ruff, mypy, scaffold tests, build, schema reproduction, `--help`/`--version`);
G3 adds the adapter tests and the Windows `.cmd` fake; G4 adds deterministic
acceptance, example-package hash identity, and the optional ClawTeam jobs; G7
runs the final matrices. A **vendor-smoke** job installs Claude Code and Codex
through `npm` on the three runners and runs `atm profile doctor` (flag
presence, `--version`/`--help`) through the real launchers without any
credential or model call; Grok is best-effort until its non-interactive
installer is verified. `.gitattributes` keeps checkouts LF so hashes and
schema reproduction agree on Windows.

Optional provider matrix:

- the same three OSes on Python 3.11;
- `uv sync --frozen --all-groups --extra clawteam`;
- ClawTeam compatibility tests only, with temporary data/config fixtures.

CI has no vendor login, model call, API key, API-test route, or secret
permission. Passing proves deterministic Python/path/process/archive/schema
and optional-provider plumbing only.

Before G7, run local deterministic and Ubuntu live gates and repeat the
history secret scan. `gh` authentication is in place (verified 2026-08-23;
account `WSH95`, `repo` scope); every push still needs its own explicit
approval. No release, tag, package registry, installer, or signed artifact is
in M1a.

## 17. Commit boundaries during product implementation

1. `chore(project): rename project to AgentTeam`
2. `docs(steward): documentation hygiene for the AgentTeam baseline`
3. `chore(core): scaffold Python CLI package with uv`
4. `feat(domain): add portable definition, run-record, review/synthesis, and run schemas`
5. `test(substrate): qualify optional ClawTeam seam`
6. `feat(harness): add isolated direct CLI adapters`
7. `feat(run): add invocation ledger and parallel ensemble runner`
8. `test(poc): add deterministic direct-harness acceptance`
9. `docs(poc): record subscription-backed Ubuntu acceptance (sanitized evidence bundle)`
10. `ci: verify direct and optional-provider plumbing` (the workflow grows at
    G2, G3, and G4; this commit closes it at G7)

Commit order inside G2–G4 may vary (commit 5 may follow 7). Include Project
Steward state with its semantic change. Never push without the separate
approval; the first push (the scaffold, at G2) is itself an approval moment.

## 18. Stop rules

- Stop on any mutation of a portable Assistant package.
- Stop before launch when a required part — including any Skill — cannot be
  delivered to the selected harness; `degraded[]` never excuses a required
  part.
- Stop rather than insert API mode if native subscription execution fails.
- Stop if an adapter needs credential-file parsing or copying.
- Fix deterministic Windows/macOS direct plumbing (green from G2) before
  product/TE-08 claims.
- A ClawTeam compatibility failure blocks provider qualification and M1b; do
  not silently fork, vendor, or make it mandatory.
- Record vendor flag drift in dated profile data/tests rather than hidden
  branching.
- Stop at the eight-call or 15-minute attempt bound, at two probe calls per
  harness, and after the initial acceptance cycle unless the owner separately
  confirms a rerun (at most two); the hard ceiling is 30 calls.
- If output exposes a secret, keep it local, rotate outside AgentTeam, and do
  not commit/upload it.
- After two failures for the same live semantic reason, return to review rather
  than tune prompts indefinitely.
- G8 ends M1a. Do not begin M1b in the same approval scope.

Falsification routing (which register row a failure falsifies, and where it
goes):

- No Codex file or config injection channel works (neither
  `model_instructions_file`, `developer_instructions`, nor workspace
  `AGENTS.md`) → HB-02 is falsified for Codex → back to
  `architecture-options.md`, not a workaround.
- The definition hash changes → find the writer (symlinked Skills, harness
  memory, adapter output) → injection fix, never an architecture change.
- Synthesis cannot attribute → record/schema fix, layer-internal.
- Grok channel or authentication fails → FAIL-HARD report; the owner revisits
  the all-three gate (ADR 0018) rather than the plan silently shrinking.
- Semantic miss with valid mechanics → definition or prompt work; after two
  failures for the same reason, return to review (rule above).

## 19. Committed later milestones

These are product obligations from the original brief, not optional ideas.
Each receives a separate detailed plan and approval:

1. **M1b — Team foundation:** substrate-neutral TeamTemplate, TeamRun, Member,
   and CoordinationSubstrate contracts; a product-owned local deterministic
   coordination provider first (file task store, mailbox, snapshot — used by
   the deterministic tests), the optional ClawTeam provider second; a written
   ClawTeam exit criterion, built from the section 10 qualification
   measurements, before PoC B (ADR 0018).
2. **M1c — dynamic-member PoC B:** reusable Lead/Implementer/Reviewer team,
   mixed harnesses, one hidden auditable temporary specialist, enforced policy
   decision, and complete archive; the Lead is invoked fresh per decision point
   with a RunStateSummary as the default hypothesis (review R6) unless evidence
   requires a resident Lead.
3. **M2 — nested-team PoC C:** temporary inner TeamRun, isolated namespace,
   result return, archive, outer continuation, explicit achieved isolation,
   recovery, and the `atm` MCP server.
4. **M3 — evolution and artifacts:** overlays (Base + User + Reviewed
   Evolution) and their proposals/review, artifact manifest/lock, per-host
   resolution, credential-free export/import (M1a already proves cross-OS hash
   identity), and modification detection.
5. **M4 — operations:** deterministic process/metric/checkpoint/log monitors,
   schedulers, triggers, health/restart policy, and fresh Assistant invocation
   for interpretation/decisions/escalation; unattended native runs use
   subscription OAuth on the owner-operated persistent host (Q5), which is why
   M1a is attended-only as a milestone boundary.
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
and MIT holder line; and, for r2: the approval artefact (DECISIONS entry naming
file + SHA), harness-selection precedence with `decided_by`, three Skills in
the example and their per-harness channels, cross-OS hash identity, probe
verification levels, overlay deferral with reserved fields, the public
repository at G2, the sanitized evidence bundle, falsification routing, and
the documentation-hygiene list; and, for r3: the Claude recipe without
`--safe-mode`, the Grok `.grok/skills/` and Codex channels, the pre-first-push
checklist and gate-by-gate CI growth, the Member execution binding (one
invocation or one ensemble), the launcher policy, the V1 archive contract, the
complete selection algorithm, the required-Skill rule, promotion-only parser
fixtures, the failed/abandoned waiver semantics, and the 30-call ceiling.

Implementation begins only after review comments are resolved and the owner
explicitly marks this plan approved.

Project-local sources remain the M0.1 review, harness capability evidence,
architecture synthesis, historical PoC proposal, and product requirements.
Volatile vendor CLI/auth facts must be rechecked at their execution gate.
ClawTeam compatibility is anchored to the full Git revision above; uv behavior
is anchored to the installed `uv 0.11.26` help captured during planning.

## 22. Merge record (r2, 2026-08-23)

r2 merges `docs/plans/m1-agentteam-direct-slice.md` (independent proposal,
written against `3407ec9` without reading r1) and the findings of
`docs/reviews/2026-08-23-m0-review-at-3407ec9.md`, cross-checked by an
independent plan agent; owner decisions are in DECISIONS 0019.

Adopted into r2 (source → section):

| Item | Source | Sections |
| --- | --- | --- |
| Harness-selection precedence with `decided_by`; solo mode | review R7/R16, proposal T4; HB-03/AD-04 | 1, 2, 3, 7, 8, 11, 12, 14, 15 |
| Three Skills in the example Assistant, rendered per harness | review R12-i; AD-09/AD-02 | 6, 7, 11, 12, 14, 15 |
| Cross-OS hash identity, `.gitattributes`, canonical hash spec | review R12-ii; AR-03; cross-check C9 | 4, 6, 7, 15, 16 |
| `RunRecordV1` as the one-Member subset of the TeamRun record | review R16 | 2, 6, 7 |
| Probe verification levels; day-one probes at G5 | review R22, proposal T8; cross-check C6/C11–C13 | 3, 7, 8, 9, 11 |
| Falsification routing | proposal §4, M0 `minimal-poc-plan.md` §7 | 18 |
| Mechanical vs semantic traceability of acceptance | review R12-iii | 3, 14 |
| ClawTeam exit-criterion inputs; M1b provider order; Lead fresh per decision point | ADR 0018; review R2/R6 | 10, 19 |
| Reviewed sanitized evidence bundle | review H13 | 3, 13, 17 |
| Documentation hygiene list in G1 | review H3, H6, H8–H12, R7, R19 | 3, 4, 17 |
| Approval artefact convention | review R20; ADR 0018 | 2, 3, 21 |
| Review/synthesis schemas in the vendors' dialect intersection; CI artefacts; oracle outside workspace + matcher; Windows `.cmd`/env baseline; local state layout; "call" definition; total budget; `attendance`/`auth_mode`; harness ids | cross-check C1–C19 | 6, 7, 8, 9, 12, 14 |
| Public MIT repository and first push at G2 after the G1 rename; CI from the scaffold; `gh` authenticated | owner decision 2026-08-23 | 2, 3, 16, 17 |

Conflicts and resolutions: semantic conditions stay gating (owner), with the
two-tier labelling; the three-concurrent-leg cycle stays (ADR 0013) and the
proposal's solo runs are covered deterministically; the TypeScript fixture
stays; `OverlayV1` is deferred to M3 with reserved fields (owner); export/import
stays in M3; no separate design-spec document (this plan is the spec); the
ClawTeam G4 qualification stays and now feeds the M1b exit criterion.

Not adopted from the proposal: an early operational-mode slice (owner: code/dev
teams first); its T-numbering and tier names (gate names G0–G8 are referenced
by steward files); a `noop` harness kind (fakes run behind the real adapters);
`--max-budget-usd` as the control (calls/time instead); extra CLI verbs
(`harness list|check`, `ledger`, `ensemble show`, `assistant export|import`);
live solo runs; any TeamTemplate/coordination behaviour in M1a.

### r3 (2026-08-23) — review findings on r2 resolved

Multi-agent review verdict on r2: "do not approve yet" — five blocking findings
and required corrections; architecture choices confirmed. Resolved in r3:

| Finding | Resolution | Sections |
| --- | --- | --- |
| `--safe-mode` disables Skills/plugins (verified: `claude --help` 2.1.241) | Claude recipe without `--safe-mode`: isolated config home, `--setting-sources user`, `--strict-mcp-config` + empty MCP config, explicit tool restriction, `--no-session-persistence`; Skill channel candidates probe-selected | 2, 11 |
| Grok Skill path; Codex `--ignore-rules` | Grok `.grok/skills/` primary, `.agents/skills/` fallback (both listed by `grok inspect` 1.0.5, verified locally); Codex `--ignore-rules` is `.rules`-only (verified: `codex exec --help`), `AGENTS.md` fallback valid | 11 |
| G2 required the full CI matrix before G3/G4; publication before secret/notice/name checks | Pre-first-push checklist at G2; CI grows by gate (G2 smoke → G3 adapters → G4 acceptance/ClawTeam/hash → G7 final); G7 renamed "Final CI matrices" | 3, 16, 17 |
| One Member with one harness binding vs three legs + synthesis | `execution {kind: invocation \| ensemble, ref}`; one `EnsembleRecordV1` per Member in the cycle; `team-execution-model.md` §4 amended ("one execution at a time") | 7, 12 |
| Windows launcher coverage; `PATH` missing | Explicit launcher policy (resolve `.cmd` shims to `node` + script; fail-closed allowlist otherwise); Windows-only `.cmd` fake; `PATH`/`SystemDrive` in the baseline; vendor-smoke CI job | 9, 15, 16 |
| Other: `effective_definition_hash` computed, not client-supplied; required Skills fail before launch; probe captures gitignored + reviewed promotion; waiver closes as failed/abandoned, never PASS; complete selection algorithm; V1 archive contract; Q5 in M4; budget = 1 cycle + ≤2 owner-confirmed reruns, ceiling 30 | as listed | 2, 7, 11, 12, 14, 15, 18, 19 |
