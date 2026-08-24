---
updated_at: 2026-08-24T15:35:17Z
updated_by: claude
session_status: active
branch: main
last_commit: ddd9edb
---
# Handoff

## Now

**G6 remains open; G6.R1–R3 are closed, reviewed, and committed** (the commit
carrying this handoff: `fix(schema,run): close G6.R1-R3 live-rerun blockers`).
Delivery-time vendor projection (strip `$schema`/`$id`/`title`, canonical
schemas byte-identical, Codex on the same projected document), Grok
`structuredOutputError` persistence with fixture/fake/runner coverage, and the
recursive owner-only archive (events opener, write-time tightening,
`secure_tree()` at both finalize paths) are all green in both modes: core
441+4 skips, extra 453+3, compatibility 12, plus the full CI-mirror block.
The high-effort diff review returned 10 findings, none refuted: 4 fixed, 6
dispositioned (exec-bit flattening → RISKS R34; the rest accepted residuals).
Docs verification (2026-08-24, cited in VERIFY) documents the root cause:
Claude Code validates `--json-schema` against draft-07, so the 2020-12
`$schema` declaration was rejected; every delivered keyword is
documented-supported at all three vendors.

## In flight

Nothing. No process or vendor invocation is running; no rerun is authorized.
18 of the 30-call ceiling remain; `main` is ahead of origin by 3 unpushed
commits after this one (`83e1f95`, `ddd9edb`, this commit).

## Next steps

1. Offer the owner a push of the three pending commits for a hosted 9-job CI
   check before the rerun (owner decision; not required by the recorded
   protocol; every push needs its own explicit approval).
2. Repeat the no-call gate: `uv run atm profile doctor` must report Claude
   2.1.241 / Codex 0.149.1 / Grok 1.0.5 ready/current with zero conflicts or
   staleness (any drift ⇒ stop; a re-probe costs calls and needs separate
   approval); package `fb9e98a3…` and target `25f03027…` hashes unchanged;
   refresh the official Claude subscription/CLI policy check (RISKS R23);
   confirm the normal proxy names are inherited (ADR 0027 — run from the
   normal terminal, never `env -u`, no `ANTHROPIC_API_KEY`-class variables).
3. Obtain a fresh, explicit owner confirmation for at most ONE attended rerun:
   `uv run atm run examples/run-requests/live-review.yaml` (≤8 calls; the
   command has **no built-in confirmation prompt** — it spends three calls the
   moment it starts; never `--render-only`, never `--config …ci-fake.yaml`,
   never `--no-synthesis`). Never auto-rerun; never fall back to API mode; a
   second rerun is an explicit owner ceiling decision (ADR 0033).
4. On a rerun: exit 0 → verify manifest + recursive modes on the real archive,
   run the sanitizer to a temp dir, review its output manually, update the
   ledger and close G6 (promotion of the evidence bundle stays G8). Exit 3 →
   semantic routing per plan §14. Exit 1/2 → record with first-cycle rigor and
   stop. Then wrap; G7 is a separate approval.

## Blockers

Only the owner gates: the optional pre-rerun push decision and the mandatory
fresh rerun confirmation after the no-call gate.

## Key files

- `src/agentteam/schema/__init__.py` — `vendor_projection`/`vendor_schema`/
  `vendor_schema_min`/`vendor_schema_text`, shared `_SCHEMA_DATA_KEYS`.
- `src/agentteam/run/{archive,events,workspace}.py`,
  `src/agentteam/harness/skills.py` — recursive owner-only modes.
- `tests/unit/test_vendor_projection.py` — projection + construct-set pins.
- `.project-steward/VERIFY.md` — "G6.R rerun-blocker remediation" (evidence,
  review dispositions, docs citations) above the G6 failure table.

## Tried and rejected

- Rewriting `anyOf`-nullable to `type` arrays: rejected — Codex's live PASS
  used the `anyOf` form and all three vendors document `anyOf` support.
- Stripping `description`: rejected — real model steering, live-proven via
  Codex, actively encouraged by xAI docs.
- Sweeping archive modes mid-run: rejected — would race live vendor
  processes; creation-time modes cover the pre-launch window instead.
- Setting a process-wide umask 0o077 for the crash-path window: rejected for
  now — process-global state races in-process test runners; 0700 parents
  already shield descendants (review disposition).

## Warnings

- The initial G6 cycle spent 3 calls; **18 of the 30-call ceiling remain**.
- Raw run evidence stays only under `~/.agentteam/runs/run-20260824-142351-dfc0`
  (owner-only, gitignored); nothing promoted.
- Every push needs its own explicit owner approval.
- A codex TUI process from the previous unclosed session may still be alive
  on pts/0 (pid 698697); do not type into it — this session holds the
  steward runtime claim.
- G6.R3 flattens execute bits on copied workspace/Skill files (RISKS R34) —
  harmless for the current target/Skills (no executables), revisit before any
  target ships scripts.
