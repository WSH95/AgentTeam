---
updated_at: 2026-08-24T14:29:13Z
updated_by: codex
session_status: active
branch: main
last_commit: 83e1f95
---
# Handoff

## Now

**G6 remains open after its first owner-attended cycle failed mechanically.**
Run `run-20260824-142351-dfc0` used exactly three calls with no retry or
synthesis: Codex returned a valid all-three-defect review, Claude rejected the
canonical Draft 2020-12 schema reference before structured output, and Grok
returned no structured field. The archive manifest and sanitizer pass, package
and target stayed unchanged, no evidence was promoted, and 18 of 30 calls
remain. G6.R1–R3 now gate any separately confirmed rerun.

## In flight

Nothing. No process or vendor invocation is running and no rerun is authorized.
Only `.project-steward/{HANDOFF,PLAN,PROGRESS,RISKS,VERIFY}.md` are dirty with
the auto-checkpoint plus this failure record; product, Assistant, request, and
fixture files are unchanged. The local environment remains in core mode.

## Next steps

1. Implement PLAN G6.R1–R3 without live calls: vendor-schema dialect
   projection, deterministic Grok full-schema failure coverage, and recursive
   POSIX archive modes. Preserve canonical checked-in schemas and the verified
   Grok field-only fail-hard policy.
2. Run focused regressions and the full credential-free two-mode block; review
   the changes before considering another live cycle.
3. Only after that review, repeat doctor/hashes/policy checks and obtain a new
   owner confirmation for one rerun (at most eight calls; 18 remain). Never
   auto-rerun or fall back to API mode.
4. Preserve the raw archive locally; if a later cycle passes both acceptance
   tiers, manually review sanitizer output before G6 closure/G8 promotion.

## Blockers

G6.R1: Claude rejects the canonical schema's Draft 2020-12 meta-reference.
G6.R2: Grok's full review schema produced no structured field despite the
smaller G5 probe passing. G6.R3: the protected 0700 archive root contains
event/workspace/scratch descendants with broader mode bits. All three must be
resolved and tested before any rerun decision.

## Key files

- `src/agentteam/schema/__init__.py` and the three adapters — canonical schema
  generation versus vendor-facing projection (G6.R1/R2).
- `src/agentteam/run/{archive,events,workspace}.py` — recursive owner-only live
  archive modes (G6.R3).
- `tests/unit/test_{render_claude,render_grok,run_archive}.py` and
  `tests/acceptance/test_direct_poc.py` — focused regression surfaces.
- `.project-steward/VERIFY.md` — exact sanitized G6 failure evidence.

## Tried and rejected

- A hard-coded `test-version` in the shared render-context builder made 22
  fake-profile tests correctly fail the new currency guard. The builder now
  derives one consistent current verified version from the supplied profile
  and fails closed on inconsistent versions.
- Sandboxed `uv build`/acceptance initially could not create uv cache lock
  files outside the workspace. Approved cache access (or a task-local
  `UV_CACHE_DIR` for the second acceptance run) completed the same commands.
- CI run 32734735405 proved the mocked stuck-pipe test itself was POSIX-only:
  Windows has no `os.killpg`. Testing the platform-independent drain helper
  directly retains the bounded 10s/5s assertions; the separate real POSIX
  descendant test retains group TERM/KILL coverage. Corrective run
  32735583747 passed all nine jobs.
- Do not treat Grok's exit 0 as a successful leg: its verified structured field
  was null and the parser correctly failed. Do not silently enable the
  unverified text fallback or spend a capability probe/live retry while
  diagnosing G6.R2.

## Warnings

- The initial G6 cycle spent three calls; 18 of the hard ceiling remain. No
  retry/synthesis/API fallback/push occurred. Native CLIs used their dedicated
  homes, but AgentTeam did not parse/copy credential files or record values.
- Raw run evidence remains only under the owner state directory; the temporary
  sanitized copy passed its scanner and was not promoted. Do not add either.
- The archive root is 0700 and therefore protects its descendants, but the
  explicit recursive 0700/0600 contract still failed and must be repaired.
- `select_verified(..., cli_version=None)` is render-only behavior;
  `execute_run` rejects non-live plans and missing observed versions before
  archive creation.
- Ignored fake homes under `examples/profiles/.agentteam-local/` may remain
  from deterministic acceptance; they are disposable test state, not owner
  vendor homes.
