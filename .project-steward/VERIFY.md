# Verification

How to check the project is healthy. There is no build, product code, or
automated product test suite yet; the M1a G2 scaffold introduces them (and the
AGENTS.md command table changes only then, with its own shown diff).

## G2 evidence — 2026-08-23 (gate closed)

| Check | Result |
| --- | --- |
| Repository | PASS — https://github.com/WSH95/AgentTeam is PUBLIC with license `mit`, default branch `main` (`gh repo view --json visibility,licenseInfo,defaultBranchRef`); created and first pushed on the owner's explicit approvals (DECISIONS 0024) |
| Pushed history | `main @ d9440f8`; first push was `8660e6a` (the secret-scanned SHA, 0 hits); `671c2d9` and `d9440f8` are CI fixes, each pushed on its own owner approval |
| Scaffold smoke matrix | PASS — run 32667607711 (https://github.com/WSH95/AgentTeam/actions/runs/32667607711) at `d9440f8`: **all six legs green** — ubuntu-latest/windows-latest/macos-latest x Python 3.11/3.13 (lock check, frozen sync, interpreter assert, ruff, ruff format, mypy, pytest 91, uv build, schema check, export round-trip `git diff --exit-code -- schemas`, `atm --help/--version`) |
| CI failure history (evidence, not hidden) | run 32667232109 at `8660e6a`: all legs failed at job setup — `astral-sh/setup-uv` has no floating `v10` tag → pinned to the v10.0.1 commit (`671c2d9`); run 32667352498 at `671c2d9`: macOS+Windows green, Ubuntu legs failed at the argument-less `uv python find` diagnostic (resolves `.python-version` 3.11; never auto-installs; image ships no 3.11/3.13) → explicit `uv python install <matrix>` + versioned `find` (`d9440f8`) |
| Boundaries | PASS — CI ran with `contents: read` only; no credential, vendor login, or model call anywhere; no package published |

G2 of the approved M1a plan is complete. Gate evidence per plan §3: frozen
`uv.lock`; package builds; checked-in schemas reproduce (all six legs);
`atm --help`/`--version` pass; pre-first-push checklist passed; public
repository created with MIT and pushed after explicit approval; scaffold
smoke matrix green on three OSes.

Last verified: 2026-08-23 by Claude (Fable 5) session.

## G2 local verification — 2026-08-23 (pre-push)

Execution followed the owner-approved G2 plan (drafted, independently reviewed
twice, critiqued, then approved 2026-08-23 in-session). Commits: `cc0cc5f`
chore(core) scaffold, `be5ce15` feat(domain) records+schemas; both local only.

| Check | Result |
| --- | --- |
| Local verification block (3.11) | PASS — `uv lock --check`; `uv sync --frozen --all-groups`; `ruff check .`; `ruff format --check .`; `mypy` (strict + pydantic plugin) clean; `pytest` 91 passed; `uv build`; `python -m agentteam.schema check` current; `export` round-trip leaves `git diff -- schemas` empty; `atm --help`/`--version` |
| Fresh 3.13 environment | PASS — same block (pytest 91, mypy, ruff, schema check, `atm --version`) on CPython 3.13.14 in a scratch `UV_PROJECT_ENVIRONMENT` |
| Commit 3 standalone | PASS — scratch `git worktree` at `cc0cc5f`: sync, pytest (6), ruff, mypy, `atm --version` |
| Package contents | PASS — wheel: `agentteam/py.typed` present, no `tests/`; sdist: `/src/agentteam`, `/schemas` (+README), `/README.md`, `/LICENSE`, `/pyproject.toml` only (anchored includes); wheel smoke `uv run --isolated --no-project --with <wheel> atm --version` prints `atm 0.1.0a0` |
| Schema parity | PASS — nine files reproduce byte-for-byte and are LF on disk (`git ls-files --eol`: all new tracked files `i/lf`); Draft 2020-12 metaschema valid; minimal instances of all nine records validate via `jsonschema` and unknown fields fail both sides; no pattern uses look-around; vendor-facing files have `$defs` inlined, enum-not-const, all properties required |
| Contract fixes vs approved plan | PASS — severity `critical..info` + finding `category` (§14); `default_harness` + tier/reasoning mappings (§11); target hashes (§12/§14); `undeliverable_required_parts`, observed harness, `refused` launcher branch (§9/§11); overrides keyed by harness id (§2/§8); archive-contract manifest validator (§7); terminal ⇒ `finished_at`; execution `ref`↔`kind`; AwareDatetime everywhere |
| Deviations recorded | `api-test` spelling; `clawteam` extra with direct git ref (owner choice; not PyPI-uploadable, nothing published); AGENTS.md table: `Live PoC` deferred to G4, `Schemas` row added (ADR 0023); finding `category` extends §7's field list; invocation attempt identity = `invocation_id` + `retry.attempt`; §7 "bundle hash" = `effective_definition_hash` (+ Member `package_hash`); vendor-envelope fallback decided by G5 probes |
| Pre-first-push checklist (§16) | LICENSE (MIT) + `docs/provenance.md` (no ATM code copied; dependency + ClawTeam MIT notices) PASS; name checks 2026-08-23: GitHub `WSH95/AgentTeam` 404, PyPI `agentteam` 404, local `atm` absent — re-run immediately before creation; history secret scan: see the line below |
| History secret scan | recorded at the STOP question: `git log -p --all` at the final local HEAD through the key-shaped regex set + private-key headers; result and scanned SHA quoted in the push approval; pushed HEAD must equal that SHA |
| Public-visibility facts (not secrets) | commit author e-mail; `Claude-Session:` trailers; 43 `/home/wsh/...` paths in dated docs; tracked `.project-steward/{state.json,config.toml,backend.json}`; candidate-context wording in history — accepted with ADR 0019 (public at G2) |

Last verified: 2026-08-23 by Claude (Fable 5) session (no model call, no
credential read, no ClawTeam install, no push).

## G1 rename and documentation-hygiene verification — 2026-08-23

| Check | Result |
| --- | --- |
| Move (plan §4 items 1–2) | PASS — the owner moved the repository between sessions; at session start the working directory was `/home/wsh/Documents/AgentTeam`, `/home/wsh/Documents/assistant-team-system-dev` no longer existed, `main @ 025d02a` matched the handoff, the tree was clean, no merge/rebase was in progress, and `command -v atm` found no executable on `PATH` |
| Root files (plan §4 item 4) | PASS — `README.md` states alpha/pre-implementation status and links the steward files including QUESTIONS; `LICENSE` is MIT with `Copyright (c) 2026 ShuhanWang`; `.gitattributes` is `* text=auto eol=lf`; `git ls-files --eol` showed all 56 tracked files `i/lf w/lf`, so no renormalisation occurred; `.gitignore` adds Python/`uv` build and cache paths plus `.agentteam/` and `.env*` outside the steward-managed block |
| Identity amendments (plan §4 item 3) | PASS — only living documents changed (discovery landing page, `product-intent.md` frontmatter, one `legacy-atm-disposition.md` question note, PROJECT.md); panel, critic, evidence, decision, and progress text was not rewritten — `git grep -w ats` still lists the same historical files; `CLAUDE.md` remains the thin `@AGENTS.md` adapter; `AGENTS.md` untouched |
| Hygiene list (plan §4 item 6; review H3, H6, H8–H12, R7, R19) | PASS except the deferred item — PROJECT.md success criteria + volatile pins/scope decision moved out (H3); glossary defines HarnessAdapter, CoordinationSubstrate, Run/direct run, `atm`, legacy ATM, `independence {declared, achieved}` (H10/R10/R16); DECISIONS 0022 adds append-only amendment markers for 0007/0009/0012 (R19); VERIFY M0.1 counts corrected and PROGRESS re-sorted newest-first (H9); RISKS has ID/Owner/Status columns, 33 rows R01–R33 (H12); 10 critic files carry closure notes and the fix-pass file a provenance note, the three FAIL blockers spot-checked (H8); `minimal-poc-plan.md` banner confirmed and its pre-r3 Claude bullet amended (H6); both READMEs link QUESTIONS and `config.toml` names where its pointer lives (H11). **Deferred by design:** the HB-03 register amendment (R7) waits for the owner's QUESTIONS answer |
| Local toolchain baseline (moved here from PROJECT.md) | PASS — read-only `--version` checks, no model call: Claude Code 2.1.241, Codex 0.149.0, Grok Build 1.0.5, OpenClaw 2026.7.1-2, Hermes 0.20.4, `uv` 0.11.26 with uv-managed CPython 3.11.16 and 3.13.14, system `python3` 3.8.10; Ubuntu host without tmux |
| Local Markdown targets | PASS — 53 tracked Markdown files scanned, 30 local links checked, 0 broken |
| Markdown fences | PASS — 60 fence markers across 53 files, 0 unbalanced |
| Secret-pattern scan | PASS — 0 API-key-shaped values and 0 private-key headers across tracked files |
| Scope | PASS — commit 1 touched root files, living docs, and steward state; commit 2 is docs/steward only (`.md` plus `config.toml`); no source, dependency, CI workflow, repository, AGENTS.md, credential, model call, or push |
| Patch hygiene | PASS — `git diff --check` exits 0 for both commits |

Last verified: 2026-08-23 by Claude (Fable 5) session (documentation-only; no
credential values or model prompts used).

## G0 approval record — 2026-08-23

| Check | Result |
| --- | --- |
| Approval artefact | PASS — DECISIONS 0021 names `docs/plans/m1a-direct-harness-poc.md` r3 and commit `0f3e478`; the status line was flipped in the following commit |
| Steward consistency | PASS — PLAN M1a marked approved; QUESTIONS current gate = G1; HANDOFF carries the exact G1 move commands and the fresh-session instruction |
| Scope | PASS — documentation/steward only; no move, code, dependency, repository, or push |
| Patch hygiene | PASS — `git diff --check` exits 0 |

Last verified: 2026-08-23 by Claude (Fable 5) session.

## Current M1a r3 review-resolution verification — 2026-08-23

| Check | Result |
| --- | --- |
| Documentation-only scope | PASS — `docs/plans/m1a-direct-harness-poc.md` (r3), one sentence in `docs/discovery/team-execution-model.md` §4 (v2.3), Project Steward records; no code, rename, dependency, credential, model call, CI, remote change, or push |
| Review claims verified read-only | PASS — `claude --help` (2.1.241): `--safe-mode` disables skills/plugins/hooks/MCP, `--bare` never reads OAuth; `codex exec --help` (0.149.0): `--ignore-rules` = execpolicy `.rules` only; `grok inspect` (1.0.5) in a scratch dir lists `.grok/skills/` and `.agents/skills/` as project skill roots; scratch dir removed |
| r3 edit coverage | PASS — header/§1/§2/§3/§6.1/§7/§9/§11/§12/§14/§15/§16/§17/§18/§19/§21/§22 updated; gate names unchanged; status still *proposed* |
| Decision consistency | PASS — ADR 0020 ↔ QUESTIONS (budget, Claude channel) ↔ PLAN gate lines ↔ RISKS rows ↔ HANDOFF next steps |
| Patch hygiene | PASS — `git diff --check` exits 0 |

Last verified: 2026-08-23 by Claude (Fable 5) session (documentation-only).

## Current M1 plan-merge verification — 2026-08-23

| Check | Result |
| --- | --- |
| Documentation-only scope | PASS — `docs/plans/m1a-direct-harness-poc.md` (r2), a banner on `docs/plans/m1-agentteam-direct-slice.md`, and Project Steward records only; no code, rename, dependency, credential, model call, CI, remote change, or push |
| r2 edit coverage | PASS — every row of the approved edit list is present (header, §1–§4, §6–§19, §21, new §22); gate names G0–G8 unchanged; status still *proposed* |
| Decision consistency | PASS — ADR 0019 ↔ QUESTIONS closures ↔ PLAN M1a lines ↔ HANDOFF next steps; ADRs 0012–0018 not reopened |
| `gh` authentication | PASS — `gh auth status` read-only: account `WSH95`, `repo` scope, SSH; no token value recorded |
| Local Markdown targets | see the session's checks recorded in HANDOFF (links in touched documents resolve; future `schemas/`/`examples/` paths are named, not linked) |
| Patch hygiene | PASS — `git diff --check` exits 0 |

Last verified: 2026-08-23 by Claude (Fable 5) session (documentation-only).

## Current provider-neutral documentation verification — 2026-08-23

| Check | Result |
| --- | --- |
| Documentation-only scope | PASS — architecture, planning, evidence, and Project Steward records only; no product code, dependency, credential operation, model call, CI workflow, remote change, or push |
| Prospective-route neutrality | PASS — 0 candidate model, endpoint, credential-variable, or key-prefix identifiers; the provider-name inventory has exactly 1 occurrence, confined to the factual ClawTeam preset list |
| Generic contract retention | PASS — provider/profile/protocol/model fields remain conceptual; credentials remain environment-name-only; API mode remains separate from native auth with no fallback |
| CI and approval boundary | PASS — M1a hosted CI remains deterministic and credential-free; no API-test route is selected or approved and product implementation remains review-gated |
| Decision/history traceability | PASS — ADR 0017 records the neutrality rule; candidate-context history remains recoverable from Git while unrelated third-party capability evidence is preserved |
| Local Markdown targets | PASS — 50 tracked Markdown files scanned, 12 local links checked, 0 broken |
| Markdown fences | PASS — 60 fence markers across 50 tracked Markdown files, 0 unbalanced files |
| Secret-pattern scan | PASS — 0 common API-key-shaped values and 0 private-key headers |
| Patch hygiene | PASS — `git diff --check` exits 0 |

Validation removes tentative route selection from current tracked documentation;
it does not choose or test a provider/model, change CI, approve M1a, or run a
vendor harness.

Last verified: 2026-08-23 by Codex (documentation-only; no credential values or
model prompts used).

## Current Python/optional-provider rebaseline verification — 2026-08-23

| Check | Result |
| --- | --- |
| Documentation-only scope | PASS — only architecture/plan/Project Steward records changed (`state.json` metadata included); no product source, dependency install, rename, credential operation, model call, remote change, push, or generated product artifact |
| Architecture-decision coverage | PASS — Python `>=3.11`/`uv`/Hatchling; checked-in JSON Schema edge; `atm` then M2 MCP; built-in shell-free direct runner; optional exact-pinned in-process ClawTeam boundary; one data root/namespace-only claim; M1b–M4 obligations |
| ClawTeam boundary consistency | PASS — full revision `01198332ef9270c32c5460b8a178f964fc0df451` and `mcp>=1,<2` appear in the proposed plan/decision records; M1a excludes ClawTeam process backends and confines imports to one compatibility module |
| Guarded instruction change | PASS — the owner-approved `AGENTS.md` diff changes only the title, product description, and primary stack above managed blocks; command/task/session managed blocks are byte-unchanged |
| Historical/current-state separation | PASS — living landing/model/steward documents point to the re-baselined M1a proposal; former TypeScript/CLI-first mechanics remain only as explicitly superseded decisions or labelled M0 evidence |
| Frozen requirement matrix | PASS without re-judgment — `existing-systems-fit-gap.md` is untouched and the `product-intent.md` diff is below the frozen register; the prior 54×11 structural regression remains applicable |
| Local Markdown targets | PASS — 50 Markdown files scanned, 12 local links checked, 0 broken |
| Markdown fences | PASS — 60 fence markers across 50 Markdown files, 0 unbalanced files |
| Secret-pattern scan | PASS — 0 API-key-shaped values and 0 private-key headers in the documentation/steward scope |
| Patch hygiene | PASS — `git diff --check` exits 0 |

Validation establishes a coherent documentation and plan rebaseline. It does
not approve product implementation, install/test ClawTeam, execute a vendor
harness, or provide Windows/macOS/live-runtime evidence.

Last verified: 2026-08-23 by Codex (documentation-only; no credential values or
model prompts used).

## Previous M1a planning verification — 2026-08-23 (superseded stack baseline)

| Check | Result |
| --- | --- |
| M0.1 commit boundary | PASS — `3407ec9` contains the completed 22-file documentation review; the worktree was clean immediately afterward |
| Planning-only scope | PASS — proposed implementation plan plus Project Steward plan/decision/question/risk/handoff/verification state only; no product code, dependency, rename, AGENTS/CLAUDE edit, credential operation, model call, remote change, or push |
| Required decision coverage | PASS — AgentTeam/`atm`; TypeScript/Node; Claude + Codex + Grok direct-first; native subscription profiles; model/effort precedence; full local evidence; deterministic CI/live Ubuntu split; API-test and ClawTeam deferral |
| Current runtime baseline | PASS — local Node 24.16.0, npm 11.13.0, pnpm 11.22.0, Claude Code 2.1.241, Codex 0.149.0, and Grok Build 1.0.5 rechecked without a model call |
| Volatile primary-source check | PASS — Node 22/24 remain LTS; Claude auth/env precedence and Codex model/effort/profile configuration rechecked; Anthropic's Help Center says the separate Agent SDK/`claude -p` credit change is paused |
| Local Markdown targets | PASS — the five project-local plan sources and the PLAN-to-plan link resolve |
| Markdown fences | PASS — 14 fence markers (7 balanced blocks) in the proposed plan |
| Secret-pattern scan | PASS — 0 candidate-route-key-shaped values and 0 private-key headers in the planning/steward scope |
| Patch hygiene | PASS — `git diff --check` exits 0 |

The proposed plan is
`docs/plans/m1a-direct-harness-poc.md`. Validation establishes that it is a
complete, internally linked planning artifact; it does not approve the plan or
provide implementation/live-runtime evidence.

Last verified: 2026-08-23 by Codex (planning-only; no credential values or
model prompts used).

## Current M0.1 verification — 2026-08-22

| Check | Result |
| --- | --- |
| Current local CLI baseline | PASS — Claude Code 2.1.241, Codex 0.149.0, Grok Build 1.0.5, OpenClaw 2026.7.1-2 |
| Sanitized native-auth status | PASS for Claude subscription OAuth and Codex ChatGPT login; Grok active login not tested |
| Fit-gap structural regression | PASS — 54 register IDs map one-to-one to 54 matrix rows; 11 non-empty system cells per row; priorities and cell syntax valid; 0 errors |
| Canonical architecture answer | PASS — exactly 3 copies and 0 byte-level line mismatches across `architecture-options.md`, `minimal-poc-plan.md`, and discovery `README.md` |
| Local Markdown links | PASS — 47 Markdown files scanned, 12 local `.md` links checked, 0 broken. *Correction (2026-08-23, G1 hygiene, review H9; re-counted with `git ls-tree 3407ec9`): 49 tracked Markdown files existed at `3407ec9` — the scan silently excluded `AGENTS.md` and `CLAUDE.md`.* |
| Placeholder inventory | PASS with 3 intentional matches — all mark the still-open implementation-language decision (`PROJECT.md` once; `reuse-vs-build-analysis.md` twice). *Correction (2026-08-23, G1 hygiene, review H9; re-scanned at `3407ec9`): 5 `TBD` markers, not 3 — `AGENTS.md:5` and `evidence/panel/proposal-B-independent-layer.md:42` were missed; all five concerned the then-open implementation-language decision, so the PASS reading stands with the corrected count.* |
| Secret-pattern scan | PASS — 0 candidate-route-key-shaped values and 0 private-key headers |
| Patch hygiene | PASS — `git diff --check` exits 0 |

The fit-gap regression is deliberately **structural**, not a second semantic
review of all 594 system cells. It confirms that documentation edits did not
drop, duplicate, shift, or corrupt a requirement row. The M0 matrix is trusted
except for the targeted AD-07 semantic correction documented in
`docs/discovery/evidence/m0-product-architecture-review-2026-08-22.md` F9.

No model prompt, API-test-provider request, live ClawTeam run, live OpenClaw run, or
Windows/macOS execution was performed. Hosted CI coverage is a future
milestone requirement, not evidence already obtained. No credential value or
authentication file was inspected.

Last verified: 2026-08-22 by Codex (credential-free documentation review).

## Historical M0 note

The W3 critic/fix-pass artifacts remain historical evidence. Current project
state does not rely on the former future-dated owner-read-through claim or the
former claim that no placeholder markers existed.
