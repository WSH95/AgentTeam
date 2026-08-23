---
updated_at: 2026-08-23T22:39:52Z
updated_by: cli
session_status: closed
branch: main
last_commit: f5e7cbb
---
# Handoff

## Now

**M1a G3 local work is COMPLETE; stopped at the push gate (2026-08-23).** G2 closed earlier the same day. The approved plan is
`docs/plans/m1a-direct-harness-poc.md` r3 (DECISIONS 0021). G2 ran under an
owner-approved per-gate execution plan (the owner's standing working
agreement: every coding gate gets its own reviewed plan first).

Public repository: **https://github.com/WSH95/AgentTeam** (PUBLIC, MIT,
default `main`) — created and first pushed (`8660e6a`, secret-scanned, 0 hits)
on the owner's explicit approval; two CI fixes (`671c2d9` setup-uv pin,
`d9440f8` explicit matrix-Python install) each pushed on their own approval
(DECISIONS 0024). **Scaffold smoke matrix: all six legs green** at `d9440f8`
— ubuntu/windows/macos x Python 3.11/3.13, run
https://github.com/WSH95/AgentTeam/actions/runs/32667607711 (VERIFY "G2
evidence").

What exists in code: `pyproject.toml` (agentteam 0.1.0a0, Hatchling >=1.27,
Typer/Pydantic v2/PyYAML, optional `clawteam` extra @0119833 + `mcp>=1,<2`),
frozen `uv.lock`, `src/agentteam/` (`cli.py` with `--help`/`--version` only;
`domain/` = nine closed V1 records per plan §7 incl. the review-contract
fixes from the G2 plan; `schema/` exporter/check; `py.typed`), nine checked-in
JSON Schemas + `schemas/README.md` (model-only invariants), 91 unit tests
(red-first), CI workflow, `docs/provenance.md`. AGENTS.md command table is
live (ADR 0023).

## In flight

**Waiting on the owner's push approval for G3** (commits `4d6e082`
feat(harness) and `f5e7cbb` feat(cli) + the steward close commit). After the
push: watch the six CI legs — the Windows legs run the `.cmd` shim suite for
the first time (needs `node` on the runner, preinstalled on windows-latest).
On green: VERIFY "G3 evidence", PLAN tick, HANDOFF for G4, wrap.

## Next steps

1. **G3 needs its own per-gate execution plan first** (owner working
   agreement; use plan mode, review the draft, get approval). Scope per plan
   §3/§9/§11: `HarnessAdapter` protocol + Claude/Codex/Grok adapters
   (render/invoke/parse against deterministic fakes), the shared shell-free
   process runner (asyncio, process-group termination, 15-min cap, single
   transient retry), launcher policy incl. the Windows-only `.cmd` fake with
   metacharacters, Skill-channel rendering per harness, selection algorithm
   with `decided_by` + hard failure for forbidden/ineligible requests, exit
   codes 0/1/2/3/130, `claude` alias, `atm assistant validate` + `atm
   profile init/validate/doctor` (no probes until G5), YAML loaders
   (aware-datetime rule), archive hash V1 implementation; adapter tests into
   CI (commit 6 of §17; workflow grows).
2. Optional later: AGENTS.md `Live PoC` row at G4 (own shown diff); HB-03
   register amendment whenever the owner answers the QUESTIONS item.

## Blockers

- None for planning G3. Live-call work stays behind G5/G6 gates (probes <= 2
  per harness; ceiling 30 calls; owner-attended).

## Key files

- `src/agentteam/` + `schemas/` + `tests/` — the G2 code (see VERIFY for the
  exact verification block; run everything as `env -u PYTHONPATH uv run ...`).
- `.github/workflows/ci.yml` — scaffold matrix; grows at G3/G4/G7.
- `.project-steward/VERIFY.md` — "G2 evidence" + "G2 local verification".
- `.project-steward/DECISIONS.md` — 0023 (AGENTS table), 0024 (repo + push).
- `docs/plans/m1a-direct-harness-poc.md` — §9/§11/§12/§15 are the G3 spec.
- The archived G2 execution plan:
  `~/.claude/plans/continue-i-want-to-toasty-ladybug.md` (session-local).

## Tried and rejected

- Never push without an explicit owner approval; never force-push.
- Do not remove the `*.md` ruff exclusion; never run a formatter over docs.
- No `--all-extras` (clones ClawTeam); the extra is G4-only.
- No `--safe-mode` in anything Claude; no credential parsing; no API-mode
  fallback; no model calls in tests/CI.
- `uv python find` without a version argument is a trap (resolves
  `.python-version`, never auto-installs) — keep the explicit install+find.

## Warnings

- This host exports `PYTHONPATH=/opt/ros/foxy/...` — always
  `env -u PYTHONPATH uv run ...` locally.
- The repository is public: dated docs carry `/home/wsh/...` paths, commit
  trailers carry session URLs (accepted, ADR 0019/0024 context).
- Vendor-facing schema envelope is G5-probe-tested; the fallback (stripped
  vendor copy, envelope stamped on parse) is planned but NOT pre-implemented.
- Grok auth stays `unverified` until its first live leg; ClawTeam
  qualification is G4 and must never contaminate the direct core.
