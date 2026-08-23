---
updated_at: 2026-08-23T15:30:12Z
updated_by: cli
session_status: closed
branch: main
last_commit: edc14ff
---
# Handoff

## Now

**M1a G1 is done (2026-08-23).** The approved plan is
`docs/plans/m1a-direct-harness-poc.md` revision r3 (approval artefact
DECISIONS 0021; approved text `0f3e478`). G1 landed as the two commits the plan
prescribes (§17 items 1–2):

1. `edc14ff` — `chore(project): rename project to AgentTeam`: the owner moved
   the repository (never copied) to `/home/wsh/Documents/AgentTeam` between
   sessions (same history, clean tree, old path gone, no `atm` on `PATH`);
   this session added root `README.md` (alpha status), `LICENSE` (MIT,
   `Copyright (c) 2026 ShuhanWang`), `.gitattributes` (`* text=auto eol=lf`;
   all 56 tracked files were already LF, no renormalisation), the
   implementation `.gitignore` (outside the steward-managed block), and identity
   amendments on living documents only (discovery landing page, `product-intent.md`
   frontmatter, one `legacy-atm-disposition.md` note). Dated M0 records keep
   their `ats`/"Assistant Team System" wording by design.
2. The commit that carries this handoff — `docs(steward): documentation
   hygiene for the AgentTeam baseline` (plan §4 item 6; review H3, H6, H8–H12,
   R7, R19): PROJECT.md success criteria, volatile pins/scope decision moved
   out; glossary terms HarnessAdapter / CoordinationSubstrate / Run–direct run /
   `atm` / legacy ATM / `independence {declared, achieved}`; DECISIONS 0022
   (append-only amendment markers for 0007/0009/0012); VERIFY M0.1 counts
   corrected + PROGRESS re-sorted; RISKS `ID/Owner/Status` columns (R01–R33);
   closure notes on all 10 critic files + provenance note on the fix-pass file;
   `minimal-poc-plan.md` banner confirmed and its pre-r3 Claude bullet amended;
   READMEs link QUESTIONS; `config.toml` pointer. `last_commit` above is the
   pre-change baseline because a commit cannot name its own SHA.

**Deliberately not done in G1:** the HB-03 register amendment (review R7) —
the plan allows it only after the owner answers the open QUESTIONS item; the
`AGENTS.md` managed command table — waits for the G2 scaffold and needs its own
shown diff and explicit approval (ADR 0008/0014); any propagation of the r3
Claude recipe (no `--safe-mode`) into the living discovery documents beyond the
landing-page supersession note and the MPP amendment — the approved plan §11
is authoritative; a wider pass is optional hygiene, not a gate.

Architecture and policy are unchanged: Python `>=3.11` with `uv` and
Hatchling; checked-in JSON Schema records; the `atm` CLI (later MCP) as the
language-neutral edge; built-in shell-free direct runner; ClawTeam optional,
exact-pinned, confined to one compatibility module; native subscription auth
only; hosted CI credential-free; never push without explicit approval.
G1 verification: VERIFY.md top section (links 53/30/0, fences 60/53/0, secret
scan 0, diff-check PASS, toolchain versions re-verified read-only).

## In flight

Nothing. The tree is clean after the hygiene commit. No source scaffold,
dependency install, credential operation, model invocation, CI workflow, remote
creation, or push has occurred in M1a so far.

## Next steps

1. **G2 — Python foundation (local, no approval needed for the scaffold
   itself):** `pyproject.toml` (distribution/import package `agentteam`,
   version `0.1.0a0`, `requires-python = ">=3.11"`, Hatchling, console script
   `atm = "agentteam.cli:main"`, runtime deps Typer + Pydantic v2 + PyYAML only,
   optional `clawteam` extra pinned to `01198332ef9270c32c5460b8a178f964fc0df451`
   with `mcp>=1,<2`, dev group pytest/pytest-asyncio/jsonschema/Ruff/mypy +
   stubs), committed `uv.lock`, `src/agentteam/` layout per plan §6, the V1
   JSON Schemas checked in and reproduced deterministically from Pydantic
   models (LF), `atm --help` / `atm --version` passing, scaffold tests. Commit
   boundaries: `chore(core): scaffold Python CLI package with uv`, then
   `feat(domain): add portable definition, run-record, review/synthesis, and
   run schemas` (plan §17). Use `uv 0.11.26` (installed); uv-managed CPython
   3.11.16/3.13.14 exist; system `python3` is 3.8 — never use it.
2. **G2 — pre-first-push checklist (plan §16):** history secret scan over all
   commits; LICENSE + third-party notices; `docs/provenance.md` (legacy ATM
   provenance, ADR 0011 item 6); repository/distribution-name checks
   (`WSH95/AgentTeam`, PyPI name `agentteam`, local `atm` command — only the
   last is checked so far: free).
3. **G2 — repository and first push: STOP and ask.** Create the public
   `WSH95/AgentTeam` (MIT) and push the scaffold **only after the owner's
   explicit approval at that moment** (`gh` is authenticated: account `WSH95`,
   `repo` scope, SSH). Then the scaffold smoke matrix (lock, Ruff, mypy,
   scaffold tests, build, schema reproduction, `--help`/`--version`) must be
   green on Ubuntu/Windows/macOS before G3. After the scaffold exists, propose
   the AGENTS.md managed command-table diff (plan §4) and get explicit
   approval before applying it; record it in DECISIONS.
4. G3–G8 in order per the approved plan; live reruns each separately
   confirmed (ceiling 30 calls); every further push is its own visible gate.
5. Whenever the owner answers the HB-03 QUESTIONS item: apply the register
   (v3.4) or glossary amendment as a small docs-only commit.

## Blockers

- None for the G2 scaffold. The first push and repository creation are an
  explicit approval moment; do not pre-empt it.
- Grok Build 1.0.5 exposes login but no status command; dedicated-profile auth
  is proved by the first controlled live leg at G6, not by documentation.
- The optional ClawTeam extra has not been installed or qualified; that
  evidence belongs to G4 (`uv sync --extra clawteam` in a project venv only).
- API-test timing and target remain intentionally undecided (ADR 0017) and do
  not block M1a.

## Key files

- `README.md` (root, new) — alpha status, orientation, naming convention.
- `LICENSE`, `.gitattributes`, `.gitignore` — G1 root files.
- `docs/plans/m1a-direct-harness-poc.md` — **r3, approved**; §4 G1 (done),
  §5 runtime baseline, §6 layout, §7 contracts, §8 CLI, §16 CI/publication,
  §17 commit boundaries, §18 stop rules.
- `docs/discovery/README.md` — landing page with the naming amendment and the
  Claude-recipe supersession note; `docs/discovery/evidence/glossary.md` —
  amended 2026-08-23 (six new terms).
- `.project-steward/PLAN.md` — G1 ticked; G2–G8 open.
- `.project-steward/DECISIONS.md` — 0022 amendment markers (new); 0021 G0
  approval; 0020 r3 resolutions + budget ceiling; 0019 merge; 0018 review;
  0017 neutrality; 0014–0016 architecture/roadmap.
- `.project-steward/QUESTIONS.md` — current gate G2; HB-03 still open (owner).
- `.project-steward/RISKS.md` — now `ID | … | Owner | Status` (R01–R33).
- `.project-steward/VERIFY.md` — G1 section on top; toolchain baseline lives
  here now, not in PROJECT.md.
- `.project-steward/PROJECT.md` — charter with success criteria (H3 applied).
- `docs/discovery/evidence/critics/*` — closure/provenance notes appended.

## Tried and rejected

- Do not rewrite dated M0 records (panel, critics, evidence, MPP §2–§8, old
  plans) for the rename; amendment notes only (plan §4 item 3).
- Do not apply the HB-03 register amendment before the owner answers.
- Do not edit `AGENTS.md`/`CLAUDE.md` outside a shown, approved diff.
- Do not name a tentative API-test provider, endpoint, model, credential
  variable, or URL; do not use API mode as a native-auth fallback; never ask
  for a key in chat.
- Do not fork/vendor ClawTeam to pass qualification; do not move the core to
  TypeScript for a DSH edge.
- `--safe-mode` must not return to the Claude recipe (it disables Skills,
  plugins, hooks, MCP); `--bare` never reads OAuth.

## Warnings

- Both G1 commits are local only. Nothing has ever been pushed; the remote
  does not exist yet. Never push without explicit approval.
- Historical evidence files cite scratchpad paths under the old directory name
  (`/tmp/claude-1000/-home-wsh-Documents-assistant-team-system-dev/...`) —
  dated records, not live paths.
- Living discovery documents (architecture-options, ADM, TEM, HBM, fit-gap,
  reuse) still describe Claude isolation as `--safe-mode --no-session-persistence`
  in several places; the landing page and MPP carry supersession notes and the
  approved plan §11 wins. Treat any such sentence as dated.
- PROGRESS.md early timestamps (through 2026-08-22) are approximate
  session-written stamps; git history is authoritative for event order.
- Earlier candidate-context wording remains in Git history (no credential
  value); rewriting history would be a separate destructive action.
- Full live evidence will be sensitive local state: gitignored, owner-only,
  never automatically committed or uploaded.
- r3 names future paths (`schemas/…`, `examples/…`, `fixtures/…`,
  `docs/evidence/…`, `docs/provenance.md`) that G2+ create; they are
  deliverables, not links.
