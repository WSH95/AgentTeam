---
updated_at: 2026-08-24T23:22:49Z
updated_by: claude
session_status: active
branch: main
last_commit: e066937
---
# Handoff

## Now

**The M1b plan is at draft r4 — three review rounds survived, all
findings resolved, NOT approved.** Full chain: r1 (`14dc218`) → review 1
(7 blocking + 3 hygiene; `docs/reviews/…-at-14dc218.md`) → r2
(`54728c8`; ADR 0039 — HB-03 deferred) → review 2 (6 blocking + 3
medium; `…-at-54728c8.md`) → r3 (`6d3f329`; ADR 0040 — MemberResultV1;
stable ClawTeam root) → review 3 (4 blockers + 3 medium;
`…-at-6d3f329.md`, `e066937`; the reviewed text's SHA-256 cited by the
reviewer and re-verified) → **r4 resolves all seven** (the commit
carrying this handoff; §21 r3→r4 table; ADR 0041). Every finding in all
three rounds was re-verified against the tree before resolution. r4's
substance: the member-result output pipeline pinned end to end
(`RenderContext.output_contract` → schema delivery → the adapter's
`StructuredExtractor` + `MemberResultV1.model_validate` →
`RunArchive.write_member_result()` at `legs/inv-<member>/member-result.json`
with an artifact reference; **`HarnessAdapter.parse()` untouched**);
team-mode target semantics (a member may mutate its own isolated
workspace; declared-deliverable-only propagation with a seven-case
negative test set; direct-mode immutability unchanged);
nullable-until-launch execution bindings with lifecycle validators (7a
stub renders create no invocation records); the committed
`CLAWTEAM_DISPOSITION` gating both the CLI and the success-oriented test
suite under `failed-routed` (dated, VERIFY-cited skip + strict-xfail
reproduction; CI green either way); accurate ClawTeam cleanup semantics
(upstream retains `snapshots/<space>` — qualification-verified) with
adapter-owned deletion after a verified copy-out; the fault-abort scope
pinned to lifecycle steps 6–9 with finalization ops exempt and a
`tasks()`-raise row (twelve provider rows); and the containment
allowlist frozen to four enumerated locations, scanned
case-insensitively.

## In flight

Nothing after the r4 commit. Zero live calls spent; tree green
(453 passed + 4 skipped under a plain terminal).

## Next steps (a NEW approval scope — nothing starts automatically)

1. **Owner G0 decision on r4** — approve (DECISIONS entry naming
   `docs/plans/m1b-team-foundation.md` + r4's commit SHA; status flips
   in the following commit), or another confirmation pass in a fresh
   session against r4's frozen SHA (plan §20 is the charter; §21 the
   three-round resolution history).
2. Only after G0: implementation per plan §3 gates G1–G7 and §16 commit
   boundaries.
3. At G0 the approval ADR also carries the glossary CoordinationSubstrate
   `stop` amendment (plan §20 follow-up).
4. Pushes: `main` is now 7 ahead of origin (`14dc218`, `9802775`,
   `54728c8`, `e89a75f`, `6d3f329`, `e066937`, the r4 commit); **nothing
   pushed** — every push needs explicit owner approval
   (`never_push = true`).

## Blockers

None mechanical. Implementation is blocked by design on G0. Open owner
items: G0; the §20 finalize-at-approval list; the HB-03 semantic
question (open in QUESTIONS.md).

## Key files

- `docs/plans/m1b-team-foundation.md` — **r4, the approval target.**
- `docs/reviews/2026-08-24-m1b-plan-review-at-{14dc218,54728c8,6d3f329}.md`
  — the three immutable review records.
- `.project-steward/DECISIONS.md` ADRs 0039–0041 — the review/resolution
  trail and the owner decisions.
- `docs/plans/m1a-direct-harness-poc.md`,
  `docs/evidence/clawteam-qualification-2026-08-23.md`,
  `src/agentteam/compat/clawteam.py` — house style, the 233/281 baseline
  + caveats, and the seam (its `create_space` gains `leader` at G5).

## Tried and rejected (session highlights for a successor)

- Every review finding in all three rounds was verified against the tree
  BEFORE resolution (anchors in ADRs 0039–0041 and PROGRESS).
- Rejected: changing `HarnessAdapter.parse()` for member results — the
  team runner validates via the existing `StructuredExtractor` instead
  (round-3 reviewer's shape; strictly more additive).
- Rejected: extending direct-mode target immutability to team mode — a
  member producing a deliverable must mutate its own workspace copy;
  propagation is declared-files-only.
- Rejected: unconditional collection of the success-oriented ClawTeam
  suite — disposition-gated, dated, VERIFY-cited; never silent.

## Warnings

- **5 of 30 live calls remain from M1a; M1b's budget is ZERO live
  calls.** `member-result-v1`'s live vendor acceptance is explicitly M1c
  evidence.
- r4 is NOT approved: no product code, no schema files, no register or
  glossary amendments until G0.
- Local pytest on this host needs a plain terminal:
  `env -u PYTHONPATH NO_COLOR=1 TERM=dumb uv run pytest` (rich ANSI +
  a ROS-Foxy PYTHONPATH leak; neither is a tree problem).
- An untracked `.codex/` directory exists at the repo root (not created
  by this session; left untouched; owner to decide whether to gitignore).
- Capability evidence stays version-bound (Claude 2.1.241 /
  Codex 0.149.1 / Grok 1.0.5); Grok re-entry needs fresh probes + an
  owner decision (ADR 0036).
