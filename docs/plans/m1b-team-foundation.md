# AgentTeam M1b team-foundation plan — draft r1

- Status: **draft r1, proposed 2026-08-24 — NOT approved.** r1 expands the
  r0 skeleton (committed at `856d525`, the M1a G8 naming deliverable) into a
  full plan — contracts, gates, test matrix, budget, stop rules — per the r0
  approval checklist. Implementation starts only after this plan is
  independently reviewed and approved as a `DECISIONS.md` entry naming this
  file and its commit SHA (the M1a §21 convention; ADR 0021 precedent; the
  status line flips to `approved` in the following commit because a commit
  cannot name its own SHA). Per M1a plan §18, nothing here begins in the
  M1a approval scope.
- Revision baseline: r0 was `856d525`
  (`docs(plans): draft M1b team foundation (proposed; G8 naming
  deliverable)`). The independent review reads the tree at the commit
  carrying this r1 text, per the `3407ec9`/`317bb52` review precedent
  (immutable dated record in `docs/reviews/`, findings valid for that SHA
  only).
- Prerequisites carried in: the G4-qualified ClawTeam seam
  (`docs/evidence/clawteam-qualification-2026-08-23.md`), ADR 0015 (exact
  pin, extra-only, subprocess backend never used), ADR 0018 (measurement
  decides), ADR 0037 (build-vs-reuse reaffirmed post-G6).
- Sections marked **[finalize-at-approval]** carry proposed wording the
  owner finalizes at approval; every such item is listed once in section 20.

## 1. Outcome and milestone boundary

TeamTemplates composed of portable Assistant definitions execute as fresh
TeamRuns over an optional coordination substrate behind the
`CoordinationSubstrate` seam; declared vs achieved enforcement is recorded
honestly. Harness launching stays exclusively on the M1a built-in direct
runner — no coordination provider ever launches a harness. This is the
first half of the PROJECT.md M1b–M2 criterion; hidden ephemeral members
belong to M1c (PoC B) and nested TeamRuns plus the MCP server to M2
(M1a plan §19).

M1b is done when:

1. the team contracts of section 6 are versioned JSON Schemas beside the
   nine V1 schemas, with the run record extended — never duplicated;
2. a committed three-Member TeamTemplate executes as a fresh TeamRun
   through the `atm` CLI on the deterministic tier (fake harnesses, local
   deterministic provider) with the section 13 lifecycle evidence green on
   every core CI leg;
3. the same lifecycle passes over the optional ClawTeam provider on the
   three-OS extra job, inside the qualified seam's containments;
4. the ClawTeam exit-criterion measurement of section 10 is recorded; and
5. zero live model calls were made — M1b's evidence is deterministic by
   charter (section 11), and M1a's remaining live-call ledger is untouched.

A direct run remains the one-Member case of a TeamRun, recorded with the
same record family (glossary "Run / direct run"); every direct-mode
behavior, record, and test of M1a continues to pass unchanged.

## 2. Product and architecture decisions

1. **Provider order** (ADR 0018 decision 2; reaffirmed ADR 0037): the
   product-owned **local deterministic coordination provider comes first**
   — file task store, file mailbox, snapshot — and drives every
   deterministic test and hosted CI leg. The optional ClawTeam provider
   comes second, behind the G4-qualified seam.
2. **A coordination provider never launches a harness.** Harness execution
   stays on the M1a direct runner and its process contract (M1a §9). A
   provider coordinates spaces, members, tasks, messages, and snapshots —
   nothing else. ClawTeam's `SubprocessBackend`, tmux, wsh, template
   launcher, keepalive, and CLI chain remain unused (ADR 0015).
3. **One record kind for runs.** `RunRecordV1` is extended with team-mode
   coordination fields (section 6); no `team-run-v1` schema file and no
   second run record kind exist (M1a §7; glossary "TeamRun"). A direct-mode
   `run.json` stays valid byte-for-byte.
4. **ClawTeam stays optional, extra-only, exactly pinned** to
   `0.3.0 @ 01198332ef9270c32c5460b8a178f964fc0df451` with `mcp>=1,<2`;
   every `clawteam` import stays confined to the one owned compatibility
   module `src/agentteam/compat/clawteam.py` (ADR 0015). The new provider
   module of section 9.2 imports that seam, never `clawteam` itself.
5. **Isolation claims stay honest.** The achieved isolation claim for the
   ClawTeam provider is `namespace` only; the local provider records
   `data-dir` (its space is a per-run directory). `independence
   {declared, achieved}` is recorded per run and never upgraded
   (PROJECT.md enforcement-honesty constraint; glossary).
6. **The ClawTeam exit criterion finalizes at approval and is decided
   before PoC B** (section 10; ADR 0018/0037/0038; the open QUESTIONS
   item). Its measurement is a gate of this plan (G6).
7. **Zero live calls in M1b** (section 11). Live team execution begins
   with M1c PoC B under its own owner-approved ceiling.
8. **All ClawTeam-specific code lives inside the measurement boundary** —
   `src/agentteam/compat/` plus `src/agentteam/coordination/clawteam.py`
   (section 10). ClawTeam-conditional code anywhere else violates a stop
   rule; this keeps the exit-criterion numerator honest.
9. **The CLI keeps one execution entry.** `atm run` accepts the new
   `team-run-request` kind; the only new verb is `atm team validate`
   (section 7) **[finalize-at-approval]**.
10. **Approval convention**: owner approval of this plan is a DECISIONS
    entry naming this file and the commit SHA of the approved text,
    recorded after the independent review and before any product source
    work (G0); the status line flips in the following commit.

## 3. Delivery sequence and gates

Implementation follows these gates in order. A failed gate stops the later
work named in its stop rule. Each closed gate writes a `VERIFY.md` entry
headed `## M1b G<n> <name> — <date>` with a `| Check | Result |` table in
the house format (commands, commit SHAs, CI run IDs).

| Gate | Work | Evidence required |
| --- | --- | --- |
| G0 | Approve this plan | Independent review recorded in `docs/reviews/` for the frozen r1 SHA; findings resolved (revision r2 if needed); owner approval as a DECISIONS entry naming this file and the approved commit SHA, committed before product source work; status flips to `approved` in the following commit |
| G1 | Team contracts and schemas | `TeamTemplateV1` and `TeamRunRequestV1` models land with `team-template-v1.schema.json` and `team-run-request-v1.schema.json` checked in; `run-record-v1.schema.json` regenerated with the team-mode extension; both new kinds registered in `SCHEMA_MODELS` with `minimal_payloads()` entries; `uv run python -m agentteam.schema check` green (no missing/stale/orphan file); the entire pre-M1b core suite passes unchanged (direct-mode regression); `atm team validate` passes on the committed example template |
| G2 | CoordinationSubstrate protocol and local provider | `coordination/protocol.py` and `coordination/local.py` land; the shared provider-conformance suite (section 14) is green over the local provider — space/member lifecycle, dependency auto-unblock, cycle rejection, send/receive claim semantics, snapshot round-trip, cleanup, and two-space no-crossover; the suite runs on the six-leg core CI job |
| G3 | Team runner integration | `atm run` executes the committed `team-run-request` end to end on fake harnesses over the local provider: instantiate → run → archive per section 11; `--render-only` writes every member's rendered invocation without launching; the roster lives in the run record with `tasks[].substrate_id` mapping recorded; direct-mode runs and records remain byte-compatible |
| G4 | Deterministic team-lifecycle acceptance | The section 13 acceptance is green through the CLI on all six core legs (3 OS × Python 3.11/3.13); every mechanical condition of section 13 is asserted by tests; no vendor executable is invoked anywhere in the job (fakes only) |
| G5 | ClawTeam provider parity | `coordination/clawteam.py` lands behind the extra; the same conformance suite plus the section 13 lifecycle pass over the ClawTeam provider on the three-OS `clawteam` job; containment tests hold (event-bus reset, one process-scoped data root, opaque `atm-<hex8>` namespaces, owner `~/.clawteam` refused, no subprocess/tmux import); the caveat behaviors are pinned by tests (run layer stops its own processes before provider cleanup; roster reconciliation across the two rosters); the whole directory skips cleanly without the extra on the core legs |
| G6 | Exit-criterion measurement | The pinned section 10 command is run and recorded in VERIFY: numerator and denominator LOC, the ratio against 1.5×, and test LOC reported as context; the accept/drop decision packet for the owner is prepared — the decision itself is taken by the owner before PoC B, not at this gate |
| G7 | M1b close | VERIFY entries current for G1–G6; PLAN.md gate rows closed with SHAs/run IDs; live-call ledger unchanged (5 of the M1a 30-call ceiling remain, zero spent in M1b); the M1c PoC B draft r0 is proposed-not-approved, naming its live budget ask and the exit-criterion decision status; M1c remains separately planned |

Cross-cutting stop rule: a ClawTeam-provider failure at G5 never alters
local-provider evidence and never blocks G7 on the local path — it blocks
describing ClawTeam as a qualified provider and routes to the section 10
decision (do not silently fork, vendor, or make it mandatory — M1a §18). A
local-provider failure at G2–G4 blocks everything after it; there is no
ClawTeam fallback path, because the local provider is the product path
(ADR 0018).

## 4. Runtime and dependency baseline (delta to M1a §5)

M1a §5 stands unchanged: Python `>=3.11`, Hatchling, `uv` with committed
lock, `src/agentteam/` layout, version `0.1.0a0`, no publication.

M1b deltas:

- **No new runtime dependency is expected.** The local provider uses the
  standard library (file operations, JSON) plus the already-present
  Pydantic models. Adding any dependency requires a documented reason
  (M1a §5 rule).
- The `clawteam` extra is unchanged: exact pin
  `01198332ef9270c32c5460b8a178f964fc0df451` + `mcp>=1,<2`, installed only
  via `uv sync --frozen --all-groups --extra clawteam`, never on core legs.
- No version bump, wheel, sdist, or release decision is part of M1b.

## 5. Repository layout (delta to M1a §6)

New paths only; everything in M1a §6 stays where it is.

```text
src/agentteam/
  coordination/
    __init__.py        # provider registry: local always, clawteam if importable
    protocol.py        # CoordinationSubstrate Protocol, op types, error taxonomy
    local.py           # LocalCoordinationProvider (file task store, mailbox, snapshot)
    clawteam.py        # ClawTeamCoordinationProvider (imports agentteam.compat.clawteam only)
  domain/team.py       # TeamTemplateV1, TeamRunRequestV1 (+ embedded sub-models)
  commands/team.py     # `atm team validate`
schemas/
  team-template-v1.schema.json
  team-run-request-v1.schema.json
  run-record-v1.schema.json          # regenerated with the team-mode extension
examples/
  teams/development.yaml             # the committed three-Member template (section 13)
  run-requests/team-review.yaml      # the committed team-run request
tests/
  coordination_suite.py              # shared conformance base (not test_-prefixed)
  unit/test_team_template.py
  unit/test_team_selection.py
  integration/test_coordination_local.py
  integration/test_team_run_execute.py
  compatibility/test_clawteam_provider.py
  acceptance/test_team_lifecycle.py
```

Naming rationale (this plan is the G8 naming deliverable's continuation):
the package is `coordination/` because the seam is named
`CoordinationSubstrate` and the source tree uses singular functional nouns
(`domain`, `harness`, `run`, `resolution`); `team` stays the domain concept
(`domain/team.py`) and the reserved selection layer
(`resolution/selection.py`), not a package. `MemberV1` content stays
embedded in the run record exactly as `MemberRecordV1` is today — no
standalone member schema file. Exactly two new schema files exist; the
run-record file is regenerated, not duplicated. Existing modules amended in
place: `domain/run.py` (team-mode fields; the two reserved markers),
`resolution/selection.py` (the reserved `team` layer),
`run/` (team lifecycle beside the direct state machine),
`commands/run.py` (kind dispatch).

### 5.1 Run-state layout (delta to M1a §6.1)

`~/.agentteam/` is unchanged. Inside a run directory, a team-mode run adds
one `coordination/` subtree — the local provider's space (task store,
inboxes, events, snapshots) lives there, so the run archive inherently
contains the coordination half and inherits the owner-only permission
sweep and the SHA-256 manifest. The ClawTeam provider fixes its one
process-scoped data root under the run's local state, uses an opaque
`atm-<hex8>` namespace, and its snapshot is copied into the archive before
the mutable space is removed (stop-before-cleanup, section 11). Nothing
under `~/.agentteam/` is ever committed.

## 6. Data contracts **[finalize-at-approval: optional/reserved field sets]**

The M1a §7 rules hold for every new record: closed objects
(`additionalProperties: false`), `schema_version: 1`, a fixed `kind`,
canonical snake_case JSON, YAML or JSON accepted for human-authored inputs,
unknown fields fail validation. Field lists below are the contract at plan
altitude — names and invariants, not JSON blobs; exact optional/reserved
sets finalize at approval (section 20).

**`TeamTemplateV1`** (`kind: team-template`; human-authored; the portable,
persistent composition — TC-01..TC-06 of
`docs/discovery/team-execution-model.md` §2):

- `id`, `version`, `summary` — stable identity; content-addressed by the
  same package/file hashing discipline as Assistant packages.
- `members[]` — **by reference** (TC-01): `{name, assistant: <path ref>,
  relationships?, visibility?}`. Multiple members may reference the same
  Assistant package; the reference is resolved and hashed per member at
  instantiation.
- `lead` — the coordinating Member's name (TC-02).
- `handoff` — `{required_fields[], acks[]}` vocabulary (TC-02 conventions;
  data consumed by Members, transported by the substrate).
- `independence[]` — `{between: [a, b], declared: advisory | mechanical,
  means[]}` (TC-03). Declaring `mechanical` fails closed in M1b: no
  provider or run-layer enforcement of the message-edge rule exists yet
  (that is M1c+ evidence), so the committed example declares `advisory`.
- `visibility_defaults` — `{persistent_members, dynamic_members}` (TC-04);
  in M1b every member is persistent and the dynamic default is dormant
  data.
- `preferences` — team-level, project-independent (TC-06):
  `harness_preferences` per member name (data; precedence in section 7 of
  this plan and M1a §11) and `run_defaults`.
- `workflow_skeleton[]` — `{subject, owner, blocked_by[]}` task shapes
  with placeholders; a shape, never a project's task list.
- **Reserved-empty in M1b**: `dynamic_members` (M1c; must be absent or
  empty — a request that needs it fails closed, exit 2) and `constraints`
  (the HB-03 team-constraint concept; section 20 carries the owner
  options) **[finalize-at-approval]**.
- **Must NOT contain** (TC-06/AD-05; schema- and validator-enforced where
  expressible, `--strict-content`-checked otherwise): repo/paths/branches,
  workspace directories, a project's concrete tasks, harness session ids,
  Surface bindings, runtime agent ids, credentials or environment values,
  run results, ephemeral member definitions.

**`TeamRunRequestV1`** (`kind: team-run-request`; human-authored; the
team-mode sibling of `RunRequestV1`): `template` (path), reserved
`overlay_refs: []` (M3, must stay empty — R15 is not foreclosed),
`workspace`, `task_file`, per-member `harness_overrides` (user layer),
optional per-member model/effort overrides, `substrate: local | clawteam`
(default `local`), visibility overrides, `output_dir`, evidence settings,
and timeout/retry settings that may lower but never raise the M1a §9 caps.
Runtime ids, timestamps, and results never appear in a request.

**`RunRecordV1` team-mode extension** (`kind: run-record` — the same
record kind and file, regenerated): `mode` gains `team`. A direct-mode
record is unchanged field-for-field (the one-Member subset). A team-mode
record carries:

- `template {ref, hash}` — the resolved TeamTemplate identity;
- `members[]` — the full roster; each entry is today's `MemberRecordV1`
  (`name`, `assistant` ref + package hash, per-member
  `effective_definition_hash`, `execution {kind: invocation | ensemble,
  ref}` — one execution at a time, M1a §7) extended with
  `origin: persistent` (M1c adds `ephemeral`), `visibility: visible |
  hidden`, and the member's recorded harness selection;
- `substrate {kind: local | clawteam, namespace}`;
- `tasks[]` — run-level task rows `{id, subject, status, owner,
  blocked_by[], substrate_id}`; run-level ids map to provider ids via
  `substrate_id` (team-execution-model §8);
- `independence {declared, achieved}` — declared from the template,
  achieved recorded honestly per run (`namespace` for ClawTeam, `data-dir`
  for the local provider), never upgraded;
- `events` — reference to the run's append-only event log (existing
  `events.jsonl` mechanism), which gains run-level team events
  (member added, task created/unblocked/completed, message sent, snapshot
  taken);
- **Reserved for M2** (must be absent/null/empty in M1b, validator
  enforced): `parent`, `depth`, `nested_runs[]`.

Model validators pin the mode split: direct mode requires `member` and
forbids the team fields; team mode requires `template`, `members[]`
(length ≥ 2), and `substrate`, and forbids `member`. `RunRequestV1`,
`HarnessInvocationV1`, `EnsembleRecordV1`, `BundleManifestV1`, and both
vendor-facing schemas are unchanged.

**`CoordinationSubstrate`** is a typed Python protocol (section 8), not an
external record; its operations are the glossary's create-space / member /
task / wait / message / snapshot / stop / cleanup surface. Provider
identity and achieved isolation travel inside the run record
(`substrate`, `independence.achieved`), so no new schema file is needed
for it.

## 7. Public CLI contract (delta to M1a §8) **[finalize-at-approval: verb set]**

```text
atm run [<request.yaml|request.json>] [...]   # unchanged flags; the file's
                                              # kind discriminates:
                                              # run-request | team-run-request
atm team validate <template> [--json]         # the one new verb
```

- `atm run` stays the single execution entry. A `team-run-request` file
  routes to the team lifecycle of section 11; every existing flag keeps
  its meaning where applicable, and `--render-only` writes every member's
  rendered invocation without launching anything. This preserves "a direct
  run is the one-Member case of a TeamRun" at the CLI layer and avoids a
  second execution verb with its own precedence semantics. `atm team run`
  is explicitly rejected (the M1a r2 merge already rejected extra CLI
  verbs once; §22 "Not adopted").
- `atm team validate` mirrors `atm assistant validate`: schema + reference
  + prohibited-content validation of a TeamTemplate package, `--json`
  includes the template hash. Rationale: authoring and CI need a cheap
  validation path that never touches a provider. Recorded fallback if the
  review objects to any new verb: fold template validation into
  `atm run --render-only`, which must validate the template transitively
  anyway.
- Exit codes are unchanged: `0` success, `1` runtime/harness failure, `2`
  invalid/unsafe input (including a request whose reserved fields are
  non-empty), `3` semantic acceptance failure, `130` cancellation.
- The AGENTS.md managed command table needs no row change in M1b planning
  or implementation (`Test` stays `uv run pytest`; there is no M1b live
  row). Any later table change follows the shown-diff approval convention
  (ADR 0023/0025 precedent).

Selection precedence (delta to M1a §11): the reserved `team` layer becomes
real. Preference order is **user > Assistant > team > default** — a
member's user-level override (request `harness_overrides` / CLI) wins,
then the member Assistant's `harness_policy` preference, then the
template's `preferences.harness_preferences[member]`, then the profile
default; `selection.decided_by` gains `team` and records the deciding
layer per invocation. Hard eligibility stays exactly M1a §11 steps 1–3:
candidates, forbidden-removal, fail-closed user requests. Whether a
team-level *constraint* (e.g. reviewer ≠ implementer harness) may bind
above an Assistant preference is the open HB-03 question — section 20
carries the owner options; until it is answered, `constraints` stays a
reserved-empty template field and no constraint semantics ship
**[finalize-at-approval]**. `DecidedBy`'s "forced variants" stay reserved
(no force mode ships in M1b). The register (v3.4) amendment remains a
docs-only follow-up after the owner answers, outside this plan's commits.

## 8. Python interfaces: the CoordinationSubstrate protocol

The second declared seam (glossary; ADR 0007/0014) becomes a typed
synchronous `Protocol` in `coordination/protocol.py`. Its shape follows
the de-facto surface the qualified seam already exposes
(`ClawTeamCompat`), generalized and made provider-neutral:

- lifecycle: `create_space() -> space_id`, `add_member(space, name)`,
  `members(space)`, `cleanup(space)`;
- tasks: `create_task(space, subject, *, blocked_by)`, `task(space, id)`,
  `tasks(space)`, `update_task(space, id, status, *, caller)` — dependency
  ids validated and cycles rejected provider-neutrally before the provider
  is called (team-execution-model §8);
- wait: a bounded, deterministic poll helper over `tasks()` with an
  explicit timeout — a protocol-level default implementation, not a
  provider thread;
- messages: `send(space, sender, recipient, body)`,
  `receive(space, recipient, *, limit)` — claim consumes; addressing is
  bounded to the run's roster by the run layer before delivery;
- snapshots: `snapshot(space, tag)`, `read_snapshot(space, id)`,
  `restore(space, id)`;
- identity: `info()` — provider kind, version/revision, achieved isolation
  level.

Glossary-mapping note: the glossary's `stop` operation is deliberately
**not** a provider method. Stopping processes is the run layer's job — it
stops its own harness invocations (M1a §9 process contract) **before**
calling provider `cleanup`, because provider cleanup never stops processes
(a recorded ClawTeam caveat, section 10). The protocol therefore has no
process operations at all, which is what makes decision 2 of section 2
structurally true.

Error taxonomy: `CoordinationError` (base), `SpaceUnavailableError`,
`TaskCycleError`, `UnknownRecipientError`, provider-specific unavailability
(`ClawTeamUnavailableError` passes through untranslated only inside the
provider module). Every error path maps to exit `1` (runtime) or `2`
(invalid input) per the M1a table.

Run-layer boundary rules (team-execution-model §8, §9): the run layer owns
the roster — substrate membership is a projection of it; run-level task
ids map to provider ids via `substrate_id`; message addressing outside the
roster is refused before the provider sees it; run-level events (member
added, task transition, message, snapshot) are appended to the run's event
log by the run layer, never inferred from provider internals; the
AgentTeam process runner supplies output and exit status independently of
any provider.

## 9. Coordination providers

### 9.1 Local deterministic provider (`coordination/local.py`, first)

Product-owned, stdlib-only, and the substrate for every deterministic test
and CI leg (ADR 0018 decision 2):

- **File task store**: JSON task rows under the space directory; explicit
  `blocked_by[]`; completing the last blocker auto-unblocks a task
  (`blocked → pending`); dependency cycles rejected at creation; status
  transitions validated; a deterministic id scheme (`t-<seq>`).
- **File mailbox**: per-recipient directories; `send` writes one message
  file; `receive` claims and consumes atomically (a second receive is
  empty); ordering is deterministic (sequence-numbered file names, never
  wall-clock-dependent ordering).
- **Snapshot**: one JSON bundle of the space (members, tasks, messages,
  events) written atomically; `read_snapshot` and `restore` round-trip it.
- **Space**: a directory under the run's `coordination/` subtree
  (section 5.1) — one space per run, so achieved isolation is recorded as
  `data-dir`; two spaces never share files by construction.
- **Determinism guarantees** (asserted by tests): no wall-clock coupling
  in observable ordering, atomic writes (write-then-rename), identical
  behavior on the three OSes, and no background threads.

### 9.2 Optional ClawTeam provider (`coordination/clawteam.py`, second)

A thin adapter from the protocol onto the qualified seam — it imports
`agentteam.compat.clawteam` and nothing from `clawteam` directly, so the
one-module import confinement of ADR 0015 is preserved verbatim. The six
G4 containments carry forward unchanged (extra-only import; one fixed
process data root with the owner's `~/.clawteam` refused; opaque
`atm-<hex8>` names and explicit file primitives; event bus replaced and
hook loader disarmed before any operation; no subprocess/tmux/wsh/template
launcher/keepalive/CLI chain; version/revision/isolation recorded via
`info()`).

The qualification report's recorded caveats stand and are restated here
because the exit criterion requires them accepted in writing (verbatim
from `docs/evidence/clawteam-qualification-2026-08-23.md`): "two rosters
(ClawTeam's own member list vs any layer view), no parent link for nested
teams, cleanup does not stop processes, and every containment above is
caller-written code, not configuration." The provider pins the first and
third behaviorally: roster reconciliation is tested (the run record roster
is authoritative; the provider's member list is a projection checked for
parity), and the run layer's stop-before-cleanup ordering is tested.
"No parent link" is dormant in M1b (nesting is M2) but recorded now.

## 10. ClawTeam exit criterion and measurement rule **[finalize-at-approval]**

The r0 draft wording, carried verbatim (proposed by the 2026-08-23 review
R2/R13 via the open QUESTIONS item and the G4 feed-forward paragraph):

> The ClawTeam provider remains a supported substrate only if the provider
> glue plus its workarounds measure **≤ 1.5× the local deterministic
> provider's LOC** (measured as in the G4 qualification report — the seam's
> 233 LOC / 281 test-LOC baseline), **and** the recorded caveats — two
> rosters, no parent link for nested teams, cleanup never stops processes,
> every containment is caller-written code — are **accepted in writing**.
> Otherwise the local deterministic provider becomes the product path and
> ClawTeam support is dropped without replacement.

r1 pins the measurement rule the r0 parenthetical left open — what counts
as "provider glue plus its workarounds" now that the local provider will
exist. Proposed rule, finalized at approval:

- **Metric**: physical lines by `wc -l` over `*.py` files — exactly the
  G4 qualification method, which reproduces the 233/281 baseline.
- **Numerator** (ClawTeam side): production code that exists only because
  ClawTeam is supported — `src/agentteam/compat/` plus
  `src/agentteam/coordination/clawteam.py`.
- **Denominator** (local side): `src/agentteam/coordination/local.py` —
  production code that exists only to implement the local provider.
- **Excluded from both sides**: the shared seam and contracts
  (`coordination/protocol.py`, `coordination/__init__.py`,
  `domain/team.py`), which exist regardless of provider count.
- **Test LOC**: excluded from the ratio on both sides and reported
  alongside as context (ClawTeam: `tests/compatibility/`; local:
  `tests/integration/test_coordination_local.py`). Rationale: test volume
  measures assurance appetite, not integration burden; counting it would
  penalize writing tests.
- One-sentence form: **count what you would delete if you dropped that
  provider — production code only, the shared seam excluded on both
  sides.**
- Pinned command, recorded verbatim in the G6 VERIFY entry:

  ```text
  find src/agentteam/compat src/agentteam/coordination/clawteam.py -name '*.py' -exec cat {} + | wc -l
  cat src/agentteam/coordination/local.py | wc -l
  ```

- **Anti-gaming boundary**: section 2 decision 8 (all ClawTeam-specific
  code confined to the two numerator packages) is a stop rule, so the
  numerator cannot shrink by relocating glue into the run layer.

Timeline: the criterion's wording finalizes at this plan's approval (G0);
the measurement is recorded at G6; the accept/drop **decision** is the
owner's, taken before PoC B starts (normally at M1c plan approval, as a
DECISIONS entry that either accepts the four caveats in writing with the
recorded ratio, or drops ClawTeam support without replacement). Until that
decision, ClawTeam remains "optional and qualified", never "the product
path".

## 11. Team-run lifecycle and budget

The team-mode lifecycle (team-execution-model §3, trimmed to M1b scope;
numbered like the M1a §12 state machine):

1. Validate the profile set, the TeamTemplate (`atm team validate`
   semantics), and the TeamRunRequest; reserved fields (`overlay_refs`,
   `dynamic_members`, `constraints`, `parent`/`depth`/`nested_runs`) must
   be empty; a request needing M1c/M2 behavior fails closed (exit 2)
   before any side effect.
2. Resolve each member's Assistant package independently; build one
   immutable bundle and canonical hash per member; record per-member
   `effective_definition_hash`.
3. Resolve harness selection per member (user > Assistant > team >
   default; `decided_by` recorded per invocation; hard eligibility per
   M1a §11).
4. Create the pending team-mode `run.json` (full roster, template ref +
   hash, declared independence) **before** the coordination space exists
   and before any process starts.
5. Materialize one isolated workspace per member (the M1a per-leg copy
   mechanism); target hashes detect mutation.
6. Create the provider space, register the roster projection, and create
   tasks from `workflow_skeleton` through the `CoordinationSubstrate`
   protocol; record `tasks[].substrate_id` and the achieved isolation
   level.
7. Render and launch member invocations through the direct runner only
   (Lead first), fresh sessions, no provider involvement in process
   management; in M1b's deterministic tier the run layer drives task
   transitions and handoff messages mechanically (member-driven
   choreography is M1c's live question — R12).
8. Enforce the M1a retry discipline unchanged (one transient same-harness
   retry; never substitute a harness).
9. Complete tasks; verify dependency auto-unblock; deliver
   roster-addressed messages; take the final snapshot.
10. Stop all AgentTeam-owned processes, snapshot the provider space into
    the archive, then provider `cleanup` (stop-before-cleanup, always in
    that order).
11. Re-hash every member bundle (mutation check), finalize the archive
    (manifest, owner-only modes), write the terminal record, and return
    the stable exit code.

**Budget.** M1b's evidence is deterministic by charter (section 1): the
providers are file-operation coordination with no model involvement, and
member invocations in every M1b test and CI leg run on the committed fake
harnesses. Therefore **the M1b live-call budget is zero**. A "call" keeps
its M1a §7 definition (one CLI invocation of a vendor harness). Any live
call inside M1b scope is a stop-rule violation (section 17); a felt need
for live de-risking routes to the M1c plan, which sets its own
owner-approved ceiling. M1a's remaining ledger (5 of the 30-call ceiling,
ADR 0038) stays reserved for future individual owner decisions and is not
an M1b allowance. **[finalize-at-approval]**

## 12. Evidence and privacy (delta to M1a §13)

M1a §13 stands: gitignored local run state, owner-only permissions, typed
argv placeholders, environment names only, no automatic git add or upload.

M1b deltas: the coordination state (task store, inboxes, events, snapshot)
lives inside the run directory and is covered by the same permission sweep
and SHA-256 manifest; the R34 exec-bit caveat is inherited unchanged (the
G6.R3 flattening contract binds until the owner revises it — revisit
before any workspace or Skill ships an executable). **No new evidence
class exists**: M1b's milestone evidence is CI logs plus committed
deterministic fixtures, so no sanitized evidence bundle and no promotion
step is needed. Task and message fixtures are authored content and must
contain no secrets, no absolute paths, and no owner-machine facts.

## 13. Deterministic team-lifecycle acceptance

The milestone evidence (G4), run through the CLI on every core leg:

- **Fixture**: `examples/teams/development.yaml` — three Members
  (`lead`, `implementer`, `reviewer`) with `lead: lead`, a `reviews`
  relationship, `advisory` declared independence between reviewer and
  implementer, per-member team harness preferences, and a three-task
  `workflow_skeleton` (plan → implement blocked-by plan → review
  blocked-by implement). Members reference the existing example
  `code-reviewer` Assistant package by relative path — multiple members
  referencing one Assistant is legal (TC-01), keeps the pinned
  example-package hash surface untouched, and is sufficient because M1b's
  claim is mechanical lifecycle, not distinct role content (that is M1c).
  `examples/run-requests/team-review.yaml` runs it against the committed
  `fixtures/review-target` workspace on the fake harnesses
  (`examples/profiles/ci-fake.yaml`).
- **Mechanical conditions**, each asserted by a test:
  1. roster parity — `run.json members[]`, the provider's member list, and
     the template roster agree; the run-record roster is authoritative;
  2. DAG closure — all skeleton tasks reach a terminal status; the
     blocked task unblocked exactly when its blocker completed; cycles
     rejected at creation;
  3. messages bounded to the run — handoff messages deliver only between
     roster names; an out-of-roster recipient is refused before the
     provider sees it;
  4. snapshot round-trip — the final snapshot is in the archive and
     `read_snapshot`/`restore` reproduce the space;
  5. per-member records — every member carries its own
     `effective_definition_hash`, its `decided_by` (including `team` where
     the template preference decided), and one execution binding;
  6. terminal `run.json` with `independence {declared, achieved}` recorded
     honestly (`advisory`/`data-dir` local; `advisory`/`namespace`
     ClawTeam);
  7. mutation check — every member bundle re-hashes identically;
  8. direct-run regression — the M1a deterministic acceptance
     (`direct-review.yaml`) still passes in the same job, unchanged.
- **Multi-step shapes on purpose**: the R33 lesson (probes are single-turn
  and cannot see multi-turn failure classes) applies to team lifecycles
  too — the skeleton exercises sequential dependent tasks with handoffs,
  not one degenerate task. The R12 mitigation is structural: protocol
  state lives in the task DAG and structured records, never in prose
  parsed from member output.
- **Zero live calls**: no vendor executable is invoked anywhere in the
  acceptance path; the fakes are launched through the same process runner
  as real harnesses (M1a §15 discipline).

## 14. Deterministic test plan

Normal tests never invoke a vendor model (M1a §15 rule; unchanged local
verification block, including `uv run python -m agentteam.schema check`).

- **Schema parity**: `minimal_payloads()` in `tests/conftest.py` gains
  `team-template-v1.schema.json` and `team-run-request-v1.schema.json`
  entries plus a team-mode `run-record` payload; the existing data-driven
  parity test then covers all eleven schema files and the orphan check
  covers the directory.
- **Unit**: `test_team_template.py` — TC-01..06 field validation, the
  must-NOT-contain prohibitions, reserved-empty enforcement
  (`dynamic_members`, `constraints`), template hashing;
  `test_team_selection.py` — the four-layer precedence (user > Assistant
  > team > default), `decided_by: team`, fail-closed user requests
  unchanged, forced variants still rejected; run-record mode-split
  validators (direct forbids team fields; team requires roster ≥ 2 and
  forbids `member`; reserved M2 fields must be empty).
- **Provider conformance** (`tests/coordination_suite.py`, a shared base
  class that is not collected directly): space/member lifecycle; task
  create/get/list/update; dependency auto-unblock; cycle rejection; task
  status validation; mailbox send/receive claim semantics (second receive
  empty); deterministic ordering; snapshot create/read/restore round-trip;
  cleanup scoped to the space; two spaces with no task/message crossover;
  `info()` identity. The suite is instantiated twice:
  `tests/integration/test_coordination_local.py` (core, six legs) and
  `tests/compatibility/test_clawteam_provider.py` (extra-only, three
  legs) — mirroring the M1a G4 qualification scenarios so the two
  providers are held to one standard.
- **Integration**: `test_team_run_execute.py` — the section 11 lifecycle
  over the local provider with fake harnesses: pending-before-side-effect,
  per-member workspaces, render-all-before-launch, stop-before-cleanup
  ordering, archive finalization, `--render-only`, exit codes, reserved
  fields fail closed.
- **Acceptance**: `test_team_lifecycle.py` — the section 13 conditions
  end-to-end through the CLI.
- **Compatibility**: the ClawTeam provider suite stays in
  `tests/compatibility/` with the existing `importorskip` conftest and the
  owner-state guard, so the six core legs keep proving clean skip without
  the extra. No new pytest marker is introduced (`--strict-markers`; the
  split stays directory + CI-job based).
- **Cross-platform**: the local provider's file semantics (atomic rename,
  ordering, permissions) run on all three OSes on the core job; any
  Windows/macOS deviation is fixed, never skip-listed silently (M1a §18
  discipline).

## 15. CI (delta to M1a §16)

No new jobs; the 12-job shape holds:

- **scaffold** (3 OS × Python 3.11/3.13, six legs): gains the local
  provider conformance suite, the team unit/integration tests, the
  section 13 team acceptance through the CLI on fakes, and `atm team
  validate` on the committed template — alongside everything it already
  runs (schema check/reproduction, direct acceptance, example-package
  hash identity).
- **clawteam** (3 OS × Python 3.11, three legs): gains the ClawTeam
  provider conformance + lifecycle tests beside the existing 12
  qualification scenarios.
- **vendor-smoke** (3 OS): untouched — it proves credential-free vendor
  launcher plumbing, which M1b does not change; treat a red as dated
  capability evidence per the standing note.

CI still has no vendor login, model call, API key, or secret; passing
proves deterministic plumbing and optional-provider coordination only
(PROJECT.md cross-platform constraint).

## 16. Commit boundaries during product implementation

Numbered Conventional-Commit subjects (M1a §17 style; steward state
travels with its semantic change; every push separately approved;
`never_push` remains in force):

1. `feat(domain): add team-template and team-run-request contracts; extend the run record with team mode`
2. `feat(coordination): add the CoordinationSubstrate protocol and the local deterministic provider`
3. `feat(run): execute team-run requests over the coordination seam`
4. `test(poc): add deterministic team-lifecycle acceptance`
5. `feat(coordination): add the optional ClawTeam provider behind the qualified seam`
6. `docs(steward): record the M1b exit-criterion measurement (G6)`
7. `docs(steward): close M1b; propose the M1c PoC B draft`

CI workflow growth (additions to existing jobs) lands with commits 2, 4,
and 5. Commit order inside G1–G3 may interleave where a contract detail is
discovered during runner work; gate closure order never changes.

## 17. Stop rules

- **Any live model call inside M1b scope is a stop-rule violation.** Live
  team execution begins with M1c PoC B under its own owner-approved
  ceiling; M1a's remaining 5-of-30 ledger is not an M1b allowance.
- A coordination provider must never launch, supervise, or stop a harness
  process; stop if any provider change would require it — harness
  execution stays on the direct runner (section 2 decision 2).
- Stop if team-mode work would break a direct-mode record, test, CLI
  behavior, or schema — the one-Member subset stays byte-compatible
  (section 2 decision 3).
- ClawTeam-conditional code outside `src/agentteam/compat/` plus
  `src/agentteam/coordination/clawteam.py` is a violation (the section 10
  measurement boundary).
- A ClawTeam provider failure blocks describing ClawTeam as qualified and
  blocks G5; it never blocks the local path; do not silently fork, vendor,
  or make it mandatory (M1a §18, carried).
- Stop on any run-time mutation of a portable Assistant package or
  TeamTemplate; the mutation check covers every member bundle and the
  template.
- Always stop AgentTeam-owned processes before provider `cleanup`;
  provider cleanup never stops processes (recorded caveat; section 8).
- No dynamic member creation, no nested runs, no MCP, no overlays:
  requests or templates carrying them fail closed (exit 2); reserved
  fields stay empty (sections 6, 19).
- Never upgrade `independence.achieved`; record honestly; a template
  declaring `mechanical` fails closed in M1b (no enforcement evidence
  exists yet).
- After two consecutive failed attempts to make the ClawTeam provider pass
  a conformance scenario without violating a containment, stop adding
  workarounds and route to the section 10 decision.
- If output exposes a secret, keep it local, rotate outside AgentTeam, and
  do not commit/upload it (M1a §18, carried).
- G7 ends M1b. Do not begin M1c in the same approval scope.

Falsification routing (observation → what it falsifies → destination):

- The local provider cannot satisfy a protocol operation deterministically
  → the section 8 operation spec is wrong → plan revision (amendment per
  ADR 0022/0033 convention), never a provider-specific hack in the run
  layer.
- The ClawTeam provider cannot pass a conformance scenario inside its
  containments → dated addendum to the qualification evidence → feeds the
  section 10 exit-criterion decision (RISKS R01/R08 rows), not a silent
  fork.
- The team-mode extension forces a breaking change to a direct-mode record
  → section 6 contract design error → plan revision before code
  (protects "one record kind").
- Team acceptance is flaky on one OS → file-semantics bug in the provider
  or runner (R30-class) → fix with a platform-scoped regression test,
  never a skip-list.
- A felt need for live evidence to de-risk member choreography (R12) →
  M1b's deterministic tier is the wrong place → route to the M1c plan's
  budget ask.

## 18. Committed later milestones (deltas and handoffs)

M1a §19 remains the roadmap of record. M1b-specific handoffs:

- **M1c (PoC B)** inherits: the live-budget ask (its own ceiling; M1a's
  5-of-30 remain individual owner decisions), the section 10 exit-criterion
  decision (taken before PoC B starts), dynamic-member policy enforcement
  over the reserved `dynamic_members` field, `origin: ephemeral`, the
  hidden-member roster projection, and the R12 live tool-call-compliance
  question. The two-leg live reality (ADR 0036) stands until fresh Grok
  probes plus an owner decision.
- **M2** inherits: the reserved `parent`/`depth`/`nested_runs[]` fields,
  the nesting contract (team-execution-model §6), and the `atm` MCP
  server over the same versioned contracts.
- **M3** inherits: `overlay_refs` stays reserved-empty on every record
  M1b touches, and per-member `effective_definition_hash` remains computed
  state — the R15/overlay question is not foreclosed and must be answered
  before M3 starts.

## 19. Explicitly outside M1b

- Live team execution, PoC B, and any model call (M1c);
- dynamic/ephemeral/hidden member creation and its policy enforcement
  (M1c); nested TeamRuns and the MCP server (M2); overlays and evolution
  (M3); operational mode and watchers (M4);
- ClawTeam process spawning, tmux, keepalive, board, templates-as-launcher,
  and upstream issues/PRs (Q4 stays a separate owner decision; plan
  capability as if none merges);
- ACP, daemons, messaging surfaces, Hermes/OpenClaw/Telegram (Q6 stays
  open; deferred integrations);
- the HB-03 register (v3.4) amendment itself — a docs-only follow-up after
  the owner answers (section 7);
- mechanical independence enforcement claims of any kind;
- everything in M1a plan §20 not explicitly brought in scope here.

## 20. Approval checklist, finalize-at-approval decisions, and traceability

**What the independent review must confirm** (the review charter; each
item tickable against the frozen tree):

1. scope: deterministic-only M1b, zero live calls, M1c/M2/M3 boundaries
   (sections 1, 11, 18, 19);
2. provider order and the never-launches-a-harness rule (sections 2, 8);
3. one record kind: the team-mode extension keeps direct-mode `run.json`
   byte-compatible; exactly two new schema files (sections 2, 5, 6);
4. contract fidelity: section 6 against team-execution-model TC-01..TC-06
   and §3, the glossary terms, and the reserved markers in
   `domain/run.py` / `resolution/selection.py`;
5. ClawTeam constitution intact: extra-only, exact pin, one import module,
   containments, caveats restated verbatim (sections 4, 9.2);
6. exit criterion: r0 wording carried verbatim; the measurement rule is
   symmetric, mechanical, and anti-gameable; the decision timeline is
   owner-owned (section 10);
7. gate evidence is mechanically checkable and each gate names its VERIFY
   entry (section 3);
8. test matrix and CI mapping: conformance suite shared across providers,
   core-vs-extra job split, no new marker, direct regression retained
   (sections 14, 15);
9. stop rules and falsification routing cover the risks register rows
   R01/R02/R08/R12/R30-class/R33-lesson/R34 (sections 12, 13, 17);
10. approval/traceability mechanics: DECISIONS entry naming file + SHA,
    status flip in the following commit, review immutability (header,
    sections 2, 3).

**What the owner decides at approval** (all [finalize-at-approval] items):

- the ClawTeam exit-criterion wording and the section 10 measurement rule;
- the zero-live-call budget (section 11);
- the CLI surface: kind-discriminated `atm run` plus the single
  `atm team validate` verb (section 7);
- the section 6 optional/reserved field sets as specified;
- **HB-03 disposition** — the open question (QUESTIONS.md): does a
  team-level *constraint* (e.g. reviewer ≠ implementer harness) bind above
  an Assistant preference? Options:
  - **A — filter-then-prefer (recommended):** team constraints are
    eligibility *filters* (they prune candidates exactly like an
    Assistant's `forbidden` list; a conflicting explicit user request
    fails hard, matching M1a §11's no-silent-override rule); preference
    order stays user > Assistant > team > default; `decided_by` records
    the deciding layer. Cross-member constraints become expressible —
    an Assistant-level policy cannot see the other member's binding.
  - **B — preference layer only:** no constraint concept; cross-member
    constraints are structurally inexpressible.
  - **C — constraints above user:** team constraints silently re-select
    over an explicit user request — listed for completeness and
    recommended against: silent override falsifies `decided_by` honesty.
  - **Defer:** ship the team preference layer only; `constraints` stays a
    reserved-empty field; the semantics wait for the owner's answer.
    (Sections 6 and 7 are written so any of A/B/defer lands without
    contract churn; C would require reworking section 7.)

**Traceability.** Register/requirement rows this plan implements or
touches: TC-01..TC-06 and TE-01, TE-02, TE-03 (deterministic tier), TE-06,
TE-07 (sections 6, 11, 13); TE-04/TE-05 deferred (M1c/M2, section 18);
HB-03 (section 7/20); XC-04 audit (sections 8, 12). Risk rows: R01/R08
(section 9.2, 17 routing), R02 (no fork modules reused), R12 (sections 11,
13, 17), R30-class file semantics (section 14), R33 lesson (section 13),
R34 (section 12). Open questions: exit criterion (section 10, finalizes
here), HB-03 (this section), Q4/Q6 (section 19, stay outside), R15/overlay
(section 18, not foreclosed). Decisions inherited: ADRs 0003, 0007, 0014,
0015, 0016, 0018, 0021, 0022, 0033 (amendment convention), 0036, 0037,
0038.

Implementation begins only after review findings are resolved and the
owner explicitly marks this plan approved (G0). Project-local sources:
`docs/discovery/team-execution-model.md` (v2.3), the glossary,
`docs/evidence/clawteam-qualification-2026-08-23.md`, and the M1a plan as
amended; volatile facts (CLI versions, capability evidence) are rechecked
at their execution gate, not trusted from this text.

## 21. Revision record

- **r0** (2026-08-24, `856d525`): 7-section skeleton — the M1a G8 naming
  deliverable (provider order, named contracts, draft exit-criterion
  wording, PoC boundary, outside list, approval checklist).
- **r1** (2026-08-24, this commit): full expansion per the r0 approval
  checklist item 1. Every r0 section maps into r1; nothing is dropped:

| r0 section | r1 home |
| --- | --- |
| Status / prerequisites block | header (status, baseline, prerequisites) |
| Outcome | section 1 |
| Named contracts (deferred at r0) | section 6 (specified), 2, 5 |
| Provider order | sections 2, 9 |
| ClawTeam exit criterion (draft wording) | section 10 (wording verbatim + measurement rule) |
| PoC boundary | sections 1, 11 (budget), 18, 19 |
| Explicitly outside | section 19 |
| Approval checklist | sections 3 (G0), 20 |

Wording changes against r0 are additive except one refinement: the r0
exit-criterion parenthetical "(measured as in the G4 qualification
report — the seam's 233 LOC / 281 test-LOC baseline)" is expanded into the
explicit section 10 measurement rule (production-code ratio, tests
reported as context); the r0 blockquote itself is carried unchanged and
both finalize at approval. Amendments after approval follow the ADR
0022/0033 convention (in-document marker plus a dated amendment table) at
amendment time.
