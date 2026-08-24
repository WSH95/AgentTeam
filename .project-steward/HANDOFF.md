---
updated_at: 2026-08-24T15:48:28Z
updated_by: claude
session_status: active
branch: main
last_commit: 9b8d116
---
# Handoff

## Now

**G6 remains open after its second owner-attended cycle
(`run-20260824-154050-7a98`) failed at synthesis attribution — but the
mechanical tier passed live for the first time and G6.R1–R3 are proven in
vivo.** All three legs succeeded with valid projected schemas on attempt 1
(Grok 8.7s — the null-field failure is gone; Codex 62.9s; Claude 122.2s — the
draft-07 rejection is gone); the real archive is recursively 0700/0600 with a
clean manifest and clean sanitizer scan. Exit 1: the synthesis report's
`agreements[].sources` used bare invocation ids where the validator requires
`invocation_id:finding_id` pairs (merged findings used pairs correctly); the
task document's own "Refer to legs only by invocation id" line steers toward
the error. The first formal live semantic evaluation FAILED: cond-2 (Codex 1,
Grok 0 identified defects), cond-3 (union misses `input-mutation`), cond-4
(Claude's four high non-matching findings), cond-5 (attribution) — real
defects were located but labeled outside the oracle alias vocabulary, and
Grok emitted a zero-finding progress narration. 16 of 30 calls spent; **14
remain**.

## In flight

Nothing running. Next work is deterministic: G6.R4 (synthesis attribution
steering), then the owner scopes G6.R5 and any further cycle.

## Next steps

1. Implement G6.R4 without live calls: synthesis instructions + task-builder
   wording + schema `description` fields state the `invocation_id:finding_id`
   pair convention for every `sources` list (bare ids only in
   `asserted_by`/`not_asserted_by`); regressions; two-mode block.
2. Put the G6.R5 scope to the owner: (a) Assistant-definition taxonomy /
   severity / final-output discipline (changes the pinned package hash
   `fb9e98a3…` — re-pin in ci.yml and records); (b) true-synonym-only oracle
   aliases (an acceptance-bar change — owner approval required); (c) task or
   definition steering against premature structured output (the Grok
   narration). Never widen the oracle with generic labels.
3. Only after R4 (and any approved R5 work) passes the credential-free block
   and review: repeat the no-call gate and ask the owner for a NEW explicit
   decision on a further cycle (ADR 0020 allows a second confirmed rerun;
   ≤8 calls fits the 14 remaining). Never auto-rerun.
4. Push decision still held (owner chose "hold" at 15:39Z): `main` is ahead
   of origin by 4 commits after the failure-record commit.

## Blockers

G6.R5 scope and any further live cycle are owner decisions. §18 note: one
more live failure for the same semantic reason mandates a return to review.

## Key files

- `src/agentteam/synthesis/` (INSTRUCTIONS_FILE) and
  `src/agentteam/run/synthesis.py:38-52` (`build_synthesis_task`) — G6.R4.
- `src/agentteam/domain/review.py` — `sources` field descriptions (travel
  inside the delivered schema; canonical files regenerate).
- `fixtures/review-target.oracle.json` — alias lists (owner-gated).
- `~/.agentteam/runs/run-20260824-154050-7a98` — raw archive (local only);
  sanitized copy scanned clean in the session scratchpad.
- `.project-steward/VERIFY.md` — "G6 second live cycle" evidence table.

## Tried and rejected

- Accepting bare leg ids in agreement sources: rejected — cond-5's
  attribution guarantee needs finding-level pairs; the validator stays
  fail-hard and the steering gets fixed instead.
- Treating the semantic failures as R1-class schema work: rejected — plan
  §14 routes semantic misses to definition/prompt work, and the evidence
  (right files/lines, wrong labels) is steering, not dialect.

## Warnings

- **14 of the 30-call ceiling remain**; a further cycle (≤8) fits once, with
  ≥6 spare. ADR 0033: the ceiling binds before any allowance.
- Raw evidence for both cycles stays only under `~/.agentteam/runs/`
  (owner-only, gitignored); nothing promoted; promotion is G8.
- Four commits unpushed after the failure record; every push needs its own
  explicit owner approval (owner chose to hold at 15:39Z).
- The codex TUI process from the earlier unclosed session may still be alive
  on pts/0 (pid 698697); do not type into it.
- Vendor version drift at any future doctor gate forces a stop (re-probes
  cost calls and need separate approval).
