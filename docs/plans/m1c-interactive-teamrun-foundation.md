# AgentTeam M1c interactive TeamRun foundation — approved r2

- Status: **APPROVED FOR IMPLEMENTATION** by the owner's 2026-08-25
  instruction to implement the reviewed r2 plan. Approval does not authorize
  a live model call, dependency download, push, or history rewrite.
- Predecessor: M1b Plan R6, complete through G7.
- Successor: `m1d-dynamic-member-poc.md` r2.
- Live budget: a conditional hard maximum of **18** Claude/Codex calls, or
  **23** total calls only if Grok passes the fresh no-call qualification gate.
  G7 still requires a separate attended owner go. M1a calls do not transfer.

## 1. Outcome

M1c turns the batch-only product into a local interactive engineering-agent
host without weakening or silently migrating any V1 contract. A reusable
Assistant or TeamTemplate remains project-independent. Starting chat creates
one bounded run for one user-defined top-level goal, which may contain any
number of work items and turns. Each Member gets a fresh provider-owned
session whose context is retained until reset or run closure.

All interactive Team Members use one user-supplied project worktree. AgentTeam
serializes dispatched turns, observes the workspace before and after each
turn, and never auto-commits, resets, stashes, or attributes concurrent user
edits to a Member. The Lead may propose completion with criterion evidence;
only the user may accept success. Closure disposes every provider session and
run-scoped runtime store while preserving the local AgentTeam audit archive.
A later goal always creates a new run and fresh sessions against the latest
project state.

An interrupted controller may attach to the same nonterminal run only when
provider continuity is proved. Context loss is never repaired by silently
opening a replacement session. The user must reset the affected Member or
abort/close the run.

## 2. Architectural ownership and integration rule

AgentTeam owns portable definitions, policy, the work graph, workspace
serialization, completion acceptance, provider-neutral records, and the
audit archive. Exactly one `MemberExecutionProvider` owns each Member's
session/process, prompt queue, cancellation, recovery handle, and provider
cleanup.

The optional `direct-acp` implementation is a thin standalone/reference
provider around pinned `acpx/runtime` and ACP agents. AgentTeam does not
implement ACP wire framing, scrape terminal output, or wrap a native team host
inside a second ACP session manager. Future OpenClaw, DSH, Hermes, ClawTeam,
or other integrations implement `MemberExecutionProvider` by calling their
native control plane while AgentTeam retains the product contracts above.

M1b's optional ClawTeam coordination provider remains unchanged on the batch
path. Its accept/drop integration ruling is deferred to M1d D0, where the
exact M1c close commit and current native-control evidence can be considered.
The old Grok FAIL-HARD applies to the native headless adapter; a fresh ACP
no-call qualification may admit Grok to M1c without changing that result.

## 3. Compatibility and schema registry

All V1 models, checked-in schemas, archive bytes, commands, and batch behavior
remain compatible. `atm run` remains a leaf command. Interactive records are
new closed contracts resolved by a schema registry keyed by
`(kind, schema_version)`; code must not use a version-only union or rewrite
existing V1 kinds.

M1c adds:

- `team-template` version 2 (`TeamTemplateV2`);
- `interactive-run-request` version 1 (`InteractiveRunRequestV1`);
- `interactive-run-record` version 1 (`InteractiveRunRecordV1`);
- `member-session` version 1 (`MemberSessionV1`);
- `turn-record` version 1 (`TurnRecordV1`);
- `work-item` version 1 (`WorkItemV1`);
- `control-request` and `control-receipt` version 1;
- `completion-proposal` version 1;
- `run-event` version 1;
- provider capability/doctor records; and
- `catalog-index` version 1.

`InteractiveRunRecordV1` has its own kind and is not an extension of the old
`run-record` union. Model-only invariants are documented and tested alongside
the generated JSON Schemas.

## 4. TeamTemplateV2 and migration

TeamTemplateV2 preserves the V1 meanings of members, Lead, relationships,
visibility, handoff, independence, preferences, workflow, and reserved
constraints. Member definitions use exact catalog Assistant
`id/version/content_hash` references. A workflow may have zero or more tasks,
multiple tasks may belong to one Member, and an empty blueprint is valid for
interactive planning.

Workspace layout is explicit:

- `shared-supplied`: all Members operate serially on the supplied worktree;
- `per-member-worktree`: V1-compatible isolated worktrees.

M1c interactive runs support only `shared-supplied`; mechanically reject a
different layout. The dynamic-member policy is present as a closed, disabled
shape so unknown fields fail closed; M1d activates its semantics.

`atm team migrate --to 2` is non-destructive. Its default faithfully maps V1
to `per-member-worktree`. `--shared-supplied` is an explicit semantic change
and the generated diff says so. The command never overwrites its V1 input.
V1 TeamTemplates continue to run through the batch runner unchanged.

Assistant chat synthesizes a one-Member TeamTemplateV2 with the target as the
primary/Lead. M1d dynamic creation remains Team-only.

## 5. Managed library

`$AGENTTEAM_HOME/library` is a locked, atomic, content-addressed store. A
catalog index records exact active revisions. `(kind, id, version)` with
different bytes is a hard collision; identical re-import is idempotent. Team
imports resolve every exact Assistant reference under the same lock and are
all-or-nothing.

Unmanaged packages require an explicit `--path`. Before execution AgentTeam
validates and snapshots their exact bytes into the run archive; later source
changes cannot change the active run.

Public library commands are:

- `atm assistant import|list|show|chat`;
- `atm team import|list|show|chat|migrate`;
- `atm runs list|status|attach|cleanup`; and
- `atm runtime install|doctor direct-acp`.

The existing `atm run` direct/batch surface stays byte- and behavior-stable.

## 6. MemberExecutionProvider contract

The provider SPI supplies:

1. `describe()` and `doctor()` with no model call;
2. `open_member()` returning a durable provider session reference;
3. `start_turn()` yielding correlated events and a terminal turn result;
4. `cancel_turn()` with explicit queued/running/terminal disposition;
5. `verify_continuity()` that proves the same session rather than replacing
   it;
6. `close_member()` for logical/session/process cleanup facts; and
7. `dispose_run()` for exact run-scoped local state removal.

Capability records separately report persistent turns, recovery, permission
events, workspace enforcement, tool filtering, native-spawn control, process
stop observability, local-state deletion, and provider-history deletion.
Unsupported or unknown is not treated as supported.

Two deterministic providers are required: an owned-process fake that proves
process-tree/cancel/cleanup behavior, and an external-host fake that proves a
provider can truthfully report a host it cannot stop or erase.

Close records distinguish logical session close, process disposition, local
state deletion, and provider-side history disposition. `closed` is permitted
only after every required fact is terminal; an external-host limitation stays
visible rather than being reported as deletion.

## 7. Direct ACP reference provider

The Python wheel includes a Node adapter manifest and lock as package
resources. Installation is explicit through
`atm runtime install direct-acp`; chat never downloads, uses global packages,
or invokes an unpinned `npx` fallback.

The approved candidate pins are:

- `acpx@0.13.1`;
- `@agentclientprotocol/codex-acp@1.6.2`;
- `@agentclientprotocol/claude-agent-acp@0.69.0`; and
- the installed `grok agent stdio` command, admitted only by doctor evidence.

The checked-in npm lock/integrity metadata is authoritative. Node runtime
state lives below
`$AGENTTEAM_HOME/runs/<run-id>/runtime/direct-acp`; it never uses or mutates
`~/.acpx`. The provider points each ACP agent at the executable and
authenticated home selected by the existing AgentTeam profile.

`atm runtime doctor direct-acp` checks Node, installed package integrity,
agent executable/version, ACP initialize/load/close, and declared
capabilities without prompting a model. Resume/load must succeed before any
prompt on attach. If the pinned API cannot prove strict same-session load,
G2 fails: AgentTeam will not reimplement missing ACP protocol or manufacture a
replacement conversation.

## 8. Interactive lifecycle

Run phases are `initializing`, `open`, `completion-pending`, `interrupted`,
`recovery-required`, `closing`, `close-failed`, and `closed`. Outcome is
separate and unset until final closure, then `succeeded`, `cancelled`,
`failed`, `timed-out`, or `abandoned`. Cleanup facts are separate from both.

The controller takes a durable canonical-workspace reservation plus an
ephemeral controller lock. A second interactive run against the same path is
refused while separate projects may run concurrently. On abnormal host loss
the durable reservation remains; `atm runs attach` is the only recovery
shell. Before provider continuity is established it offers status, reset,
abort, and close actions only—never a prompt.

A Member reset first closes/disposes the old generation, then creates a new
generation from the immutable Assistant snapshot plus a deterministic
`RunStateSummary`; no old transcript is injected. Ctrl-C cancels the active
turn and leaves the run open. EOF/detach or controller loss marks the run
interrupted, never succeeded.

## 9. Work, workspace, and completion

One Member turn is active per interactive run. Each dispatch observes the
canonical path, Git HEAD/status when present, and stable diff/tree
fingerprints before and after. These checkpoints are observational: no
commit, reset, stash, checkout, or cleanup of user files is allowed.

The Lead manages a normalized work-item graph. M1c control requests may
create/update/assign work items and propose completion. A canonical
`ControlRequestV1` is produced from a native provider action, ACP-injected
tool call, or schema-valid structured control frame. AgentTeam persists a
queued `ControlReceiptV1`; side effects occur only after the source turn and
its events have committed. Dynamic-member controls are denied until M1d.

The Lead proposes completion with `done_when` evidence. The phase becomes
`completion-pending`. User rejection returns the run to `open`; only user
acceptance can produce `succeeded` and begin close.

## 10. Permission policy

Effective permission is the intersection of Assistant, Team/Member, run, and
provider ceilings. Unknown classifications deny. Provider-classified reads
inside the workspace may be allowed. Mutation requires both a
`workspace-write` Member grant and attended user approval. Network,
outside-workspace, full-access, unknown tools, and silent machine clients fail
closed unless an explicit approved policy covers them.

Native provider spawning must be disabled, intercepted, or reported
unsupported. AgentTeam never claims roster enforcement when the provider can
create invisible workers outside its control.

## 11. TTY and stream protocol

TTY chat defaults to the Lead and supports `/to`, `/members`, `/tasks`,
`/reset`, `/cancel-turn`, `/proposal`, `/accept`, `/continue`, `/abort`,
`/detach`, and `/help`.

`--stream-json` is correlated bidirectional NDJSON. A protocol negotiation
precedes mutation. Every client command has an id; every receipt/event carries
the run id, sequence, correlation id where applicable, and schema identity.
Malformed, duplicate, fragmented, out-of-order, or unsupported input is
handled deterministically without desynchronizing subsequent frames. This is
the single future local-UI/MCP seam; M1c does not expose a public MCP server.

## 12. Delivery gates

| Gate | Exit evidence |
| --- | --- |
| G0 | Owner approves exact r2 bytes; SHA-256 and architectural decisions are recorded |
| G1 | Registry, contracts/schemas, library, migration, negative tests, and unchanged V1 behavior |
| G2 | Provider SPI, both fakes, packaged direct-ACP runtime, strict-resume/cleanup conformance, and anti-reimplementation check |
| G3 | Lifecycle, retained context, shared scheduler/checkpoints, reset, permissions, completion, close, interruption, and recovery |
| G4 | Catalog-addressed chat, TTY, negotiated NDJSON, work-item controls, events, and archive export |
| G5 | Deterministic acceptance/fault matrix, full V1 regression, and Ubuntu/Windows/macOS evidence |
| G6 | Fresh current-version no-call probes and an honest supported/excluded capability record |
| G7 | Separate attended owner go, bounded live matrix, sanitized evidence, and exact ledger reconciliation |
| G8 | Evidence/CI/risk review and M1c close |

## 13. Deterministic acceptance

The deterministic matrix proves multi-turn context, reset isolation,
same-run attach, cross-run isolation, exact cleanup, permission denial and
approval, malformed/fragmented NDJSON, provider crash, shared latest code,
dirty-tree preservation, external drift, workspace reservation, multiple work
items, completion reject/continue and accept/close, queued-control commit
ordering, and owned-process versus external-host close truthfulness.

Tests use temporary home/library/run directories and never touch owner ACP or
vendor state. V1 schema reproduction, direct-runner, TeamRun, optional
ClawTeam, and archive tests remain green.

## 14. Conditional live matrix

No call begins from plan approval. G7 requires green deterministic and no-call
gates plus a fresh attended owner go.

The base ceiling is 18 Claude/Codex attempted prompts: five lifecycle calls
per supported provider (establish context, recall, reset-isolation, new-run
isolation, and continuity/close); four workflow calls across providers
(shared-worktree change, another Member review, Lead completion proposal, and
user-reject/continue); and four individually justified diagnostics, never
automatic retries.

If and only if Grok passes G6's ACP no-call strict-resume, workspace,
permission, structured-event, and close checks, its five lifecycle calls are
added and the hard ceiling becomes 23. Failed attempted prompts count. M1d's
live budget remains zero.

## 15. Stop rules and boundaries

- Stop for an owner decision before changing an approved contract, adding a
  dependency/pin, weakening a fail-closed rule, spending a live call, or
  broadening integration scope.
- Direct/native host providers beyond the reference provider are future work.
- The ClawTeam disposition is an M1d D0 decision; existing M1b behavior stays
  available meanwhile.
- HB-03 team-constraint precedence remains deferred and reserved.
- Dynamic Members are M1d; nested TeamRuns and public MCP are M2; definition
  evolution is M3; background operations are M4.
- Hidden is presentation, never secrecy. Raw local transcripts never enter a
  reusable package or sanitized export by default.
