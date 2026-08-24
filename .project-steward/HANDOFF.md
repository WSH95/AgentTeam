---
updated_at: 2026-08-24T17:13:59Z
updated_by: cli
session_status: closed
branch: main
last_commit: 58775a9
---
# Handoff

## Now

**M1a G6 is CLOSED: the Ubuntu subscription-backed live PoC passed BOTH
acceptance tiers**, and the closure push is hosted-CI green 9/9 (run
32755012269 at `58775a9`). The passing cycle (`run-20260824-170359-58d9`,
fifth of the session) ran under the ADR 0036 amended gate — Claude + Codex
legs + Claude synthesis, three calls, all valid on attempt 1, zero retries;
the synthesis attributed six merged findings with valid
`invocation_id:finding_id` pairs. **25 of the 30-call ceiling are spent; 5
remain — every further live call is an individual owner ceiling decision.**
The session closed G6 through five owner-gated cycles: G6.R1–R3
(schema-delivery projection, Grok error persistence, recursive owner-only
archive — commit `9b8d116`), G6.R4 (synthesis pair-source steering,
`355ff57`), G6.R5 (category/severity/final-output discipline + true-synonym
oracle aliases, hash re-pinned `fb9e98a3…`→`fd54eae7…`, ADR 0034,
`cd92bd7`), G6.R6 (`--max-turns 40`, falsified live, ADR 0035, `1ef11d3`),
and the ADR 0036 gate amendment (`7e49c28`) after Grok's four-cycle
FAIL-HARD (headless turn-cap, `cancelled` at `num_turns: 2`, cause
unreachable from the recipe at grok 1.0.5).

## In flight

Nothing. Everything through `58775a9` is committed AND pushed; only the
wrap commit containing this handoff is local (unpushed, per push policy).
`git status` is clean apart from the wrap-commit contents.

## Next steps

1. **G7 — final CI matrices** (separate owner approval to start): per plan
   §16 — the credential-free core OS×Python matrix and optional ClawTeam
   matrix are already green at `58775a9`; G7 adds the vendor-smoke job and
   repeats the history secret scan.
2. **G8 — close M1a**: owner reviews the clean sanitized bundle from the
   passing run (this session's copy lives in the session scratchpad; it can
   be regenerated any time from the local archive with
   `sanitize_run_archive`), then commit it under
   `docs/evidence/m1a-live-2026-08-24/`; the G8 record must state the
   ADR 0036 amendment and Grok's FAIL-HARD explicitly; draft M1b naming the
   local deterministic provider first and the ClawTeam exit criterion.
3. Push the wrap commit on its own approval.
4. Optional later: revisit the all-three gate when a new Grok CLI version
   ships (fresh probes + owner decision; RISKS R27/R33); follow-ups noted
   in reviews — exec-bit flattening (R34), sweep-helper extraction,
   chmod-failure reporting.

## Blockers

None. G7 and G8 each need their own owner approval to start; any live call
needs an individual ceiling decision (5 remain).

## Key files

- `.project-steward/VERIFY.md` — the complete five-cycle G6 evidence trail
  (newest first) incl. hosted-CI 9/9 at `58775a9`.
- `.project-steward/DECISIONS.md` — ADRs 0034 (steering scope + oracle
  aliases), 0035 (§18 ruling + turn budget), 0036 (amended gate).
- `~/.agentteam/runs/run-20260824-170359-58d9` — the passing raw archive
  (owner-only, gitignored; the G8 bundle source). Earlier failed cycles:
  `…142351-dfc0`, `…154050-7a98`, `…161600-9d69`, `…165045-d353`.
- `examples/run-requests/live-review.yaml` — the amended two-leg request
  (pinned by `test_live_request_runs_the_amended_leg_set`).
- `docs/plans/m1a-direct-harness-poc.md` §22 — "Amendments during G6
  execution" table (ADRs 0034–0036, spend reconciliation).

## Tried and rejected

- Grok text-channel fallback for the null field: rejected — the cancelled
  agent loop produces no review in any channel; fail-hard held correctly.
- `--max-turns` as the Grok fix: implemented, then falsified in-argv
  (identical `cancelled`@2); kept in the recipe as a safety ceiling.
- Weakening the attribution validator or widening the oracle with generic
  labels: rejected — steering was fixed at the sources instead, and cycle 5
  proved it live.

## Warnings

- **5 of 30 live calls remain.** The ADR 0020 allowances are exhausted;
  ADR 0033 discipline applies to every future call.
- Test counts are mode-dependent and moved this session: core 448+4 skips /
  extra 460+3 + compat 12. The pinned example-package hash is now
  `fd54eae7dbaa…` (test_hash_identity.py + ci.yml).
- Capability evidence remains version-bound (Claude 2.1.241 / Codex 0.149.1
  / Grok 1.0.5); any CLI drift forces doctor/probe reassessment first.
- Raw run archives stay local-only under `~/.agentteam/runs/`; never track,
  export, or upload them; promotion is the reviewed G8 bundle only.
- A codex TUI process from the pre-session crash may still be alive on
  pts/0 (pid 698697); do not type into it before closing it.
