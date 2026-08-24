---
title: Independent review of the M1b team-foundation plan r1 at commit 14dc218
status: final review record — findings dated 2026-08-24, valid for the tree at `14dc218` only
date: 2026-08-24
reviewer: independent review session at the owner's request; the verdict below was delivered verbatim by the owner on 2026-08-24 (reflowed from terminal line-wrapping; wording unchanged)
scope: docs/plans/m1b-team-foundation.md revision r1 as committed in `14dc218` (`docs(plans): expand M1b team-foundation plan to r1 (proposed for independent review)`), read against the repository at that SHA
decisions_recorded_in: `.project-steward/DECISIONS.md` 0039 (2026-08-24); the later G0 approval remains its own entry
companion: none
---

# Independent review — M1b plan r1 at `14dc218`

## 0. Verdict and how to read this

This file records the independent review verdict verbatim as delivered.
Findings 1–7 are approval-blocking; the hygiene items follow. Resolutions
are tracked in the plan's r2 revision record
(`docs/plans/m1b-team-foundation.md` §21) and ADR 0039 — this file is a
dated record and is not edited after the fact; follow-ups live in
`.project-steward/`.

## 1. Verdict (verbatim)

Do not approve M1b r1 at 14dc218 yet. The architecture direction is sound,
but seven approval-blocking ambiguities or contradictions require r2.

1. ClawTeam completion is contradictory. M1b "done" requires ClawTeam
   lifecycle parity (docs/plans/m1b-team-foundation.md:36), while G5
   failure explicitly does not block G7
   (docs/plans/m1b-team-foundation.md:115). Define G5 as either mandatory
   or a recorded PASS | DROP disposition. I recommend allowing
   local-foundation completion only after ClawTeam's supported/dropped
   status is explicit.

2. The schema-change inventory is incorrect. R1 says HarnessInvocationV1
   is unchanged (docs/plans/m1b-team-foundation.md:274), but
   selection.decided_by gains team
   (docs/plans/m1b-team-foundation.md:319), necessarily regenerating
   harness-invocation-v1.schema.json. G1 must name that change. Also
   require JSON-Schema-level negative tests for invalid direct/team field
   combinations; Pydantic model validators alone do not protect non-Python
   consumers.

3. HB-03 option A is not implementable from this plan. constraints is
   defined and tested only as reserved-empty
   (docs/plans/m1b-team-foundation.md:229), while approval may select
   filter-then-prefer without defining its schema, cross-member algorithm,
   or failure cases (docs/plans/m1b-team-foundation.md:802). Recommend
   choosing Defer for M1b, or fully specifying and testing option A in r2
   before approval.

4. The claimed team-selection evidence is underdetermined. Every example
   member reuses code-reviewer, whose Assistant preference starts with
   Claude (examples/assistants/code-reviewer/assistant.yaml:43); Assistant
   preferences outrank team preferences. Therefore template preferences
   alone cannot produce decided_by: team, and all members default to
   Claude. Add an Assistant fixture with no applicable preference, and
   explicitly require either a team-decided selection and mixed harnesses
   or defer those claims.

5. Team execution lacks a decision-complete task data flow. The plan names
   task_file, workflow placeholders, owned DAG tasks, and member launches,
   but never defines interpolation, the task/context rendered to each
   Member, when blocked owners may launch, or how invocation
   success/failure changes task state
   (docs/plans/m1b-team-foundation.md:484). Without this, acceptance could
   launch everyone first and merely flip task rows afterward. Specify
   runnable-task scheduling, handoff payload construction, task
   completion/failure propagation, and corresponding ordering assertions.

6. The public request and provider interfaces remain ambiguous. Per-member
   harness/model/effort override shapes and their merge behavior with
   existing global CLI flags are unspecified; ensemble/synthesis behavior
   is also unresolved. Separately, create_space() takes no lead, while the
   existing ClawTeam seam creates a hard-coded atm-lead
   (src/agentteam/compat/clawteam.py:124), conflicting with exact roster
   parity. Define the wire shapes and CLI rules, and change space creation
   to accept the logical Lead or define an explicit identity mapping.

7. Failure finalization and archive durability are incomplete. The normal
   lifecycle snapshots and cleans up, but no contract covers provider
   failure, partial launch, timeout, or cancellation while guaranteeing a
   terminal record and stop-before-cleanup. Consuming mailbox reads can
   also erase messages before the final snapshot unless an independent
   audit log exists. Add fault-injection tests for every lifecycle phase
   and specify durable message history, snapshot location/reference, and
   local-provider cleanup semantics.

Hygiene corrections:

- The normative glossary includes stop in CoordinationSubstrate, while r1
  deliberately removes it; record that amendment in the normative
  docs/decision history.
- The revision record says nothing from r0 was dropped, although
  TeamRunV1/MemberV1 were replaced by an extended record family.
- Make the ClawTeam LOC boundary mechanically enforced with a static
  containment test, not only a prose stop rule.

## 2. Disposition

Every finding was independently re-verified against the tree at `14dc218`
by the executing session before any resolution work (all ten confirmed;
verification anchors recorded in PROGRESS and ADR 0039). Resolutions land
as plan revision r2; the owner's HB-03 decision (finding 3) is **Defer**
— recorded in ADR 0039. This record is valid for `14dc218` only.
