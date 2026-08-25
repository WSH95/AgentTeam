# AgentTeam M1b team-foundation plan — approved r6

- Status: **approved 2026-08-24 at G0 (ADR 0044).** The owner approved the
  frozen r6 text at full commit
  `760a8ae8c7021b0427bf29c84f005bebdd453bf6` after the independent
  confirmation at `87d23c6`. r6 resolves
  the four implementation-blocking areas and the medium/consistency
  corrections of the fifth independent review (of r5;
  `docs/reviews/2026-08-24-m1b-plan-review-at-12ca6c7.md`; resolutions
  mapped in section 21), after r5 resolved the fourth round, r4 the third,
  r3 the second, and r2 the first
  (`docs/reviews/2026-08-24-m1b-plan-review-at-3d0211a.md`,
  `docs/reviews/2026-08-24-m1b-plan-review-at-6d3f329.md`,
  `docs/reviews/2026-08-24-m1b-plan-review-at-54728c8.md`,
  `docs/reviews/2026-08-24-m1b-plan-review-at-14dc218.md`).
  Implementation starts only after owner approval as a `DECISIONS.md`
  entry naming this file and its commit SHA (the M1a §21 convention; ADR
  0021 precedent; the status line flips to `approved` in the following
  commit because a commit cannot name its own SHA). Per M1a plan §18,
  nothing here begins in the M1a approval scope.
- Revision baseline: r5 was full commit
  `12ca6c730f99816ed79c6e0537de021d25dd24b2` (fourth-round findings
  resolved; reviewed again; plan SHA-256
  `95ff6ab3816efd61db845216b34aecb64b8d22efde3f13a727027c612a44acf4`);
  r4 was `3d0211a`; r3 was `6d3f329`; r2 was `54728c8`; r1 was `14dc218`; r0 was
  `856d525` (`docs(plans): draft M1b team foundation (proposed; G8
  naming deliverable)`).
- Prerequisites carried in: the G4-qualified ClawTeam seam
  (`docs/evidence/clawteam-qualification-2026-08-23.md`), ADR 0015 (exact
  pin, extra-only, subprocess backend never used), ADR 0018 (measurement
  decides), ADR 0037 (build-vs-reuse reaffirmed post-G6), ADR 0039 (r1
  review recorded; HB-03 constraints deferred out of M1b), ADR 0040 (r2
  review recorded; MemberResultV1 and the stable ClawTeam root chosen by
  the owner), ADR 0041 (r3 review recorded; the snapshot-retention
  policy), ADR 0042 (r4 review recorded; explicit workspace grants,
  durable execution allocation, cleanup verification handshake,
  publication barrier, canonical deliverables, occurrence-level
  containment), ADR 0043 (r5 review recorded; explicit team render scope,
  isolated Grok project profiles, launch-time target baselines, and the
  task/invocation terminal-state matrix).
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
   section 14 static containment scan (AST imports plus an exact
   occurrence inventory), not only by the section 17 stop rule.
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
12. **Workspace mutation is an explicit, least-privilege task grant**
    (ADR 0042). Every workflow task declares `workspace_access:
    read-only | workspace-write` (default `read-only`), the resolved
    grant is audited in the team run record, and adapters map it to
    version-supported controls. Direct runs and synthesis remain
    read-only and byte/argv-compatible (sections 6, 11.1).
13. **Execution binding means durable allocation, not inferred history.**
    A null team-member binding means no durable invocation was allocated;
    allocation and binding precede the provider's `running` transition
    and process spawn. Model validators enforce only in-record rules; an
    archive verifier enforces the invocation/run-record bijection
    (sections 6, 11.1, 11.4).
14. **Snapshot retention uses an explicit cleanup handshake.** The run
    layer passes its verified-copy-out result to provider cleanup, which
    returns a path-free structured outcome. ClawTeam deletes only the
    verified snapshot; every unverified path retains it (sections 8, 9.2,
    11.6; ADR 0042 refines ADR 0041's intent).
15. **Task completion is a publication barrier.** Result persistence,
    deliverable archive/materialization, and handoff ledger/send finish
    before provider completion can unblock successors. Declared-content
    errors fail the task; infrastructure publication errors abort the run
    (sections 11.2–11.4).
16. **Team rendering is explicit and never mutates an authenticated
    vendor home.** `RenderContext.invocation_scope` is a standalone
    discriminator (`standalone` default | `team-member`); only the team
    runner selects `team-member`. It is independent of output shape and
    workspace access. Grok team profiles are collision-checked,
    per-invocation project files; direct/synthesis recipes remain exact
    regressions (section 11.1; ADR 0043).
17. **Run-task terminal states describe what happened, not merely what
    the provider still projects.** `failed` is the causal task failure,
    `cancelled` is non-causal durably allocated work stopped before task
    completion by abort or user cancellation, and `abandoned` is
    non-causal never-allocated/never-launched cascade remainder.
    Provider-completion ambiguity cannot rewrite a successfully published
    invocation (sections 6, 11.3–11.4; ADR 0043).
18. **Approval convention**: owner approval of this plan is a DECISIONS
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
| G0 | Approve this plan | Five independent reviews are recorded in `docs/reviews/` (r1 `14dc218`, r2 `54728c8`, r3 `6d3f329`, r4 `3d0211a`, r5 `12ca6c7`); findings resolved; owner approval as a DECISIONS entry naming this file and the approved commit SHA, committed before product source work; status flips to `approved` in the following commit |
| G1 | Team contracts and schemas | `TeamTemplateV1`, `TeamRunRequestV1`, and `MemberResultV1` models land with `team-template-v1.schema.json`, `team-run-request-v1.schema.json`, and `member-result-v1.schema.json` checked in; workflow tasks gain optional-default-read-only `workspace_access`, team run `tasks[]` audit the required resolved value and the three run-only terminals, and one shared `SubstrateKind` in `domain/team.py` is imported by `domain/run.py`; `run-record-v1.schema.json` is regenerated as the mode-discriminated `oneOf` (direct variant field-identical) and `harness-invocation-v1.schema.json` is regenerated with `team` in the `DecidedBy` enum — **three new files, two regenerated, nothing else** (section 8 types remain internal); all new kinds are registered, direct/team schema variants and lifecycle negatives are tested, `member-result-v1` passes the vendor-dialect lint, the pre-M1b suite stays green, and `atm team validate` passes on the committed template |
| G2 | CoordinationSubstrate protocol and local provider | `coordination/protocol.py` (status/DTO/error types plus `CleanupOutcome`) and `coordination/local.py` land; the shared conformance suite is green over the local provider — including both `copy_out_verified` cleanup values, path-free outcomes, inoperability plus archive-snapshot survival, and all existing lifecycle/task/mailbox/snapshot/no-crossover cases; the occurrence-level containment scan lands on all core legs |
| G3 | Team runner integration | `atm run` executes the committed request over fakes/local per section 11: access resolution and exact scope-aware adapter rendering, disposable preflight plus the state-free render-only branch, copy verification followed by launch-time target baselines, durable invocation allocation/binding before running/spawn, member-result persistence, canonical deliverable archive/materialization, the completion publication barrier, handoff transport/blinding, ledger, cleanup handshake, archive binding verifier, and terminal-state-aware failure finalization; the expanded fault matrix is green; run records audit `tasks[].substrate_id` and `workspace_access`; direct/synthesis paths remain byte/argv-compatible |
| G4 | Deterministic team-lifecycle acceptance | The section 13 acceptance is green through the CLI on all six core legs, including exact read-only/workspace-write grants (`plan` and `review` read-only; `implement` workspace-write), a real fake-created deliverable, ordering/publication, transport, ledger, blinding, at least one `decided_by: team`, and at least two harnesses; no vendor executable is invoked |
| G5 | ClawTeam provider disposition | `coordination/clawteam.py` lands behind the extra; **either** the same conformance suite plus the section 13 lifecycle pass over the ClawTeam provider on the three-OS `clawteam` job — with containment tests holding (event-bus reset, the one process-scoped data root of section 9.2, opaque `atm-<hex8>` namespaces, owner `~/.clawteam` refused, no subprocess/tmux import), the seam's `create_space` carrying the logical lead, `members()` reconciling to the full roster, the `running ↔ in_progress` mapping and error translations pinned, caveat behaviors pinned (stop-before-cleanup ordering; roster reconciliation), verified-true deleting only the exact snapshot and every false/failure path retaining it with path-free outcomes, and clean skip without the extra on the core legs — **or** the failed branch is applied: a dated failure record is written and routed to the section 10 decision, the registry's committed `CLAWTEAM_DISPOSITION` marks `clawteam` **unsupported** (`substrate: clawteam` exits 2 citing the VERIFY record), the success-oriented provider suite is disposition-gated by a dated, VERIFY-cited module-level skip while the failing reproduction is retained as a dated strict-xfail outside that skipped module (section 9.2), and required CI is green. Both outcomes close the gate; only the disposition differs |
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
                       #   and not marked unsupported; carries the committed
                       #   CLAWTEAM_DISPOSITION metadata exposed through a
                       #   generic registry API and read by the test gate
    protocol.py        # CoordinationSubstrate Protocol, SubstrateTaskStatus,
                       #   DTOs (SubstrateTask, SubstrateMessage, SubstrateInfo,
                       #   CleanupOutcome),
                       #   error taxonomy
    local.py           # LocalCoordinationProvider (file task store, mailbox, snapshot)
    clawteam.py        # ClawTeamCoordinationProvider (imports agentteam.compat.clawteam
                       #   only; status mapping and error translation live here)
  domain/team.py       # TeamTemplateV1, TeamRunRequestV1, MemberResultV1,
                       #   shared SubstrateKind (+ embedded sub-models:
                       #   MemberOverridesV1, HandoffPayloadV1)
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
  unit/test_import_containment.py      # AST import scan + occurrence inventory (§14)
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
  `harness/` (the additive output-contract and workspace-access dispatch
  of sections 6/11.1 — `member-result` rendering beside the untouched
  review path, with direct/synthesis argv unchanged),
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
- `workflow_skeleton[]` — task shapes `{id, subject, owner, blocked_by[],
  workspace_access?}` with placeholders; `workspace_access` is
  `read-only | workspace-write`, optional only so omission has the closed
  default `read-only`. It is a shape, never a project's task list. `id` is a slug
  unique within the template and is what `blocked_by[]` references
  (forward-declared references are legal — validation is
  declaration-order-insensitive; registration order is section 11's
  concern); `owner` is a roster name. **Owner bijection (M1b):** the
  skeleton's owners are exactly the member set, one task each. This is an
  explicit V1 product constraint that keeps one member equal to one
  invocation and makes success require one durable binding per member;
  it is not inferred from field requiredness. M1c relaxes it with the
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
- Declared deliverable paths are validated and canonically collision-keyed
  by the run layer against the member's isolated workspace (NFC,
  casefolded comparison on every OS, every component checked without
  following symlinks); handling is section 11.2's.
- There is deliberately **no status field**: mechanical success is the
  run layer's judgment (M1a rule — exit 0 plus valid structured output);
  member-reported blocking/acking is M1c choreography.
- **The output pipeline, end to end** (the internal interface, pinned):
  `RenderContext` gains an `output_contract` discriminator
  (`normalized-review` default | `member-result`; the existing synthesis
  discriminator is untouched) and a `workspace_access` discriminator
  (`read-only` default | `workspace-write`), plus the independent
  `invocation_scope` discriminator (`standalone` default | `team-member`).
  Direct and synthesis callers use all defaults and render byte-for-byte
  as before; the team runner supplies `team-member` and the resolved task
  grant. Neither `output_contract` nor `workspace_access` is a side channel
  for scope. `schema_name_for` returns
  `member-result-v1.schema.json` when the contract says so, and delivery
  uses the same per-vendor channels and `vendor_projection`.
  **`HarnessAdapter.parse()` is not touched**: the team runner extracts
  the structured payload through the adapter's existing
  `StructuredExtractor` and validates it with
  `MemberResultV1.model_validate` — a validation failure is an invocation
  failure under the M1a mechanical rule. The validated result's canonical
  archive home is `legs/inv-<member>/member-result.json`, written by a
  new `RunArchive.write_member_result()` beside `write_review()` and
  recorded as a `member-result` artifact reference on the invocation — so
  the result survives regardless of raw-stream retention.
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
    `MemberRecordV1` shape (`name`, `assistant` ref + package hash,
    per-member `effective_definition_hash`, `execution {kind, ref}`)
    extended with `origin: persistent` (M1c adds `ephemeral`),
    `visibility: visible` (hidden is M1c), and the member's recorded
    harness selection — with one team-variant divergence: **`execution`
    is nullable until durable allocation** (`null` means no pending
    invocation record was ever allocated; the direct variant keeps its
    required binding, so field-identity stands). Representable model
    validators require every binding on `succeeded`, require every
    present binding to have `kind == invocation`, and reject duplicate
    refs. They deliberately do not infer historical task states. The
    archive verifier supplies the cross-file invariant at finalization:
    every present ref resolves to one terminal invocation; every durable
    member invocation has exactly one binding; null has no invocation
    record. Per-member
    workspace `target {before, after}` hashes are recorded on the
    invocation **as facts** — team-mode mutation semantics are section
    11.2's; the direct-mode immutability condition is not a team-mode
    rule;
  - `substrate {kind: local | clawteam, namespace, snapshot {id, path,
    sha256}}` — `kind` uses the single `SubstrateKind` alias defined in
    `domain/team.py` and imported by `domain/run.py`; the snapshot reference
    is the section 11.6 copy-out;
  - `tasks[]` — run-level task rows `{id, subject, status, owner,
    blocked_by[], workspace_access, substrate_id}`; `workspace_access`
    is the required resolved grant from the template (omission already
    defaulted to `read-only`); `id` **is** the skeleton id;
    `substrate_id` is the provider-minted id (null until registered);
    status ∈ `blocked | pending | running | completed | failed | cancelled |
    abandoned` — the run vocabulary is the section 8 protocol vocabulary
    plus the three **run-only terminals** `failed`/`cancelled`/`abandoned`,
    which never cross the protocol; `failed` is a causal failure,
    `cancelled` is non-causal durably allocated work stopped before task
    completion by abort or SIGINT, and `abandoned` is non-causal
    never-allocated or never-launched remainder. The run-level rows are
    authoritative; the provider's projection is secondary. The record's
    `blocked_by[]` holds
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
`task-cancelled`, `task-abandoned`, `message-sent`, `message-claimed`,
`snapshot-taken`, `snapshot-archived`, `snapshot-failed`,
`snapshot-retained`, `processes-stopped`,
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
- `--render-only` is a distinct pre-execution branch: it validates,
  resolves, selects, and emits the section 11.1 stub renders under the
  requested output root, then exits 0. It creates no run archive,
  provider space, real member workspace, invocation record, or execution
  binding and launches nothing.
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
vocabulary is the run-record vocabulary minus the three run-only terminals
(`failed`, `cancelled`, `abandoned` — section 11.3); (ii) protocol ↔ ClawTeam upstream
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
- `CleanupOutcome {space_closed, snapshot_state, warning_codes[]}` from
  `cleanup()`, where `snapshot_state ∈ none | retained | removed |
  unknown`. Warning codes are a closed, path-free enum covering upstream
  cleanup and snapshot deletion; they carry no exception text, root path,
  or owner-machine fact. This is an internal immutable DTO, not a JSON
  Schema.
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
  `cleanup(space, *, copy_out_verified: bool) -> CleanupOutcome`. The run
  layer passes `true` only after `snapshot` + `read_snapshot` + atomic
  archive write + digest verification all succeeded; all other paths pass
  `false`;
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

Successful-cleanup postcondition (provider-neutral, asserted by the
conformance suite): when `CleanupOutcome.space_closed` is true, further
operations on the space raise `SpaceUnavailableError`; when
`copy_out_verified` is true the run-layer archive copy remains readable.
Provider-side snapshot disposition is reported honestly by
`snapshot_state` and is provider-specific — never inferred from space
inoperability.

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
through untranslated only inside the provider module. Operational errors
map to exit `1` (runtime) or `2` (invalid input) per the M1a table;
finalization cleanup/deletion problems are normalized into
`CleanupOutcome.warning_codes` and follow section 11.4's non-masking
hygiene rule.

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
  writes a `closed` tombstone and **deletes nothing**, irrespective of
  `copy_out_verified`; it returns `space_closed: true` and
  `snapshot_state: retained` when a snapshot exists (`none` otherwise).
  The space is archive-resident and is sealed by the manifest, which
  finalizes after cleanup (section 11.6).
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
server later) satisfy the seam's one-root rule. **What cleanup actually
leaves (qualification-verified):** successful upstream `cleanup` removes
the namespace's team/task state but **retains `snapshots/<space>` in the
root by upstream design** — the G4 suite asserts exactly that survival.
The retention policy (ADR 0041, made executable by ADR 0042's handshake):
`cleanup(space, copy_out_verified=...)` always attempts upstream cleanup.
When and only when the flag is true, it also attempts deletion of that
space's exact `snapshots/<space>` subtree inside AgentTeam's fixed root;
both actions are attempted even if either fails, and their path-free
warning codes are aggregated in `CleanupOutcome`. A successful deletion
reports `removed`; false retains an existing snapshot and reports
`retained`; no snapshot reports `none`; an inspection failure reports
`unknown`. Cleanup/deletion warnings are hygiene and never mask a green
run. A failed copy-out already fails the run and deliberately passes
false, leaving the provider-side snapshot as surviving evidence. Events
name only the opaque namespace, snapshot state, and warning codes — never
the root path. The root lives **outside the run archive**: the archive's
ClawTeam evidence is the run-layer snapshot copy-out and message ledger
(sections 11.5–11.6), while residual root data is unmanaged local state
outside any manifest. Tests use temporary roots via the seam's reset
hatch and assert deletion cannot escape the exact space subtree.

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

**The failed branch** (G5 disposition `failed-routed`): the registry's
committed **`CLAWTEAM_DISPOSITION`** constant
(`coordination/__init__.py`, set at G5 close in the same commit as the
VERIFY entry) is the single fact both surfaces read. The CLI side:
`substrate: clawteam` exits 2 at step-1 validation citing the VERIFY
disposition record (structurally outside the fault matrix, whose scope is
runs that wrote the pending record). The CI side: the success-oriented
provider suite (`tests/compatibility/test_clawteam_provider.py`) is
gated at module level by a **dated skip citing the same VERIFY record**
— dated, reasoned, disposition-driven, never silent — while the failing
scenario is retained as a **dated strict-xfail in a dedicated test file
outside that module-level skip**, with its node id asserted by a
failed-routed collection regression, so the reproduction flips visibly
if upstream behavior changes (the RISKS R02 xfail precedent). The CLI
queries only `provider_disposition(substrate)` and contains no
ClawTeam-specific branch/token. The pre-existing qualification scenarios keep their own
status honestly: a seam-level failure applies the same dated gating
scoped to exactly the scenarios it breaks, recorded in the same VERIFY
entry. Required CI is green under either disposition. Un-gating requires
a re-qualification event; full removal rides the owner's section 10 drop
decision.

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
  containment scan (AST imports + exact occurrence inventory) — so the numerator
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
   grammar, handoff vocabulary, workspace-access vocabulary), and the TeamRunRequest (`goal` present
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
   M1a §11) and resolve each owned task's `workspace_access` (omission →
   `read-only`). A team-member Grok selection on Windows is unsupported
   in M1b and fails here with exit 2 before a run directory: the bundled
   1.0.5 guide documents kernel enforcement only for Linux/macOS, and the
   stop rule forbids an unsandboxed continuation. **Render-only branches
   here** into section 11.1's disposable stub rendering and exits without
   entering step 4.
4. Create the pending team-mode `run.json` — full roster, template ref +
   hash, declared independence, and the **complete `tasks[]`** (DAG roots
   `pending`, the rest `blocked`, resolved `workspace_access`,
   `substrate_id: null`; lifecycle
   nullability per section 6) — **before** the coordination space exists
   and before any process starts.
5. Materialize one isolated workspace per member with the M1a per-leg
   copy mechanism. This step is **copy verification only**: hash the
   source, copy, and require `hash(copy) == hash(source)`. It does not
   populate an invocation's `target.before`.
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
   member with a deterministic handoff stub in disposable roots before
   any launch (exit 2 on failure); **7b** — at each launch, compose the
   real task document, materialize all incoming handoffs, render the final
   invocation in its real workspace, then compute `target.before` from
   that launch-ready workspace while excluding renderer-owned files by the
   same rule used for `target.after`.
8. Launch on readiness only (section 11.1): after 7b, durably write the
   pending invocation and its run-record binding, then claim/mark the
   provider task `running`, then spawn through the direct runner. Use
   fresh sessions, no provider process management, and the unchanged M1a
   one-transient-retry/no-substitution discipline.
9. Publish completion through section 11.3's barrier: persist the result,
   archive and materialize deliverables, ledger/send non-blinded
   handoffs, and terminalize the invocation before provider `completed`
   can auto-unblock successors; then update run state/events and schedule.
   Failure enters the cascade or fault abort according to section 11.3.
10. Finalize per sections 11.4–11.6: stop all AgentTeam-owned processes,
    take and archive the final snapshot (iff a space was created), then
    provider cleanup — always in that order.
11. Re-hash every member bundle (mutation check), run the **terminal
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
  Step 7a (*render-preflight-all-before-any-launch*) renders each member
  with a fixed handoff stub in disposable scratch/config/workspace roots,
  proving channel delivery, access mapping, environment policy, and argv
  guards without touching the real member workspace. Normal execution
  removes/excludes those roots before step 7b; render-only emits the same
  stub records beneath its requested output root and, per section 7,
  never creates execution state. Stub renders create no invocation
  records or bindings. Step 7b (*final-render-before-each-launch*)
  composes the real task document and renders in the real workspace when
  the task is pending; this is the archived render. A launch-time render
  failure is exit-1 runtime, fails that task, and leaves both invocation
  and binding absent.
- **Launch-time target baseline and durable allocation/binding point.**
  Step 5 proves copy identity only. During 7b, after incoming deliverables
  and blinding markers are materialized and the final renderer has
  declared every `files_written` path, compute `target.before` over the
  launch-ready workspace excluding those renderer-owned paths exactly as
  `target.after` does. Thus the baseline contains the received handoff but
  not injected task/config/Skill files. Only then write the
  deterministic `inv-<member>` pending invocation atomically, then write
  `members[].execution` to `run.json`, then transition the provider/run
  task to `running` and spawn. If binding or later launch fails, the
  finalizer discovers the deterministic invocation path, repairs the
  binding if necessary, and terminalizes the invocation. Thus anything
  that reached `running` has a resolvable binding, while `execution:
  null` means exactly that no pending invocation was allocated. The
  archive verifier enforces this cross-file rule before the manifest.
- **Workspace-access adapter mapping** (`invocation_scope: team-member`
  only; exact sets, no allow/deny overlap):
  - Claude read-only allows `Read,Grep,Glob,LS,Skill` and denies
    `Write,Edit,NotebookEdit,Bash,WebFetch,WebSearch`; workspace-write
    allows `Read,Grep,Glob,LS,Skill,Write,Edit` and denies
    `NotebookEdit,Bash,WebFetch,WebSearch`. Both retain `dontAsk`.
  - Codex read-only selects `-s read-only`; workspace-write selects
    `-s workspace-write` and explicitly adds
    `-c sandbox_workspace_write.network_access=false`. Both retain the
    current `approval_policy="never"` and `--ignore-user-config`. The
    workspace-write switch governs the shell filesystem sandbox; r6 keeps
    network disabled explicitly instead of treating write access as a
    network grant.
  - Grok on Linux/macOS writes exactly one guarded project file at
    `<member-workspace>/.grok/sandbox.toml`, recorded in
    `RenderedInvocationV1.files_written`; it never writes
    `$GROK_HOME/sandbox.toml`, because that is the persistent authenticated
    home and auth cannot be relocated. It `lstat`s `.grok` (creating an
    owner-only real directory if absent; refusing a symlink/non-directory)
    and exclusively creates `sandbox.toml`; if that leaf already exists as
    any filesystem object, rendering fails rather than overwriting target
    content. Through an injectable token source, the adapter obtains
    one 128-bit `secrets.token_hex(16)` nonce per render and names the
    profile `agentteam_<32-lowercase-hex>_<ro|rw>`; this works identically
    for real, disposable-preflight, and state-free render-only calls. The
    read-only form extends `read-only`, the writable form extends
    `workspace`, and both set `restrict_network = true`; the adapter passes
    that exact name to `--sandbox`, with the direct runner's cwd pinned to
    the member workspace so Grok discovers the project file. Before
    writing, it parses the existing
    persistent `$GROK_HOME/sandbox.toml` read-only (missing is valid) and
    fails closed if the file is unreadable/malformed or already defines
    the generated name under `profiles`, because Grok 1.0.5 otherwise lets the
    global profile win with a warning. Custom profiles are required for
    **both** grants because the built-ins can warn and continue when kernel
    enforcement is unavailable, whereas an explicitly requested custom
    profile fails closed. On Windows the mapping is refused at lifecycle
    step 3; fake/argv unit coverage remains OS-agnostic through injected
    platform facts.
  `invocation_scope: standalone` (all direct and synthesis callers) never
  enters these branches and retains its current read-only render recipe
  byte-for-byte — in particular, direct Grok remains exactly
  `--sandbox read-only` and writes no project sandbox file.
- **Version/evidence boundary.** These argv/tool mappings were rechecked
  without model calls on 2026-08-24 against installed Claude Code
  2.1.243, Codex CLI 0.149.1, and Grok 1.0.5 (`--help` plus Grok's bundled
  sandbox guide). The guide documents the custom-profile mechanism and
  fail-closed distinction on Linux/macOS, not a Windows kernel sandbox.
  That is planning evidence, not a live capability
  upgrade: version drift still fails the existing profile gate, and M1c
  must re-probe and run one writable declared-deliverable acceptance per
  then-supported harness before claiming live support.
- Team invocation ids are `inv-<member-name>`; the archive reuses the
  `legs/` layout; the existing `leg-started`/`leg-retry`/`leg-finished`
  events are reused per member invocation.

### 11.2 Handoff payload construction, blinding, and member context

- The per-member task document (`legs/inv-<member>/task.md`) is composed
  by the run layer: (1) the member's interpolated task subject, (2) the
  request `task_file` content verbatim, (3) a handoff section.
- On each mechanically successful member exit, before task completion,
  the run layer constructs one
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
- **Team-mode target semantics** (direct-mode immutability is unchanged
  and stays direct-only — the cond-1 evaluator and the shared-before-hash
  notion belong to the direct acceptance path, which team mode never
  runs): a member **may mutate its own isolated workspace copy** — that
  is what producing a deliverable is; `target {before, after}` is
  recorded per invocation as fact and is never a team-mode failure
  condition. Propagation is exclusively via **declared deliverables**:
  each declared path is a `RelPath` whose spelling must already be NFC.
  A canonical key `NFC(path).casefold()` is used on **every OS** for
  duplicate, prefix, and destination-collision checks, so `Foo`/`foo`
  collide uniformly and a decomposed Unicode spelling is rejected. The
  run layer `lstat`s every path component without following symlinks and
  requires the leaf to be a regular file — no directory, symlinked
  parent/leaf, traversal, or missing target. The casefolded `handoff/`
  tree is reserved. It also builds a deny-prefix set from every
  workspace-relative `RenderedInvocationV1.files_written` path: the exact
  file plus every non-root parent is reserved, and a deliverable equal to
  or below any prefix is rejected, preventing injected AGENTS/Skill files
  from being re-exported. Every contract violation exit-fails that
  invocation. **Undeclared writes are permitted but inert**: visible in
  the recorded after-hash, never propagated anywhere.
- **Deliverable materialization**: before a successor's baseline
  workspace hash is computed, the run layer materializes the deliverables
  it received into the successor's isolated workspace under
  `handoff/<predecessor-task-id>/`. It hashes the source, copies to the
  archive, verifies the archive digest, copies from the archive, and
  verifies the materialized digest before publication — closing mutation
  and copy-corruption windows. The final renderer then declares its owned
  writes, and the successor's recorded baseline is computed only afterward
  with those writes excluded exactly as they are from the after-hash. The
  baseline therefore includes the handoff and the successor can actually
  read its inputs; lifecycle step 5's copy digest is never reused as
  `target.before`.
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
- **Completion publication barrier** (one order, no alternatives): after
  exit 0, (1) extract and validate `MemberResultV1`; (2) write its
  canonical artifact; (3) validate/archive/hash every declared
  deliverable; (4) materialize every outgoing edge and prepare its
  handoff/blinding marker; (5) append each non-blinded ledger row and
  complete its provider `send`; (6) write the terminal successful
  invocation; (7) call provider `update_task(..., completed)`, which may
  auto-unblock; (8) update run `tasks[]`, emit `task-completed` and
  `task-unblocked`, then schedule. No successor baseline/render/launch can
  observe a completion before steps 1–6 finish. Invalid structured output
  or declared-content/path violations are invocation/task failures and
  use the dependency cascade. Artifact/ledger/materialization/hash I/O,
  provider send, or provider completion errors are infrastructure faults
  and abort the run; already-published ledger rows remain honest evidence
  and are never replayed. The step-7 fault window is special because step
  6 is already durable: if provider completion raises before or after its
  state commit, the invocation **stays `succeeded`**, the owning run task
  becomes `failed`, and the run fault-aborts. Its provider projection may
  be `running` (pre-commit raise) or `completed` (post-commit raise); both
  exact outcomes are legal and tested, and the scheduler launches no
  successor even if the provider already auto-unblocked one. Publication
  faults in steps 1–5 instead terminalize that invocation `failed` and its
  owning task `failed` before the abort.
- **Missing-body fault abort**: a claim that returns fewer bodies than
  the successor's incoming **completed, non-blinded** edges is a fault
  abort before launch (transport loss is infrastructure; launching with a
  silently empty handoff would violate transport fidelity invisibly).
  The non-blinded qualifier is load-bearing: without it, the committed
  fixture's blinded reviewer edge would abort the green path.

### 11.3 Task state propagation and the failure cascade

- After durable allocation/binding, launch begins with
  `update_task(running, caller=owner)`. Exit 0 plus a valid
  `MemberResultV1` begins, but does not itself finish, the success path:
  only section 11.2's completed publication barrier may call
  `update_task(completed, caller=owner)`. The provider then auto-unblocks
  dependents (`blocked → pending`), observed through `wait`; only after
  the run record/events reconcile may the scheduler launch them.
- **`failed`, `cancelled`, and `abandoned` never cross the protocol** — a
  correctness property, not a convenience: a failed task is never
  provider-side `completed` during the ordinary cascade, so provider
  auto-unblock cannot fire for its dependents. The sole exception is the
  explicitly ambiguous post-commit `update_task(completed)` fault in
  section 11.2: publication already succeeded, so the invocation remains
  succeeded while the run task records the infrastructure failure.
  Residual-projection rule by closure cause: a `failed` row may project
  `pending` (pre-allocation launch failure), `running`
  (execution/publication failure), or `completed` only in that post-commit
  fault; a `cancelled` row projects `pending` (aborted after allocation but
  before provider claim) or `running`; an `abandoned` row projects `blocked`
  or `pending`. A surviving sibling's completion may auto-unblock
  an abandoned row provider-side, which is unobserved and harmless because
  the scheduler issues no further waits or launches after failure/abort
  begins.
- Two named failure modes (exhaustive **by cause**):
  - **Failure cascade** (a task-level outcome): invocation failure
    post-retry, attempt timeout, launch-time render failure, invalid
    `MemberResultV1`, or an unsafe/missing declared deliverable → the
    run-level task `failed` → every transitive dependent `abandoned`
    eagerly (the event log reads causally: `task-failed` adjacent to its
    dependents' `task-abandoned`) → no further launches; **in-flight
    sibling invocations run to completion** (the M1a process contract
    terminates trees only for cancellation or timeout of *that*
    invocation — their evidence is kept, and their completions still
    reach the provider); any remaining never-allocated tasks are closed by
    the terminal sweep as `abandoned` at finalization (section 11.4); the
    run finalizes `failed`, exit 1.
  - **Fault abort** (an infrastructure failure): any provider operation
    raises **during lifecycle steps 6–9 — including the `tasks()` polling
    underneath `wait`** — or `wait` raises `WaitTimeoutError`, a handoff
    claim comes up short, or member-result/deliverable archive I/O,
    digest verification, successor materialization, ledger append, or
    handoff publication fails (section 11.2) → first freeze scheduling;
    mark the causal task `failed` when one exists (including a
    launch-preparation failure with no invocation); before the successful
    invocation write, terminalize any allocated causal invocation
    `failed`, while a pre-allocation cause keeps a null binding; after that
    write, apply section 11.2's provider-completion pairing. Then terminate
    non-causal in-flight member process trees per M1a §9 and mark those
    invocations `cancelled`; finalization's terminal sweep marks their
    tasks `cancelled` and only never-allocated remainder `abandoned`. Run
    `failed`, exit 1.
    **Finalization-phase provider operations are explicitly exempt from
    fault-abort semantics**: the copy-out compound (`snapshot` /
    `read_snapshot`), `cleanup`, and the section 9.2 snapshot deletion
    follow their own section 11.4 rows — a green-path copy-out failure
    fails the run; a cleanup or deletion failure is hygiene and the green
    run still exits 0.
- Snapshot-time status parity is asserted exactly for run-level rows
  whose status is in `SubstrateTaskStatus`, via per-provider test-side
  bundle readers (the ClawTeam reader translates `in_progress → running`;
  test LOC, ratio-exempt per section 10);
  `failed`/`cancelled`/`abandoned` rows are asserted against the
  cause-specific residual-projection rule only where the fixture makes the
  residual deterministic (fault-matrix rows).
- Team-run success = every run-level task `completed` and every member
  invocation succeeded. Team-mode exit codes are 0/1/2/130; exit 3 is
  unused (section 7).

### 11.4 Failure finalization contract

Standing invariant: **every run that wrote the pending record (step 4)
ends with, in order: stop every AgentTeam-owned process (the
`processes-stopped` event is emitted exactly once per finalization,
zero terminations permitted) → best-effort snapshot copy-out iff a space
was created → provider cleanup attempted iff a space was created → the
**terminal sweep** → terminal `run.json` with every row terminal
(`completed | failed | cancelled | abandoned`) **and every member's
execution binding consistent** — present for every durably allocated member invocation,
`null` exactly where no invocation record exists; every present ref
resolves to one terminal invocation and every invocation has one binding
(the archive verifier, not a history-guessing model validator, enforces
the cross-file rule on the step-5, step-7a, launch-render, post-allocation,
cascade, fault-abort, and cancellation paths) → finalized manifest.** Nothing may
reorder stop before cleanup, skip the sweep, or write the manifest before
the terminal record. The sweep is run-record-only (it never crosses the
protocol) and applies one exhaustive closure table: keep already-terminal
rows unchanged; if a task's provider-completion call returned but its run
row did not reconcile, finish it as `completed` and emit its missing
completion/unblock reconciliation events exactly once without scheduling;
mark the causal task
`failed` before the sweep, including the provider-completion ambiguity;
mark every non-causal durably allocated task that did not finish provider
completion `cancelled` and emit `task-cancelled` (terminalize a nonterminal
invocation `cancelled`, but preserve an already-`succeeded` invocation);
mark every remaining never-allocated/never-launched row `abandoned` and
emit `task-abandoned`. No successful invocation is rewritten. This is the
single mechanism that discharges the all-terminal invariant for arbitrary DAGs — cascade
remainders, fault aborts, and cancellation all resolve through it.

Per phase:

| Phase (step) | On failure |
| --- | --- |
| Validate / resolve / selection (1–3) | exit 2, **no run directory**; skeleton-id cycle/self/unknown and access-vocabulary rejection happen here, provider-neutrally |
| Render-only branch (after 3) | emit disposable stub render records under the requested output root, exit 0; **no run archive, provider space, real member workspace, invocation, or binding** |
| Pending record (4) | archive-creation failure: exit 2, nothing to finalize (M1a semantics) |
| Workspaces (5) | archive exists, no space yet — terminal `failed` + manifest; source-hash mismatch exit 2, copy mismatch exit 1 (mirrors M1a); only source/copy digests exist, never an invocation `target.before` |
| Space / roster / task registration (6) | if `create_space` itself failed there is no space — **no snapshot, no cleanup, and no `provider-cleanup` event** (the fault matrix asserts its absence; the record's `substrate.namespace` and `snapshot` stay null per the section 6 nullability — the same fact seen from events and record); mid-phase failure: best-effort snapshot, cleanup attempted; terminal sweep closes never-launched rows as `abandoned` (`substrate_id` null where never registered); exit 1 |
| Render preflight (7a) | exit 2 **with** an archive (M1a render-error parity); disposable render roots do not contaminate real workspaces; snapshot/cleanup as above; no invocation was allocated |
| Launch loop (7b–9) | failure cascade or fault abort per section 11.3; exit 1 |
| Cancellation (SIGINT, any phase ≥ 4) | the team analog of the direct runner's cancellation finalizer: terminate process trees; every durably allocated but incomplete task becomes `cancelled` (a nonterminal invocation becomes `cancelled`, an already-succeeded invocation is preserved); never-allocated tasks become `abandoned`; best-effort snapshot, cleanup attempted, terminal sweep, run **`cancelled`** (the existing run status), manifest, exit 130 |
| Final snapshot fails on the otherwise-green path (10) | run `failed`, exit 1 — the snapshot is section 13 acceptance evidence; a run without it did not meet its contract (`substrate.snapshot` null per section 6). On an already-failing path, a `snapshot-failed` event is recorded and the primary `failure_reason` is kept |
| Cleanup/deletion warns (10) | **finalization-exempt from fault abort**: record `CleanupOutcome.space_closed`, `snapshot_state`, and path-free `warning_codes` on `provider-cleanup`; emit `snapshot-retained` when applicable; never alter `failure_reason` or status. A green run remains `succeeded`, exit 0 because the copy-out was already verified; no raw exception text or stable-root path enters events |
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

**Snapshot copy-out is a verified four-step compound performed by the run
layer for both providers**: provider `snapshot(space, tag)` →
`read_snapshot` of that id → atomic write to
`coordination/snapshot.json` → read-back SHA-256 agreement with the bytes
returned by the provider. Only completion of all four steps sets
`copy_out_verified = true` and populates
`substrate.snapshot {id, path, sha256}`; any failure records
`snapshot-failed`, leaves the field null, and sets false. The run layer
then calls `cleanup(space, copy_out_verified=...)` exactly once. Local
cleanup tombstones and retains its archive-resident space regardless of
the flag. ClawTeam cleanup always attempts upstream cleanup and, only for
true, attempts exact-space snapshot deletion per section 9.2; false
retains. The returned `CleanupOutcome` is recorded without paths. Because
cleanup precedes terminal-record/manifest finalization, all surviving
archive-resident local data is sealed; ClawTeam's archive evidence is the
verified copy-out plus ledger, while any retained stable-root data is
honestly reported unmanaged local state.

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
  member (the owner bijection). The template explicitly grants
  `workspace_access: workspace-write` only to `implement`; `plan` and
  `review` explicitly declare `read-only` (the omitted default is tested
  separately). `lead` and `reviewer` reference the
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
  5. per-member records and access — every member carries its own
     `effective_definition_hash` and one `invocation` execution binding,
     and every successful member invocation parsed a valid
     `MemberResultV1` **archived at `legs/inv-<member>/member-result.json`
     with its `member-result` artifact reference** (present regardless of
     raw-stream retention); `tasks[].workspace_access` records the exact
     resolved grant, and fake render records prove the plan/review members
     read-only and implementer writable without changing direct/synthesis
     renders;
  6. team-decided, mixed selection — at least one member records
     `decided_by: team` (the `implementer`), and at least two distinct
     harnesses appear across members (TE-03 deterministic evidence);
  7. terminal `run.json` with `independence {declared: advisory,
     achieved: data-dir}` recorded honestly (ClawTeam leg: `namespace`)
     and the section 6 lifecycle nullability satisfied (`succeeded` ⇒
     namespace, achieved, and snapshot all present);
  8. immutability and target facts — every member **bundle** re-hashes
     identically and the **template** re-hashes identically (definition
     immutability); workspace `target {before, after}` hashes are
     recorded facts per the section 11.2 team-mode semantics — the
     implementer's after-hash differs by design (its declared
     deliverable), step 5's copy hash is not an invocation baseline, and
     the reviewer's launch-time baseline includes its materialized handoff
     while excluding final-renderer-owned files by the same rule as its
     after-hash; no team-mode condition requires `after == before`; the
     direct-run regression (`direct-review.yaml`, with its unchanged
     direct-mode immutability condition) still passes in the same job;
  9. ordering/publication — for every dependency edge (a, b), the
     predecessor's member-result write, deliverable archive + verified
     materialization, and any ledger/send all precede
     `task-completed(a)`; that event precedes
     `leg-started(inv-<owner(b)>)` in `events.jsonl`. Exactly one
     `leg-started` exists per member (partial-order assertions over
     structured fields, never timestamps alone);
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
  member, invalid `workspace_access`, missing resolved access in a team
  task row, an unknown task status (with valid fixtures covering each of
  `failed`/`cancelled`/`abandoned`), reserved fields non-empty, an unknown
  `decided_by` value — each
  must be rejected by the schema itself, not only by the models.
  Model-level negatives cover only representable section 6 invariants
  (`succeeded` with a null namespace/achieved/snapshot rejected; the
  failed/cancelled allowances accepted; succeeded with null execution,
  a non-invocation kind, or duplicate execution refs rejected). Archive
  verifier tests separately reject missing/dangling/nonterminal refs,
  unbound allocated invocations, and a null binding with an invocation
  record. A **vendor-dialect lint**
  asserts `member-result-v1` obeys the intersection rules (every property
  required, closed, nullable-required optionals, look-around-free
  patterns), like the review schemas.
- **Unit**: `test_team_template.py` — TC-01..06 field validation,
  skeleton ids (forward-declared `blocked_by` legal; cycles/self/unknown
  exit 2), the owner bijection, `workspace_access` enum/default,
  placeholder grammar, handoff
  vocabulary bounds, the must-NOT-contain prohibitions, reserved-empty
  enforcement (`dynamic_members`, `constraints`, non-visible
  `visibility`), the reserved `synthesis` member name, template hashing.
  `test_team_request.py` — `goal` validation, the `members` override map
  (roster-name keys; `model`/`effort` require `harness`), the team-mode
  CLI flag gate (each rejected flag exits 2), kind dispatch, the
  unsupported-substrate rejection. `test_team_selection.py` — the
  four-layer precedence (user > Assistant > team > default),
  `decided_by: team`, fail-closed user requests unchanged, forced
  variants still rejected. Adapter render tests pin
  `RenderContext.invocation_scope` as an independent defaulted
  discriminator and exact team access recipes: disjoint Claude allow/deny
  sets for each grant; Codex's sandbox enum plus explicit writable-network
  denial; and Grok's per-invocation name, guarded workspace-local
  `.grok/sandbox.toml`, `files_written` declaration, no persistent-home
  write, parent-symlink/non-directory rejection, malformed/global-name/
  pre-existing-project-file rejection, member-workspace cwd, and
  Windows refusal. Tests inject the nonce source and platform facts so the
  fake/argv assertions are deterministic and OS-agnostic.
  Direct/synthesis renders are byte-identical; the direct
  Grok regression pins `--sandbox read-only` and no project sandbox write.
  Run-record mode-split and nullability
  validators sit beside the schema-level negatives.
  `test_import_containment.py` — the **static containment scan** (core
  legs, no extra needed): an **AST import scan** (`Import`/`ImportFrom`
  roots) proving `clawteam` is importable only from
  `src/agentteam/compat/clawteam.py` and `agentteam.compat` only from
  `src/agentteam/coordination/clawteam.py` (plus `tests/compatibility/`),
  **plus a case-insensitive textual-reference scan over `src/agentteam/`
  with a frozen occurrence inventory**: (a)
  `src/agentteam/compat/` — any use; (b)
  `src/agentteam/coordination/clawteam.py` — any use; (c)
  `src/agentteam/coordination/__init__.py` — exactly one registry-key
  constant `"clawteam"`, one lazy-module constant
  `"agentteam.coordination.clawteam"`, one assignment target and one load
  of `CLAWTEAM_DISPOSITION`; (d) `src/agentteam/domain/team.py` — exactly
  one `SubstrateKind` literal occurrence `"clawteam"`; (e)
  `src/agentteam/domain/run.py` — **zero** case-insensitive token
  occurrences because it imports the shared alias from `domain/team.py`.
  The CLI calls only the
  generic `provider_disposition(substrate)` registry API and has zero
  case-insensitive token occurrences. Tests compare normalized AST
  occurrence tuples plus raw case-insensitive token counts (comments and
  docstrings do not create an escape hatch); any new occurrence fails and
  requires an explicit plan/ADR amendment against the LOC boundary.
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
  snapshot create/read/restore round-trip; cleanup with both verification
  flags and exact `CleanupOutcome` shapes — successful closure makes
  post-cleanup ops raise `SpaceUnavailableError`, the verified archive
  survives, and provider-side retention/removal is asserted only where
  that provider promises it; two spaces with
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
  workspaces, staged rendering (7a disposable stubs, no invocation
  records; 7b launch-time), state-free `--render-only`, durable
  allocation/binding before provider-running/spawn, launch-on-ready order,
  exact audited access grants, the member-result pipeline
  (`output_contract` dispatch → schema delivery → `StructuredExtractor` +
  `MemberResultV1.model_validate` → `write_member_result` + artifact
  reference; the direct review path bit-identical), deliverable
  validation/archiving/materialization under the section 11.2 target
  semantics — with the full negative set: declared write (green),
  undeclared write (inert, recorded in the after-hash), missing declared
  path, directory, symlink leaf, symlinked parent, exact duplicate,
  `Foo`/`foo` collision, decomposed-NFC spelling, casefolded `handoff/`,
  and renderer-owned AGENTS/Skill path or deny-prefix collision — each
  exit-failing that invocation. Tests verify source→archive and
  archive→successor hashes, the completion publication barrier, handoff
  claim/embed, blinding, ledger-before-send, stop → verified copy-out →
  cleanup handshake ordering, archive verification/finalization, exit
  codes, and reserved fields fail closed.
  `test_team_run_faults.py` — the **fault-injection matrix**, with a
  `FaultInjectingProvider` double (wraps the local provider and can raise
  before or after delegating a named method). Rows cover **all eleven
  runtime-invoked provider methods plus the protocol `wait` helper**:
  `create_space`, `info`, `add_member`, `create_task`, `update_task`
  (distinct running and completed windows; completed has pre-commit and
  post-commit raises), `tasks` (raise — the provider polling method
  underneath `wait`, distinct from the helper-timeout row; fault abort),
  `send`, `receive`, `wait` (helper timeout), `snapshot`, `read_snapshot`, `cleanup` (**not** a
  fault abort — finalization-exempt per section 11.3: an injected cleanup
  exception is normalized to a warning outcome, and the green row still
  finishes `succeeded` exit 0 with `provider-cleanup` facts recorded and
  the snapshot already verified) (`restore` is conformance-only and never runtime-invoked — no
  row, by that sentence). Cleanup cases cover true-delete, false-retain
  after snapshot/read/archive-write/digest failure, upstream-cleanup
  warning, deletion warning, both warnings aggregated, and green exit 0
  only when copy-out was already verified. Non-provider rows: member
  invocation failure post-retry (asserts the in-flight sibling
  **finishes**, its completion still reaches the provider, and
  dependents go `abandoned` eagerly); attempt timeout; launch-time render
  failure; pending-invocation write failure, interruption after invocation
  allocation but before binding, binding-write failure, spawn failure,
  member-result write failure, deliverable archive
  I/O/digest failure, successor materialization failure, ledger append
  failure; the missing-body abort (injected on the transported edge);
  SIGINT cancellation (exit 130); fault abort with a member in flight
  (process tree terminated, invocation and task `cancelled`). **A `receive` raise
  is a fault abort** (taxonomy by cause: provider raise =
  infrastructure). `read_snapshot` gets two rows — green path (run
  `failed` exit 1, `snapshot-failed` event, null `substrate.snapshot` per
  section 6) and failing path (`snapshot-failed` event, primary
  `failure_reason` kept). The provider-completion rows pin the publication
  ambiguity exactly: pre-commit raise leaves the provider task `running`;
  post-commit raise leaves it `completed` and its dependent provider task
  `pending`; in both rows the already-published invocation stays
  `succeeded`, the owning run task is `failed`, the run fails, and no
  successor launches. Publication faults before the successful invocation
  write pair invocation `failed` with task `failed`; a causal pre-allocation
  fault pairs task `failed` with a null binding; non-causal allocated work
  caught by abort makes the task `cancelled`, terminalizing a nonterminal
  invocation `cancelled` while preserving an already-succeeded invocation;
  a provider-completion call known to have returned reconciles to
  `completed`; never-allocated/never-launched remainder is `abandoned`.
  Barrier-controlled sibling rows pause after allocation/before provider
  running, while the process is running, and after the successful
  invocation write/before provider completion, plus after provider
  completion returns/before run-row reconciliation, to prove the exact
  pending/running residuals, both invocation pairings, and completed
  reconciliation without a successor launch. Every
  row asserts: terminal `run.json` with all-terminal `tasks[]` (the terminal
  sweep and this pairing table observed), **execution-binding
  consistency** through the archive verifier (a binding for every
  allocated invocation, null iff no invocation record; asserted across
  pre-allocation, allocation/binding, running/spawn, cascade, fault-abort,
  and cancellation windows), publication ordering/no successor launch
  before its predecessor barrier, **exactly
  one `processes-stopped`** (unconditional), a `provider-cleanup` event
  **iff a space id was minted** (the `create_space` row asserts its
  absence, together with the null namespace/snapshot of section 6), no
  orphan process, and a clean manifest verification. The cascade rows use
  a **tests-only parallel-branch template** (a root; two parallel mid
  tasks — one fails, the sibling completes on merit; a dependent of the
  failed task, eager-abandoned; a task blocked only on the survivor,
  never launched, closed `abandoned` by the sweep) so eager abandonment,
  sibling-on-merit completion, terminal-sweep closure of an unrelated branch, and
  the all-terminal invariant are proven generally; the committed 3-chain
  acceptance fixture is unchanged. The matrix is **G3 evidence**.
- **Acceptance**: `test_team_lifecycle.py` — the section 13 conditions
  1–12 end-to-end through the CLI.
- **Compatibility**: the ClawTeam provider suite stays in
  `tests/compatibility/` with the existing `importorskip` conftest and the
  owner-state guard, so the six core legs keep proving clean skip without
  the extra. Under a `failed-routed` disposition the **whole
  success-oriented provider suite is gated by the committed
  `CLAWTEAM_DISPOSITION`** — a dated, VERIFY-cited module-level skip —
  while the failing scenario is retained as a dated strict-xfail in a
  dedicated file **outside that module-level skip**; a collection test
  asserts its node id remains collected under `failed-routed`. Thus the
  three-leg job is green under either disposition and nothing is silently
  skipped. No new pytest marker is introduced
  (`--strict-markers`; the split stays directory + CI-job based).
- **Cross-platform**: the local provider's file semantics (atomic rename,
  ordering, permissions) run on all three OSes on the core job; any
  Windows/macOS deviation is fixed, never skip-listed silently (M1a §18
  discipline). Team-Grok rendering is affirmatively refused on Windows at
  preflight (exit 2, no run directory), while platform-injected unit tests
  keep both grant recipes covered on every host; vendor-smoke remains
  unchanged and still skips Grok.

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
  stays green under either G5 disposition (parity, or the
  disposition-gated suite plus the dated strict-xfail of the failed
  branch, section 9.2).
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
  `src/agentteam/coordination/clawteam.py` is a violation except for the
  exact declarative AST/token inventory in section 14. The CLI must stay
  substrate-generic; any occurrence-count change stops for plan/ADR
  review before the LOC boundary can expand.
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
- Stop if a requested workspace grant cannot be mapped to a
  version-supported fail-closed adapter control; never silently broaden
  a read-only task or continue unsandboxed. Direct and synthesis renders
  must remain byte/argv-compatible. In particular, refuse team Grok on
  Windows, any project/global profile collision, or any attempt to write
  the persistent authenticated `GROK_HOME`; never downgrade to a built-in
  warning-and-continue team profile.
- Stop if a deliverable path is non-NFC, collides after casefolding,
  traverses a symlinked component, or intersects `handoff/` or a
  renderer-owned workspace prefix; cross-platform archive identity is
  part of the contract, not a host-dependent best effort.
- Always stop AgentTeam-owned processes before provider `cleanup`, and
  always run the terminal sweep and write the terminal record **before**
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
  channels plus one writable declared-deliverable smoke per
  then-supported harness, after a fresh version-bound probe proves its
  access control** (deterministically proven only with fakes in M1b; a
  named risk until then),
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
item tickable against the frozen tree — five passes are recorded at r1
`14dc218`, r2 `54728c8`, r3 `6d3f329`, r4 `3d0211a`, and r5 `12ca6c7` in
`docs/reviews/`, resolved per section 21):

1. scope: deterministic-only M1b, zero live calls, M1c/M2/M3 boundaries
   (sections 1, 11, 18, 19);
2. provider order, the never-launches-a-harness rule, and the explicit
   ClawTeam disposition at close with a green-CI failed branch
   (sections 1, 2, 3, 8, 9.2);
3. one record kind: the mode-discriminated union keeps direct-mode
   `run.json` byte-compatible; exactly three new + two regenerated schema
   files; the mode split is schema-level-enforced, representable
   lifecycle nullability is model-enforced, and execution cross-file
   integrity is archive-verified, all with negative tests
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
   terminals and residual projections, claim semantics, explicit audited
   workspace access, independent standalone/team-member render scope,
   exact collision-safe project-local adapter controls, launch-on-ready
   with disposable staged rendering and a state-free render-only branch,
   the pinned member-result pipeline (`output_contract` →
   `StructuredExtractor` + validation → `write_member_result`; `parse()`
   untouched), the team-mode target semantics (member-owned mutation; copy
   verification distinct from the launch-time baseline; canonical
   declared-deliverable-only propagation), nullable-until-
   durable-allocation execution bindings with model/archive validation,
   handoff construction/transport/blinding, the completion publication
   barrier, provider-completion ambiguity, failure cascade and fault abort
   (finalization ops exempt), and the finalization invariant with the
   terminal sweep, causal `failed` / interrupted `cancelled` /
   never-allocated `abandoned` pairing, and binding consistency
   (sections 6, 8, 11);
8. gate evidence is mechanically checkable and each gate names its VERIFY
   entry; the fault matrix (eleven runtime-invoked provider methods plus
   the protocol `wait` helper, with conditional assertions) is G3 evidence
   (sections 3, 14);
9. test matrix and CI mapping: conformance suite shared across providers
   with local-only guarantees separated, core-vs-extra job split, no new
   marker, direct regression retained, containment scan on core legs
   (sections 14, 15);
10. stop rules and falsification routing cover the risks register rows
    R01/R02/R08/R12/R30-class/R33-lesson/R34/R36/R37
    (sections 12, 13, 17);
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
  `risks`), plus the optional-default-read-only task
  `workspace_access` grant.

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
(section 14), R33 lesson (section 13), R34 (section 12), R36
(workspace-write live evidence deferred to M1c), R37 (run-task/invocation
terminal-pair integrity). Open questions:
exit criterion (section 10, finalizes at approval), HB-03 (deferred,
open), Q4/Q6 (section 19, stay outside), R15/overlay (section 18, not
foreclosed). Decisions inherited: ADRs 0003, 0007, 0014, 0015, 0016,
0018, 0021, 0022, 0033 (amendment convention), 0036, 0037, 0038, 0039,
0040, 0041, 0042, 0043.

Implementation begins only after review findings are resolved and the
owner explicitly marks this plan approved (G0). Project-local sources:
`docs/discovery/team-execution-model.md` (v2.3), the glossary,
`docs/evidence/clawteam-qualification-2026-08-23.md`, the M1a plan as
amended, and the five review records; volatile facts (CLI versions,
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
- **r3** (2026-08-24, `6d3f329`): resolved the second independent
  review (of r2; `docs/reviews/2026-08-24-m1b-plan-review-at-54728c8.md`;
  ADR 0040). Findings and resolutions:

| Finding | Resolution | Sections |
| --- | --- | --- |
| B1 — pending team record not representable | Lifecycle nullability: pending/running permit null namespace/achieved/snapshot; `succeeded` requires all three; failed/cancelled allow null snapshot (copy-out failure) and null namespace iff no space; model validators documented in `schemas/README.md`, negative-tested; mirrored by the fault-matrix conditionality | 6, 11.4, 13, 14 |
| B2 — provider task semantics incomplete | `SubstrateTaskStatus` (protocol-only vocabulary; run layer writes `running`/`completed`); `running ↔ in_progress` bidirectionally in the ClawTeam adapter (seam untouched for status); run-only `failed`/`abandoned` never sent (auto-unblock-safety rationale + residual-projection rule); claim semantics (`TaskClaimError`) with strict transitions local-only; frozen DTOs incl. the remaining-vs-declared `blocked_by` disambiguation; `UnknownTaskError` + conformance relabel (provider cycles unconstructable); deterministic topological registration (Kahn + declaration order) | 3, 6, 8, 9.1, 9.2, 11, 11.3, 13, 14, 20 |
| B3 — team results were review-shaped | **Owner decision (ADR 0040): `MemberResultV1` now** — third new vendor-facing schema (`summary`/`deliverables`/`risks`, dialect-intersection-linted); additive harness output-contract dispatch (review path untouched, regression-pinned); deliverables = declared paths validated/hashed/archived and materialized into the successor workspace pre-baseline-hash; live vendor acceptance is a named M1c handoff | 2, 5, 6, 11.2, 13, 14, 15, 16, 18, 20 |
| B4 — automatic handoffs vs declared independence | **Blinded handoff** on declared-independence edges: no mailbox message/ledger row (the run layer never creates the declared-away edge); deliverables still materialize (the artifact under review); summary/risks omitted; marker recorded; missing-body abort counts non-blinded edges only; acceptance asserts transport on plan→implement and blinding on implement→review | 6, 11.2, 11.5, 13, 17 |
| B5 — failed-routed had no green-CI path | The failed branch: provider registry marks `clawteam` unsupported (`substrate: clawteam` exits 2 citing VERIFY); failing reproduction retained as a dated strict-xfail (R02 precedent); required CI green; close requires it (stop rule) | 1, 3, 6, 9.2, 14, 15, 17 |
| B6 — finalization vs fault matrix conflicts | Step 11 reordered (sweep → terminal record → manifest last); the **abandon sweep** named once and referenced by cascade/abort/cancellation; `processes-stopped` unconditional, `provider-cleanup` iff a space was minted (absence asserted on the `create_space` row); the matrix covers every runtime op named at r3 (including `info`, `receive`, `read_snapshot`; `restore` conformance-only); `receive` raise = fault abort; copy-out defined as the three-step compound; parallel-branch tests-only template proves the general case | 11, 11.2–11.6, 13, 14, 17 |
| M1 — parity fixture cannot hold two run-record payloads | `minimal_payloads()` stays filename-keyed with the direct payload; `run_record_variant_payloads()` drives both variants + negatives | 6, 14, G1 |
| M2 — containment scan insufficient | AST import scan + textual token allowlist over `src/agentteam/` (catches `from clawteam`, dynamic imports, import-free branches) | 2, 10, 14 |
| M3 — per-run ClawTeam root broke the one-root rule | Stable `~/.agentteam/clawteam/` process root with per-run namespaces — **restores the ADR 0015 design**; multi-run processes supported (tests, M2 MCP); root outside the archive (ledger + copy-out are the archive evidence; "leftovers manifested" claims removed); tests use temp roots | 2, 5.1, 9.2, 11.6, 12, 18 |

- **r4** (2026-08-24, `3d0211a`): resolves the third independent
  review (of r3; `docs/reviews/2026-08-24-m1b-plan-review-at-6d3f329.md`;
  ADR 0041; the reviewed r3 text's SHA-256 verified against the
  reviewer's citation). Findings and resolutions:

| Finding | Resolution | Sections |
| --- | --- | --- |
| B1 — MemberResultV1 lacked a decision-complete output pipeline | The pipeline pinned end to end: `RenderContext.output_contract` discriminator; `schema_name_for` returns the member-result schema; the team runner extracts via the adapter's existing `StructuredExtractor` and validates with `MemberResultV1.model_validate` (**`HarnessAdapter.parse()` untouched**); canonical archive home `legs/inv-<member>/member-result.json` via `RunArchive.write_member_result()` + a `member-result` artifact reference — survives raw-retention-off | 3 (G3), 6, 13, 14 |
| B2 — deliverable creation vs the target-mutation contract | Team-mode target semantics defined: a member may mutate its own isolated workspace; `target {before, after}` recorded as fact, never a team-mode failure condition; direct-mode immutability and the cond-1 evaluator unchanged and direct-only; propagation exclusively via declared, validated regular files (no dirs/symlinks/traversal/duplicates/`handoff/` collisions); undeclared writes permitted-but-inert; the full negative set tested | 6, 11.2, 13, 14 |
| B3 — the sweep closed tasks but not execution bindings | Team-variant `execution` nullable-until-launch with lifecycle validators (`succeeded` requires all; `failed`/`cancelled` permit null only for never-launched owners); 7a stub renders create no invocation records; the finalization invariant and the fault matrix assert binding consistency on the step-5/7a/cascade/abort/cancel paths | 6, 11.1, 11.4, 14 |
| B4 — failed-routed still left the ClawTeam job red | The committed `CLAWTEAM_DISPOSITION` (registry) is the one fact the CLI and the test gate read: under failed-routed the success-oriented provider suite gets a dated, VERIFY-cited module-level skip; the reproduction stays strict-xfail; qualification scenarios gated only where a seam-level failure breaks them; required CI green under either disposition | 3 (G5), 5, 9.2, 14, 15 |
| M5 — successful cleanup described inaccurately | Corrected per the qualification evidence: upstream cleanup retains `snapshots/<space>` in the root; policy (ADR 0041): adapter-owned deletion after a **verified** copy-out (failure = hygiene event, green exits 0); failed copy-out deliberately retains the provider-side snapshot, path named in the failure detail | 9.2, 11.6 |
| M6 — taxonomy vs cleanup; missing `tasks()` row | Fault-abort scope pinned to lifecycle steps 6–9 (incl. the `tasks()` polling under `wait`); finalization ops (copy-out, cleanup, snapshot deletion) explicitly exempt with their own §11.4 rows; a `tasks()`-raise row added beside the timeout row (twelve provider rows); the cleanup row pins `succeeded`/exit 0 on green | 11.3, 11.4, 14 |
| M7 — the containment allowlist was not frozen | Case-insensitive scan with an exactly-enumerated allowlist (compat/ any; coordination/clawteam.py any; coordination/__init__.py registry id + disposition only; domain/team.py kind literal only); the allowlist is diff-visible test data commented with the §10 boundary | 10, 14 |

- **r5** (2026-08-24, `12ca6c7`): resolves the fourth independent
  review (of r4 at full commit
  `3d0211a456cedb356aa512cb5f257b448dbb70e1`, plan SHA-256
  `e1c7f222ce22785b37eb22fca553281d0936b5367313a3a7b9a1d38c587200c9`;
  `docs/reviews/2026-08-24-m1b-plan-review-at-3d0211a.md`; ADR 0042).
  Findings and resolutions:

| Finding | Resolution | Sections |
| --- | --- | --- |
| H1 — real adapters remained read-only | `workspace_access` is an explicit optional-default-read-only workflow-task field and a required resolved run-task fact. The fixture grants write only to `implement`; exact Claude/Codex/Grok mappings are pinned from no-call evidence, team Grok gets generated fail-closed custom profiles for both grants, direct/synthesis renders stay unchanged, and live writable acceptance is an M1c handoff | 2, 3, 5, 6, 11.1, 13, 14, 18, 20 |
| H2 — execution invariant depended on unavailable history | Null now means no durable invocation allocation. Final render → pending invocation → run-record binding → provider running → spawn is the one order; model validators enforce representable facts and the archive verifier enforces the cross-file bijection. Render-only is a state-free pre-execution branch and normal preflight uses disposable roots | 2, 3, 6, 7, 11.1, 11.4, 14, 20 |
| H3 — snapshot deletion lacked a handshake | `cleanup(space, *, copy_out_verified) -> CleanupOutcome` carries the verified-copy-out fact and returns path-free closure/retention/warning facts. Local retains; ClawTeam always attempts upstream cleanup and deletes only the exact verified snapshot, retaining every unverified path; cleanup/deletion warnings remain non-masking hygiene | 2, 3, 8, 9.1, 9.2, 11.4, 11.6, 14 |
| M1 — completion publication was unordered | One barrier persists the member result, validates/archives/materializes deliverables, ledger/sends handoffs, and terminalizes the invocation before provider completion can unblock; content errors cascade as task failures, infrastructure publication errors fault-abort; ordering and every failure window are injected/tested | 2, 3, 11.2, 11.3, 13, 14 |
| M2 — containment froze files, not occurrences | The test now freezes exact normalized AST/token occurrences in the two declarative exception files; the CLI uses generic `provider_disposition(substrate)` with zero token occurrences; the failed-routed strict-xfail lives outside the skipped success module and its collection is asserted | 2, 3, 9.2, 10, 14, 17 |
| M3 — deliverable paths were not canonically safe | Require NFC and all-OS casefold collision keys; `lstat` every component; reserve casefolded `handoff/` and renderer-written files plus non-root parent prefixes; verify source→archive→materialized digests; expand the negative matrix with case, Unicode, parent-symlink, and injected-file cases | 6, 11.2, 13, 14, 17 |
| C1 — stale counts/traceability/rationale | Current text says twelve runtime provider operations and four reviews, inherits ADRs 0041/0042, names R36, and defines owner bijection as the deliberate M1b one-member/one-task constraint rather than field-requiredness | 2, 6, 14, 20, 21 |

- **r6** (2026-08-24, this commit): resolves the fifth independent review
  (of r5 at full commit
  `12ca6c730f99816ed79c6e0537de021d25dd24b2`, plan SHA-256
  `95ff6ab3816efd61db845216b34aecb64b8d22efde3f13a727027c612a44acf4`;
  `docs/reviews/2026-08-24-m1b-plan-review-at-12ca6c7.md`; ADR 0043).
  Findings and resolutions:

| Finding | Resolution | Sections |
| --- | --- | --- |
| H1 — Claude writable allow and deny sets collided | Both grants now pin complete, disjoint sets: read-only allows `Read,Grep,Glob,LS,Skill` and denies `Write,Edit,NotebookEdit,Bash,WebFetch,WebSearch`; writable adds `Write,Edit` to allow and removes them from deny; both retain `dontAsk` | 11.1, 14 |
| H2 — Grok team dispatch/profile location was unsafe | Added independent `RenderContext.invocation_scope` (`standalone` default / `team-member`), never inferred from access or output. Team Grok writes a guarded, recorded project `.grok/sandbox.toml`, never persistent `GROK_HOME`; a per-render 128-bit nonce gives the custom profile name and an injected source keeps tests deterministic. The parsed global file, malformed input, name collision, and pre-existing project path all fail closed. Both grants use custom profiles; direct Grok stays byte-identical on built-in `read-only` | 2, 6, 11.1, 14, 17 |
| H3 — `target.before` still inherited the step-5 copy time | Step 5 now verifies source/copy equality only. Each invocation baseline is computed at launch after incoming handoff materialization and final render, excluding `files_written` by the same rule as `after`; acceptance pins the reviewer's handoff-inclusive baseline | 3, 11, 11.1, 11.2, 13, 14 |
| M4 — containment omitted `domain/run.py` | `SubstrateKind` is defined once in `domain/team.py`; `domain/run.py` imports it and is frozen at zero case-insensitive `clawteam` occurrences | 3, 5, 6, 14 |
| M5 — provider-completion and abort paths produced false `abandoned` pairings | Added run-only task `cancelled` plus `task-cancelled`; the terminal sweep preserves completed/failed, cancels non-causal allocated work without rewriting an already-succeeded invocation, and reserves abandoned for never-allocated remainder. Pre-barrier publication faults pair failed/failed; a pre- or post-commit provider-completion raise preserves the already-succeeded invocation, fails its task/run, pins the residual provider projection, and launches no successor | 2, 6, 8, 11.2–11.4, 14, 20 |
| M6 — Grok Windows enforcement was unpinned | Team Grok is refused at step-3 preflight on Windows (exit 2, no run directory); unit/fake argv coverage uses injected platform facts and remains OS-agnostic; vendor-smoke is unchanged | 11, 11.1, 14, 15, 17 |
| C1 — `wait` was counted as a provider method | The plan consistently says eleven runtime-invoked provider methods plus one protocol `wait` helper over `tasks()` | 8, 14, 20 |
| C2 — Codex network posture and direct Grok regression needed precision | Team Codex workspace-write explicitly pins `sandbox_workspace_write.network_access=false`; read-only retains the vendor-default denial under `--ignore-user-config`. Direct/synthesis recipes remain exact regressions, including direct Grok `--sandbox read-only` | 11.1, 14, 17 |
| C3 — fifth-round traceability/steward state | The frozen review carries the full commit and plan hashes; ADR 0043 records the r6 decisions; PLAN/HANDOFF/QUESTIONS name five review rounds; R36 is tightened and R37 tracks terminal-pair drift | Header, 2, 3, 20, 21; steward records |

Amendments after approval follow the ADR 0022/0033 convention
(in-document marker plus a dated amendment table) at amendment time.
