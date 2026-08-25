# AgentTeam M1d dynamic-member PoC B — approved r2

- Status: **APPROVED FOR DETERMINISTIC IMPLEMENTATION** by the owner's
  2026-08-25 instruction to implement the reviewed r2 plan.
- Precondition: exact M1c G8 close commit and current provider capability
  record.
- Live budget: **zero**. No model call or live dynamic-member support claim is
  authorized by this plan.

## 1. Outcome

M1d proves that the user or a retained-context Lead can add exactly one
run-scoped specialist to an open TeamRun, delegate bounded work against the
same latest project tree, receive a normalized result in a new Lead turn,
include it in a completion proposal, optionally propose the exact specialist
package for reuse, and close every session without mutating the TeamTemplate
or any persistent Assistant package.

Lead-created specialists default hidden and user-added specialists default
visible. Hidden changes only the normal roster projection. The audit roster,
policy request/decision, exact definition/hash, creation saga, session, turns,
work, messages, result, proposal, reconciliation, and cleanup remain complete.

M1d is Team-only. Assistant chat cannot create dynamic Members.

## 2. D0 integration decision

Before source implementation beyond shared M1c contracts, D0 records:

1. the exact M1c G8 commit and capability evidence;
2. accept or drop of the optional M1b ClawTeam provider and its four known
   caveats; and
3. how native worker spawning is disabled, intercepted, or detected for each
   qualified interactive provider.

AgentTeam does not double-wrap ClawTeam, OpenClaw, Hermes, DSH, or another
native host with direct ACP. A future integration calls that platform's native
control plane through `MemberExecutionProvider`. The direct-ACP provider
remains a standalone/reference path.

## 3. Dynamic policy and contracts

M1c owns the closed policy carrier and generic control envelope. M1d activates
the policy and adds `control-request` version 2 with `member.create`, plus:

- `member-create-decision` version 1;
- `ephemeral-member-definition` version 1;
- `member-creation-record` version 1;
- `delegation-record` version 1;
- `member-result` version 1 for interactive delivery; and
- `template-proposal` version 1.

The policy names whether user additions are allowed, allowed creators
(`user`, `lead`), maximum total run-created Members (one for this PoC),
allowed provider/harness and visibility values, workspace-access ceiling,
whether catalog/generated definitions are allowed, and whether promotion may
be proposed.

Every create request has an idempotency id, actor, Member name, definition
source, requested provider/harness, visibility, workspace access, and initial
work item. Unknown fields and enum values deny.

## 4. Ephemeral Assistant package

A generated specialist is materialized as a complete existing
`AssistantDefinitionV1` package under the run archive, including
`assistant.yaml`, persona, principles, collaboration instructions, harness
policy, and all other required package files. It uses the existing canonical
archive hash algorithm. The closed generated subset may express role,
purpose, principles, collaboration instructions, and harness preferences. It
may reference already-resolved catalog capabilities but cannot install
artifacts, write vendor homes, add hooks/plugins, or mutate the source
catalog.

Catalog-sourced specialists resolve an exact immutable Assistant revision.
Both sources are snapshotted before roster/session effects.

## 5. Policy-first creation saga

Creation is a durable saga:

`requested -> denied | allowed -> materialized -> roster-reserved ->`
`session-opening -> active`.

The journal is committed before and after every side effect. Only `active`
Members appear in the normal roster or accept delegation. Failure records the
precise failed step, attempts compensation in reverse order, and leaves the
run `recovery-required` whenever exact cleanup or reconciliation cannot be
proved. A half-created Member is never silently adopted or exposed as active.

Replaying the same idempotency id with byte-equivalent normalized payload
returns the recorded result without side effects. Reusing the id with a
changed payload is denied and audited. Any second dynamic Member request is
denied before materialization.

## 6. Work graph, delegation, and result return

Dynamic work extends the interactive work-item graph; it never rewrites the
V1 static DAG. A new item may depend on known items, but dependencies of
running or terminal items are immutable. Cycles, unknown owners, retroactive
blockers, and reassignment of terminal work fail before persistence.

The requesting Lead turn commits before the specialist turn begins,
preserving M1c's single-turn workspace scheduler. Session activation creates
an `ACK` delegation state. The specialist returns `DONE` with
`MemberResultV1 {summary, deliverables, risks}` or `BLOCKED` with a truthful
reason. AgentTeam commits the result, workspace checkpoint, and work state,
then starts a new retained Lead turn carrying the normalized result. The
specialist may receive more turns in the same run and retains its own context
until reset or closure.

## 7. Native-spawn control and reconciliation

Qualified providers must disable or intercept native worker spawning. When a
provider can only observe it, AgentTeam periodically reconciles its provider
roster/session view with the audit roster. Any unregistered provider Member or
session pauses dispatch, records an incident, and sets `recovery-required`;
it is never silently adopted, ignored, or reported as policy-compliant.

Direct provider calls are outside the mechanical policy boundary and must be
reported as such. No provider integration may own an independent AgentTeam
policy database or second roster projection.

## 8. Promotion proposal

An ephemeral Member may propose an exact reusable Assistant package. The
proposal contains source run/Member/generation, candidate id/version, exact
bytes and content hash, project-fact/secret/path scans, and a human-readable
diff.

M1d may publish only a previously unused `id@1`. Acceptance reacquires the
catalog lock, revalidates that approved bytes/hash and scans are unchanged,
and atomically imports that immutable revision. A collision or drift rejects
without catalog mutation. Rejection changes nothing. Evolving an existing
Assistant revision or updating TeamTemplate references remains M3.

## 9. Gates

| Gate | Exit evidence |
| --- | --- |
| D0 | Exact M1c G8 commit, ClawTeam ADR, zero-live boundary, and native-spawn control record |
| D1 | V2 control plus policy, decision, definition, saga, delegation, result, projection, and proposal contracts/materializer |
| D2 | Journaled saga, idempotency, compensation, recovery, reconciliation, and work/session integration |
| D3 | ACK/DONE/BLOCKED delegation, new-Lead-turn result delivery, visible/audit projections, and exact promotion accept/reject |
| D4 | Deterministic hidden-specialist PoC and complete policy/fault matrix |
| D5 | Cross-platform regression, exact cleanup/evidence/risk review, and deterministic milestone close |

## 10. Deterministic acceptance

The positive PoC uses a fake retained-context Lead that creates exactly one
hidden specialist, observes the shared latest code, delegates a bounded work
item, receives a normalized result in a new Lead turn, cites it in a
completion proposal, receives user acceptance, and closes every provider and
run store exactly.

Negative cases include wrong creator, disabled manual creation, second Member,
provider/harness, visibility, access, malformed definition, unresolved
catalog reference, artifact/vendor mutation, idempotency collision, roster
collision, illegal dependency rewrite, out-of-band provider Member, changed
promotion bytes, catalog collision, and failure before/after every journal,
materialization, reservation, session, result, publication, and cleanup step.
Every denial precedes effects. Persistent TeamTemplate and Assistant hashes
remain byte-identical.

## 11. Boundaries and stop rules

- One dynamic level and one run-created Member only; no nested TeamRun or
  parent/depth semantics.
- Lead-mediated delegation only; no arbitrary peer-to-peer topology.
- No artifact installation, automatic definition optimization, UI/MCP
  integration, or live-model claim.
- Stop for an owner decision before changing approved contracts, adding a
  dependency/provider pin, weakening policy/cleanup, or making a live call.
- Native OpenClaw/DSH/Hermes/ClawTeam provider implementations remain separate
  future milestones unless D0 explicitly scopes one in.
