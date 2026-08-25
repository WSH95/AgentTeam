# AgentTeam M1c dynamic-member PoC B plan — draft r0

> **Historical planning input for the candidate r1 split.** The proposed,
> unapproved review drafts are
> `m1c-interactive-teamrun-foundation.md` and
> `m1d-dynamic-member-poc.md`. Neither draft authorizes implementation or a
> live call. This r0 remains unchanged below this banner for comparison.

- Status: **PROPOSED — NOT APPROVED.** This r0 is the M1b G7 naming
  deliverable only. It does not authorize product implementation, dependency
  changes, live model calls, or a push. M1c needs its own expanded plan,
  independent review, frozen revision, and explicit owner G0 approval.
- Predecessor: M1b Plan R6, approved at `760a8ae` and implemented through G7.
  M1b supplies TeamTemplate/TeamRun/MemberResult contracts, the local provider,
  the optional ClawTeam provider at `parity-green`, and deterministic lifecycle
  evidence. M1b spent zero live calls.
- Roadmap source: M1a plan section 19 item 2 and M1b plan section 18.

## 1. Proposed outcome and boundary

PoC B should prove that a reusable Lead/Implementer/Reviewer TeamTemplate can
create one temporary specialist through an AgentTeam-owned policy gate, use it
in the task DAG, and archive it completely while omitting it from the normal
user-facing roster projection. The specialist is hidden for presentation, not
for security: the archive and audit projection remain complete, and provider
rosters may still expose it.

The default hypothesis is a fresh Lead invocation at each decision point with
a RunStateSummary, not a resident Lead. The detailed plan must falsify or retain
that hypothesis before implementation. Harness launching remains in the
product-owned runner; no coordination provider launches or stops a harness.

## 2. Decisions and evidence required before G0

1. **ClawTeam exit criterion — pending owner decision.** G6 measured
   `516 / 486 = 1.061728395x`, below the approved `1.5x` ceiling. Before PoC B
   begins, the owner must choose either to keep optional ClawTeam support while
   accepting all four recorded caveats, or to drop it without replacement.
   This draft does not infer the answer. The local provider remains the product
   path under either choice.
2. **Live-budget ask — proposed, not approved.** Reserve a new M1c ceiling of
   **18 live model calls total**: up to three current-version capability probes,
   up to two six-call PoC B cycles, and up to three individually approved
   diagnostic calls. Each cycle still requires a fresh owner go at a green
   no-call gate; there is no automatic live retry or API-mode fallback. The
   five calls left under M1a's 30-call ceiling do not transfer into M1c and
   remain individual owner decisions.
3. **Harness set and claims — unresolved until fresh probes.** Start planning
   from the M1b deterministic set, but describe live support only for clients
   whose then-current structured-output and workspace controls pass the M1c
   probe. Grok's prior task-scale limitation and Windows team refusal remain
   evidence boundaries, not silent exclusions or passes.
4. **HB-03 constraints — still owner-owned.** Team-level constraint precedence
   remains reserved. The expanded plan must either receive the owner answer or
   keep constraints outside M1c without inventing semantics.

## 3. Proposed contract delta

- Replace the reserved-empty `dynamic_members` field with a closed policy that
  names allowed creators, a positive maximum count, and allowed harnesses.
- Add an archived ephemeral-member shape carrying at least `visibility:
  hidden`, `origin: ephemeral`, `created_by`, the policy decision, the resolved
  Assistant definition/hash, and its invocation/task references.
- Define separate complete/audit and visible roster projections. Hidden is a
  UI projection only; records must state achieved enforcement and provider
  visibility honestly.
- Relax M1b's one-task-per-static-member owner bijection only as much as needed
  for policy-approved ephemeral tasks, while retaining unique task ownership,
  acyclicity, and terminal-state consistency.
- Activate the reserved handoff-ack vocabulary and define the minimum
  member-to-member messaging operations needed by PoC B. No general chat or
  surface protocol belongs here.
- Keep `parent`, `depth`, and `nested_runs[]` reserved for M2 and
  `overlay_refs` reserved-empty for M3.

Every public schema change must be additive or explicitly versioned, vendor
dialect checked where model-facing, and accompanied by JSON-Schema and model
negative tests. The expanded plan must pin the exact shapes before G0.

## 4. Proposed delivery gates

| Gate | Proposed work | Minimum evidence before close |
| --- | --- | --- |
| G0 | Review and approve the expanded M1c plan | Frozen plan SHA, independent findings resolved, the exit-criterion decision recorded, exact live ceiling approved, and every owner choice explicit |
| G1 | Dynamic-member contracts and schemas | Closed policy/member/projection shapes; static M1b records remain valid; reserved M2/M3 fields unchanged; negative and vendor-dialect tests green |
| G2 | Product-owned creation policy | Allow/deny is decided and durably recorded before any task, provider, workspace, or harness side effect; every AgentTeam-mediated creation uses the gate; provider-bypass limits are explicit and tested |
| G3 | Dynamic lifecycle integration | Policy-approved member/task allocation, complete and visible roster projections, handoff acking, message enforcement, archive reconstruction, failure finalization, and cleanup are deterministic |
| G4 | Deterministic PoC B acceptance | Fake-harness workflow creates exactly one hidden ephemeral specialist, completes the DAG, preserves definitions, proves audit/visible projections, and records declared versus achieved enforcement on every core CI leg |
| G5 | Current-version live capability gate | Under a separately approved go and ceiling: member-result structured-output channel plus read-only/workspace-write controls are freshly probed for every candidate supported harness |
| G6 | Live PoC B acceptance | One owner-attended workflow produces valid member results and a declared writable deliverable on every then-supported harness; semantic and mechanical results are recorded separately |
| G7 | M1c close | Sanitized evidence reviewed, hosted deterministic matrix green, live ledger reconciled, risks/claims current, and M2 remains separately planned and unapproved |

G0–G4 are zero-call work. G5 and G6 may not begin merely because this draft
exists; they require the approved M1c plan, an approved exact ceiling, a green
deterministic gate, and a fresh owner go.

## 5. Proposed deterministic acceptance

The committed PoC B fixture should use the reusable development team and add
one specialist after the Lead makes an explicit creation request. Acceptance
must prove all of the following without a vendor executable:

1. an allowed request is policy-decided and recorded before creation, while
   wrong creator, excess count, disallowed harness, malformed definition, and
   replayed/colliding identity requests fail before side effects;
2. the specialist owns a real DAG task, produces a schema-valid MemberResult,
   and participates only through the declared handoff/message edges;
3. the visible roster contains only the declared team while the audit roster,
   run record, task history, invocation, result, messages, and archive contain
   the specialist and its provenance;
4. the static template and every persistent Assistant definition hash remain
   unchanged; ephemeral state exists only in the run archive;
5. provider reconciliation detects an out-of-band or unregistered member and
   records the boundary instead of claiming universal enforcement;
6. faults at policy persistence, member/task allocation, launch, result,
   publication, projection, and cleanup produce truthful terminal pairs and no
   successor launch after an ambiguous commit; and
7. local and whichever optional-provider disposition the owner selected pass
   the same normalized lifecycle evidence on the supported OS matrix.

## 6. Member-result live-acceptance handoff

M1b proves `member-result-v1` only through deterministic fakes. M1c must obtain
the first live vendor acceptance evidence for that full schema through every
then-supported client's structured-output channel. After a fresh version-bound
probe establishes the exact access mapping, M1c must also run one writable
declared-deliverable smoke per then-supported harness and verify:

- the task's resolved workspace grant matches rendered controls;
- only declared deliverables propagate, with digest verification;
- persistent vendor homes and portable definitions remain unchanged;
- the MemberResult validates and links to the invocation/task/archive; and
- unsupported or drifted clients fail closed and are not described as live
  supported.

This is a named risk and required handoff, not evidence supplied by M1b.

## 7. Explicitly outside this draft

- M2 nested TeamRuns, parent/depth semantics, and the `atm` MCP server;
- M3 overlays/evolution and artifact installation;
- M4 resident operations, schedulers, watchers, or unattended model use;
- coordination-provider process launching, tmux, keepalive, or shell backends;
- hidden-member secrecy, pairwise filesystem isolation, or a universal claim
  that direct provider callers cannot bypass AgentTeam policy;
- Hermes/OpenClaw/messaging-surface expansion without a separate evidence and
  owner decision; and
- any product implementation or live call under the M1b approval scope.

## 8. Stop and approval rules

- A live call before the approved M1c G5/G6 go is a stop-rule violation.
- The owner exit-criterion decision is required before PoC B begins.
- A policy path that can create an AgentTeam-mediated member without the one
  durable gate blocks live work; provider-direct bypasses must be recorded and
  bound the claim rather than hidden.
- A current harness that cannot prove the structured result or exact workspace
  control is excluded from the live-support claim pending an owner decision;
  tests are not weakened to preserve the candidate set.
- M2/M3/M4 work or a new dependency requires a separately approved scope.

The next authorized action after M1b is planning and independent review of an
expanded M1c revision. It is not implementation.
