# AgentTeam M1a direct-harness PoC implementation plan

- Status: **proposed for review — not approved for implementation**
- Plan date: 2026-08-23
- Baseline commit: `3407ec9` (`docs(discovery): apply M0 product architecture review`)
- Planned product name: **AgentTeam**
- Planned repository: `WSH95/AgentTeam`
- Planned CLI: `atm`

This is the implementation plan to execute after explicit approval. Writing
this document does not authorize the directory/repository rename, source-code
changes, dependency installation, credential setup, live harness calls,
GitHub repository creation, or a push. Each external or credentialed gate
below remains separately visible.

## 1. Outcome and milestone boundary

M1a will implement both solo direct execution and the acceptance-critical
ensemble case. It will prove that one portable Assistant definition can be
resolved without mutation, rendered into three installed coding harnesses,
executed as three fresh independent review legs, and synthesized with
attributable evidence.
The first-pass harnesses are:

1. Claude Code;
2. Codex CLI;
3. Grok Build CLI.

The three review legs run concurrently. After all three finish successfully,
a separate fresh Claude Code invocation synthesizes their normalized reports.
There is no cross-harness fallback: a failed required leg makes the ensemble
fail. One retry is allowed only for a classified transient failure.

M1a implements the direct subprocess path only. It deliberately stops before
ClawTeam integration, reusable TeamTemplates, dynamic Members, nested
TeamRuns, ACP transport, OpenClaw/Telegram surfaces, or API-gateway testing.
Those are later milestones and do not enter this implementation by accident.

## 2. Confirmed product decisions

The following are inputs to this plan, not choices left to the implementer:

- Final product name: **AgentTeam**. The historical ATM experiment remains
  historical; the new product nevertheless uses `atm` as its CLI command.
- Local directory after the rename:
  `/home/wsh/Documents/AgentTeam`.
- Future public repository: `WSH95/AgentTeam`.
- Implementation language: TypeScript on Node.js.
- Canonical product documentation: English.
- Public license: MIT, with
  `Copyright (c) 2026 ShuhanWang`.
- Package is private during M1a. There is no npm publication in this
  milestone.
- Portable Assistant data remains harness- and substrate-neutral. Concrete
  vendor model IDs, effort values, executable locations, login state, and
  provider endpoints belong in local HarnessProfiles or an ephemeral
  RunRequest, never in the portable definition.
- Native unattended runs use the owner's subscription login in each installed
  vendor CLI. AgentTeam does not copy, read, export, broker, or upload
  credentials.
- Windows and macOS evidence comes from credential-free GitHub-hosted CI and
  proves deterministic process plumbing only. Live subscription-backed
  acceptance runs only on the owner's Ubuntu host.
- The deferred API-test route is replaceable. M1a neither requests an
  OpenRouter key nor implements or invokes that route.
- ATM source may be copied or adapted when useful because it is owner-authored.
  Any reuse must still record provenance and preserve third-party notices and
  obligations.

## 3. Delivery sequence and gates

Implementation proceeds in this order. A failed gate stops later work.

| Gate | Work | Evidence required to pass |
| --- | --- | --- |
| G0 | Approve this plan | Owner explicitly approves the reviewed plan; plan status changes to `approved` and is committed before source implementation |
| G1 | Rename and re-baseline | Clean worktree; target path absent; directory becomes `/home/wsh/Documents/AgentTeam`; current product docs use AgentTeam/`atm`; historical evidence remains attributable; AGENTS diff approved and applied |
| G2 | TypeScript foundation | Locked dependencies; strict ESM build; schemas generated and round-trip tested; `atm --help` and `atm --version` pass |
| G3 | Direct harness core | Claude, Codex, and Grok adapters pass argv/env/parser contract tests against deterministic fake executables; no model call |
| G4 | Deterministic PoC | The complete three-leg-plus-synthesis state machine passes locally with fake harnesses, including failures, retry, cancellation, redaction, and archive reconstruction |
| G5 | Native-auth preflight | Owner completes one interactive login per dedicated vendor config home; `atm profile doctor` reports only sanitized status; no credential value is read or printed |
| G6 | Ubuntu live PoC | Three parallel subscription-backed legs and a separate Claude synthesis meet every semantic and evidence criterion in section 14 |
| G7 | Public CI | After a separate explicit publication/push approval, create `WSH95/AgentTeam`, push MIT-licensed history, and pass the credential-free Ubuntu/Windows/macOS Node matrix |
| G8 | M1a close | Verification and sanitized result summary are current; no secret or raw run evidence is tracked; M1b is only proposed, not started |

## 4. Rename and repository re-baseline

G1 is one controlled semantic change, performed only from a clean committed
tree.

1. Recheck that `/home/wsh/Documents/AgentTeam` does not exist and that no
   `atm` executable collision is present on the owner host.
2. Move the repository directory; do not copy it or initialize a second Git
   repository. Reopen the session from the new path and verify the same HEAD,
   branch, and clean status.
3. Update current project identity in `.project-steward/PROJECT.md`, current
   state files, the discovery landing page, and new top-level product docs.
   Preserve historical panel, critic, evidence, decision, and progress text as
   dated records. Where needed, add a terminology note instead of performing
   an indiscriminate `ats`/`ATM` replacement.
4. Add a root `README.md`, `LICENSE`, and `.gitignore`. The README will state
   that M1a is an alpha direct-harness PoC, not a production team runtime.
5. Keep `CLAUDE.md` as the thin `@AGENTS.md` adapter.

`AGENTS.md` is guarded. Immediately before editing it, show this previously
approved exact non-managed-block diff again and obtain the required explicit
approval:

```diff
-# Assistant Team System
+# AgentTeam

-Portable, harness-independent Assistant definitions and reusable Team templates, executed as fresh TeamRuns over existing agent harnesses (ClawTeam, Claude Code, Codex, OpenClaw, Hermes, ...). Supersedes the ATM experiment.
+Portable, harness-independent Assistant definitions and reusable Team templates, executed as fresh TeamRuns over existing agent harnesses (ClawTeam, Claude Code, Codex, OpenClaw, Hermes, ...). Supersedes the legacy ATM experiment; the new product CLI is `atm`.

-Primary language/stack: Markdown (discovery phase; implementation language TBD after architecture review).
+Primary language/stack: TypeScript on Node.js; Markdown documentation.
```

The managed command table will then be updated through Project Steward to:

| Task | Command |
| --- | --- |
| Build | `pnpm build` |
| Test | `pnpm test` |
| Lint | `pnpm lint` |
| Typecheck | `pnpm typecheck` |
| Live PoC | `pnpm poc:live` (owner host only; consumes subscription usage) |

## 5. Runtime and dependency baseline

M1a is one package at the repository root:

- package name: `agentteam`;
- version: `0.1.0-alpha.0`;
- `private: true`;
- license metadata: `MIT`;
- binary map: `atm` -> `dist/cli.js`;
- module format: strict ESM;
- Node engine: `>=22`;
- package manager: `pnpm@11.22.0` recorded in `packageManager`;
- CI Node versions: 22 and 24, both current LTS lines as of this plan;
- compiler: TypeScript with `strict`, `noUncheckedIndexedAccess`, and
  `exactOptionalPropertyTypes`;
- no bundler in M1a: `tsc` emits the CLI and library modules.

Runtime dependencies are limited to:

- `commander` for CLI parsing;
- `zod` for closed runtime schemas and inferred TypeScript types;
- `yaml` for YAML RunRequests and definitions.

Development dependencies are TypeScript, Vitest, ESLint, `typescript-eslint`,
and their required type packages. The lockfile is committed. New dependencies
require a documented reason; no harness SDK is introduced because M1a uses
installed CLI subprocesses.

## 6. Planned repository layout

```text
src/
  cli.ts
  commands/
    assistant-validate.ts
    profile.ts
    run.ts
  domain/
    assistant.ts
    overlay.ts
    harness-profile.ts
    run-request.ts
    invocation.ts
    ensemble.ts
    errors.ts
  resolution/
    assistant-resolver.ts
    model-policy.ts
  harness/
    adapter.ts
    process-runner.ts
    environment.ts
    claude.ts
    codex.ts
    grok.ts
  run/
    direct-runner.ts
    ensemble-runner.ts
    retry-policy.ts
    archive.ts
    redaction.ts
  schema/
    emit-json-schema.ts
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
docs/
  plans/
  provenance.md
.github/workflows/ci.yml
```

Generated schemas are checked in and verified against their Zod sources so
other tools can consume the contracts without running TypeScript.

## 7. Data contracts

Every persistent record is closed (`additionalProperties: false`), carries
`schema_version: 1` and a fixed `kind`, and serializes to canonical
snake_case JSON. YAML and JSON are accepted for human-authored inputs. Runtime
records are JSON only. Unknown fields fail validation rather than being
discarded.

### 7.1 `AssistantDefinitionV1`

The M1a slice contains:

- stable metadata: `id`, semantic `version`, `display_name`, `description`;
- instruction files: persona, principles, and review method, resolved relative
  to the package root and included in the bundle hash;
- semantic capability requirements and explicit artifact references;
- portable permission intent such as read-only review;
- abstract harness hints such as quality/latency intent, with no vendor model
  ID or concrete effort enum;
- optional substrate-neutral coordination guidance;
- content exclusions that reject credentials, provider endpoints, local home
  paths, process/session IDs, and runtime state.

Definition resolution never edits the package. Before and after a run, the
runner hashes every resolved definition file and fails the run if any hash
changes.

### 7.2 `OverlayV1`

The narrow overlay slice supports Base plus User Overlay with:

- target Assistant ID and compatible version range;
- allowed instruction/harness-hint patches;
- provenance (`source`, timestamp, author label);
- deterministic precedence and a resolution report;
- rejection of fields outside the M1a allowlist.

Reviewed Evolution proposals remain outside M1a; this schema does not silently
turn a run result into a persistent definition change.

### 7.3 `HarnessProfileSetV1`

This file is local, gitignored, and contains no credential values. For each of
`claude`, `codex`, and `grok` it records:

- executable path or command name;
- expected version constraint and capability flags;
- dedicated vendor config-home path;
- auth mode fixed to `native_subscription` in M1a;
- optional default model and effort;
- mapping from abstract Assistant hints to concrete model/effort values;
- timeout and approved proxy policy;
- names, never values, of environment variables that may be required.

The schema leaves an adapter seam for a later `api_test` profile kind, but M1a
does not accept or execute that kind.

### 7.4 `RunRequestV1`

The ephemeral RunRequest contains:

- Assistant package and optional Overlay paths;
- target workspace and task-file paths;
- `mode: direct`;
- one or more unique harnesses; a single harness is a solo run and multiple
  harnesses are independent ensemble legs;
- optional synthesis policy for a multi-harness run;
- optional per-harness model/effort overrides;
- output directory override;
- timeout, evidence, and retry settings within schema limits.

Run IDs, timestamps, attempts, resolved models, subprocess data, and results
belong in runtime records, not in the RunRequest. The CLI may override fields
for one invocation; it writes the fully resolved request into the local run
archive.

The M1a live acceptance request fixes the harness list to
`[claude, codex, grok]` and the synthesis harness to `claude`; those are
acceptance-fixture constraints, not limitations of the direct-run schema.

### 7.5 `HarnessInvocationV1` and `EnsembleRecordV1`

Each invocation record contains the run/ensemble/attempt IDs; requested and
observed harness version; requested and observed model/effort where available;
definition bundle hash; normalized, redacted argv; environment-variable names
and policy decisions but no values; cwd placeholder; start/end/duration;
stdout/stderr/result artifact references and hashes; usage fields reported by
the harness; retry classification; exit code/signal; schema outcome; and a
terminal status.

Cost is not fabricated. Codex remains `cost_source: unavailable`. A vendor
reported number from Claude or Grok is stored as vendor-reported telemetry and
not described as the user's incremental subscription charge. No public price
table is used to derive USD.

The Ensemble record names all three leg invocation IDs, the synthesis
invocation and its input IDs, attribution links, aggregate status, and the
mechanical and semantic acceptance results separately.

## 8. CLI contract

The implemented commands are:

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

Prompts and multiline instructions are passed by file or stdin, never embedded
as user-controlled command strings. Subprocesses use argv arrays with
`shell: false`.

Exit codes are stable:

- `0`: command and requested acceptance checks succeeded;
- `1`: runtime or harness failure;
- `2`: invalid CLI input, schema, profile, or unsafe environment;
- `3`: execution completed but PoC semantic acceptance failed;
- `130`: owner cancellation.

## 9. Model and effort resolution

Concrete resolution is per harness and is recorded. Highest precedence wins:

1. `--model` / `--effort` CLI override;
2. RunRequest override;
3. local HarnessProfile mapping from a portable Assistant hint;
4. local HarnessProfile default;
5. vendor CLI default.

An unspecified model or effort therefore stays unspecified all the way to the
vendor unless a local mapping/default supplies it. M1a does not hard-code the
models currently installed on the owner host. Unsupported values fail before
a model call where the adapter can validate them; otherwise the vendor error
is recorded without fallback.

## 10. Native authentication and isolation

AgentTeam uses one installed binary per vendor and a dedicated AgentTeam config
home per vendor. The owner authenticates interactively once into each dedicated
home using the same eligible subscription account they normally use for that
vendor. `atm profile init` creates non-secret directories/config and prints the
login commands; it does not automate a browser, scrape tokens, or copy an
existing credential store.

The intended owner actions at G5 are equivalent to:

```text
CLAUDE_CONFIG_DIR=<agentteam-config>/harnesses/claude claude auth login
CODEX_HOME=<agentteam-config>/harnesses/codex codex login
GROK_HOME=<agentteam-config>/harnesses/grok grok login --oauth
```

Actual paths are printed locally and are never committed. Claude and Codex
status commands are parsed through a strict allowlist of non-secret fields.
Grok 1.0.5 exposes login but no status subcommand, so `doctor` can verify its
binary/config isolation but the first controlled live leg is the auth proof.

For every native run, the environment builder:

- starts from a minimal cross-platform allowlist needed for process execution;
- sets only the selected dedicated config-home variable;
- records environment names, never values;
- fails closed if API-key, alternate-provider, base-URL, or unapproved proxy
  variables could override or redirect subscription authentication;
- never opens credential files;
- never falls back to an API provider when native auth fails.

Harness isolation recipes are:

- **Claude Code:** `-p`, `--safe-mode`, `--no-session-persistence`, isolated
  `CLAUDE_CONFIG_DIR`, task on stdin, rendered instructions by file, structured
  JSON output, and read-only review tools. Do not use `--bare`, because it
  disables OAuth/keychain access.
- **Codex:** `codex exec`, `--ephemeral`, `--ignore-user-config`,
  `--ignore-rules`, isolated `CODEX_HOME`, task on stdin, instructions through
  `model_instructions_file`, `--sandbox read-only`, approval `never`, JSONL
  stream plus output schema.
- **Grok Build:** isolated `GROK_HOME`, `GROK_MEMORY=0`,
  `GROK_SUBAGENTS=0`, leader mode disabled in the dedicated config,
  `--no-subagents`, `--disable-web-search`, `--sandbox read-only`, prompt and
  agent definition by file, and structured JSON output.

Claude usage accounting is treated conservatively. Anthropic's June 15 help
center update says the announced separate monthly Agent SDK credit was paused;
for now Agent SDK and `claude -p` still draw from subscription usage limits.
The implementation therefore budgets by calls and time, not an assumed free
credit or synthetic USD amount, and rechecks this policy before a live cycle.

Before any hosted or multi-user subscription execution is considered in a
future milestone, vendor terms must be reviewed again. M1a is narrower:
owner-operated CLIs on the owner's persistent machine.

## 11. Adapter and process contracts

All adapters implement one interface:

```ts
interface HarnessAdapter {
  probe(context: ProbeContext): Promise<HarnessCapabilityReportV1>;
  render(context: RenderContext): Promise<RenderedInvocationV1>;
  invoke(rendered: RenderedInvocationV1, signal: AbortSignal): Promise<RawInvocationV1>;
  parse(raw: RawInvocationV1): Promise<NormalizedReviewV1>;
}
```

`render` is pure with respect to the Assistant package. It creates only
run-scoped files. `invoke` delegates to one shared process runner. `parse`
validates vendor output and returns the same normalized review schema for all
three harnesses.

The process runner:

- uses `child_process.spawn` with `shell: false`;
- concurrently drains stdout and stderr to prevent deadlock;
- tees raw byte streams into access-restricted local evidence;
- writes records atomically through a same-directory temporary file and
  rename;
- creates the pending invocation record before spawning;
- enforces a 15-minute attempt timeout;
- on cancellation/timeout, terminates the process tree (POSIX process group;
  Windows `taskkill.exe` invoked as an argv array) and records the outcome;
- finalizes every started invocation to a terminal state, including crashes.

## 12. Direct ensemble state machine

1. Parse and validate the profile, Assistant, Overlay, and RunRequest.
2. Resolve paths, overlay precedence, abstract model hints, and concrete local
   profile/CLI overrides.
3. Build one immutable definition bundle; compute its canonical SHA-256 hash.
4. Create a pending run archive before any harness side effect.
5. Copy the review fixture into three isolated leg workspaces and apply each
   harness's read-only policy. No leg can read another leg's output directory;
   target hashes detect any sandbox-policy bypass.
6. Render all three invocations from the same bundle hash.
7. Start Claude, Codex, and Grok concurrently with fresh-session isolation.
8. Classify each mechanical result. Retry that same harness once only for
   network interruption, rate limiting, service unavailability, or timeout.
9. Do not retry auth, permission, invalid-input, schema, semantic, or unknown
   failures. Do not substitute another harness.
10. Require all three normalized leg reports before synthesis.
11. Start a fresh Claude synthesis invocation. Its only review inputs are the
    three labelled normalized reports; it does not inspect the target and does
    not receive the hidden defect oracle.
12. Validate synthesis schema and attribution, evaluate deterministic semantic
    checks against the hidden oracle, re-hash the Assistant package, finalize
    the archive, and return the stable exit code.

The maximum is eight model calls per acceptance cycle: three initial legs,
three possible one-time leg retries, one synthesis, and one possible transient
synthesis retry. AgentTeam never starts a second cycle automatically; a rerun
requires explicit owner approval.

## 13. Evidence and privacy

Default run data lives below a gitignored local AgentTeam state directory, not
under portable definitions. Each run retains:

```text
run.json
resolved-request.json
bundle/manifest.json
invocations/<id>/invocation.json
invocations/<id>/stdout.raw
invocations/<id>/stderr.raw
invocations/<id>/result.normalized.json
ensemble.json
events.ndjson
manifest.sha256.json
```

Raw streams and normalized model output are retained locally because they are
needed to diagnose attribution and parser failures. POSIX files use owner-only
permissions; Windows relies on the user's profile ACL and receives a warning
if the output path is outside it. Recorded argv replaces sensitive/path values
with typed placeholders. Environment records contain names and policy results
only. Credential files and values are never evidence inputs.

M1a provides no automatic `git add`, publish, upload, or raw-evidence export.
Only a separately reviewed, human-sanitized result summary may be committed.

## 14. PoC fixture and live semantic acceptance

The committed review target is a small TypeScript module with three labelled
defects that are safe because the fixture is reviewed statically and never
executed as production code:

- **D1 — command injection:** attacker-controlled text reaches a shell command;
- **D2 — off-by-one:** a boundary calculation omits or includes one item;
- **D3 — caller-input mutation:** an in-place operation mutates an input owned
  by the caller.

The Assistant definition requests a security/correctness review and a fixed
structured report. Acceptance uses semantic IDs and normalized locations, not
exact model wording.

All of the following must pass in one live cycle:

1. Claude, Codex, and Grok each complete as an independent fresh leg with the
   same definition bundle hash and target hash.
2. Each leg identifies D1 and at least one of D2/D3 with an actionable
   explanation.
3. The union of leg findings identifies D1, D2, and D3.
4. No leg invents a critical finding outside the fixture oracle; lesser extra
   observations are recorded but do not fail unless they contradict the code.
5. Claude synthesis lists all three defects, identifies which leg(s) asserted
   each one, and distinguishes agreement from disagreement.
6. Every attribution resolves to an actual leg invocation ID; synthesis may
   not claim an unprovided source.
7. The Assistant package is byte-identical before and after the run.
8. Every started attempt has a terminal invocation record; hashes reconstruct
   the archive; no credential value or raw evidence is tracked by Git.
9. Mechanical success and semantic acceptance are both explicit. A valid JSON
   report that misses the semantic bar exits `3`, not `0`.

## 15. Deterministic test plan

No normal build, lint, unit, integration, or CI test may invoke a vendor model.
Fake harness executables exercise the real adapter/process/archive code and
record received argv, stdin, cwd, and environment names.

Required deterministic coverage includes:

- strict acceptance/rejection and JSON-Schema parity for all six V1 contracts;
- Assistant exclusion rules, path traversal rejection, bundle hashing, and
  before/after immutability;
- Overlay allowlist and precedence;
- model/effort precedence, including vendor-default passthrough;
- exact Claude/Codex/Grok argv and environment rendering;
- spaces, Unicode, backslashes, long paths, CRLF, and executable suffixes;
- stdout/stderr concurrency, partial lines, invalid UTF-8 handling, and large
  streams;
- structured-output success, malformed JSON, schema mismatch, nonzero exit,
  missing output, and contradictory terminal signals;
- transient classification and exactly-one retry;
- no retry for auth/schema/semantic/permission/unknown failures;
- timeout, owner cancellation, process-tree cleanup, and exit `130`;
- atomic pending-to-terminal records and recovery of an interrupted archive;
- path/argv/environment redaction and secret-shaped fixture values;
- solo direct execution with each adapter and no synthesis invocation;
- three-way parallel fanout followed only then by synthesis;
- required-leg failure suppressing synthesis;
- attribution validation and all live semantic predicates against deterministic
  canned reports;
- CLI help/version/JSON modes and exit-code contract.

Local G4 verification is:

```text
pnpm install --frozen-lockfile
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm test:acceptance
```

`pnpm poc:live` is excluded from `pnpm test`, `pnpm verify`, and CI.

## 16. GitHub CI and publication

The workflow matrix is:

- OS: `ubuntu-latest`, `windows-latest`, `macos-latest`;
- Node: 22 and 24;
- install: Corepack plus `pnpm install --frozen-lockfile`;
- checks: lint, typecheck, unit/integration tests, build, and deterministic
  acceptance with fake harnesses.

The workflow contains no vendor login, model call, API key, OpenRouter route,
or secret permission. Permissions are read-only except the minimum GitHub
metadata needed to check out source. Passing jobs prove cross-platform Node,
path, subprocess, timeout, archive, and schema plumbing only.

Before G7:

1. run the full local deterministic and Ubuntu live gates;
2. inspect tracked files and history for secrets and raw run evidence;
3. verify MIT text, third-party licenses, and `docs/provenance.md`;
4. recheck the `WSH95/AgentTeam` repository name and public naming collisions;
5. ask the owner for explicit approval to create a public repository and push;
6. have the owner restore valid `gh` authentication without sharing the token;
7. create/push without rewriting history, then observe all six CI jobs.

No npm package, release artifact, tag, or package-registry credential is part
of M1a.

## 17. Commit boundaries during implementation

Subject to clean diffs, use these semantic boundaries rather than one large
implementation commit:

1. `chore(project): rename project to AgentTeam`
2. `chore(core): scaffold strict TypeScript CLI package`
3. `feat(domain): add portable definition and run schemas`
4. `feat(harness): add isolated direct CLI adapters`
5. `feat(run): add invocation ledger and parallel ensemble runner`
6. `test(poc): add deterministic direct-harness acceptance`
7. `docs(poc): record subscription-backed Ubuntu acceptance`
8. `ci: verify direct harness plumbing across supported platforms`

Project Steward state is included with the commit that changes it. No commit
is pushed without the separate G7 approval.

## 18. Stop and rollback rules

- Any mutation of a portable Assistant package is a hard PoC failure.
- If one of the three native subscription modes cannot run unattended on the
  owner host, stop. Do not insert an API-key or alternate-harness fallback.
- If an adapter requires credential-file parsing/copying, stop and redesign
  the auth boundary.
- If deterministic Windows/macOS plumbing fails, fix the direct seam before
  considering ClawTeam or ACP.
- If a vendor flag has drifted, update dated HarnessProfile capability data and
  tests; do not hide the drift in ad hoc branching.
- If the eight-call bound or 15-minute attempt bound is reached, finalize the
  archive and stop for owner review.
- If live output exposes a secret, stop, keep the artifact local, rotate the
  affected secret outside AgentTeam, and do not commit or upload the run.
- If G6 fails twice for the same semantic reason, return to architecture/product
  review rather than tuning prompts indefinitely.
- G8 ends M1a. Do not begin the ClawTeam/CoordinationSubstrate milestone in the
  same approval scope.

## 19. Explicitly out of scope

- ClawTeam adapter, task DAG, inbox, worktree, registry, or upstream PRs;
- `CoordinationSubstrate` implementation;
- ACP, WebSocket, daemon, or persistent leader transport;
- reusable TeamTemplates or multi-member team execution;
- dynamic/hidden Members, ephemeral Assistant creation, nested TeamRuns;
- Reviewed Evolution proposal generation or automatic definition updates;
- Hermes, OpenClaw, Telegram, scheduling, long-running surfaces, or UI;
- API-test/OpenRouter execution, key handling, base-URL canary, or provider
  compatibility claims;
- npm publication, binaries/installers, releases, or signed artifacts;
- hosted or multi-user subscription credential service.

## 20. Approval checklist

Reviewers should challenge this document against the following concrete
questions. Approval means the resulting answers are acceptable without
silently changing scope:

- Is direct-first M1a the right falsifiable slice before ClawTeam?
- Are the six V1 contracts narrow enough for M1a and sufficient to keep the
  later HarnessAdapter/CoordinationSubstrate seams open?
- Are separate vendor config homes plus owner-performed login an acceptable
  interpretation of native subscription OAuth?
- Are the three defects and semantic thresholds strong enough to prove useful
  multi-harness review without turning model quality into a brittle wording
  test?
- Are one transient retry, 15 minutes per attempt, and eight calls per cycle
  acceptable limits?
- Is full local/raw evidence with no automatic export the right privacy
  boundary?
- Is publication after local deterministic + Ubuntu live acceptance, followed
  by credential-free hosted CI, the right ordering?
- Are AgentTeam, `WSH95/AgentTeam`, `atm`, TypeScript/Node, English docs, and
  the MIT holder line recorded correctly?

Implementation starts only after the owner resolves review comments and
explicitly marks this plan approved.

## 21. Sources and traceability

Project-local sources:

- [M0.1 product/architecture review](../discovery/evidence/m0-product-architecture-review-2026-08-22.md)
- [Harness capability evidence](../discovery/evidence/harness-cli-capabilities-a.md)
- [Architecture direction](../discovery/architecture-options.md)
- [Historical PoC proposal](../discovery/minimal-poc-plan.md) — input only,
  not inherited scheduling
- [Product requirements](../discovery/product-intent.md)

Volatile primary sources rechecked 2026-08-23:

- [Node.js release status](https://nodejs.org/en/about/previous-releases)
- [Claude Code environment variables and auth precedence](https://code.claude.com/docs/en/env-vars)
- [Claude Code authentication](https://code.claude.com/docs/en/authentication)
- [Anthropic's paused Agent SDK/`claude -p` credit change](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan)
- [Codex configuration reference](https://developers.openai.com/codex/config-reference)
- [Grok Build repository](https://github.com/xai-org/grok-build)
