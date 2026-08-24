# AgentTeam M1b team-foundation plan — draft r3

- Status: **draft r3, proposed 2026-08-24 — NOT approved.** r3 resolves the
  six implementation-blocking findings and three medium corrections of the
  second independent review (of r2;
  `docs/reviews/2026-08-24-m1b-plan-review-at-54728c8.md`; resolutions
  mapped in section 21), after r2 resolved the first-round review
  (`docs/reviews/2026-08-24-m1b-plan-review-at-14dc218.md`).
  Implementation starts only after owner approval as a `DECISIONS.md`
  entry naming this file and its commit SHA (the M1a §21 convention; ADR
  0021 precedent; the status line flips to `approved` in the following
  commit because a commit cannot name its own SHA). Per M1a plan §18,
  nothing here begins in the M1a approval scope.
- Revision baseline: r2 was `54728c8` (first-round findings resolved;
  reviewed again); r1 was `14dc218` (expanded full plan; reviewed);
  r0 was `856d525` (`docs(plans): draft M1b team foundation (proposed;
  G8 naming deliverable)`).
- Prerequisites carried in: the G4-qualified ClawTeam seam
  (`docs/evidence/clawteam-qualification-2026-08-23.md`), ADR 0015 (exact
  pin, extra-only, subprocess backend never used), ADR 0018 (measurement
  decides), ADR 0037 (build-vs-reuse reaffirmed post-G6), ADR 0039 (r1
  review recorded; HB-03 constraints deferred out of M1b), ADR 0040 (r2
  review recorded; MemberResultV1 and the stable ClawTeam root chosen by
  the owner).
- Sections marked **[finalize-at-approval]** carry proposed wording the
  owner finalizes at approval; every such item is listed once in section
  20.

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
3. the ClawTeam provider's status is **explicit and recorded** at close:
   either the same lifecycle and conformance evidence is green over the
   ClawTeam provider on the three-OS extra job, or a dated failure record
   exists and is routed to the section 10 exit-criterion decision with the
   section 3 failed branch applied (provider unsupported; reproduction
   retained; CI green) — close never happens with ClawTeam's
   supported/failed status implicit;
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
3. **One record kind for runs.** `RunRecordV1` is extended with a team
   mode; no `team-run-v1` schema file and no second run record kind exist
   (M1a §7; glossary "TeamRun"). Internally the record is a
   mode-discriminated union (direct | team variants) under the public
   name `RunRecordV1`; externally it is one `run-record` kind in one
   schema file whose `oneOf` closes each mode's exact field set, and the
   direct variant is field-identical to today's schema with its
   validators carried verbatim — a direct-mode `run.json` stays valid
   byte-for-byte.
4. **ClawTeam stays optional, extra-only, exactly pinned** to
   `0.3.0 @ 01198332ef9270c32c5460b8a178f964fc0df451` with `mcp>=1,<2`;
   every `clawteam` import stays confined to the one owned compatibility
   module `src/agentteam/compat/clawteam.py` (ADR 0015). The new provider
   module of section 9.2 imports that seam, never `clawteam` itself.
5. **Isolation claims stay honest.** The achieved isolation claim for the
   ClawTeam provider is `namespace` only (one process-scoped data root,
   opaque per-run namespaces — the ADR 0015 design, section 9.2); the
   local provider records `data-dir` (its space is a per-run directory).
   `independence {declared, achieved}` is recorded per run and never
   upgraded (PROJECT.md enforcement-honesty constraint; glossary).
6. **The ClawTeam exit criterion finalizes at approval and is decided
   before PoC B** (section 10; ADR 0018/0037/0038; the open QUESTIONS
   item). Its measurement is a gate of this plan (G6), and the milestone
   closes only with ClawTeam's disposition explicit (section 1 item 3,
   section 3 G7).
7. **Zero live calls in M1b** (section 11). Live team execution begins
   with M1c PoC B under its own owner-approved ceiling.
8. **All ClawTeam-specific code lives inside the measurement boundary** —
   `src/agentteam/compat/` plus `src/agentteam/coordination/clawteam.py`
   (section 10) — and the boundary is **mechanically enforced** by the
   section 14 static containment scan (AST import scan plus a
   textual-reference allowlist), not only by the section 17 stop rule.
   This keeps the exit-criterion numerator honest.
9. **The CLI keeps one execution entry.** `atm run` accepts the new
   `team-run-request` kind; in team mode the request file is the sole
   run-shaping input (section 7); the only new verb is `atm team
   validate` (section 7) **[finalize-at-approval]**.
10. **M1b team members execute as single invocations.** Team-mode
    ensembles and synthesis are structurally inexpressible in the M1b
    contracts (section 6) and revisit later with evidence; `execution
    {kind: ensemble}` remains the direct variant's mechanism. Hidden
    visibility and team-level `constraints` are reserved and fail closed
    in M1b — HB-03 constraint semantics are deferred out of M1b entirely
    (owner decision 2026-08-24, ADR 0039; the question stays open in
    QUESTIONS.md).
11. **Team members produce `MemberResultV1`, the provider-neutral member
    result** (owner decision 2026-08-24, ADR 0040): every M1b team-member
    invocation emits the new vendor-facing `member-result` structured
    output (section 6) instead of a review; `NormalizedReviewV1` remains
    the direct/ensemble legs' contract, and that live-proven path is
    untouched. Deliverables are member-declared workspace paths that the
    run layer validates, hashes, archives, and materializes for
    successors (section 11.2) — never raw streams.
12. **Approval convention**: owner approval of this plan is a DECISIONS
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
| G0 | Approve this plan | Independent reviews recorded in `docs/reviews/` (done for r1 at `14dc218` and r2 at `54728c8`; any further pass recorded the same way); findings resolved; owner approval as a DECISIONS entry naming this file and the approved commit SHA, committed before product source work; status flips to `approved` in the following commit |
| G1 | Team contracts and schemas | `TeamTemplateV1`, `TeamRunRequestV1`, and `MemberResultV1` models land with `team-template-v1.schema.json`, `team-run-request-v1.schema.json`, and `member-result-v1.schema.json` checked in; `run-record-v1.schema.json` regenerated as the mode-discriminated `oneOf` (direct variant field-identical) and `harness-invocation-v1.schema.json` regenerated with `team` in the `DecidedBy` enum — **three new files, two regenerated, nothing else** (the section 8 protocol enum and DTOs are internal types, no schema files); all new kinds registered in `SCHEMA_MODELS` with `minimal_payloads()` entries (the run-record entry stays the direct payload; a separate parameterized variant fixture covers both modes); `uv run python -m agentteam.schema check` green (no missing/stale/orphan file); **jsonschema-level negative tests** reject invalid direct/team field combinations against the checked-in schema; `member-result-v1` passes the vendor-dialect intersection lint (section 14); the entire pre-M1b core suite passes unchanged (direct-mode regression); `atm team validate` passes on the committed example template |
| G2 | CoordinationSubstrate protocol and local provider | `coordination/protocol.py` (with `SubstrateTaskStatus`, the DTOs, and the error taxonomy) and `coordination/local.py` land; the shared provider-conformance suite (section 14) is green over the local provider — space/member lifecycle with the lead recorded at creation, dependency auto-unblock, unknown-referent rejection, task-claim semantics, protocol-vocabulary enforcement, send/receive claim semantics, snapshot round-trip, cleanup postcondition (inoperability + snapshot survival), and two-space no-crossover; the static containment scan lands; the suite runs on the six-leg core CI job |
| G3 | Team runner integration | `atm run` executes the committed `team-run-request` end to end on fake harnesses over the local provider per section 11: deterministic topological task registration, staged rendering (7a preflight stubs, 7b launch-time renders), launch-on-ready scheduling, member-result parsing with deliverable archiving and materialization, handoff transport (and blinding on declared-independence edges) through the substrate, the coordination ledger, and the failure-finalization contract; the **fault-injection matrix of section 14 is green** (terminal record, conditional cleanup-event assertions, unconditional `processes-stopped`, no orphans in every row); `--render-only` emits exactly the 7a stub renders without launching; the roster lives in the run record with `tasks[].substrate_id` mapping recorded; direct-mode runs and records remain byte-compatible |
| G4 | Deterministic team-lifecycle acceptance | The section 13 acceptance is green through the CLI on all six core legs (3 OS × Python 3.11/3.13), including the ordering, transport-fidelity, ledger, and blinded-handoff conditions, at least one `decided_by: team` selection, and at least two distinct harnesses across members; no vendor executable is invoked anywhere in the job (fakes only) |
| G5 | ClawTeam provider disposition | `coordination/clawteam.py` lands behind the extra; **either** the same conformance suite plus the section 13 lifecycle pass over the ClawTeam provider on the three-OS `clawteam` job — with containment tests holding (event-bus reset, the one process-scoped data root of section 9.2, opaque `atm-<hex8>` namespaces, owner `~/.clawteam` refused, no subprocess/tmux import), the seam's `create_space` carrying the logical lead, `members()` reconciling to the full roster, the `running ↔ in_progress` mapping and error translations pinned, caveat behaviors pinned (stop-before-cleanup ordering; roster reconciliation), and clean skip without the extra on the core legs — **or** the failed branch is applied: a dated failure record is written and routed to the section 10 decision, the provider registry marks `clawteam` **unsupported** (`substrate: clawteam` exits 2 citing the VERIFY record), the failing reproduction is retained in `tests/compatibility/` as a dated strict-xfail referencing that record, and required CI is green. Both outcomes close the gate; only the disposition differs |
| G6 | Exit-criterion measurement | The pinned section 10 command is run and recorded in VERIFY: numerator and denominator LOC, the ratio against 1.5×, and test LOC reported as context; the accept/drop decision packet for the owner is prepared — the decision itself is taken by the owner before PoC B, not at this gate |
| G7 | M1b close | VERIFY entries current for G1–G6; PLAN.md gate rows closed with SHAs/run IDs; **the ClawTeam disposition line is recorded in VERIFY: `parity-green | failed-routed | dropped-by-owner`** (section 1 item 3); the hosted matrix is green under whichever disposition holds; live-call ledger unchanged (5 of the M1a 30-call ceiling remain, zero spent in M1b); the M1c PoC B draft r0 is proposed-not-approved, naming its live budget ask, the exit-criterion decision status, and the member-result live-acceptance handoff (section 18); M1c remains separately planned |

Cross-cutting stop rule: a ClawTeam-provider failure at G5 never alters
local-provider evidence and never blocks G7 on the local path — it blocks
describing ClawTeam as a qualified provider, sets the G5 disposition to
`failed-routed`, applies the failed branch above, and feeds the section 10
decision (do not silently fork, vendor, or make it mandatory — M1a §18).
Close is possible with a failed ClawTeam provider, but never with an
**implicit** one, and never with red required CI. A local-provider failure
at G2–G4 blocks everything after it; there is no ClawTeam fallback path,
because the local provider is the product path (ADR 0018).

## 4. Runtime and dependency baseline (delta to M1a §5)

M1a §5 stands unchanged: Python `>=3.11`, Hatchling, `uv` with committed
lock, `src/agentteam/` layout, version `0.1.0a0`, no publication.

M1b deltas:

- **No new runtime dependency is expected.** The local provider and the
  coordination ledger use the standard library (file operations, JSON)
  plus the already-present Pydantic models. Adding any dependency requires
  a documented reason (M1a §5 rule).
- The `clawteam` extra is unchanged: exact pin
  `01198332ef9270c32c5460b8a178f964fc0df451` + `mcp>=1,<2`, installed only
  via `uv sync --frozen --all-groups --extra clawteam`, never on core legs.
- No version bump, wheel, sdist, or release decision is part of M1b.

## 5. Repository layout (delta to M1a §6)

New paths only; everything in M1a §6 stays where it is.

```text
src/agentteam/
  coordination/
    __init__.py        # provider registry: local always; clawteam when importable
                       #   and not marked unsupported (the G5 failed branch)
    protocol.py        # CoordinationSubstrate Protocol, SubstrateTaskStatus,
                       #   DTOs (SubstrateTask, SubstrateMessage, SubstrateInfo),
                       #   error taxonomy
    local.py           # LocalCoordinationProvider (file task store, mailbox, snapshot)
    clawteam.py        # ClawTeamCoordinationProvider (imports agentteam.compat.clawteam
                       #   only; status mapping and error translation live here)
  domain/team.py       # TeamTemplateV1, TeamRunRequestV1, MemberResultV1
                       #   (+ embedded sub-models: MemberOverridesV1, HandoffPayloadV1)
  run/team.py          # the team lifecycle (section 11) beside the direct state machine
  commands/team.py     # `atm team validate`
schemas/
  team-template-v1.schema.json         # new
  team-run-request-v1.schema.json      # new
  member-result-v1.schema.json         # new (vendor-facing)
  run-record-v1.schema.json            # regenerated (mode-discriminated oneOf)
  harness-invocation-v1.schema.json    # regenerated (DecidedBy enum gains `team`)
examples/
  assistants/implementer/              # minimal second example Assistant (section 13):
                                       #   no Skills, empty harness preference
  teams/development.yaml               # the committed three-Member template
  run-requests/team-review.yaml        # the committed team-run request
fixtures/
  fake-harness/                        # gains a member-result output mode selected by
                                       #   the delivered schema (section 13)
tests/
  coordination_suite.py                # shared conformance base (not test_-prefixed)
  unit/test_team_template.py
  unit/test_team_request.py
  unit/test_team_selection.py
  unit/test_import_containment.py      # AST import scan + token allowlist (section 14)
  integration/test_coordination_local.py
  integration/test_team_run_execute.py
  integration/test_team_run_faults.py  # fault-injection matrix (section 14)
  compatibility/test_clawteam_provider.py
  acceptance/test_team_lifecycle.py
```

Naming rationale (this plan is the G8 naming deliverable's continuation):
the package is `coordination/` because the seam is named
`CoordinationSubstrate` and the source tree uses singular functional nouns
(`domain`, `harness`, `run`, `resolution`); `team` stays the domain concept
(`domain/team.py`) and the reserved selection layer
(`resolution/selection.py`), not a package. `MemberRecordV1` and the new
`MemberOverridesV1`/`HandoffPayloadV1` stay embedded sub-models — no
standalone schema files; the section 8 protocol enum and DTOs are internal
types with no schema files. **Exactly three new schema files exist and
exactly two are regenerated.** Existing modules amended in place:
`domain/run.py` (the mode-discriminated union; the two reserved markers),
`resolution/selection.py` (the `team` layer), `run/runner.py` +
`run/events.py` + `run/archive.py` (team dispatch, event fields, ledger),
`harness/` (the additive output-contract dispatch of section 6 —
`member-result` rendering and parsing beside the untouched review path),
`commands/run.py` (kind dispatch and the team-mode flag gate).

### 5.1 Run-state layout (delta to M1a §6.1)

`~/.agentteam/` gains one entry: **`~/.agentteam/clawteam/`** — the
ClawTeam provider's one process-scoped data root (`AGENTTEAM_HOME`
override applies), holding opaque per-run `atm-<hex8>` namespaces
(section 9.2). It is local state in the M1a §6.1 sense: gitignored,
owner-only, never committed, and **outside the run archive** (the
archive's coordination evidence is the ledger and the snapshot copy-out
below).

Inside a run directory, a team-mode run adds one `coordination/` subtree
with canonical paths:

- `coordination/space/` — the local provider's space (task store, inboxes,
  `consumed/`, provider snapshots); survives cleanup (section 11.6);
- `coordination/messages.jsonl` — the run-owned append-only message ledger
  (section 11.5);
- `coordination/snapshot.json` — the run-layer snapshot copy-out, for both
  providers (section 11.6).

The `coordination/` subtree sits inside the archive, so it is covered by
the SHA-256 manifest and the owner-only permission sweep.

## 6. Data contracts **[finalize-at-approval: optional/reserved field sets; MemberResultV1 fields]**

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
  relationships?}`. Member names are unique slugs; the name `synthesis`
  is **reserved** (it collides with the archive's `inv-synthesis` layout
  special case) — exit 2. Multiple members may reference the same
  Assistant package; the reference is resolved and hashed per member at
  instantiation.
- `lead` — the coordinating Member's name (TC-02); must be a roster name.
- `handoff` — `{required_fields[], acks[]}` (TC-02 conventions).
  `required_fields` ⊆ `{task_id, summary, deliverables, risks, done_when}`
  and `acks` ⊆ `{ACK, DONE, BLOCKED}` — the published vocabulary,
  validated exactly (exit 2 outside it). In M1b `acks` is dormant data:
  validated shape, no runtime behavior (member-driven acking is M1c/R12).
- `independence[]` — `{between: [a, b], declared: advisory | mechanical,
  means[]}` (TC-03). Declaring `mechanical` fails closed in M1b: no
  provider or run-layer enforcement of the message-edge rule exists yet
  (that is M1c+ evidence), so the committed example declares `advisory`.
  A dependency edge inside a declared pair gets a **blinded handoff**
  (section 11.2).
- `preferences` — team-level, project-independent (TC-06):
  `harness_preferences` keyed by member name (keys must be roster names;
  the team layer of section 7) and `run_defaults`.
- `workflow_skeleton[]` — task shapes `{id, subject, owner, blocked_by[]}`
  with placeholders; a shape, never a project's task list. `id` is a slug
  unique within the template and is what `blocked_by[]` references
  (forward-declared references are legal — validation is
  declaration-order-insensitive; registration order is section 11's
  concern); `owner` is a roster name. **Owner bijection (M1b):** the
  skeleton's owners are exactly the member set, one task each —
  structural, because `MemberRecordV1.execution` is a required field and
  a task-less member would be unrecordable; M1c relaxes this with the
  Lead-driven flow. Placeholder grammar: the only placeholder is
  `{goal}`; any other `{...}`, or an unmatched brace, fails validation
  (exit 2). Post-interpolation subjects must be single-line and
  non-empty.
- **Reserved and fail-closed in M1b**: `dynamic_members` (M1c),
  `constraints` (the HB-03 team-constraint concept — deferred out of M1b
  entirely by owner decision, ADR 0039; the semantic question stays open
  in QUESTIONS.md), and any `visibility` other than visible (hidden
  members are M1c; every M1b member is `visible`). A template carrying
  them fails validation (exit 2) **[finalize-at-approval]**.
- **Must NOT contain** (TC-06/AD-05; schema- and validator-enforced where
  expressible, `--strict-content`-checked otherwise): repo/paths/branches,
  workspace directories, a project's concrete tasks, harness session ids,
  Surface bindings, runtime agent ids, credentials or environment values,
  run results, ephemeral member definitions.

**`TeamRunRequestV1`** (`kind: team-run-request`; human-authored; the
team-mode sibling of `RunRequestV1`):

- `template` (path), `workspace`, `task_file`, `output_dir?`, evidence
  settings, and timeout/retry settings that may lower but never raise the
  M1a §9 caps; reserved `overlay_refs: []` (M3, must stay empty — R15 is
  not foreclosed).
- `goal` — **required**: the single-line subject material that `{goal}`
  interpolates from (non-empty, ≤ 200 characters, no control characters).
  It is a dedicated structured field — never derived from the task file's
  prose (the R12 discipline: protocol state is structured, not parsed).
  `task_file` remains the full work description delivered to members.
- `substrate: local | clawteam` (default `local`). Requesting `clawteam`
  while the provider is marked unsupported (the G5 failed branch) exits 2
  citing the VERIFY disposition record.
- `members` — the **entire user layer** for team mode: a map keyed by
  member name → `MemberOverridesV1 {harness?, model?, effort?}` (closed
  object). Keys must be template roster names (exit 2 otherwise); an
  empty or absent map is valid; **`model` or `effort` present requires
  `harness` present in the same object** (exit 2) — a harness-specific
  model string with the harness left to lower layers is under-determined.
- There is **no synthesis field and no per-member harness list** — team
  ensembles are structurally inexpressible in M1b (section 2 decision
  10), and there are no request-level visibility overrides (reserved,
  M1c).
- Runtime ids, timestamps, and results never appear in a request.

**`MemberResultV1`** (`kind: member-result`; **vendor-facing** — the
structured output every M1b team-member invocation produces; section 2
decision 11, ADR 0040):

- Fields: `summary` (non-empty string), `deliverables[]`
  (workspace-relative paths the member declares as its work products;
  empty allowed), `risks[]` (strings; empty allowed).
- Authored in the vendors' structured-output dialect intersection exactly
  like the review/synthesis schemas (every property required,
  `additionalProperties: false`, nullable-required optionals,
  look-around-free patterns) and delivered through the same
  `vendor_projection` (envelope stripped at delivery). A deterministic
  lint asserts the intersection rules (section 14).
- Declared deliverable paths are validated by the run layer against the
  member's isolated workspace (inside the workspace, no traversal — the
  V1 archive-contract discipline); handling is section 11.2's.
- There is deliberately **no status field**: mechanical success is the
  run layer's judgment (M1a rule — exit 0 plus valid structured output);
  member-reported blocking/acking is M1c choreography.
- **Honest evidence boundary**: M1b proves member-result deterministically
  (schema lint, fakes, CI); **live vendor acceptance of the schema is an
  explicit M1c handoff** (section 18) because M1b makes zero live calls.
  `NormalizedReviewV1` and `SynthesisReportV1` remain the direct/ensemble
  contracts, live-proven and untouched.

**`RunRecordV1` team-mode extension** (`kind: run-record` — one record
kind, one schema file, regenerated): modeled as a **mode-discriminated
union** under the public name `RunRecordV1` (the name is threaded through
the runner and archive and does not change). The generated
`run-record-v1.schema.json` becomes a `oneOf` over the two closed
variants, so each mode's exact field set is enforced **at the JSON-Schema
level** for non-Python consumers:

- the **direct variant** is field-identical to today's schema (single
  `member`, `mode: direct`) with today's validators carried verbatim — a
  direct-mode `run.json` stays valid byte-for-byte;
- the **team variant** (`mode: team`) carries:
  - `template {ref, hash}` — the resolved TeamTemplate identity;
  - `members[]` (length ≥ 2) — the full roster; each entry is today's
    `MemberRecordV1` (`name`, `assistant` ref + package hash, per-member
    `effective_definition_hash`, `execution {kind, ref}`) extended with
    `origin: persistent` (M1c adds `ephemeral`), `visibility: visible`
    (hidden is M1c), and the member's recorded harness selection; a
    variant validator pins every `execution.kind == invocation`
    (section 2 decision 10);
  - `substrate {kind: local | clawteam, namespace, snapshot {id, path,
    sha256}}` — the snapshot reference is the section 11.6 copy-out;
  - `tasks[]` — run-level task rows `{id, subject, status, owner,
    blocked_by[], substrate_id}`; `id` **is** the skeleton id;
    `substrate_id` is the provider-minted id (null until registered);
    status ∈ `blocked | pending | running | completed | failed |
    abandoned` — the run vocabulary is the section 8 protocol vocabulary
    plus the two **run-only terminals** `failed`/`abandoned`, which never
    cross the protocol; the run-level rows are authoritative, the
    provider's projection is secondary; the record's `blocked_by[]` holds
    the **declared** skeleton edges, immutable (the protocol DTO's
    remaining-blockers view is section 8's); **the step-4 pending record
    already carries the full `tasks[]`** (DAG roots `pending`, the rest
    `blocked`), so every failure phase leaves decision-complete task
    state;
  - `independence {declared, achieved}` — declared from the template,
    achieved recorded honestly per run (`namespace` for ClawTeam,
    `data-dir` for the local provider), never upgraded;
  - `events` — reference to the run's append-only event log;
  - **reserved for M2** (absent/null/empty, validator-enforced):
    `parent`, `depth`, `nested_runs[]`.
- **Lifecycle nullability** (status-conditional; model validators): while
  the record's status is `pending` or `running`, `substrate.namespace`,
  `independence.achieved`, and `substrate.snapshot` may be null (the
  pending record is written before the space exists). A `succeeded`
  record requires all three present. A `failed`, `cancelled`, or
  `timed-out` record allows a null `snapshot` when snapshot creation or
  copy-out failed, and a null `namespace` (with null `achieved`) iff the
  space was never created. These conditional rules are beyond the
  `oneOf`'s reach (the union discriminates on mode, not status), so they
  are model validators documented in `schemas/README.md`'s "invariants
  the schemas cannot express" section, with model-level negative tests
  (section 14) — and they mirror the fault-matrix conditionality of
  section 14 exactly (a no-space row asserts null namespace + null
  snapshot + no cleanup event together).

`SCHEMA_MODELS` registers the union under the `run-record` kind;
`minimal_payloads()` keeps its one-payload-per-file shape with the
**direct** run-record payload, and a separate parameterized fixture
(`run_record_variant_payloads()`) drives both-variant validation and the
negative tests (the fixture is keyed by schema filename, so it cannot
hold two run-record entries — section 14). `RunRequestV1`,
`EnsembleRecordV1`, `BundleManifestV1`, and both review-side vendor-facing
schemas are unchanged; **`HarnessInvocationV1` is regenerated** — its
`DecidedBy` enum gains `team` (section 7), an enum-only extension of
`harness-invocation-v1.schema.json`.

**`HandoffPayloadV1`** — an **embedded sub-model in `domain/team.py`**
(transport content validated on both sides; no standalone schema file).
Fields are the TC-02 vocabulary verbatim: `task_id`, `summary`,
`deliverables[]` (archive-relative path + sha256), `risks[]`, `done_when`.
Construction, transport, and blinding are specified in section 11.2;
`summary` and `risks` are sourced from the predecessor's `MemberResultV1`.

**Events.** The run's append-only `events.jsonl` (ids, names, and short
detail strings only — never bodies, paths, or environment values) gains
the team vocabulary: `space-created`, `member-added`, `task-created`,
`task-started`, `task-unblocked`, `task-completed`, `task-failed`,
`task-abandoned`, `message-sent`, `message-claimed`, `snapshot-taken`,
`snapshot-archived`, `snapshot-failed`, `processes-stopped`,
`provider-cleanup`; reused unchanged: `run-created`, `leg-started`,
`leg-retry`, `leg-finished`, `run-finished`, `run-cancelled`. The internal
`EventV1` record gains optional `task_id`, `member`, and `seq` fields so
the section 13 ordering assertions read structured fields, never parsed
prose (internal record; no schema file exists to regenerate).

**`CoordinationSubstrate`** is a typed Python protocol (section 8), not an
external record; provider identity, namespace, and the snapshot reference
travel inside the run record, so no new schema file is needed for it.

## 7. Public CLI contract (delta to M1a §8) **[finalize-at-approval: verb set]**

```text
atm run <team-request.yaml|json> [--render-only] [--output-dir <path>]
        [--config <path>] [--json]
atm team validate <template> [--json]         # the one new verb
```

- `atm run` stays the single execution entry. The request file's `kind`
  discriminates (`run-request` | `team-run-request`). **In team mode the
  request file is mandatory and is the sole run-shaping input**: the only
  flags accepted are `--render-only`, `--output-dir`, `--config`, and
  `--json` (existing precedence rules unchanged). Every other run-shaping
  flag — `--assistant`, `--workspace`, `--task-file`, `--harness`,
  `--model`, `--effort`, `--no-synthesis` — exits 2 with a message naming
  the request-file channel (`members` map, section 6). A
  `--harness member=value` repurposing is rejected: member names and
  harness ids share the Slug grammar, so the flag's key namespace would be
  undecidable by inspection. Direct mode is unchanged. `atm team run` is
  explicitly rejected (the M1a r2 merge already rejected extra CLI verbs
  once; §22 "Not adopted").
- `--render-only` in team mode emits exactly the section 11.1 step-7a
  preflight stub renders for every member, without launching anything.
- `atm team validate` mirrors `atm assistant validate`: schema + reference
  + prohibited-content + skeleton validation (ids, bijection, placeholder
  grammar, handoff vocabulary, reserved fields) of a TeamTemplate;
  `--json` includes the template hash. Recorded fallback if the review
  objects to any new verb: fold template validation into
  `atm run --render-only`, which must validate the template transitively
  anyway.
- Exit codes: `0` success, `1` runtime/harness failure, `2`
  invalid/unsafe input, `130` cancellation. **Exit `3` is unused in team
  mode** — M1b has no semantic acceptance tier (that is M1c+); the
  deterministic lifecycle evidence is mechanical.
- The AGENTS.md managed command table needs no row change in M1b planning
  or implementation (`Test` stays `uv run pytest`; there is no M1b live
  row). Any later table change follows the shown-diff approval convention
  (ADR 0023/0025 precedent).

Selection precedence (delta to M1a §11): the reserved `team` layer becomes
real as a **preference layer only** (HB-03 constraint semantics are
deferred out of M1b — owner decision, ADR 0039; the open question and its
recorded options live in QUESTIONS.md). Preference order is **user >
Assistant > team > default** — a member's `members[name].harness` override
(user) wins, then the member Assistant's `harness_policy` preference, then
the template's `preferences.harness_preferences[name]` (team), then the
profile default; `selection.decided_by` gains `team` and records the
deciding layer per invocation. Hard eligibility stays exactly M1a §11
steps 1–3: candidates, forbidden-removal, fail-closed user requests.
`DecidedBy`'s "forced variants" stay reserved (no force mode ships in
M1b). The register (v3.4) amendment remains a docs-only follow-up after
the owner answers HB-03, outside this plan's commits.

## 8. Python interfaces: the CoordinationSubstrate protocol

The second declared seam (glossary; ADR 0007/0014) becomes a typed
synchronous `Protocol` in `coordination/protocol.py`, together with the
task-status enum and the DTOs — all internal types, no schema files.

**`SubstrateTaskStatus = blocked | pending | running | completed`** — the
only task-status vocabulary that crosses the protocol, in both
directions. Two correspondences hold by construction: (i) the protocol
vocabulary is the run-record vocabulary minus the two run-only terminals
(`failed`, `abandoned` — section 11.3); (ii) protocol ↔ ClawTeam upstream
is a total bijection with the single rename `running ↔ in_progress`,
implemented in the provider adapter (section 9.2). The run layer *writes*
only `running` and `completed`; `blocked` and `pending` are
provider-computed read states (initial state from `blocked_by` at
registration; auto-unblock thereafter).

**Frozen DTOs**:

- `SubstrateTask {id, subject, status: SubstrateTaskStatus, blocked_by[]}`
  from `task()`/`tasks()`/`wait` — no owner field (ownership is run-level
  and behavioral, below). **Disambiguation: the DTO's `blocked_by[]` is
  the *remaining* uncompleted blocker provider-ids (empty once unblocked
  — the observed upstream behavior, and what makes section 13 condition 2
  testable through the DTO); the run record's `tasks[].blocked_by[]` is
  the *declared* skeleton edges, immutable.**
- `SubstrateMessage {sender, recipient, body}` from `receive()` — no
  provider ordinal (the run ledger owns sequencing; section 11.5).
- `members(space) → list[str]`; `info() → SubstrateInfo {kind, version,
  revision, achieved_isolation}`.
- `read_snapshot()`/`restore()` return **provider-shaped opaque dicts,
  deliberately not neutralized** — verbatim copy-out preserves forensic
  fidelity; the runtime never parses a bundle; vocabulary translation for
  parity assertions lives only in test-side per-provider bundle readers
  (section 14).

**Operations**:

- lifecycle: `create_space(*, lead: str) -> space_id` — the logical
  Lead's member name is part of space creation (the local provider
  records the lead as the space's first member; the ClawTeam provider
  passes it through as the leader, section 9.2); `add_member(space,
  name)` (name-only — roles, relationships, and visibility are run-record
  and template semantics with no provider consumer); `members(space)`;
  `cleanup(space)`;
- tasks: `create_task(space, subject, *, blocked_by)` — `blocked_by`
  holds already-minted provider ids only (deterministic topological
  registration, section 11 step 6; an unknown referent raises
  `UnknownTaskError`); `task(space, id)`, `tasks(space)`,
  `update_task(space, id, status, *, caller)` — status is
  `SubstrateTaskStatus`; skeleton-id cycle rejection happens
  provider-neutrally at step-1 validation, before any provider call, so a
  provider-level cycle is unconstructable;
- **claim semantics** (part of the protocol contract): `caller` is the
  owning member's name; while a task is `running`, `update_task` from a
  different caller raises `TaskClaimError`; the owner's `completed`
  succeeds and clears the claim (descriptive — post-terminal writes are
  not part of the conformance contract; strict transition validation is a
  local-provider-only guarantee, section 9.1);
- wait: a bounded, deterministic poll helper over `tasks()` with an
  explicit timeout — a protocol-level default implementation typed in the
  enum/DTO vocabulary, not a provider thread; expiry raises
  `WaitTimeoutError` (feeding the fault abort of section 11.3);
- messages: `send(space, sender, recipient, body)`,
  `receive(space, recipient, *, limit)` — claim consumes; addressing is
  bounded to the run's roster by the run layer before delivery; the
  authoritative message history is the run-owned ledger of section 11.5,
  not provider state;
- snapshots: `snapshot(space, tag)`, `read_snapshot(space, id)`,
  `restore(space, id)` — `restore` is conformance-only and is never
  invoked by the M1b runtime.

Cleanup postcondition (provider-neutral, asserted by the conformance
suite): after `cleanup(space)`, further operations on the space raise
`SpaceUnavailableError`, and the run-layer-archived snapshot copy
(section 11.6) remains readable. The postcondition is inoperability plus
snapshot survival — never file deletion.

Glossary-mapping note: the glossary's `stop` operation is deliberately
**not** a provider method. Stopping processes is the run layer's job — it
stops its own harness invocations (M1a §9 process contract) **before**
calling provider `cleanup`, because provider cleanup never stops processes
(a recorded ClawTeam caveat, section 10). The protocol therefore has no
process operations at all, which is what makes decision 2 of section 2
structurally true. The corresponding dated amendment to the glossary's
CoordinationSubstrate row is an approval-time docs follow-up recorded via
the G0 ADR (section 20) — normative discovery docs stay untouched until
this protocol shape is approved.

Error taxonomy: `CoordinationError` (base), `SpaceUnavailableError`,
`TaskCycleError` (step-1 validation), `TaskClaimError`,
`UnknownTaskError`, `UnknownRecipientError`, `WaitTimeoutError`;
provider-specific unavailability (`ClawTeamUnavailableError`) passes
through untranslated only inside the provider module. Every error path
maps to exit `1` (runtime) or `2` (invalid input) per the M1a table.

Run-layer boundary rules (team-execution-model §8, §9): the run layer owns
the roster — substrate membership is a projection of it, and the ClawTeam
provider's `members()` must **reconcile to the full roster** (upstream may
or may not include the leader in its member list — the "two rosters"
caveat — so the reconciliation glue lives inside the numerator and is
pinned by the conformance suite); run-level task ids map to provider ids
via `substrate_id`; message addressing outside the roster is refused
before the provider sees it; run-level events are appended by the run
layer, never inferred from provider internals; the AgentTeam process
runner supplies output and exit status independently of any provider.

## 9. Coordination providers

### 9.1 Local deterministic provider (`coordination/local.py`, first)

Product-owned, stdlib-only, and the substrate for every deterministic test
and CI leg (ADR 0018 decision 2):

- **File task store**: JSON task rows under the space directory; explicit
  `blocked_by[]` (minted ids only); completing the last blocker
  auto-unblocks a task (`blocked → pending`); a `claimed_by` field
  implements the section 8 claim contract (`TaskClaimError` on a second
  caller while `running`); unknown ids raise `UnknownTaskError`; a
  deterministic id scheme (`t-<seq>`). **Strict transition validation
  (`pending → running`, `running → completed` only) is a local-provider
  guarantee and test — deliberately NOT a conformance requirement**
  (upstream demonstrably accepts non-monotonic transitions).
- **File mailbox**: per-recipient directories; `send` writes one message
  file; `receive` claims atomically by moving the message file to
  `consumed/<recipient>/` (atomic rename — **never deletes**; a second
  receive is empty because the inbox is; the snapshot bundle therefore
  includes full message history). Ordering is deterministic
  (sequence-numbered file names, never wall-clock-dependent ordering).
  Consumed-retention is a local-provider guarantee and test — **not** a
  conformance requirement (ClawTeam cannot satisfy it and relies on the
  section 11.5 ledger).
- **Snapshot**: one JSON bundle of the space (members, tasks, messages —
  consumed included — events) written atomically; `read_snapshot` and
  `restore` round-trip it.
- **Space**: the directory `coordination/space/` under the run directory
  (section 5.1) — one space per run, so achieved isolation is recorded as
  `data-dir`; two spaces never share files by construction. `cleanup`
  writes a `closed` tombstone and **deletes nothing** — the space is
  archive-resident and is sealed by the manifest, which finalizes after
  cleanup (section 11.6).
- **Determinism guarantees** (asserted by tests): no wall-clock coupling
  in observable ordering, atomic writes (write-then-rename), identical
  behavior on the three OSes, and no background threads.

### 9.2 Optional ClawTeam provider (`coordination/clawteam.py`, second)

A thin adapter from the protocol onto the qualified seam — it imports
`agentteam.compat.clawteam` and nothing from `clawteam` directly, so the
one-module import confinement of ADR 0015 is preserved verbatim. The six
G4 containments carry forward unchanged (extra-only import; **one fixed
process-scoped data root** with the owner's `~/.clawteam` refused; opaque
`atm-<hex8>` names and explicit file primitives; event bus replaced and
hook loader disarmed before any operation; no subprocess/tmux/wsh/template
launcher/keepalive/CLI chain; version/revision/isolation recorded via
`info()`).

**Data root (the ADR 0015 design, restored):** the root is the stable
**`~/.agentteam/clawteam/`** (`AGENTTEAM_HOME`-relative; section 5.1),
fixed once per process, with one opaque `atm-<hex8>` namespace per run —
so multiple TeamRuns in one process (the test suite today; the M2 MCP
server later) satisfy the seam's one-root rule. `cleanup` removes the
run's namespace inside that root. The root lives **outside the run
archive**: the archive's ClawTeam evidence is the run-layer snapshot
copy-out and the message ledger (sections 11.5–11.6), and a cleanup
failure leaves unmanaged local data outside any manifest — still
hygiene-not-failure per section 11.4, recorded by the `provider-cleanup`
event and stated here honestly. Tests point the provider at temporary
roots via the seam's reset hatch.

**Adapter-resident translation** (all inside the exit-criterion
numerator, which is correct and honest): the bidirectional status mapping
`running ↔ in_progress` (the pinned seam keeps accepting upstream
vocabulary verbatim — its only G5 delta remains the `leader` parameter
below); upstream `TaskLockError → TaskClaimError` and lookup
`KeyError → UnknownTaskError`; upstream message `content →
SubstrateMessage.body`; and roster reconciliation for `members()`
(section 8).

Seam delta (G5): `ClawTeamCompat.create_space` gains a `leader: str`
parameter carrying the logical Lead's member name, replacing the
hard-coded `"atm-lead"` (the minted leader id is unchanged). The change is
confined to `src/agentteam/compat/clawteam.py`, and the qualification
**test file** updates in the same commit; the G4 qualification **evidence
document stays immutable** (a signature evolution under the same
containments is a code change, not a re-qualification event).

**The failed branch** (G5 disposition `failed-routed`): the provider
registry marks `clawteam` unsupported — `substrate: clawteam` exits 2 at
step-1 validation citing the VERIFY disposition record (structurally
outside the fault matrix, whose scope is runs that wrote the pending
record); the failing scenario is retained in `tests/compatibility/` as a
**dated strict-xfail** referencing that record, so required CI stays
green and the reproduction flips visibly if upstream behavior changes
(the RISKS R02 xfail precedent; never a silent skip). Un-xfailing
requires a re-qualification event; full removal rides the owner's
section 10 drop decision.

The qualification report's recorded caveats stand and are restated here
because the exit criterion requires them accepted in writing (verbatim
from `docs/evidence/clawteam-qualification-2026-08-23.md`): "two rosters
(ClawTeam's own member list vs any layer view), no parent link for nested
teams, cleanup does not stop processes, and every containment above is
caller-written code, not configuration." The provider pins the first and
third behaviorally: roster reconciliation is tested (the run record roster
is authoritative), and the run layer's stop-before-cleanup ordering is
tested. "No parent link" is dormant in M1b (nesting is M2) but recorded
now.

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

r1 pinned the measurement rule the r0 parenthetical left open — what
counts as "provider glue plus its workarounds" once the local provider
exists. The rule, finalized at approval:

- **Metric**: physical lines by `wc -l` over `*.py` files — exactly the
  G4 qualification method, which reproduces the 233/281 baseline.
- **Numerator** (ClawTeam side): production code that exists only because
  ClawTeam is supported — `src/agentteam/compat/` plus
  `src/agentteam/coordination/clawteam.py` (which now includes the status
  mapping, error translation, and roster reconciliation of section 9.2 —
  workarounds counted where they live).
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
  code confined to the two numerator packages) is enforced twice — by the
  section 17 stop rule and **mechanically** by the section 14 static
  containment scan (AST imports + token allowlist) — so the numerator
  cannot shrink by relocating glue into the run layer.

Timeline: the criterion's wording finalizes at this plan's approval (G0);
the measurement is recorded at G6; the accept/drop **decision** is the
owner's, taken before PoC B starts (normally at M1c plan approval, as a
DECISIONS entry that either accepts the four caveats in writing with the
recorded ratio, or drops ClawTeam support without replacement). Until that
decision, ClawTeam remains "optional and qualified" (or
"failed-routed", per the G5 disposition), never "the product path".

## 11. Team-run lifecycle and budget

The team-mode lifecycle (team-execution-model §3, trimmed to M1b scope;
numbered like the M1a §12 state machine). Sections 11.1–11.6 are the
normative sub-contracts.

1. Validate the profile set, the TeamTemplate (`atm team validate`
   semantics: schema, references, prohibited content, skeleton ids —
   cycles, self-reference, and unknown ids rejected here,
   declaration-order-insensitively — owner bijection, placeholder
   grammar, handoff vocabulary), and the TeamRunRequest (`goal` present
   and well-formed; `members` keys are roster names; `model`/`effort`
   only with `harness`; the substrate supported — an unsupported
   `clawteam` exits 2 citing its disposition record); reserved fields
   (`overlay_refs`, `dynamic_members`, `constraints`, non-visible
   `visibility`, `parent`/`depth`/`nested_runs`) must be empty; a request
   needing M1c/M2 behavior fails closed (exit 2) before any side effect.
2. Resolve each member's Assistant package independently; build one
   immutable bundle and canonical hash per member; record per-member
   `effective_definition_hash`. Interpolate `{goal}` into every skeleton
   subject (exit 2 on any grammar violation).
3. Resolve harness selection per member (user > Assistant > team >
   default; `decided_by` recorded per invocation; hard eligibility per
   M1a §11).
4. Create the pending team-mode `run.json` — full roster, template ref +
   hash, declared independence, and the **complete `tasks[]`** (DAG roots
   `pending`, the rest `blocked`, `substrate_id: null`; lifecycle
   nullability per section 6) — **before** the coordination space exists
   and before any process starts.
5. Materialize one isolated workspace per member (the M1a per-leg copy
   mechanism); target hashes detect mutation.
6. Create the provider space with the logical Lead
   (`create_space(lead=...)`), add the remaining members, and register
   the skeleton tasks through the `CoordinationSubstrate` protocol in
   **deterministic topological order** — Kahn's algorithm with the ready
   set popped in skeleton declaration order, `blocked_by` translated to
   provider ids from the already-registered prefix, so a provider never
   sees a forward reference and `task-created` events append in
   registration order; record `tasks[].substrate_id` and the achieved
   isolation level. Registration *order* is deterministic and
   reproducible; `substrate_id` *values* are provider-minted (the local
   `t-<seq>` scheme makes them reproducible on the deterministic tier;
   ClawTeam's are opaque).
7. Staged rendering (section 11.1): **7a** — render-preflight every
   member's invocation with a deterministic handoff stub, before any
   launch (exit 2 on failure; `--render-only` stops here); **7b** — at
   each launch, compose the member's real task document (section 11.2)
   and render the final invocation.
8. Launch on readiness only (section 11.1), through the direct runner,
   fresh sessions, no provider involvement in process management; enforce
   the M1a retry discipline unchanged (one transient same-harness retry;
   never substitute a harness).
9. Propagate task state per section 11.3 (completion → auto-unblock →
   next launches; failure → cascade); deliver handoffs through the
   ledger and the substrate, with blinding on declared-independence edges
   (sections 11.2, 11.5).
10. Finalize per sections 11.4–11.6: stop all AgentTeam-owned processes,
    take and archive the final snapshot (iff a space was created), then
    provider cleanup — always in that order.
11. Re-hash every member bundle (mutation check), run the **abandon
    sweep** (section 11.4), write the terminal record, then finalize the
    archive manifest **last** (owner-only modes swept), and return the
    stable exit code.

### 11.1 Runnable-task scheduling and staged rendering

- A member's invocation launches **exactly once, when its owned task
  transitions to `pending`**. At run start only DAG roots are `pending`;
  blocked owners are never launched. Simultaneously-ready tasks launch
  concurrently (the M1a gather discipline); among simultaneously-ready
  tasks, launch initiation order is skeleton declaration order
  (determinism). Launch order is DAG readiness, nothing else — in the
  committed fixture the lead owns the root task, so it happens to go
  first.
- **Staged rendering.** The adapters read task-file content at render
  time, so a successor's final render cannot precede its handoff payload.
  Step 7a (*render-preflight-all-before-any-launch*): every member's
  invocation is rendered at instantiation with a deterministic handoff
  **stub** (fixed marker text) purely to prove renderability — channel
  delivery, environment policy, argv guards — failing exit 2 before any
  launch (M1a render-all-before-launch parity). Step 7b
  (*final-render-before-each-launch*): when a task becomes `pending`, the
  run layer composes the member's real task document and renders the
  invocation; the archived render record is the launch-time render. A
  **launch-time** render failure is exit-1 runtime (validation already
  passed) and enters the section 11.3 cascade as that task's failure.
- Team invocation ids are `inv-<member-name>`; the archive reuses the
  `legs/` layout; the existing `leg-started`/`leg-retry`/`leg-finished`
  events are reused per member invocation.

### 11.2 Handoff payload construction, blinding, and member context

- The per-member task document (`legs/inv-<member>/task.md`) is composed
  by the run layer: (1) the member's interpolated task subject, (2) the
  request `task_file` content verbatim, (3) a handoff section.
- On each task completion, the run layer constructs one
  `HandoffPayloadV1` per outgoing dependency edge, filled mechanically
  from structured facts — never parsed prose: `task_id` = the completed
  run-level task id; `summary` = the predecessor's
  `MemberResultV1.summary`; `deliverables` = the archived references of
  the predecessor's **declared** deliverables (section 2 decision 11):
  the run layer validates each declared workspace-relative path, hashes
  it, and copies it under `legs/inv-<predecessor>/deliverables/` —
  archive-relative path + sha256, never raw stdout/stderr; `risks` = the
  predecessor's `MemberResultV1.risks` (recorded honestly, empty
  included); `done_when` = the successor task's interpolated subject. The
  template's `handoff` block selects which of these fields are required;
  one vocabulary applies uniformly to every edge.
- **Deliverable materialization**: before a successor's baseline
  workspace hash is computed, the run layer materializes the deliverables
  it received into the successor's isolated workspace under
  `handoff/<predecessor-task-id>/` (hash-verified copies of the archived
  files) — so the mutation check is computed over the workspace including
  the hand-off and stays intact, and the successor can actually read its
  inputs.
- **Blinded handoff on declared-independence edges** (the normative
  TC-03 means: no message edge, blinded inputs): a dependency edge whose
  two members form a declared independence pair gets **no mailbox
  message** — the run layer must not itself create the message edge the
  template declares away, regardless of `advisory`/`mechanical` (this is
  the run layer's own behavior, always under its control; member-to-member
  messaging enforcement is M1c). Deliverable materialization still
  happens — the artifact under review is exactly what a blinded reviewer
  receives — but `summary`/`risks` (the predecessor's rationale) are
  omitted, and the successor's task document carries a "handoff blinded
  by declared independence: artifact only" marker. DAG unblock is
  untouched (task state, not a message).
- Non-blinded payloads travel as the mailbox message body (canonical
  JSON): ledger append (section 11.5) → provider `send` to the dependent
  task's owner. **At the successor's launch, the run layer claims that
  member's inbox (`receive`) and embeds the claimed bodies — not its own
  retained copies — into the task document's handoff section**, ordered
  by predecessor task id (deterministic under fan-in). This makes the
  acceptance prove substrate transport into member context, not parallel
  bookkeeping: section 13's transport-fidelity condition asserts
  byte-equality between each claimed body and its ledger row.
- **Missing-body fault abort**: a claim that returns fewer bodies than
  the successor's incoming **completed, non-blinded** edges is a fault
  abort before launch (transport loss is infrastructure; launching with a
  silently empty handoff would violate transport fidelity invisibly).
  The non-blinded qualifier is load-bearing: without it, the committed
  fixture's blinded reviewer edge would abort the green path.

### 11.3 Task state propagation and the failure cascade

- Launch → `update_task(running, caller=owner)`; invocation terminal
  success (the M1a leg-success rule: exit 0 plus valid structured output
  — for a team member, a valid `MemberResultV1`) →
  `update_task(completed, caller=owner)`; the provider auto-unblocks
  dependents (`blocked → pending`), observed through the protocol `wait`
  helper; the scheduler launches newly-pending owners.
- **`failed` and `abandoned` never cross the protocol** — a correctness
  property, not a convenience: a failed task is never provider-side
  `completed`, so provider auto-unblock can never fire for its
  dependents, and the provider DAG stays consistent with the cascade by
  construction. Residual-projection rule: a `failed` row's provider
  projection remains `running`; an `abandoned` row's remains `blocked` or
  `pending` — a surviving sibling's completion is still sent to the
  provider and may auto-unblock an abandoned row provider-side, which is
  unobserved and harmless (after a cascade begins the scheduler issues no
  further waits or launches).
- Two named failure modes (exhaustive **by cause**):
  - **Failure cascade** (a task-level outcome): invocation failure
    post-retry, attempt timeout, or launch-time render failure → the
    run-level task `failed` → every transitive dependent `abandoned`
    eagerly (the event log reads causally: `task-failed` adjacent to its
    dependents' `task-abandoned`) → no further launches; **in-flight
    sibling invocations run to completion** (the M1a process contract
    terminates trees only for cancellation or timeout of *that*
    invocation — their evidence is kept, and their completions still
    reach the provider); any remaining never-launched tasks are closed by
    the abandon sweep at finalization (section 11.4); the run finalizes
    `failed`, exit 1.
  - **Fault abort** (an infrastructure failure): any provider operation
    raises, `wait` raises `WaitTimeoutError`, or a handoff claim comes up
    short (section 11.2) → the run layer terminates in-flight member
    process trees per M1a §9, marks those invocations `cancelled`, and
    finalizes per section 11.4 (the sweep closes every non-terminal
    task); run `failed`, exit 1.
- Snapshot-time status parity is asserted exactly for run-level rows
  whose status is in `SubstrateTaskStatus`, via per-provider test-side
  bundle readers (the ClawTeam reader translates `in_progress → running`;
  test LOC, ratio-exempt per section 10); `failed`/`abandoned` rows are
  asserted against the residual-projection rule only where the fixture
  makes the residual deterministic (fault-matrix rows).
- Team-run success = every run-level task `completed` and every member
  invocation succeeded. Team-mode exit codes are 0/1/2/130; exit 3 is
  unused (section 7).

### 11.4 Failure finalization contract

Standing invariant: **every run that wrote the pending record (step 4)
ends with, in order: stop every AgentTeam-owned process (the
`processes-stopped` event is emitted exactly once per finalization,
zero terminations permitted) → best-effort snapshot copy-out iff a space
was created → provider cleanup attempted iff a space was created → the
abandon sweep (every still-non-terminal `tasks[]` row → `abandoned`, with
its `task-abandoned` event) → terminal `run.json` with every row terminal
(`completed | failed | abandoned`) → finalized manifest.** Nothing may
reorder stop before cleanup, skip the sweep, or write the manifest before
the terminal record. The sweep is run-record-only (it never crosses the
protocol) and is the single mechanism that discharges the all-terminal
invariant for arbitrary DAGs — cascade remainders, fault aborts, and
cancellation all resolve through it.

Per phase:

| Phase (step) | On failure |
| --- | --- |
| Validate / resolve / selection (1–3) | exit 2, **no run directory** (M1a parity: the archive is created only after preflight); skeleton-id cycle/self/unknown rejection happens here, provider-neutrally |
| Pending record (4) | archive-creation failure: exit 2, nothing to finalize (M1a semantics) |
| Workspaces (5) | archive exists, no space yet — terminal `failed` + manifest; source-hash mismatch exit 2, copy mismatch exit 1 (mirrors M1a) |
| Space / roster / task registration (6) | if `create_space` itself failed there is no space — **no snapshot, no cleanup, and no `provider-cleanup` event** (the fault matrix asserts its absence; the record's `substrate.namespace` and `snapshot` stay null per the section 6 nullability — the same fact seen from events and record); mid-phase failure: best-effort snapshot, cleanup attempted; sweep closes the rows (`substrate_id` null where never registered); exit 1 |
| Render preflight (7a) | exit 2 **with** an archive (M1a render-error parity); snapshot/cleanup as above; no launch ever happened |
| Launch loop (7b–9) | failure cascade or fault abort per section 11.3; exit 1 |
| Cancellation (SIGINT, any phase ≥ 4) | the team analog of the direct runner's cancellation finalizer: terminate process trees, non-terminal invocations `cancelled`, best-effort snapshot, cleanup attempted, sweep, run **`cancelled`** (the existing status — no new status value ships), manifest, exit 130 |
| Final snapshot fails on the otherwise-green path (10) | run `failed`, exit 1 — the snapshot is section 13 acceptance evidence; a run without it did not meet its contract (`substrate.snapshot` null per section 6). On an already-failing path, a `snapshot-failed` event is recorded and the primary `failure_reason` is kept |
| Cleanup fails (10) | recorded as a `provider-cleanup` event with a failure detail; **never** alters `failure_reason`; on the green path the run still exits 0 — cleanup is hygiene, the evidence is already durable, and failing a correct run for hygiene would incentivize masking |
| Manifest write fails (11) | exit 1, archive left partial, error surfaced (M1a parity; the terminal record was already written) |

### 11.5 Message durability and the coordination ledger

The run layer appends every message — full envelope and body — as one row
of the run-owned append-only **`coordination/messages.jsonl`** (`{seq, ts,
sender, recipient, body}`) **before** the provider `send`
("ledger-before-send"). `events.jsonl` gains a `message-sent` event
carrying the `seq`, sender → recipient, and the body's sha256 — ids and
short details only, hash-linked to the ledger, preserving the events
contract (no bodies in events). The ledger is the authoritative message
history for **both** providers; it lives in the archive, is manifested,
and inherits the permission sweep. The local provider *additionally*
retains claimed messages under `consumed/` (section 9.1) — a
local-provider guarantee, not a conformance requirement. Blinded edges
produce no ledger row and no message (section 11.2) — the blinding marker
in the successor's task document is the record.

### 11.6 Cleanup semantics and archive survival

**Snapshot copy-out is a three-step compound performed by the run layer
for both providers**: provider `snapshot(space, tag)` → `read_snapshot`
of that id → an atomic write of the bundle to the canonical archive path
`coordination/snapshot.json`; a raise at any of the three steps is a
snapshot failure under the section 11.4 rows. The team record's
`substrate.snapshot {id, path, sha256}` references the copy-out (without
it the reference would dangle for the local provider too, since
post-cleanup `read_snapshot` raises). Provider `cleanup` then runs under
the section 8 postcondition: the space becomes inoperable; the archived
snapshot survives. Local provider: tombstone, nothing deleted, the whole
space survives under `coordination/space/`; because **cleanup precedes
manifest finalization, everything archive-resident that survives is
sealed**. ClawTeam provider: upstream cleanup removes the run's namespace
inside the stable `~/.agentteam/clawteam/` root (section 9.2) — outside
the archive by design; the archive's ClawTeam evidence is the copy-out
plus the ledger, and residual root data after a failed cleanup is
unmanaged local state, recorded by the `provider-cleanup` event.

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

M1b deltas: the archive-resident coordination evidence — the local
provider's space, the message ledger, the snapshot copy-out, and archived
deliverables — is covered by the same permission sweep and SHA-256
manifest; the ClawTeam provider's space data lives in the stable
`~/.agentteam/clawteam/` root **outside** the archive (section 9.2) and,
like all `~/.agentteam/` state, is local-only and never committed. The
R34 exec-bit caveat is inherited unchanged (the G6.R3 flattening contract
binds until the owner revises it — revisit before any workspace, Skill,
or deliverable ships an executable). **No new evidence class exists**:
M1b's milestone evidence is CI logs plus committed deterministic
fixtures, so no sanitized evidence bundle and no promotion step is
needed. Task, message, handoff, and member-result fixtures are authored
content and must contain no secrets, no absolute paths, and no
owner-machine facts.

## 13. Deterministic team-lifecycle acceptance

The milestone evidence (G4), run through the CLI on every core leg:

- **Fixture**: `examples/teams/development.yaml` — three Members
  (`lead`, `implementer`, `reviewer`) with `lead: lead`, a `reviews`
  relationship, `advisory` declared independence between reviewer and
  implementer, and the three-task skeleton `plan` → `implement`
  (blocked by `plan`) → `review` (blocked by `implement`), one task per
  member (the owner bijection). `lead` and `reviewer` reference the
  existing `code-reviewer` example package; `implementer` references the
  new minimal `examples/assistants/implementer/` package (thin
  persona/purpose/principles, **no Skills, empty `harness_policy`
  preference**) so that the template's
  `harness_preferences.implementer: [codex]` decides its harness at the
  **team** layer — the pinned `code-reviewer` package hash is untouched
  (sibling package). `examples/run-requests/team-review.yaml` supplies
  `goal`, the committed `fixtures/review-target` workspace, the task
  file, and `substrate: local`, on the fake harnesses
  (`examples/profiles/ci-fake.yaml`); every member's fake emits a valid
  `MemberResultV1` (the fakes select the member-result mode from the
  delivered schema), and the implementer's canned result declares one
  deliverable file it writes into its workspace.
- **Mechanical conditions**, each asserted by a test:
  1. roster parity — `run.json members[]`, the template roster, and the
     provider's `members()` (lead included from creation) agree exactly;
     the run-record roster is authoritative;
  2. DAG closure — all skeleton tasks reach `completed`; each blocked
     task unblocked exactly when its blocker completed (observed through
     the DTO's remaining-blockers view); skeleton cycle/unknown-id
     rejection is pinned at validation;
  3. messages bounded to the run — handoff messages deliver only between
     roster names; an out-of-roster recipient is refused before the
     provider sees it;
  4. snapshot archived — `coordination/snapshot.json` exists, matches
     `substrate.snapshot.sha256`, and reproduces the space through the
     provider's bundle reader (members/tasks/messages; task statuses
     compared in the protocol vocabulary);
  5. per-member records — every member carries its own
     `effective_definition_hash` and one `invocation` execution binding,
     and every successful member invocation parsed a valid
     `MemberResultV1`;
  6. team-decided, mixed selection — at least one member records
     `decided_by: team` (the `implementer`), and at least two distinct
     harnesses appear across members (TE-03 deterministic evidence);
  7. terminal `run.json` with `independence {declared: advisory,
     achieved: data-dir}` recorded honestly (ClawTeam leg: `namespace`)
     and the section 6 lifecycle nullability satisfied (`succeeded` ⇒
     namespace, achieved, and snapshot all present);
  8. mutation check — every member bundle re-hashes identically; the
     direct-run regression (`direct-review.yaml`) still passes unchanged
     in the same job;
  9. ordering — for every dependency edge (a, b): `task-completed(a)`
     precedes `leg-started(inv-<owner(b)>)` in `events.jsonl`, and
     exactly one `leg-started` exists per member (partial-order
     assertions over structured event fields);
  10. transport fidelity on the **non-blinded** edge (plan → implement) —
      the successor's embedded handoff bodies are byte-equal to the
      claimed mailbox messages and to their `messages.jsonl` ledger rows
      (hash-linked via the `message-sent` events);
  11. ledger consistency — every ledger row has its `message-sent` event
      (matching sha256) and, on the green path, a `message-claimed` event
      before its recipient's launch;
  12. **blinded handoff on the independence edge** (implement → review) —
      no ledger row, no `message-sent`/`message-claimed` events for that
      edge; the reviewer's task document carries the blinding marker and
      no predecessor summary/risks; the implementer's declared
      deliverable is archived under `legs/inv-implementer/deliverables/`
      **and** materialized hash-equal into the reviewer's workspace under
      `handoff/implement/`, before the reviewer's baseline hash.
- **Multi-step shapes on purpose**: the R33 lesson (probes are single-turn
  and cannot see multi-turn failure classes) applies to team lifecycles
  too — the skeleton exercises sequential dependent tasks with real
  handoff transport and blinding, not one degenerate task. The R12
  mitigation is structural: protocol state lives in the task DAG, the
  ledger, and structured records — never in prose parsed from member
  output.
- **Zero live calls**: no vendor executable is invoked anywhere in the
  acceptance path; the fakes are launched through the same process runner
  as real harnesses (M1a §15 discipline). The negative scheduling
  assertions — no `leg-started` for a member whose task never unblocked,
  and none for any not-yet-launched member after a cascade — live in the
  fault matrix (section 14), not the green acceptance.

## 14. Deterministic test plan

Normal tests never invoke a vendor model (M1a §15 rule; unchanged local
verification block, including `uv run python -m agentteam.schema check`).

- **Schema parity and negatives**: `minimal_payloads()` in
  `tests/conftest.py` keeps its one-payload-per-file shape — it gains
  `team-template-v1.schema.json`, `team-run-request-v1.schema.json`, and
  `member-result-v1.schema.json` entries, and its `run-record` entry
  stays the **direct** payload; a separate parameterized fixture
  (`run_record_variant_payloads()`) supplies valid direct and team
  payloads plus the negative set. The data-driven parity test then covers
  all **twelve** schema files and the orphan check covers the directory.
  **Schema-level negative tests** (the `jsonschema` dev dependency,
  validating against the checked-in files): a direct record carrying any
  team field, a team record carrying `member`, a team record with one
  member, reserved fields non-empty, an unknown `decided_by` value — each
  must be rejected by the schema itself, not only by the models.
  Model-level negatives cover the section 6 lifecycle nullability
  (`succeeded` with a null namespace/achieved/snapshot rejected; the
  failed/cancelled allowances accepted). A **vendor-dialect lint**
  asserts `member-result-v1` obeys the intersection rules (every property
  required, closed, nullable-required optionals, look-around-free
  patterns), like the review schemas.
- **Unit**: `test_team_template.py` — TC-01..06 field validation,
  skeleton ids (forward-declared `blocked_by` legal; cycles/self/unknown
  exit 2) and the owner bijection, placeholder grammar, handoff
  vocabulary bounds, the must-NOT-contain prohibitions, reserved-empty
  enforcement (`dynamic_members`, `constraints`, non-visible
  `visibility`), the reserved `synthesis` member name, template hashing.
  `test_team_request.py` — `goal` validation, the `members` override map
  (roster-name keys; `model`/`effort` require `harness`), the team-mode
  CLI flag gate (each rejected flag exits 2), kind dispatch, the
  unsupported-substrate rejection. `test_team_selection.py` — the
  four-layer precedence (user > Assistant > team > default),
  `decided_by: team`, fail-closed user requests unchanged, forced
  variants still rejected. Run-record mode-split and nullability
  validators beside the schema-level negatives.
  `test_import_containment.py` — the **static containment scan** (core
  legs, no extra needed): an **AST import scan** (`Import`/`ImportFrom`
  roots) proving `clawteam` is importable only from
  `src/agentteam/compat/clawteam.py` and `agentteam.compat` only from
  `src/agentteam/coordination/clawteam.py` (plus `tests/compatibility/`),
  **plus a textual-reference allowlist**: any occurrence of the token
  `clawteam` in `src/agentteam/` outside the allowlisted files fails —
  catching `from clawteam …`, dynamic imports, and import-free
  ClawTeam-specific branches (the section 10 boundary, mechanically
  enforced).
- **Provider conformance** (`tests/coordination_suite.py`, a shared base
  class that is not collected directly): space/member lifecycle with the
  lead recorded at creation and `members()` returning the full roster;
  task create/get/list/update in the **protocol vocabulary** (a status
  outside `SubstrateTaskStatus` is rejected by both providers); DTO
  shapes including the remaining-blockers semantics; dependency
  auto-unblock; **unknown-referent rejection** (`create_task`/`task`/
  `update_task` with an unknown id raises `UnknownTaskError`; the
  provider-level cycle scenario is structurally unconstructable and is
  replaced by this relabel); the **claim scenario** (a second caller
  updating a `running` task raises `TaskClaimError`; the owner's
  completion succeeds); mailbox send/receive claim semantics (second
  receive empty; `SubstrateMessage` shape); deterministic ordering;
  snapshot create/read/restore round-trip; **cleanup postcondition —
  post-cleanup ops raise `SpaceUnavailableError` and the archived
  snapshot survives (never a file-deletion assertion)**; two spaces with
  no task/message crossover; `info()` identity. Instantiated twice:
  `tests/integration/test_coordination_local.py` (core, six legs — plus
  the local-only guarantees: consumed-retention, tombstone, strict
  transition validation) and
  `tests/compatibility/test_clawteam_provider.py` (extra-only, three
  legs — plus the mapping/translation pins: `running ↔ in_progress`,
  `TaskLockError → TaskClaimError`, `KeyError → UnknownTaskError`,
  `content → body`, roster reconciliation) — the two providers held to
  one standard.
- **Integration**: `test_team_run_execute.py` — the section 11 lifecycle
  over the local provider with fake harnesses: pending-record-with-tasks
  before side effects, deterministic topological registration (a
  forward-reference skeleton registers in sorted order with exact
  `substrate_id` and `task-created` event-order assertions), per-member
  workspaces, staged rendering (7a stubs; 7b launch-time), launch-on-ready
  order, member-result parsing, deliverable validation/archiving/
  materialization, handoff claim-and-embed, blinding, ledger-before-send,
  stop → snapshot copy-out → cleanup ordering, archive finalization,
  `--render-only`, exit codes, reserved fields fail closed.
  `test_team_run_faults.py` — the **fault-injection matrix**, with a
  `FaultInjectingProvider` double (wraps the local provider, raises at a
  named op). Provider rows cover **all eleven runtime-invoked
  operations**: `create_space`, `info`, `add_member`, `create_task`,
  `update_task`, `send`, `receive`, `wait` (timeout), `snapshot`,
  `read_snapshot`, `cleanup` (`restore` is conformance-only and never
  runtime-invoked — no row, by that sentence). Non-provider rows: member
  invocation failure post-retry (asserts the in-flight sibling
  **finishes**, its completion still reaches the provider, and
  dependents go `abandoned` eagerly); attempt timeout; launch-time render
  failure; the missing-body abort (injected on the transported edge);
  SIGINT cancellation (exit 130); fault abort with a member in flight
  (process tree terminated, invocation `cancelled`). **A `receive` raise
  is a fault abort** (taxonomy by cause: provider raise =
  infrastructure). `read_snapshot` gets two rows — green path (run
  `failed` exit 1, `snapshot-failed` event, null `substrate.snapshot` per
  section 6) and failing path (`snapshot-failed` event, primary
  `failure_reason` kept). Every row asserts: terminal `run.json` with
  all-terminal `tasks[]` (the abandon sweep observed), **exactly one
  `processes-stopped`** (unconditional), a `provider-cleanup` event
  **iff a space id was minted** (the `create_space` row asserts its
  absence, together with the null namespace/snapshot of section 6), no
  orphan process, and a clean manifest verification. The cascade rows use
  a **tests-only parallel-branch template** (a root; two parallel mid
  tasks — one fails, the sibling completes on merit; a dependent of the
  failed task, eager-abandoned; a task blocked only on the survivor,
  never launched, closed by the sweep) so eager abandonment,
  sibling-on-merit completion, sweep closure of an unrelated branch, and
  the all-terminal invariant are proven generally; the committed 3-chain
  acceptance fixture is unchanged. The matrix is **G3 evidence**.
- **Acceptance**: `test_team_lifecycle.py` — the section 13 conditions
  1–12 end-to-end through the CLI.
- **Compatibility**: the ClawTeam provider suite stays in
  `tests/compatibility/` with the existing `importorskip` conftest and the
  owner-state guard, so the six core legs keep proving clean skip without
  the extra; under a `failed-routed` disposition the failing scenario is
  retained as a dated strict-xfail per section 9.2. No new pytest marker
  is introduced (`--strict-markers`; the split stays directory + CI-job
  based).
- **Cross-platform**: the local provider's file semantics (atomic rename,
  ordering, permissions) run on all three OSes on the core job; any
  Windows/macOS deviation is fixed, never skip-listed silently (M1a §18
  discipline).

## 15. CI (delta to M1a §16)

No new jobs; the 12-job shape holds:

- **scaffold** (3 OS × Python 3.11/3.13, six legs): gains the local
  provider conformance suite, the team unit/integration tests including
  the fault matrix and the containment scan, the section 13 team
  acceptance through the CLI on fakes (member-result mode included), and
  `atm team validate` on the committed template — alongside everything it
  already runs (schema check/reproduction — now over twelve files —
  direct acceptance, example-package hash identity).
- **clawteam** (3 OS × Python 3.11, three legs): gains the ClawTeam
  provider conformance + lifecycle tests beside the existing 12
  qualification scenarios (updated for the seam's `leader` parameter);
  stays green under either G5 disposition (parity, or the dated
  strict-xfail of the failed branch).
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

1. `feat(domain): add team-template, team-run-request, and member-result contracts; extend the run record with team mode`
2. `feat(coordination): add the CoordinationSubstrate protocol and the local deterministic provider`
3. `feat(run): execute team-run requests over the coordination seam` — the
   member-result render/parse dispatch in `harness/` lands here with the
   direct-path regression pinned
4. `test(poc): add deterministic team-lifecycle acceptance`
5. `feat(coordination): add the optional ClawTeam provider behind the qualified seam` — this commit also carries the seam's `create_space(leader)` signature change and the qualification-test update (section 9.2)
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
  behavior, or schema — the one-Member subset stays byte-compatible, and
  the review/synthesis vendor contracts stay untouched (section 2
  decisions 3 and 11).
- ClawTeam-conditional code outside `src/agentteam/compat/` plus
  `src/agentteam/coordination/clawteam.py` is a violation (the section 10
  measurement boundary, enforced by the section 14 static scan).
- A ClawTeam provider failure blocks describing ClawTeam as qualified and
  sets the G5 disposition to `failed-routed` with the section 9.2 failed
  branch applied; it never blocks the local path; do not silently fork,
  vendor, or make it mandatory (M1a §18, carried). **Closing M1b with
  ClawTeam's status implicit, or with red required CI, is itself a
  violation** (section 1 item 3).
- Stop on any run-time mutation of a portable Assistant package or
  TeamTemplate; the mutation check covers every member bundle and the
  template (deliverable materialization happens before the successor's
  baseline hash, section 11.2).
- Always stop AgentTeam-owned processes before provider `cleanup`, and
  always run the abandon sweep and write the terminal record **before**
  the manifest for any run that wrote the pending record (the section
  11.4 invariant); provider cleanup never stops processes (recorded
  caveat; section 8).
- No dynamic member creation, no hidden members, no nested runs, no MCP,
  no overlays, no team-mode ensembles or synthesis: requests or templates
  carrying them fail closed (exit 2); reserved fields stay empty
  (sections 6, 19).
- Never upgrade `independence.achieved`; record honestly; a template
  declaring `mechanical` fails closed in M1b (no enforcement evidence
  exists yet); the run layer never sends an automatic handoff message
  across a declared independence pair (section 11.2).
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
  section 10 exit-criterion decision (RISKS R01/R08 rows) and the G5
  failed branch, not a silent fork.
- The team-mode extension forces a breaking change to a direct-mode record
  → section 6 contract design error → plan revision before code
  (protects "one record kind").
- Team acceptance is flaky on one OS → file-semantics bug in the provider
  or runner (R30-class) → fix with a platform-scoped regression test,
  never a skip-list.
- A felt need for live evidence to de-risk member choreography or the
  member-result vendor channel (R12) → M1b's deterministic tier is the
  wrong place → route to the M1c plan's budget ask (section 18).

## 18. Committed later milestones (deltas and handoffs)

M1a §19 remains the roadmap of record. M1b-specific handoffs:

- **M1c (PoC B)** inherits: the live-budget ask (its own ceiling; M1a's
  5-of-30 remain individual owner decisions), the section 10 exit-criterion
  decision (taken before PoC B starts), **the member-result live
  handoff — first live vendor acceptance evidence for the
  `member-result-v1` schema across the vendors' structured-output
  channels** (deterministically proven in M1b; a named risk until then),
  dynamic-member policy enforcement over the reserved `dynamic_members`
  field, `origin: ephemeral` and the hidden-member roster projection (the
  reserved `visibility` semantics), member-driven handoff acking (the
  dormant `acks` vocabulary) and member-to-member messaging enforcement,
  relaxation of the owner bijection under the Lead-driven flow, team-mode
  ensembles if evidence warrants, the HB-03 constraint semantics once the
  owner answers, and the R12 live tool-call-compliance question. The
  two-leg live reality (ADR 0036) stands until fresh Grok probes plus an
  owner decision.
- **M2** inherits: the reserved `parent`/`depth`/`nested_runs[]` fields,
  the nesting contract (team-execution-model §6), the multi-run-process
  reality the stable ClawTeam root already supports (section 9.2), and
  the `atm` MCP server over the same versioned contracts.
- **M3** inherits: `overlay_refs` stays reserved-empty on every record
  M1b touches, and per-member `effective_definition_hash` remains computed
  state — the R15/overlay question is not foreclosed and must be answered
  before M3 starts.

## 19. Explicitly outside M1b

- Live team execution, PoC B, and any model call (M1c);
- dynamic/ephemeral member creation, **hidden visibility**, and their
  policy enforcement (M1c); team-mode ensembles and synthesis (M1c+, on
  evidence); member-driven acking and messaging (M1c); nested TeamRuns
  and the MCP server (M2); overlays and evolution (M3); operational mode
  and watchers (M4);
- team-level `constraints` semantics (HB-03 — deferred out of M1b by
  owner decision, ADR 0039; the question stays open);
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
item tickable against the frozen tree — the r1 and r2 passes are recorded
in `docs/reviews/2026-08-24-m1b-plan-review-at-14dc218.md` and
`docs/reviews/2026-08-24-m1b-plan-review-at-54728c8.md`, resolved per
section 21):

1. scope: deterministic-only M1b, zero live calls, M1c/M2/M3 boundaries
   (sections 1, 11, 18, 19);
2. provider order, the never-launches-a-harness rule, and the explicit
   ClawTeam disposition at close with a green-CI failed branch
   (sections 1, 2, 3, 8, 9.2);
3. one record kind: the mode-discriminated union keeps direct-mode
   `run.json` byte-compatible; exactly three new + two regenerated schema
   files; the mode split is schema-level-enforced and the lifecycle
   nullability is model-enforced, both with negative tests
   (sections 2, 5, 6, 14);
4. contract fidelity: section 6 against team-execution-model TC-01..TC-06
   and §3, the glossary terms, and the reserved markers in
   `domain/run.py` / `resolution/selection.py`;
5. ClawTeam constitution intact: extra-only, exact pin, one import module,
   containments, the stable process root (ADR 0015), caveats restated
   verbatim, the seam's `leader` delta confined to the compat module
   (sections 4, 5.1, 9.2);
6. exit criterion: r0 wording carried verbatim; the measurement rule is
   symmetric, mechanical, and mechanically enforced; the decision
   timeline is owner-owned (sections 10, 14);
7. the task data flow is decision-complete: skeleton ids and forward
   references, `goal` interpolation, owner bijection, deterministic
   topological registration, the protocol status vocabulary with run-only
   terminals and residual projections, claim semantics, launch-on-ready
   with staged rendering, member-result parsing with deliverable
   archiving/materialization, handoff construction/transport/blinding,
   the failure cascade and fault abort, and the finalization invariant
   with the abandon sweep (sections 6, 8, 11);
8. gate evidence is mechanically checkable and each gate names its VERIFY
   entry; the fault matrix (eleven provider ops, conditional assertions)
   is G3 evidence (sections 3, 14);
9. test matrix and CI mapping: conformance suite shared across providers
   with local-only guarantees separated, core-vs-extra job split, no new
   marker, direct regression retained, containment scan on core legs
   (sections 14, 15);
10. stop rules and falsification routing cover the risks register rows
    R01/R02/R08/R12/R30-class/R33-lesson/R34 (sections 12, 13, 17);
11. approval/traceability mechanics: DECISIONS entry naming file + SHA,
    status flip in the following commit, review immutability (header,
    sections 2, 3).

**What the owner decides at approval** (all [finalize-at-approval] items):

- the ClawTeam exit-criterion wording and the section 10 measurement rule;
- the zero-live-call budget (section 11);
- the CLI surface: kind-discriminated `atm run`, the team-mode flag gate,
  and the single `atm team validate` verb (section 7);
- the section 6 optional/reserved field sets as specified (including the
  reserved `constraints`, `visibility`, and `dynamic_members` handling)
  and the `MemberResultV1` field set (`summary`, `deliverables`,
  `risks`).

Approval-time docs follow-ups (ride with the G0 ADR, not this plan's
commits): the glossary's CoordinationSubstrate row gains a dated amendment
recording that `stop` is a run-layer duty (stop-before-cleanup), not a
provider method (section 8; r1-review hygiene item 1).

HB-03 is **not an approval-time fork**: the owner decided (2026-08-24,
ADR 0039) that M1b defers constraint semantics entirely; the semantic
question — whether a team-level constraint binds above an Assistant
preference — stays open in QUESTIONS.md with the recorded options, and
answers there whenever the owner takes it up.

**Traceability.** Register/requirement rows this plan implements or
touches: TC-01..TC-06 and TE-01, TE-02, TE-03 (deterministic tier —
section 13 condition 6), TE-06, TE-07 (sections 6, 11, 13); TE-04/TE-05
deferred (M1c/M2, section 18); HB-03 (deferred; section 7/this section);
XC-04 audit (sections 8, 11.5, 12). Risk rows: R01/R08 (sections 9.2, 17
routing), R02 (no fork modules reused; the failed-branch xfail follows
its precedent), R12 (sections 6, 11, 13, 17), R30-class file semantics
(section 14), R33 lesson (section 13), R34 (section 12). Open questions:
exit criterion (section 10, finalizes at approval), HB-03 (deferred,
open), Q4/Q6 (section 19, stay outside), R15/overlay (section 18, not
foreclosed). Decisions inherited: ADRs 0003, 0007, 0014, 0015, 0016,
0018, 0021, 0022, 0033 (amendment convention), 0036, 0037, 0038, 0039,
0040.

Implementation begins only after review findings are resolved and the
owner explicitly marks this plan approved (G0). Project-local sources:
`docs/discovery/team-execution-model.md` (v2.3), the glossary,
`docs/evidence/clawteam-qualification-2026-08-23.md`, the M1a plan as
amended, and the two review records; volatile facts (CLI versions,
capability evidence) are rechecked at their execution gate, not trusted
from this text.

## 21. Revision record

- **r0** (2026-08-24, `856d525`): 7-section skeleton — the M1a G8 naming
  deliverable (provider order, named contracts, draft exit-criterion
  wording, PoC boundary, outside list, approval checklist).
- **r1** (2026-08-24, `14dc218`): full expansion per the r0 approval
  checklist item 1 (21 sections; gates; contracts; test matrix; budget;
  stop rules). Every r0 section mapped into r1. **Naming resolution,
  stated explicitly (r1-review hygiene item 2): r0's `TeamRunV1` and
  `MemberV1` contract names are superseded by the extended run-record
  family** — `TeamRunV1` → the team-mode variant of `RunRecordV1`
  (one record kind, M1a §7), `MemberV1` → the embedded `MemberRecordV1`.
  A naming supersession, not a scope drop — recorded as such.
- **r2** (2026-08-24, `54728c8`): resolved the first independent review
  (`docs/reviews/2026-08-24-m1b-plan-review-at-14dc218.md`; ADR 0039) —
  explicit ClawTeam disposition, mode-discriminated union + schema-level
  negatives, HB-03 deferred (owner), the `implementer` fixture for real
  team-decided/mixed evidence, the decision-complete task data flow
  (11.1–11.3), wire shapes + `create_space(lead)`, the finalization
  invariant + ledger + copy-out (11.4–11.6), the fault matrix, and the
  static containment test.
- **r3** (2026-08-24, this commit): resolves the second independent
  review (of r2; `docs/reviews/2026-08-24-m1b-plan-review-at-54728c8.md`;
  ADR 0040). Findings and resolutions:

| Finding | Resolution | Sections |
| --- | --- | --- |
| B1 — pending team record not representable | Lifecycle nullability: pending/running permit null namespace/achieved/snapshot; `succeeded` requires all three; failed/cancelled allow null snapshot (copy-out failure) and null namespace iff no space; model validators documented in `schemas/README.md`, negative-tested; mirrored by the fault-matrix conditionality | 6, 11.4, 13, 14 |
| B2 — provider task semantics incomplete | `SubstrateTaskStatus` (protocol-only vocabulary; run layer writes `running`/`completed`); `running ↔ in_progress` bidirectionally in the ClawTeam adapter (seam untouched for status); run-only `failed`/`abandoned` never sent (auto-unblock-safety rationale + residual-projection rule); claim semantics (`TaskClaimError`) with strict transitions local-only; frozen DTOs incl. the remaining-vs-declared `blocked_by` disambiguation; `UnknownTaskError` + conformance relabel (provider cycles unconstructable); deterministic topological registration (Kahn + declaration order) | 3, 6, 8, 9.1, 9.2, 11, 11.3, 13, 14, 20 |
| B3 — team results were review-shaped | **Owner decision (ADR 0040): `MemberResultV1` now** — third new vendor-facing schema (`summary`/`deliverables`/`risks`, dialect-intersection-linted); additive harness output-contract dispatch (review path untouched, regression-pinned); deliverables = declared paths validated/hashed/archived and materialized into the successor workspace pre-baseline-hash; live vendor acceptance is a named M1c handoff | 2, 5, 6, 11.2, 13, 14, 15, 16, 18, 20 |
| B4 — automatic handoffs vs declared independence | **Blinded handoff** on declared-independence edges: no mailbox message/ledger row (the run layer never creates the declared-away edge); deliverables still materialize (the artifact under review); summary/risks omitted; marker recorded; missing-body abort counts non-blinded edges only; acceptance asserts transport on plan→implement and blinding on implement→review | 6, 11.2, 11.5, 13, 17 |
| B5 — failed-routed had no green-CI path | The failed branch: provider registry marks `clawteam` unsupported (`substrate: clawteam` exits 2 citing VERIFY); failing reproduction retained as a dated strict-xfail (R02 precedent); required CI green; close requires it (stop rule) | 1, 3, 6, 9.2, 14, 15, 17 |
| B6 — finalization vs fault matrix conflicts | Step 11 reordered (sweep → terminal record → manifest last); the **abandon sweep** named once and referenced by cascade/abort/cancellation; `processes-stopped` unconditional, `provider-cleanup` iff a space was minted (absence asserted on the `create_space` row); the matrix covers all eleven runtime ops (+`info`, `receive`, `read_snapshot`; `restore` conformance-only); `receive` raise = fault abort; copy-out defined as the three-step compound; parallel-branch tests-only template proves the general case | 11, 11.2–11.6, 13, 14, 17 |
| M1 — parity fixture cannot hold two run-record payloads | `minimal_payloads()` stays filename-keyed with the direct payload; `run_record_variant_payloads()` drives both variants + negatives | 6, 14, G1 |
| M2 — containment scan insufficient | AST import scan + textual token allowlist over `src/agentteam/` (catches `from clawteam`, dynamic imports, import-free branches) | 2, 10, 14 |
| M3 — per-run ClawTeam root broke the one-root rule | Stable `~/.agentteam/clawteam/` process root with per-run namespaces — **restores the ADR 0015 design**; multi-run processes supported (tests, M2 MCP); root outside the archive (ledger + copy-out are the archive evidence; "leftovers manifested" claims removed); tests use temp roots | 2, 5.1, 9.2, 11.6, 12, 18 |

Amendments after approval follow the ADR 0022/0033 convention
(in-document marker plus a dated amendment table) at amendment time.
