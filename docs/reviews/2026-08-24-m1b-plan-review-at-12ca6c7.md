---
title: Fifth independent review of the M1b team-foundation plan r5 at commit 12ca6c7
status: final review record — findings dated 2026-08-24, valid for the tree at `12ca6c7` only
date: 2026-08-24
reviewer: owner-supplied review, independently rechecked and adjudicated by Codex; formatting and disposition are normalized without weakening the supplied findings
scope: docs/plans/m1b-team-foundation.md revision r5 as committed in `12ca6c7` (`docs(plans): M1b r5 - resolve the r4 review findings`), read against the repository at that SHA; fifth review round following the r1–r4 records
reviewed_commit: 12ca6c730f99816ed79c6e0537de021d25dd24b2
reviewed_plan_sha256: 95ff6ab3816efd61db845216b34aecb64b8d22efde3f13a727027c612a44acf4
decisions_recorded_in: `.project-steward/DECISIONS.md` 0043 (2026-08-24), landing with the r6 follow-up; the later G0 approval remains its own entry
companion: none
---

# Fifth independent review — M1b plan r5 at `12ca6c7`

## 0. Verdict and adjudication

Do not approve r5. r5 closes the r4 contract holes in prose: explicit
`workspace_access`, durable allocation and archive verification, the
`CleanupOutcome` handshake, publication ordering, NFC/casefold deliverable
rules, and occurrence-level containment. The fifth review nevertheless
finds four implementation-blocking areas:

1. Claude's writable allow and deny sets overlap;
2. team Grok lacks a standalone/team-member dispatch fact and writes the
   authenticated persistent home rather than an isolated project profile;
3. lifecycle step 5 still supplies the wrong-time `target.before`; and
4. fault-abort finalization can pair a succeeded invocation with an
   `abandoned` owning task, with the same ambiguity affecting other
   launched work.

The supplied review classified the fourth item as medium. The adjudication
elevates it to implementation-blocking because it leaves the terminal
record contract non-deterministic. Two refinements also strengthen the
selected resolution:

- Grok project profiles use per-invocation names and fail closed on global
  name collisions because Grok 1.0.5 can prefer the global definition with
  only a warning.
- Codex's documented default network posture is off, not “typically
  allowed.” r6 nevertheless pins
  `sandbox_workspace_write.network_access=false` for team writable renders
  so workspace mutation never implicitly becomes a network grant.

The findings are frozen against full commit
`12ca6c730f99816ed79c6e0537de021d25dd24b2` and plan SHA-256
`95ff6ab3816efd61db845216b34aecb64b8d22efde3f13a727027c612a44acf4`.
Resolutions belong in plan revision r6 and ADR 0043; this record is not
edited after the fact.

## 1. Findings

### Approval blockers

1. **High — Claude writable still collides with the deny list.**

   Frozen r5 anchor: `docs/plans/m1b-team-foundation.md:1006-1008`.
   r5 keeps `Write,Edit` in `--disallowedTools` for read-only and says the
   writable recipe “adds only `Write,Edit`,” without removing them from the
   deny set. The installed help does not define an allow-plus-deny overlap
   in a way the plan can safely depend on.

   Pin the complete disjoint sets. Read-only allows
   `Read,Grep,Glob,LS,Skill` and denies
   `Write,Edit,NotebookEdit,Bash,WebFetch,WebSearch`; writable allows
   `Read,Grep,Glob,LS,Skill,Write,Edit` and denies
   `NotebookEdit,Bash,WebFetch,WebSearch`. Both retain `dontAsk`.

2. **High — the Grok team mapping is not independently keyed and writes
   the persistent authenticated home.**

   Frozen r5 anchor: `docs/plans/m1b-team-foundation.md:1009-1020`.
   `RenderContext.workspace_access` defaults to read-only for both direct
   and team calls. r5 can currently infer the team path from
   `output_contract: member-result`, but that is an undocumented side
   channel and couples output shape to sandbox selection. More seriously,
   `GROK_HOME/sandbox.toml` is the live authenticated profile home, so r5's
   recipe can overwrite owner state. Authentication cannot move to a
   disposable home.

   Add an explicit `standalone | team-member` render discriminator. For a
   team member, write the isolated workspace's `.grok/sandbox.toml`, record
   it in `files_written`, and never write persistent `GROK_HOME`. Use a
   unique per-render custom profile extending the matching `read-only`
   or `workspace` built-in. Fail closed if the project path already exists,
   the persistent sandbox file is malformed/unreadable, or it defines the
   generated name. Direct Grok must retain its exact built-in
   `--sandbox read-only` recipe.

3. **High — `target.before` is still specified at step-5 copy time.**

   Frozen r5 anchors: `docs/plans/m1b-team-foundation.md:935-936`,
   `:1072-1079`, and `:1347-1349`.
   Lifecycle step 5 retains M1a's copy-plus-target-hash wording, while the
   later deliverable contract and acceptance condition require a
   successor's baseline to include its materialized handoff. An
   implementation following step 5 would reuse the source-copy hash and
   fail that acceptance condition.

   Make step 5 copy verification only: require
   `hash(copy) == hash(source)`. Compute invocation `target.before` at
   launch after incoming handoff materialization and final rendering,
   excluding renderer-owned paths by the same rule used for `after`.

4. **Implementation blocker — the failure finalizer has no truthful
   task/invocation terminal-pair policy.**

   Frozen r5 anchors: `docs/plans/m1b-team-foundation.md:1102-1116`,
   `:1165-1170`, and `:1188-1195`.
   Publication barrier step 6 makes an invocation succeeded before step 7
   calls provider `completed`. If that provider call raises, r5's blanket
   sweep can mark the owning non-terminal task `abandoned` next to the
   succeeded invocation. A blanket abandoned result is also false for an
   in-flight sibling terminated by a fault abort.

   Add run-only task `cancelled` and an exhaustive closure matrix:
   publication failure before successful invocation terminalization gives
   invocation/task `failed`; provider completion failure after successful
   publication preserves invocation `succeeded` and marks its task
   `failed`; non-causal allocated work stopped by abort gives task
   `cancelled`, cancelling a nonterminal invocation but preserving an
   already-succeeded one; never-allocated/cascade remainder is `abandoned`;
   prior `completed` work stays completed. Inject provider
   completion failures both before and after the provider state commit;
   accept only the exact residual projections (`running` or `completed`)
   and never launch a successor.

### Medium corrections

5. **Medium — the containment inventory omits `domain/run.py`.**

   Frozen r5 anchor: `docs/plans/m1b-team-foundation.md:1439-1447`.
   The team variant's `substrate.kind` lives on `RunRecordV1`, so a literal
   `clawteam` would naturally appear in `domain/run.py` even though r5's
   frozen inventory allows the domain literal only in `domain/team.py`.

   Define one shared `SubstrateKind` in `domain/team.py`, import it from
   `domain/run.py`, and freeze `domain/run.py` at zero token occurrences.

6. **Medium — Windows team-Grok sandboxing is not supported by the cited
   evidence.**

   Frozen r5 anchor: `docs/plans/m1b-team-foundation.md:1021-1027`.
   Grok's bundled 1.0.5 guide documents kernel enforcement and custom
   fail-closed behavior for Linux/macOS, not Windows. Hosted Windows is in
   the M1b matrix while vendor-smoke still skips Grok.

   Refuse team-Grok at preflight on Windows (exit 2, no run directory) and
   keep fake/argv coverage OS-agnostic through injected platform facts.

### Consistency and traceability corrections

- `wait` is a protocol default over `tasks()`, not a provider method. Say
  eleven runtime-invoked provider methods plus one protocol `wait` helper.
- State Codex's network posture precisely: current user config is ignored,
  documented default network access is off, and team workspace-write pins
  that denial explicitly.
- Preserve the existing direct Grok `--sandbox read-only` render
  byte-for-byte in its unit regression.
- Add ADR 0043 and update PLAN/HANDOFF/QUESTIONS to five review rounds. The
  prior active-session marker is not itself a defect, but its commit/state
  facts must move to the r6 world.

## 2. Sound areas not reopened

- Zero live calls in M1b; live writable/member-result handoff remains M1c.
- `HarnessAdapter.parse()` remains untouched; team result extraction uses
  `StructuredExtractor`, `MemberResultV1.model_validate`, and
  `write_member_result`.
- Cleanup keeps local state, deletes only a verified ClawTeam snapshot,
  and preserves the qualification evidence that upstream cleanup alone
  retains it.
- The failed-routed disposition gate and separately collected dated xfail.
- Owner bijection as an explicit M1b product constraint; HB-03 deferred.
- The stable `~/.agentteam/clawteam/` root and `create_space(lead)` seam
  delta.
- Direct-mode contracts and argv remain unchanged.

## 3. Disposition

r6 is the selected docs-only remediation. It must close every finding in a
plan §21 r5→r6 table, add ADR 0043 and a terminal-pair risk row, and update
Project Steward state. No G0 approval, product source, schemas, discovery
registers, live calls, push, or live capability upgrade is implied.
