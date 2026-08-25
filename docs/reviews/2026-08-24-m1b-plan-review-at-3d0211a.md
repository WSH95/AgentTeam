---
title: Independent review of the M1b team-foundation plan r4 at commit 3d0211a
status: final review record — findings dated 2026-08-24, valid for the tree at `3d0211a` only
date: 2026-08-24
reviewer: Codex independent review at the owner's request; formatting below is normalized from the delivered review while preserving its findings and recommendations
scope: docs/plans/m1b-team-foundation.md revision r4 as committed in `3d0211a` (`docs(plans): M1b r4 - resolve the r3 review findings`), read against the repository at that SHA; fourth review round following the r1, r2, and r3 records
reviewed_plan_sha256: e1c7f222ce22785b37eb22fca553281d0936b5367313a3a7b9a1d38c587200c9
decisions_recorded_in: `.project-steward/DECISIONS.md` 0042 (2026-08-24), landing with the r5 follow-up; the later G0 approval remains its own entry
companion: none
---

# Independent review — M1b plan r4 at `3d0211a`

## 0. Verdict and how to read this

Do not approve r4 yet. The review found three high-severity contract gaps,
three medium-severity implementation gaps, and four consistency defects.
The findings below are frozen against full commit
`3d0211a456cedb356aa512cb5f257b448dbb70e1` and plan SHA-256
`e1c7f222ce22785b37eb22fca553281d0936b5367313a3a7b9a1d38c587200c9`.
Resolutions belong in plan revision r5 and ADR 0042; this record is not
edited after the fact.

## 1. Findings

### Approval blockers

1. **High — real harness adapters remain read-only while the team
   deliverable contract requires mutation.**

   The plan explicitly permits a member to mutate its isolated workspace
   and makes the committed implementer create a declared deliverable
   (`docs/plans/m1b-team-foundation.md:947`). The production adapters,
   however, still deny Claude `Write`/`Edit`, pass Codex `-s read-only`,
   and pass Grok `--sandbox read-only`
   (`src/agentteam/harness/claude.py`, `codex.py`, `grok.py`). The fake can
   satisfy the fixture while no real member can satisfy the advertised
   contract.

   Add an explicit per-task workspace-access contract with a read-only
   default, audit the resolved grant in the run record, and map writable
   access to each adapter's version-supported least-privilege controls.
   Keep direct and synthesis paths read-only and move first live writable
   acceptance to M1c.

2. **High — the execution-binding invariant is not model-validatable as
   written.**

   The team record says `execution: null` means the member never launched
   and permits null based on whether its task reached `running`
   (`docs/plans/m1b-team-foundation.md:414-420`), but the terminal model
   contains no task-state history and the sweep maps both never-launched
   and formerly-running unfinished tasks to `abandoned`. A Pydantic model
   cannot inspect event or invocation files, so the promised lifecycle
   validator cannot prove the stated rule. `--render-only` also shares
   enough lifecycle wording with execution to leave stub workspaces and
   bindings ambiguous.

   Define null as “no durable invocation record was allocated,” pin the
   allocation/binding point before provider-running/spawn, keep only
   representable model validators, and enforce the cross-file bijection in
   an archive verifier. Make render-only an explicit pre-execution branch
   with no run/provider/member/invocation state.

3. **High — verified snapshot deletion has no protocol handshake.**

   The plan requires the ClawTeam adapter to delete its provider-side
   snapshot only after the run layer has written and hash-verified the
   archive copy (`docs/plans/m1b-team-foundation.md:714-721`), but the
   protocol exposes only `snapshot`, `read_snapshot`, and `cleanup(space)`.
   The provider therefore cannot know whether copy-out verification
   succeeded. Naming the stable root's absolute path in a failure detail
   also conflicts with the event/privacy rule that paths do not escape.

   Pass the verification result explicitly to cleanup (or add a release
   operation), return a structured cleanup outcome, retain on every
   unverified path, and expose only opaque namespace/retention facts.

### Medium corrections

4. **Medium — task completion has no atomic publication barrier.**

   The plan names result persistence, deliverable archival/materialization,
   ledger/send, invocation completion, and provider task completion, but
   does not impose one ordering. If provider completion auto-unblocks a
   successor first, that successor may launch against missing artifacts or
   handoff data.

   Persist and verify the result and outgoing handoffs before the provider
   sees `completed`; only then update run state, emit completion/unblock
   events, and schedule successors. Give member-contract errors task-failure
   semantics and infrastructure publication errors run-abort semantics.

5. **Medium — containment freezes files, not the allowed occurrences.**

   The four-path textual allowlist
   (`docs/plans/m1b-team-foundation.md:1282-1298`) still lets arbitrary
   ClawTeam branches accumulate in the two declarative exception files,
   including the CLI-facing registry module. That weakens the mechanical
   LOC boundary the test is intended to defend.

   Freeze an exact AST/token multiset for the declarative exceptions, keep
   the CLI substrate-generic, and ensure the failed-routed reproduction is
   collected outside the success suite's module-level skip.

6. **Medium — deliverable path safety is not cross-platform canonical.**

   The declared-path checks cover traversal, directories, symlinks,
   duplicates, and `handoff/`, but not Unicode normalization, case-folded
   collisions, symlinked parent components, or adapter-owned files written
   into a member workspace. Those omissions can produce different archive
   contents across filesystems or let injected AGENTS/Skill files be
   re-exported as member work.

   Require NFC, reject case-folded collisions uniformly on every OS,
   `lstat` every component, exclude renderer-owned paths and their
   non-root parents, and hash-verify both archive and successor copies.

### Consistency corrections

- Section 20 says eleven provider operations although section 14 correctly
  enumerates twelve.
- The review charter refers to two review records where r4 already has
  three; r5 will have four after this record.
- The inherited ADR list omits ADR 0041.
- Owner bijection is justified by `execution` being required even though
  r4 made the team binding nullable; it should instead be stated as the
  deliberate one-member/one-task M1b product constraint.

## 2. Disposition

All findings were checked against the frozen r4 tree. The selected r5
resolution is the least-privilege path: explicit task access with
read-only default; durable-allocation execution semantics plus an archive
verifier; a cleanup verification handshake; a publication barrier;
canonical deliverable validation; and occurrence-level containment.
Direct/ensemble behavior, `HarnessAdapter.parse()`, M1b's zero-live-call
budget, and the later owner G0 approval boundary remain unchanged.
