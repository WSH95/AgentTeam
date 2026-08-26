# Interactive TeamRuns

This is the operator and integration guide for the M1c interactive foundation.
The normative contract remains the approved
[`m1c-interactive-teamrun-foundation.md`](plans/m1c-interactive-teamrun-foundation.md).

## Ownership boundary

AgentTeam owns portable Assistant and Team definitions, exact catalog
resolution, the work graph, shared-workspace scheduling, permission policy,
completion acceptance, provider-neutral records, and the audit archive.

Exactly one `MemberExecutionProvider` owns each Member's live session,
process or external-host handle, prompt queue, cancellation, continuity
proof, and provider cleanup. The bundled `direct-acp` implementation is a
standalone reference provider around exactly pinned `acpx/runtime` and ACP
agent packages. It does not implement ACP framing itself.

An OpenClaw, Hermes, DSH, ClawTeam, or similar integration should implement
`MemberExecutionProvider` by using that host's native control plane. It must
not put the native host behind AgentTeam's direct-ACP owner at the same time.
That keeps one session/process owner and avoids duplicate queues, cancellation
races, competing cleanup, or two sources of truth for the roster.

## Definitions and starting chat

Managed definitions are content-addressed below `$AGENTTEAM_HOME/library`.
Catalog chat always names an exact `id`, `version`, and stored content hash.
An unmanaged Assistant or Team requires `--path`; its exact bytes are
validated and copied into the new run archive before any provider opens.

```text
atm assistant import /path/to/assistant-package
atm team import /path/to/team-v2.yaml

atm assistant chat ASSISTANT_ID --version N \
  --workspace /path/to/project --goal "Bounded goal" \
  --done-when "Criterion one"

atm team chat TEAM_ID --version N \
  --workspace /path/to/project --goal "Bounded goal" \
  --done-when "Criterion one"
```

The interactive implementation accepts only the `shared-supplied` workspace
layout. Assistant chat creates a synthetic one-Member Team whose sole Member
is also the Lead. Every new top-level goal creates a new run and fresh Member
sessions.

## Runtime boundary

Chat never downloads a runtime or searches global npm packages. The optional
reference runtime is an explicit action:

```text
atm runtime install direct-acp
atm runtime doctor direct-acp --harness codex --json
atm runtime doctor direct-acp --harness claude-code --json
# Add --harness grok only when that current profile should be assessed.

# Only after a separate, fresh owner approval to spend model calls:
atm runtime qualify-live direct-acp --harness codex --json
```

The install command uses `npm ci` against the packaged lock and publishes to
a content-addressed directory only after integrity checks. Installed runtime
files are covered by a streamed tree digest, so later mutation invalidates the
install and its qualification. The approved pins are `acpx@0.13.1`,
`@agentclientprotocol/codex-acp@1.6.2`, and
`@agentclientprotocol/claude-agent-acp@0.69.0`.

Doctor performs no model call. For every selected current profile it checks
the native executable/version and conflict-free child environment, then uses
the packaged bridge to initialize ACP, create a session, disconnect, strictly
resume the same backend session id when supported, or prove that the
unprompted empty session can be retired before creating a replacement. It
then inspects status/capability names, closes the session, and confirms bridge
cleanup. The owner-only qualification record explicitly records
`strict-resume` or `fresh-recreate`. Persistent turns and recovery remain
`unknown` at this zero-call stage.

`qualify-live` is the sole bypass for proving those two capabilities. It
requires one exact harness, an attended TTY, and a fresh default-no
confirmation. Once confirmed, it attempts at most five prompts with no retry:
context establishment, recall after a full provider/bridge restart, reset
isolation, new-run isolation, and final continuity/close. Success writes an
owner-only `ProviderLiveAttestationV1` plus manifest hashes for its evidence
runs; a failed attempted lifecycle overwrites an older pass with a failure
record. Windows live qualification is currently paused.

Both records are bound to the platform, packaged lock, installed-tree digest,
native version, ACP command, config home, and a hash of child-environment names
and values. Changing any of those facts makes chat fail closed until doctor
and the attended live qualifier pass again; environment values themselves are
not stored. Chat never invokes either qualifier implicitly.

## Lifecycle and recovery

Each run holds a durable reservation for its canonical workspace plus an OS
controller lease. A second run against the same path is refused; runs against
different projects may proceed concurrently. Turns within one run are
serialized.

Ctrl-C requests cancellation of the queued or running turn and keeps the run
open. EOF or `/detach` marks it interrupted and preserves the durable
reservation. `atm runs attach RUN_ID` acquires the recovery shell, but no
prompt is accepted until every provider proves the same durable session.
Context loss after any attempted turn is never repaired with a replacement.
For a generation with no archived turn of any status, recovery may visibly
retire and recreate it only when prior suspension and exact retirement are
proved; the generation increments and both records remain auditable. Reset
first closes and disposes the old generation, then opens a fresh generation
from immutable definition snapshots and a deterministic `RunStateSummary`;
it never injects the old transcript.

The Lead may propose completion with evidence for every `done_when` entry.
Rejection returns the run to open. Only attended user acceptance closes the
run with a `succeeded` outcome. Close records logical session, process, local
state, and provider-history disposition separately; required cleanup failures
remain visible as `close-failed` and retain the workspace reservation.

## Workspace and permissions

Before and after every turn, AgentTeam records the canonical path, Git HEAD,
Git status hash, and a non-following tree fingerprint. A change that appeared
between observed checkpoints is recorded as external drift with unknown
attribution. Observation never mutates Git or user files.

Effective permission is the intersection of the Assistant ceiling, the
Member/work-item workspace grant, run policy, and provider capability. Reads
must resolve inside the supplied workspace. Mutation additionally requires a
`workspace-write` grant and one attended approval. Network,
outside-workspace, native-spawn, full-access, and unknown classifications
fail closed unless an explicit supported policy covers them. M1c defines no
network, native-spawn, outside-workspace, or full-access run grant, so those
classes are denied even when an attended user is present. Provider-supplied
workspace read/write labels are accepted only when their structured input
contains paths and every path resolves inside the workspace. A machine NDJSON
client cannot claim that a human attended an approval.

## TTY commands

The TTY defaults to the Lead and supports:

```text
/to MEMBER        /members          /tasks
/reset [MEMBER]   /cancel-turn      /recover
/proposal         /accept           /continue
/abort            /close            /detach           /help
```

## NDJSON protocol

`--stream-json` is a bidirectional local-UI seam. The first valid command must
negotiate protocol version 1 and declare whether the client is `attended` or
`machine`:

```json
{"schema":{"kind":"stream-command","version":1},"id":"hello","sequence":0,"command":"negotiate","versions":[1],"client_mode":"machine"}
```

Subsequent client sequences are contiguous and every command id is unique.
Receipts and events carry their schema identity, run id, monotonically
increasing server sequence, and correlation id. Supported commands include
status, members, tasks, turn start/cancel, permission response, Member reset,
recovery, work create/update/assign, completion propose/accept/reject, abort,
close, and detach. `dynamic.*` commands are denied until M1d.

Malformed JSON, fragmented or oversized frames, duplicate ids, out-of-order
sequences, unsupported schemas, and unknown commands produce deterministic
error receipts without consuming unrelated later frames. EOF denies pending
permissions, cancels an active turn, waits for its terminal record, and marks
the nonterminal run interrupted.

## Archives

The owner-only run archive stores immutable definition snapshots, resolved
request and launch metadata, session/turn/work/control/completion records,
workspace checkpoints, correlated run events, and local raw provider streams.
Terminal archives have a verified content manifest.

Successful close finalizes the terminal record and manifest while the durable
workspace reservation is still held. The reservation and controller lease are
released only after archival succeeds. Manifest or reservation-release faults
produce a retryable `close-failed` record, retain the lease, and never claim
that the reservation was released. Ordinary pre-release failures leave the
reservation present; no such fault is reported as `closed`.

`atm runs export` accepts only a closed, manifest-valid run and writes to an
empty directory. The export excludes raw provider event streams, launch-local
metadata, the controller lock, and runtime state. `atm runs cleanup` removes
exactly one closed, valid local archive and is intentionally unrecoverable.
