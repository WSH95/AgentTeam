---
updated_at: 2026-08-23T21:17:14Z
updated_by: cli
session_status: active
branch: main
last_commit: be5ce15
---
# Handoff

## Now

**M1a G2 local work is DONE; the session is stopped at the push gate.** The
approved plan is `docs/plans/m1a-direct-harness-poc.md` r3 (DECISIONS 0021);
G2 ran under the owner-approved 2026-08-23 G2 execution plan (drafted, twice
independently reviewed, critiqued, approved in-session; archived at
`~/.claude/plans/continue-i-want-to-toasty-ladybug.md`).

Commits (all local; nothing ever pushed; no remote exists):
- `edc14ff` / `0add982` — G1 (rename; documentation hygiene).
- `cc0cc5f` — `chore(core): scaffold Python CLI package with uv`.
- `be5ce15` — `feat(domain): add portable definition, run-record,
  review/synthesis, and run schemas` (+ AGENTS.md command table, ADR 0023).
- The commit carrying this handoff — `docs(steward): record G2 local
  verification and pre-first-push checklist`.

State: 91 tests, ruff/format/mypy strict clean on 3.11 and a fresh 3.13 env;
schemas reproduce; wheel/sdist contents verified; commit 3 verified standalone
in a scratch worktree. Full results: VERIFY "G2 local verification".

## In flight

**Waiting on exactly one thing: the owner's explicit yes/no to create the
public `WSH95/AgentTeam` repository (MIT) and push `main`.** The question was
asked at the end of this session with the secret-scan result and the scanned
HEAD SHA. If the answer is not on record, NOTHING may be pushed — ask again.

## Next steps

1. **On the owner's explicit approval only** (B8 of the G2 execution plan):
   re-run the name checks (`gh api repos/WSH95/AgentTeam` → 404; PyPI
   `agentteam` → 404), confirm `git status --short` empty and HEAD equals the
   scanned SHA, then:
   `gh repo create WSH95/AgentTeam --public --source . --remote origin
   --description "Portable, harness-independent Assistant definitions and
   Team templates over existing coding-agent harnesses (alpha)"
   --disable-wiki`; `git remote -v`; `git push -u origin main`. If creation
   succeeds but the push fails: stop and ask; never retry with force.
2. Watch CI: `gh run list --workflow ci --branch main -L1 --json databaseId`
   → `gh run watch <id> --exit-status`. Six legs (ubuntu/windows/macos x
   3.11/3.13). On a failure: fix locally test-first, commit, and ask again
   before every further push.
3. All legs green → VERIFY "G2 evidence" (run URL, per-leg results,
   `gh repo view WSH95/AgentTeam --json visibility,licenseInfo`), tick the two
   open G2 boxes in PLAN, DECISIONS entry for the repository creation (date,
   URL, approval quote), HANDOFF for G3, `project-steward wrap`, final local
   commit (ask before pushing it).
4. **G3** (needs its own per-gate execution plan first — owner working
   agreement): isolated Claude/Codex/Grok adapters (render/invoke/parse,
   Skill channels, `decided_by`, launcher policy incl. the Windows `.cmd`
   fake), process runner, exit codes, `claude` alias; adapter tests into CI.

## Blockers

- The push gate (above). Nothing else blocks G2 completion except CI results.
- Grok auth verification stays a G5/G6 matter; ClawTeam qualification is G4.

## Key files

- `pyproject.toml`, `uv.lock`, `.python-version`, `.github/workflows/ci.yml`.
- `src/agentteam/` — `cli.py` (atm skeleton), `domain/` (nine V1 records),
  `schema/` (`python -m agentteam.schema export|check`), `py.typed`.
- `schemas/` — nine checked-in V1 JSON Schemas + README (model-only
  invariants).
- `tests/` — `conftest.py` (minimal payloads), `unit/` (91 tests).
- `docs/provenance.md` — provenance/notices (pre-first-push artefact).
- `.project-steward/VERIFY.md` — G2 local verification; DECISIONS 0023 —
  AGENTS.md table approval; PLAN — G2 sub-bullets.

## Tried and rejected

- Do not push or create the repository without the explicit approval quoted in
  the session; every later push is again its own gate.
- Do not run bare `ruff format` outside `src`/`tests` semantics: `*.md` is
  excluded via pyproject on purpose — never remove that exclusion to "format"
  docs.
- Do not use `--all-extras` in CI or locally by default (it clones ClawTeam);
  the extra is installed only for G4 qualification work.
- Do not add `--safe-mode` to anything Claude (plan §11); do not parse
  credential files; no API-mode fallback; no model calls in tests/CI.
- Envelope (`schema_version`/`kind`) stays required on every record including
  human-authored files; do not default it away.

## Warnings

- This host's shell exports
  `PYTHONPATH=/opt/ros/foxy/lib/python3.8/site-packages`; ALWAYS run
  `env -u PYTHONPATH uv run …` locally (CI unaffected).
- `.python-version` (3.11) steers local uv; CI must keep `UV_PYTHON` from the
  matrix (already in the workflow) or 3.13 legs silently run 3.11.
- The `clawteam` extra is a direct git reference: the distribution is not
  PyPI-uploadable as is (fine — M1a publishes nothing).
- Public-visibility facts accepted with ADR 0019 are listed in VERIFY (author
  e-mail, session trailers, `/home/wsh/...` paths in dated docs, tracked
  steward state files).
- Vendor-facing schema envelope (`schema_version`/`kind` as single-value
  enums) is probe-tested at G5; the planned fallback is a stripped vendor
  copy stamped on parse — do not pre-implement it.
