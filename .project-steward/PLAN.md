# Plan

Milestones and tasks. If an external task backend is adopted, this file
holds milestones + a pointer only (never a duplicate task list).

## M0 Discovery: 9 analysis documents self-reviewed, then STOP for product/architecture review

Detailed execution plan (approved 2026-08-21): `~/.claude/plans/i-am-starting-a-lucky-coral.md` (session-local; the durable summary is this file + `docs/discovery/README.md`).

- [x] Phase 0 — steward init; `docs/discovery/README.md`; `evidence/glossary.md`; requirement register + PoC acceptance criteria in `product-intent.md`
- [x] Phase 0 — initial commit `chore: initialize Project Steward project management` (78272d8)
- [x] W1 "Understand" (189ea87) — 10 evidence agents → `docs/discovery/evidence/*.md` (clawteam-model, clawteam-spawn-platform, clawteam-probe-log, fork-delta, openclaw-native-and-telegram-verification, harness-cli-capabilities-a/-b, dsh-agent-teams-and-gui, claude-agent-teams-hermes-openbot, atm-salvage)
- [x] `product-intent.md` prose completed; register frozen 2026-08-22 (AR-06 added)
- [x] W2a-1 — fit-gap matrix (4 agents, 2 layers each) → merged `existing-systems-fit-gap.md`
- [x] W2a-2 (700485a) — `reuse-vs-build-analysis.md`, `legacy-atm-disposition.md`, `assistant-domain-model.md`, `team-execution-model.md`, `harness-broker-model.md`
- [x] W2b (e15b6f2) — architecture panel (3 biased architects → 2 judges → owner tiebreak → synthesis) → `architecture-options.md`; then `minimal-poc-plan.md`
- [x] W3 — per-document adversarial critics + completeness critic (c01b910 findings); fix pass under owner decisions D1–D15; re-checks all PASS
- [x] M0 critic/fix-pass records preserved as historical evidence; the former 2026-08-23 owner-read-through claim is not relied upon by current verification
- [x] Steward bookkeeping (PROGRESS/DECISIONS/QUESTIONS/RISKS/HANDOFF); final commit `docs(discovery): M0 discovery documents (9) + evidence`
- [x] M0 discovery package delivered; no code

## M0.1 Product/architecture review and documentation refresh (2026-08-22)

- [x] Verify current installed CLI versions, headless/isolation flags, sanitized auth state, and current OpenClaw/Telegram facts without live model calls or credential reads
- [x] Record owner decisions: hosted CI boundary; advisory PoC/mechanical production enforcement; native subscription OAuth; ATM reuse authorization; Claude Code + Codex + Grok Build first pass; API-test provider separation
- [x] Correct AD-07's omitted hidden-if-desired clause and its derived fit-gap text; retain the other matrix analysis
- [x] Mark the detailed M0 PoC proposal provisional and re-baselining-required; do not schedule a specific draft source or implementation
- [x] Run documentation regression checks and close M0.1 handoff

## M1a AgentTeam direct-harness PoC (approved — G0 done 2026-08-23)

Approved implementation plan (revision r3, approved text at `0f3e478`, DECISIONS 0021):
[`docs/plans/m1a-direct-harness-poc.md`](../docs/plans/m1a-direct-harness-poc.md).

- [x] Commit the completed M0.1 documentation review (`3407ec9`)
- [x] Record the owner-confirmed product identity, stack, auth, first-pass harness, model-policy, evidence, and live-test boundaries
- [x] Draft the exact direct-first implementation sequence, contracts, CLI, test matrix, live acceptance bar, publication gate, and stop rules
- [x] Commit the proposed plan and steward records as the multi-agent review baseline
- [x] Re-baseline the plan and current architecture documents for Python 3.11+/`uv`, a language-neutral edge, a built-in direct runner, and optional in-process coordination providers
- [x] Keep prospective API-test provider/model/endpoint selection unspecified across tracked documentation; preserve generic profile and secret-handling contracts
- [x] Independent review of the `3407ec9` baseline recorded (`docs/reviews/2026-08-23-m0-review-at-3407ec9.md`) with an independent M1 proposal for comparison (`docs/plans/m1-agentteam-direct-slice.md`); owner decisions in ADR 0018 — owner merges/selects before the approval step
- [x] Merge the independent proposal into M1a revision r2 (ADR 0019): selection precedence/`decided_by`, three Skills per harness, cross-OS hash identity, run record, probe levels, falsification routing, evidence bundle, docs-hygiene list, overlay deferred to M3, public repo at G2
- [x] Resolve the multi-agent review findings on r2 → revision r3 (ADR 0020): Claude recipe without `--safe-mode`, Grok `.grok/skills/`, pre-first-push checklist + gate-by-gate CI growth, Member execution binding (TEM §4 amended), Windows launcher policy + `.cmd` fake, computed hash only, required-Skill rule, promotion-only fixtures, waiver semantics, selection algorithm, V1 archive contract, budget ceiling 30
- [x] Incorporate multi-agent review findings without starting implementation (r3, ADR 0020)
- [x] Obtain explicit owner implementation approval, mark the reviewed plan `approved`, and commit any review resolutions (G0: DECISIONS 0021; status flipped)
- [x] G1 — rename/re-baseline the local project as AgentTeam (owner moved the repo 2026-08-23; root README/LICENSE/.gitattributes/.gitignore + identity amendments in `chore(project): rename project to AgentTeam`); documentation-hygiene docs-only commit (M1a §4 item 6; ADR 0022) — HB-03 register amendment deferred until the owner answers the QUESTIONS item; AGENTS command table waits for the G2 scaffold
- [x] G2 — Python foundation and public repository (execution per the approved 2026-08-23 G2 plan; commits `cc0cc5f` + `be5ce15` + CI fixes `671c2d9`/`d9440f8`; closed 2026-08-23)
  - [x] `uv`/Hatchling scaffold: pyproject, frozen `uv.lock`, `src/agentteam/`, `atm --help/--version`, py.typed, CLI tests
  - [x] Nine V1 domain records + checked-in JSON Schemas with reproduction/parity tests; `schemas/README.md`
  - [x] CI scaffold smoke matrix workflow (3 OS x 3.11/3.13; uv 0.11.26 pinned; schema steps included)
  - [x] Pre-first-push checklist: LICENSE + notices, `docs/provenance.md`, name checks (GitHub/PyPI 404 2026-08-23; `atm` free); history secret scan at the final local HEAD
  - [x] AGENTS.md managed command table (owner-approved diff; DECISIONS 0023)
  - [x] Public https://github.com/WSH95/AgentTeam (MIT) created and pushed on explicit approvals (DECISIONS 0024; first push `8660e6a`)
  - [x] Scaffold smoke matrix green on Ubuntu/Windows/macOS x 3.11/3.13 (run 32667607711 at `d9440f8`; VERIFY "G2 evidence")
- [x] G3 — direct harness core (per the owner-approved 2026-08-23 G3 plan; commits `4d6e082` + `f5e7cbb` (+ fixes `42c43be`, `37219bb`); closed 2026-08-23)
  - [x] V1 archive hasher, package loader + content heuristics, §11 selection with `decided_by`, model/effort precedence, env builder (conflicts fail closed, data-driven), launcher policy (npm `.cmd` shim parser + allowlist + refused), async process runner (tree kill, cancel, 130)
  - [x] Claude/Codex/Grok adapters: verified argv recipes, Skill channels, injection records, undeliverable-required-parts before launch, argv guard, redaction by construction; parser fixtures (promotion-only after G5) + fakes + `ci-fake.yaml`; example `code-reviewer` package (3 Skills)
  - [x] Full deterministic CLI: exit codes, `assistant validate`, `profile init/validate/doctor` (no `--probe`), `run --render-only`; CI smoke step
  - [x] 121 new tests (212 total) green on 3.11 + fresh 3.13; Windows-only `.cmd` suite runs on the windows CI legs
  - [x] Pushed on explicit approvals; six CI legs green incl. the Windows `.cmd` suite (run 32674468887 at `37219bb`; VERIFY "G3 evidence")
- [x] G4 — pass the deterministic direct-runner PoC locally (incl. solo mode, selection precedence, three Skills per harness, example-package hash identity) and qualify the optional, exactly pinned ClawTeam import/coordination seam without using its subprocess backend; write its qualification report (closed 2026-08-23: commits `e699c91`/`48cac73`/`b8d5f9d`; all nine CI checks green at `b8d5f9d`, run 32681299831; 354 tests with the extra, 342 + clean skip without; both acceptance tiers PASS deterministically; VERIFY "G4 evidence")
- [x] G5 — complete owner-driven dedicated native-auth profile setup and the bounded day-one probes (closed 2026-08-24; ADR 0031)
  - [x] Runtime/profile integration: persistent authenticated homes for live runs, synthetic render-only homes, version-bound verified-only readiness, fixed adapter ladders, and an exclusive managed Claude Skill lease (`549804f`)
  - [x] Credential-free implementation: secure `profile init`, sanitized no-call doctor, attended `doctor --probe`, selectable authoritative `--reprobe-ready`, owner-only pending/terminal captures, atomic per-call capability updates, deterministic fakes, and local validation (404 passed, 3 Ubuntu-skipped Windows tests after the live-found proxy/Claude/Grok corrections)
  - [x] Owner ran `profile init`; schema/0700-0600 permissions and a sanitized signed-out pre-login doctor baseline passed (actual versions: Claude 2.1.241, Codex 0.149.1, Grok 1.0.5)
  - [x] Resolve the falsified no-proxy assumption: standard native profiles inherit the owner's trusted terminal/Sing-box proxy unchanged; doctor/runtime/probe parity, names-only reporting, explicit-deny behavior, local profile migration, and normal-environment no-call doctor are green (ADR 0027)
  - [x] Owner ran each printed native login command with the normal proxy environment intact; post-login no-call doctor reports Claude/Codex signed in, Grok unverified pending probe, and zero conflicts
  - [x] Owner confirms the three harness probes individually (up to six calls), reviews raw local captures, promotes only sanitized fixtures, and closes G5 only if every required readiness row passes
    - [x] Claude call 1 timed out at 180.64s with zero output; evidence persisted and the owner declined the fallback while diagnosing. Fix the missing `Skill` permission, strengthen the fake, and rerun the full block (392 passed; ADR 0028)
    - [x] Claude's second/final actual invocation passed all five required rows in 174.77s; Codex call 1 passed all seven required rows in 25.79s. Both are current-version ready and are skipped by subsequent probes (`probe-20260824T063407Z-53c52838`)
    - [x] Grok confirmed invocation 1 was rejected locally in 44ms because bare `-p` requires a value when combined with `--prompt-file`; no model ran. Probe/live argv and the fake were corrected. Grok's second/final invocation then passed native auth, prompt-file, rules, structured output, and JSON-in-`text` in 12.36s, but invented two wrong-length Skill markers even though `grok inspect --json` discovered both files (`probe-20260824T064233Z-139f93bd`; ADR 0029)
    - [x] Review owner-only raw captures, verify all manifest hashes/0700-0600 permissions, and manually promote sanitized Claude/Codex/Grok envelope/event shapes. Identifiers, prompts, markers, commands, reasoning, model names, and usage values remain synthetic; parser-focused tests pass
    - [x] Retain the original Grok stop: its first two confirmed invocations did not verify a Skill channel, so no hidden retry occurred and G6 remained prohibited (ADR 0029)
    - [x] Under the explicit owner-approved gate revision, corrected Grok call 1 exited 0 in 16.562s and verified both independent workspace Skill markers plus all other required rows (`probe-20260824T070542Z-60bf6738`; ADR 0030). All three profiles are currently ready
    - [x] Implement selectable authoritative re-probes: repeatable harness selection, `claude` alias, `not-selected` reporting, all-profile preflight, profile-order calls, invalid-combination exit 2, forced-failure downgrade, two-call ceiling, and warning prompts (404 tests + full credential-free block green)
    - [x] Fresh all-three forced reassessment passed in one call each under `probe-20260824T075919Z-1edf636a`: Claude 10.363s/5 rows, Codex 20.490s/7 rows, Grok 17.195s/8 required rows. All manifests/hashes and 0700/0600 modes passed review; no-call doctor reports all three ready with no conflicts/staleness. G5 closed; no G6 call started
- [x] G5.R — resolve the 2026-08-24 independent-review findings before G6 (`docs/reviews/2026-08-24-g5-review-at-317bb52.md`; ADR 0032); closed at `e722c15` after local two-mode parity and hosted run 32735583747 passed all nine jobs
  - [x] R1/R2 — `from typer import Abort` in `commands/profile.py` and the probe CLI test: the external `click` import was an undeclared dependency (typer 0.27 vendors Click) that broke every core-mode CI leg, and the wrong Abort class made prompt Ctrl-C exit 1 instead of 130. Fixed; both dependency modes green (core 392+4, extra 404+3)
  - [x] R8 — the CI deterministic-acceptance step now provisions the disposable fake vendor homes (`examples/profiles/.agentteam-local/vendors/*`) that the G5 live preflight requires to exist; the step was green at G4 only because the gate predates it
  - [x] R3 — close managed-skills leases on every `_run_body` exit path: the workspace-copy hash-mismatch `return` and any exception outside `(RenderError, EnvironmentConflictError, TargetError)` leak acquired leases (Skills stay installed in the persistent Claude home); wrap prepare+execute in one `try/finally`; add a mismatch-path test
  - [x] R4 — bound the probe kill-escalation: send the group SIGKILL unconditionally after the SIGTERM grace and give the final `communicate()` a timeout + abandoned-pipes fallback (as `harness/process.py` already does); add a SIGTERM-surviving-descendant test
  - [x] R5 — enforce channel currency at the consumption point: `select_verified`/adapters must not pick a stale-verified ladder row that preflight only aggregate-checked; add a mixed-currency ladder test
  - [x] R6 — persist `ParsedLegV1` problems (the live Codex `-o`/JSONL disagreement) onto the invocation record instead of discarding them, and stop logging the agreement note into `problems`; add a live-disagreement test
  - [x] H9 — close the named test gaps alongside R3–R6: `--disallowedTools` content and `--safe-mode`/`--bare` absence assertions, ADR 0028's negative fake branch, Grok snake-case `structured_output`, adapter-level channel RenderErrors, the `execute_run` live gate, untested live-preflight branches, and a prompt test that drives real `typer.confirm`
  - [x] Hosted CI follow-up — run 32734735405 at `30c17b5` was 7/9 green because the stuck-pipe regression forced a POSIX `os.killpg` monkeypatch on Windows; `e722c15` tests the platform-independent drain helper directly, and run 32735583747 passed all six scaffold plus all three ClawTeam jobs
- [ ] G6 — pass the Ubuntu subscription-backed live PoC
  - [x] Initial owner-attended cycle `run-20260824-142351-dfc0` stopped after three calls with no retry or synthesis: Codex produced a valid review covering all three seeded defects; Claude rejected the canonical review schema's Draft 2020-12 meta-schema reference; Grok returned `structuredOutput: null` / `model did not produce structured output`; mechanical FAIL, semantic unevaluated, 18 of 30 calls remain
  - [x] G6.R1 — project checked-in canonical review/synthesis schemas into the real vendor dialect intersection before argv/file delivery (canonical `$schema`/`$id` metadata must not make Claude resolve an unsupported meta-schema); retain canonical exported schemas unchanged and add full review/synthesis render regressions (closed 2026-08-24: `vendor_projection` strips `$schema`/`$id`/`title` at delivery only, Codex switched to the projected file text, canonical exports byte-identical, docs-verified draft-07 root cause; VERIFY "G6.R rerun-blocker remediation")
  - [x] G6.R2 — diagnose the Grok full-review-schema failure from the sanitized field/error shape, preserve the fail-hard verified-field policy, and add deterministic coverage; do not silently consume unverified `text`, reassess capabilities, or spend another live call (closed 2026-08-24: construct set pinned to probe-proven ∪ {enum, anyOf, description}, `structuredOutputError` persisted on records, fixture/fake/runner coverage; grok-4.6-build's field output for the projected schema stays live-unproven until the rerun)
  - [x] G6.R3 — make every POSIX live-archive descendant owner-only, including `events.jsonl`, copied workspace trees, and adapter scratch/Skill files; extend permission acceptance from selected record files to recursive directories `0700` and files `0600` (closed 2026-08-24: umask-proof events opener, write-time tightening for workspace copies and Skill installs, `secure_tree()` at both finalize paths, recursive acceptance walk; exec-bit flattening recorded as RISKS R34)
  - [x] After G6.R1–R3 pass the credential-free block and review, repeat the no-call gate and obtain separate owner confirmation for at most one rerun; never auto-rerun (consumed 2026-08-24: gate green, owner confirmed, `run-20260824-154050-7a98` spent 4 calls and failed exit 1 at synthesis attribution; **mechanical tier passed live for the first time** and R1–R3 are proven in vivo; 14 of 30 calls remain)
  - [x] G6.R4 — steer synthesis attribution deterministically: the synthesis instructions and task document must state that every `sources` entry (agreements and merged findings) is the `invocation_id:finding_id` pair of a real leg finding while `asserted_by`/`not_asserted_by` are bare invocation ids; fix the task builder's "Refer to legs only by invocation id" line; carry the convention in the schema `description` fields so it travels inside the delivered document; add regressions (no live call) (closed 2026-08-24: instructions/task/schema-description steering + content pins; core 444+4 / extra 456+3 / compat 12; VERIFY "G6.R4")
  - [x] G6.R5 — steer leg semantics (owner-scoped before any further cycle): precise defect-category vocabulary and severity discipline in the Assistant definition (package hash re-pin required if it changes), true-synonym oracle aliases only (owner approves any acceptance-bar change), and final-output-only emission steering for the Grok leg; cond-2/3/4 failures and the 8.677s zero-finding Grok narration are the evidence; a further live cycle needs a new explicit owner decision (closed 2026-08-24 under the owner-selected full scope, ADR 0034: methods/task discipline, hash re-pinned `fd54eae7…`, true-synonym aliases with a generic-label guard; core 446+4 / extra 458+3 / compat 12; VERIFY "G6.R5"; third cycle authorized to prepare, final go at the gate)
  - [x] Third cycle (owner final go at the gate, 2026-08-24) failed on the Grok leg only: `stopReason: cancelled` at `num_turns: 2` — the headless agent loop is turn-capped and the adapter passes no `--max-turns`, so no final structured object can exist for a multi-turn review; Claude and Codex legs were valid again (2/2 consecutive). 11 of 30 calls remain; both ADR 0020 reruns consumed (VERIFY "G6 third live cycle")
  - [x] G6.R6 — pass an explicit generous `--max-turns` in the Grok adapter recipe so the headless agent loop can complete before its final structured emission; render regressions; deterministically unprovable until a live cycle (closed 2026-08-24 under the §18 owner ruling, ADR 0035: all-three gate kept, `GROK_MAX_TURNS = 40`, one beyond-allowance cycle authorized with the final go at the gate; core 447+4 / extra 459+3 / compat 12)
  - [x] Fourth cycle (ADR 0035 beyond-allowance; owner final go at the gate) failed exit 1 on the Grok leg only, with `--max-turns 40` verified in argv and an identical `cancelled`@`num_turns: 2` null result — the turn-budget hypothesis is falsified; Claude/Codex legs valid for the third consecutive cycle. 8 of 30 calls remain; the §18 gate question returns to the owner (VERIFY "G6 fourth live cycle")
- [ ] G7 — final CI matrices: credential-free core OS×Python matrix, optional ClawTeam compatibility matrix, and the vendor-smoke job; history secret scan repeated
- [ ] G8 — close M1a (reviewed sanitized evidence bundle committed; M1b draft names the local deterministic provider first and the ClawTeam exit criterion) and stop before TeamRun implementation

## M1b Team foundation (committed roadmap; outside the M1a approval scope)

- [ ] Prepare and approve a separate plan for TeamTemplate/TeamRun foundations, task/message/archive contracts, and the CoordinationSubstrate protocol
- [ ] Implement TeamRun orchestration and the optional ClawTeam provider behind the qualified compatibility boundary; keep harness launching on the built-in direct runner
- [ ] Preserve one AgentTeam-owned process data root with opaque team namespaces; claim namespace separation only

## M1c Dynamic-member PoC B (committed roadmap)

- [ ] Implement the product-owned dynamic-member policy gate and hidden/archive roster projections
- [ ] Prove the PoC B workflow with mechanical enforcement for every AgentTeam-mediated creation; record provider-bypass limits explicitly

## M2 Nested TeamRun PoC C + MCP (committed roadmap)

- [ ] Implement parent/child TeamRun lineage, result carrier, stop/cleanup, and isolation evidence
- [ ] Prove the PoC C nested-run acceptance contract
- [ ] Add an `atm` MCP server over the same versioned JSON contracts and core services

## M3 Evolution and artifacts (committed roadmap)

- [ ] Implement reviewed evolution overlays/proposals and portable artifact manifest/lock/resolution reporting

## M4 Long-running operations (committed roadmap)

- [ ] Implement deterministic watchers, RunStateSummary, decision log, and restart policy without requiring a resident LLM or gateway

## Optional later integrations and surfaces

- [ ] Reassess a small native TypeScript DSH adapter only if DSH becomes a primary daily harness; do not move the Python core for edge convenience
- [ ] Plan Hermes, OpenClaw, Telegram/surfaces, replaceable API-test providers, and any upstream ClawTeam changes independently when evidence and priority justify them
