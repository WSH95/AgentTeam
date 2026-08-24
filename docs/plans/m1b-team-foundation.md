# AgentTeam M1b team-foundation plan — draft r0

- Status: **draft r0, proposed 2026-08-24 — NOT approved.** Produced as the
  M1a G8 deliverable that "names the local deterministic provider first and
  the ClawTeam exit criterion" (M1a plan §3 G8 row). Implementation starts
  only after this draft is expanded, independently reviewed, and approved as
  a `DECISIONS.md` entry naming this file and its commit SHA (the §21
  convention; ADR 0021 precedent). Per M1a plan §18, nothing here begins in
  the M1a approval scope.
- Prerequisites carried in: the G4-qualified ClawTeam seam
  (`docs/evidence/clawteam-qualification-2026-08-23.md`), ADR 0015 (exact
  pin, extra-only, subprocess backend never used), ADR 0018 (measurement
  decides), ADR 0037 (build-vs-reuse reaffirmed post-G6).

## Outcome (PROJECT.md M1b–M2 criteria, first half)

TeamTemplates composed of portable Assistant definitions execute as fresh
TeamRuns over an optional coordination substrate behind the
`CoordinationSubstrate` seam; declared vs achieved enforcement is recorded
honestly. Harness launching stays exclusively on the M1a built-in direct
runner — no coordination provider ever launches a harness.

## Named contracts (to be specified at approval, not here)

`TeamTemplateV1` (Assistants by reference, roles, visibility), `TeamRunV1`
(fresh run instance; `RunRecordV1` remains its one-Member subset),
`MemberV1` (execution `{kind: invocation | ensemble}` binding, M1a plan §7),
and the `CoordinationSubstrate` protocol (task store, mailbox, snapshot,
opaque namespace). All external records are versioned JSON Schemas beside
the nine V1 schemas.

## Provider order

1. **Local deterministic coordination provider FIRST** (product-owned): file
   task store, file mailbox, snapshot — drives every deterministic test and
   hosted CI leg (ADR 0018 decision 2).
2. **Optional ClawTeam provider SECOND**, behind the G4-qualified seam:
   exact pin `0.3.0 @ 0119833…` + `mcp>=1,<2`, extra-only install, imports
   confined to the one compatibility module, isolation claim `namespace`
   only, `SubprocessBackend` never used.

## ClawTeam exit criterion (draft wording; written before PoC B, finalized at M1b approval)

> The ClawTeam provider remains a supported substrate only if the provider
> glue plus its workarounds measure **≤ 1.5× the local deterministic
> provider's LOC** (measured as in the G4 qualification report — the seam's
> 233 LOC / 281 test-LOC baseline), **and** the recorded caveats — two
> rosters, no parent link for nested teams, cleanup never stops processes,
> every containment is caller-written code — are **accepted in writing**.
> Otherwise the local deterministic provider becomes the product path and
> ClawTeam support is dropped without replacement.

(Source: the open QUESTIONS item filed by the 2026-08-23 review R2/R13; the
G4 feed-forward paragraph. This wording is proposed, not decided.)

## PoC boundary

M1b delivers contracts, the two providers, and deterministic team-lifecycle
evidence only. The live dynamic-member PoC B (Lead/Implementer/Reviewer with
a hidden temporary specialist, mechanical policy enforcement for
AgentTeam-mediated creation) is M1c; nested TeamRuns and MCP are M2 (M1a
plan §19). Any live calls need their own owner ceiling decisions (5 of the
M1a 30-call ceiling remain; M1b sets its own budget at approval).

## Explicitly outside

ClawTeam spawning/tmux/keepalive/board/upstream PRs (Q4 stays a separate
owner decision); ACP/daemons/messaging surfaces (Hermes/OpenClaw/Telegram —
later milestones; Q6); overlays/evolution (M3); everything in M1a plan §20.

## Approval checklist

1. Expand this draft to a full plan (contracts, gates, test matrix, budget,
   stop rules) in its own session.
2. Independent review (the 3407ec9/317bb52 precedent).
3. Owner approval recorded in `DECISIONS.md` naming the file + commit SHA;
   only then does implementation begin.
