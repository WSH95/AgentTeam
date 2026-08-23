---
title: Reuse-vs-build analysis — cheapest reuse rung per gap
status: draft v2.2 — Python core and optional-provider decision applied
date: 2026-08-22
owns: per-gap cheapest reuse rung (source, licence, cost/risk, platform) and the bolding rule (§1); ClawTeam four-mode verdict (§2.9); fork-only feature classification (§3); selective-reuse modules (§4); upstream-friendly extension candidates (§5); components new by evidence (§6); licence table (§7); substrate mapping (§8); new-vs-borrowed (§9); open questions (§10); inconsistencies with fit-gap (§11)
depends_on: product-intent.md (register), existing-systems-fit-gap.md (G-ids, cells), evidence/*.md; consumed by architecture-options.md (which alone states the smallest-layer answer)
---

# Reuse-vs-build analysis

> Reading guide: for every gap `G-*` in `existing-systems-fit-gap.md` §"Consolidated gap list" this document names the **cheapest rung** on the reuse ladder (XC-03) that closes it, a candidate source, its licence (XC-01), cost/risk and a platform note (XC-02). It never ranks architecture options and never says which layer to build — that is `architecture-options.md`. Requirements are cited by ID from `product-intent.md` §3.

> 2026-08-23 implementation amendment: AgentTeam's core is Python 3.11+ with `uv`; its external records remain JSON-Schema-defined and language-neutral. ClawTeam is the first **optional** coordination provider, pinned by full commit when installed, and all of its imports are confined to one owned compatibility/provider module. The direct runner remains independent of ClawTeam. The tables below retain the M0 rung analysis as evidence; they do not require the implementation to adopt every cheapest mechanism.

## 1. Method

**Ladder.** 1 configuration/composition · 2 thin adapter (wrapper over existing CLIs/seams, unchanged; 2a = over the CLI, flag-drift risk only; 2b = library import of "Alpha" seams, API-drift risk [ev:clawteam-spawn-platform#F15]) · 3 upstream-friendly extension (bounded PR) · 4 selective licensed module reuse · 5 fork only when necessary · 6 new implementation only if nothing else satisfies.

**Bolding rule (applied uniformly to all 54 rows).** Bold = the lowest rung at which the requirement, *as worded in the register*, is actually satisfied — not the lowest at which something related exists. When a NEW data object (or a new field on one of the new objects: Assistant definition, TeamTemplate/Member entry, HarnessProfile, policy, record, lock, Proposal) is required to satisfy the wording, the object is rung 6 and its materialization/projection is rung 1–2 — bold **6** and annotate "1–2 to materialize". A rung-1/2 row therefore needs no new object or field for the requirement as worded; lower rungs listed after the bold one are the mechanisms the object rides on; higher rungs listed are optional shadows (e.g. a ClawTeam PR) that are never required. Rung 3 entries are listed only next to their rung-1/2 twin.

**Evidence standard.** Claims cite `[ev:<file>#Fn]` or `Repo/path:line`; fit-gap cells are taken as given (disagreements only in §11); a rung resting on an unverified cell carries `?`.

**Cost** (borrow/adapt step only): `h` hours · `d` ≤5 working days · `w` 1–4 weeks · `—` nothing to borrow or build (no cost). **Risk** `low|med|high (factor)` uses the original merge/platform/verification criteria. **Platform**: Ubuntu, macOS, Windows; GitHub-hosted CI can verify deterministic OS plumbing but not live auth/model behavior. Licences/permissions: MIT · Apache · proprietary invocation-only · owner-authorized ATM internal reuse. ATM has no public licence, but the owner authorizes AgentTeam to copy/adapt it; record provenance and preserve third-party notices [ev:m0-product-architecture-review-2026-08-22#F7]. Current versions: CT 0.3.0@0119833, CTF 0.3.0+openclaw2, OC 2026.7.1-2, CC 2.1.241, CX 0.149.0, Grok 1.0.5, HM 0.20.4.

## 2. Per-gap table

### 2.1 AD — Assistant definition

| Gap (= Req) · P | Best existing | Rung | Candidate source (licence) | Cost, risk, platform | Evidence |
|---|---|---|---|---|---|
| G-AD-01 (M) | HM S! | **6** neutral object; 1 to materialize | shape ideas: Hermes `distribution.yaml`+`SOUL.md`, DG `AgentRecord`, kit SOUL/IDENTITY/AGENTS split (MIT); ATM role-template (owner-authorized) | d, low, any | [ev:claude-agent-teams-hermes-openbot#F24][ev:dsh-agent-teams-and-gui#F18] |
| G-AD-02 (M) | CT Xs!; ATM idea | **6** vocabulary; 1 Agent Skills name; 3 fields on CT `AgentDef` | Agent Skills spec (public); ADR 0022 `requires.capabilities/artifacts` (owner-authorized) | d, low, any | [ev:atm-salvage#F8][ev:atm-salvage#F10] |
| G-AD-03 (S) | DG S! | **6** permissions/collaboration/escalation fields on the new definition object (small); 1 permissions enforced via harness flags; 4 collaboration-schema ideas | CC `--permission-mode`, CX `--sandbox`, Grok `--allow/--deny`, HM `--yolo`, OC `tools.allow/deny` (prop./Apache/MIT); DG `qualityGate`/handoff, kit HANDOFF/ACK/DONE/BLOCKED (MIT) | d, low, any | [ev:harness-cli-capabilities-a#F11][ev:harness-cli-capabilities-b#F21][ev:harness-cli-capabilities-b#F14][ev:dsh-agent-teams-and-gui#F25] |
| G-AD-04 (M) | OC C! | **6** policy object; 4 precedence-chain pattern | CTF `model_resolution.py` (70 lines, stdlib; MIT); OC `model{primary,fallbacks}` | d, low, any | [ev:clawteam-openclaw-fork-delta#F15][ev:clawteam-openclaw-fork-delta#F28] |
| G-AD-05 (M) | DG S! | **6** strict schema + exclusion validator on the new definition object; 1 run-side isolation knobs keep run facts out | CC `--safe-mode --no-session-persistence`; CX `--ephemeral`/`CODEX_HOME`; Grok isolated home/memory; HM fresh profile; OC session key; DG `.strict()` (pattern) | h, low, any | [ev:m0-product-architecture-review-2026-08-22#F3][ev:harness-cli-capabilities-b#F24][ev:dsh-agent-teams-and-gui#F20] |
| G-AD-06 (C) | OC S! | **1** | OC `agents.list[].identity{name,emoji,avatar,theme}`, `set-identity --from-identity` (MIT); Member binding → G-MS-03 | h, low, OC (Gateway for channels) | [ev:openclaw-native-and-telegram-verification#F3] |
| G-AD-07 (M) | OC S! (full native behavior; CT/CTF/DT need visibility; CC composes; HM/CX unverified) | **1** native OC child-session mechanism; hidden elsewhere = G-TC-04 (6 field + 2 filtered roster; CT flag at 3 optional); portable definition object = G-AD-01 | OC `sessions_spawn`; CC `--agents` + background subagents; HM `delegate_task`/`--source tool`; CT `spawn` (MIT/prop.) | d, low (rung 2 shadow; merge risk only if the CT PR is pursued), OC needs Gateway | [ev:openclaw-native-and-telegram-verification#F14][ev:m0-product-architecture-review-2026-08-22#F9] |
| G-AD-08 (M) | DG S! | **2** renderer from one definition into each harness format | CC `.claude/agents/*.md`/`--agents`; HM profile `SOUL.md`; OC workspace files; CT `AgentDef.task`/`--skill` | d/harness, med (flag drift), any | [ev:harness-cli-capabilities-a#F17][ev:harness-cli-capabilities-b#F24] |
| G-AD-09 (M) | OC S! | **6** composite (with G-AD-01); 1 inside each harness; harness composition = G-HB-05 | as G-AD-08 | —, low, any | [ev:harness-cli-capabilities-b#F9][ev:clawteam-model#F15] |

### 2.2 EV — Evolution

| Gap (= Req) · P | Best existing | Rung | Candidate source (licence) | Cost, risk, platform | Evidence |
|---|---|---|---|---|---|
| G-EV-01 (M) | HM Xs! | **6** project-independence filter; 1 interception point `?` | HM `pre_tool_call` hooks/curator ledger; CC `PreToolUse`; OC `session-memory` hook (MIT/prop.) | d, med (verif.), any | [ev:claude-agent-teams-hermes-openbot#F28][ev:harness-cli-capabilities-b#F21][ev:harness-cli-capabilities-b#F14] |
| G-EV-02 (M) | HM Xs! | **6** 3-layer merge/conflict rules; borrow the 2-layer ownership split | HM distribution-owned vs user-owned paths; CT whole-file override (MIT) | d, low, any | [ev:claude-agent-teams-hermes-openbot#F24][ev:clawteam-probe-log#F4] |
| G-EV-03 (M) | DG Xs!; ATM idea | **6** Proposal object; 2 approval transport | CT `plan_submit/approve/reject` (MIT); DG retrospective text; ATM typed proposal (owner-authorized) | d, low, CT file-based | [ev:clawteam-model#F17][ev:clawteam-model#F21] |
| G-EV-04 (M) | HM S! | **6** never-persist rule in the schema/validator of the new definition and overlay objects (shared with G-AD-05); 1 run-side knobs (G-AD-05) | G-AD-05 knobs; HM export hard-excludes `memories/ sessions/ .env` (MIT, pattern) | h, low, any | [ev:claude-agent-teams-hermes-openbot#F24][ev:harness-cli-capabilities-a#F19] |
| G-EV-05 (S) | DG Xs!; ATM idea | **6** review workflow with provenance; 4 ledger/version/preview patterns | HM curator `ledger`; DG version/import patterns (MIT); ATM MAC'd decision + plan-hash (owner-authorized) | d–w, low, any | [ev:claude-agent-teams-hermes-openbot#F28][ev:dsh-agent-teams-and-gui#F20] |
| G-XC-03 (M) | HM R1! (fit-gap XC-03 uses rung marks) | meta (not bolded; counted separately in "Reading across"): 1 materialize into OC/HM/CC/CX/Grok; 2/4 render into CT templates / lift DG schemas; 6 three new objects | rows above | — | fit-gap §XC-03 |

### 2.3 TC — Team composition

| Gap (= Req) · P | Best existing | Rung | Candidate source (licence) | Cost, risk, platform | Evidence |
|---|---|---|---|---|---|
| G-TC-01 (M) | DG S! | **6** template object; 2 render into CT TOML for execution; 4 schema idea | CT `~/.clawteam/templates/*.toml` (`leader/agents[]/tasks[]`, per-agent `command`); DG `SquadRecord→AgentRecord` (MIT) | d, low, CT file-based | [ev:clawteam-probe-log#F4][ev:clawteam-model#F13] |
| G-TC-02 (M) | DG S!; CT C! | **6** relationship/handoff fields (small); 1 lead via CT `template.leader`; 4 schema ideas | DG/kit handoff patterns (MIT); ATM `topology.allow` (owner-authorized) | d, low, any | [ev:dsh-agent-teams-and-gui#F24][ev:openclaw-native-and-telegram-verification#F5] |
| G-TC-03 (S) | DG C!; OC C! | **6** enforcement-level field (`advisory` / `mechanical`); 1 advisory by construction; 3 CT inbox ACL for mechanical | CT/HM/CC/DG mechanisms; ATM ADR 0026 (owner-authorized) | d, low (advisory); med (mechanical extension), any | [ev:clawteam-model#F4][ev:dsh-agent-teams-and-gui#F25] |
| G-TC-04 (S) | HM C?~ (`--source tool` unprobed; W3 re-score) | **6** `visibility` field on the new template/Member entry; 2 layer-side filtered roster over `clawteam team status` (global `--json`) — ClawTeam's `team status`/`board show` still list the Member, so the layer keeps "two rosters"; 3 CT `TeamMember.hidden` + board filter (optional PR, §5); 1 HM `--source tool` (Hermes-only `?`) | CT `team/models.py:65-87` (no visibility field), `commands.py:1533-1560` (`team status` emits members as JSON); HM `chat --source tool` (MIT) | d, low (rung 2 shadow; merge risk only if the PR is pursued; HM unverified), any | [ev:clawteam-model#F1][ev:clawteam-probe-log#F10][ev:harness-cli-capabilities-b#F6] |
| G-TC-05 (M) | OC C! | **6** policy fields; 2 enforce in the caller before `spawn`; 1 inside OC/HM/DT | OC/HM/DT controls (MIT); ATM `spawn{intraRole,maxDepth}` (owner-authorized) | d, low, OC Gateway, others none | [ev:openclaw-native-and-telegram-verification#F21][ev:claude-agent-teams-hermes-openbot#F22] |
| G-TC-06 (M) | DG S!; CT C! | **6** team-preference field (small); 1 harness/backend keys in CT template | CT `TemplateDef.command/backend`; DG record (MIT) | h, low, any | [ev:clawteam-probe-log#F4][ev:dsh-agent-teams-and-gui#F18] |

### 2.4 TE — Team execution

| Gap (= Req) · P | Best existing | Rung | Candidate source (licence) | Cost, risk, platform | Evidence |
|---|---|---|---|---|---|
| G-TE-01 (M) | CT S! | **1** CT `launch`/`spawn`; 3 surface spawn failures (PR #167) + `TaskDef.blocked_by`, or 2 wrapper checking `"Error"` per member; alt 1 HM `kanban create` (Hermes-only) | CT `commands.py:4034-4215`; HM kanban (MIT) | d, low (rung 1/2); med (merge) only for the PR, CT subprocess: Ubuntu/macOS; Windows partial (see G-TE-08); HM kanban needs gateway | [ev:clawteam-probe-log#F15][ev:clawteam-probe-log#F23] |
| G-TE-02 (M) | CT S! | **1** (CT/CC/CX/DC fresh; OC session key; HM fresh profile); 3 CTF `OPENCLAW_WORKSPACE`→`_DIR` fix | CT `--session-id` per spawn, opt-in `--resume`; G-AD-05 knobs | h, low, any | [ev:clawteam-spawn-platform#F19][ev:harness-cli-capabilities-b#F4] |
| G-TE-03 (M) | CT C! | **1** per-agent `command` (explicit positional argv, no `--task`); 2b in-process custom backend (`register_backend`) for Hermes/Grok argv; or 3 adapter branches | CT `spawn/__init__.py:10-29`, `AgentDef.command`; CTF `adapters.py:64-82` (MIT) | d, low (rung 1); med (API/merge) for 2b/3, subprocess: Ubuntu/macOS; Windows partial (see G-TE-08) | [ev:clawteam-probe-log#F16][ev:clawteam-spawn-platform#F17] |
| G-TE-04 (M) | OC S! | **1** spawn (CT/OC/CC/HM); hidden = G-TC-04 (2 filtered roster; CT flag at 3 optional); OC sub-agent persona only as `--message-file` prefix | as G-AD-07 | d, low (rung 2 shadow), OC Gateway, others none | [ev:openclaw-native-and-telegram-verification#F14][ev:clawteam-model#F1] |
| G-TE-05 (M) | OC P! (delegation tree; tie HM, DT) / CT Xs! (inner team, W3 re-score) | **2a** wrapper over the CT CLI (`team spawn-team B -n <self>`→`spawn --team B`→`task wait B --agent <self>`→`inbox receive B` / `inbox send <outer> <creator>`→`team snapshot`→stop (`spawn --replace`, or SIGTERM to the pids in `teams/B/spawn_registry.json`; no stop verb exists)→`team cleanup`); 2b the same over library seams (`TeamManager`, `waiter`, `snapshot`, `registry.stop_agent`); 3 `TeamConfig.created_by` parent link (optional — the parent link otherwise lives in the layer's run record); 6 result-contract/isolation record | CT CLI (2a) or `manager.py`, `waiter.py`, `snapshot.py`, `registry.py` (2b) (MIT); HM kanban `--parent` (links only) | d–w, 2a low–med (flag drift; cleanup leaves processes, so stop-before-cleanup is the wrapper's job), 2b med (API drift), CT file-based, no tmux | [ev:clawteam-model#F22][ev:clawteam-probe-log#F18][ev:clawteam-probe-log#F19][ev:clawteam-probe-log#F20][ev:clawteam-probe-log#F21][ev:clawteam-spawn-platform#F15] |
| G-TE-06 (S) | CT S! | **1** CT DAG/inbox/watcher; 3 `--blocked-by` validation + liveness column (CTF has it); alt 1 HM kanban, DG (DSH) | CT `store/file.py`, `mailbox.py`, `leader_watcher.py`; CTF `commands.py:1598-1629` (MIT) | h–d, low, any (CT); HM gateway | [ev:clawteam-probe-log#F7][ev:clawteam-probe-log#F10] |
| G-TE-07 (M) | DG S! (tie DT); CT Xs! (W3 re-score) | **2** caller captures stdout/exit code and writes the run record; 1 CT snapshot/events/registry + harness transcripts; 3 logs dir + read `CLAWTEAM_EXIT_CODE` (PR #159) | CT `snapshot.py:123-183`, `session_locators/*`; CTF last-80-lines capture (MIT) | d, med (merge), any | [ev:clawteam-spawn-platform#F21][ev:clawteam-probe-log#F14] |
| G-TE-08 (M) | CTF C! | **1** `skip_permissions: false` in the layer-written ClawTeam config — `os.getuid()` at `adapters.py:53` sits inside `if skip_permissions:` (`adapters.py:49`; config default `True`, `config.py:59`), so it is never evaluated and the layer renders permission flags into the argv itself; + **2** wrapper captures the exit code and delivers prompts by file (the Windows subprocess branch has no keepalive and no exit-code env); 3 PR #159 guard and 4 CTF `platform_compat.py` optional; harness CLIs on Windows per docs `~` | CT `adapters.py:49-53`, `config.py:59`; CTF `platform_compat.py` (130 lines) (MIT) | h–d, high (platform: no Windows CI anywhere; unprobed off this host), Windows = subprocess backend only (cmd.exe branch) | [ev:clawteam-spawn-platform#F20][ev:clawteam-openclaw-fork-delta#F19][ev:harness-cli-capabilities-a#F14] |
| G-XC-02 (M) | OC S! | **6** two independent dimensions in the HarnessProfile (tiny); 1 OC docs/`requires`; ATM compatibility idea | OC skills metadata (MIT); ADR 0022 (owner-authorized) | h, low, any | [ev:harness-cli-capabilities-b#F11][ev:atm-salvage#F10] |

### 2.5 HB — Harness brokerage

| Gap (= Req) · P | Best existing | Rung | Candidate source (licence) | Cost, risk, platform | Evidence |
|---|---|---|---|---|---|
| G-HB-01 (M) | CT Xs! | **6** data model; 4 extract flag knowledge from CT adapters/keepalive/locators; 1 seed from evidence checklists | CT adapter knowledge (MIT); ATM adapter-contract query names (owner-authorized) | d, low, any | [ev:clawteam-spawn-platform#F1][ev:harness-cli-capabilities-a#F16] |
| G-HB-02 (M) | CC S! | **1** per-harness channels; 2 renderer; CT's system-prompt drop for non-claude avoided by rung-2 backend or fixed at 3 (~20 lines) | CC `--append-system-prompt[-file]`, `--add-dir`, `--mcp-config`; Grok `--rules`; CX `-c developer_instructions` `?`; OC per-run workspace; HM `SOUL.md`/env overlay | d, med (CX verif.), any | [ev:harness-cli-capabilities-a#F17][ev:harness-cli-capabilities-b#F24] |
| G-HB-03 (M) | OC C?~; CT Xs! | **6** user > Assistant > default policy (the brief's "role-level"); 4 CTF `model_resolution.py` pattern; 1 pass the resolved command to CT `spawn` | CTF `model_resolution.py:29-70`; CT command precedence (MIT) | d, low, any | [ev:clawteam-openclaw-fork-delta#F15][ev:clawteam-probe-log#F17] |
| G-HB-04 (S) | OC C?~; CT/DC Xs! (W3 re-score) | **2** caller retries with the next harness; 4 CTF `spawn_with_retry` backoff; 1 model-level fallbacks | CTF `spawn/__init__.py:46-70`; CT `--replace`; CC `--fallback-model`, OC `model.fallbacks`, HM `hermes fallback` (MIT/prop.) | h–d, low, any | [ev:clawteam-openclaw-fork-delta#F13][ev:clawteam-probe-log#F21] |
| G-HB-05 (M) | CT P!; DC Xs! | **2** fan-out (N invocations); 6 synthesis record with per-harness attribution; synthesis step = one more invocation (1) | CT template with N commands; DC scripts; CC workflows, HM MoA (same-runtime precedents) | d, low, any | [ev:clawteam-probe-log#F16][ev:harness-cli-capabilities-a#F10] |
| G-HB-06 (S) | OC S! | **1** OC cron `--command`/hooks; 2 caller invokes the executable directly (avoids CT's `-p` append and DEVNULL) | OC `cron add --command`; CC hooks/monitors `?`; CT `spawn subprocess -- <exe>` | h, low, OC Gateway; direct call any | [ev:openclaw-native-and-telegram-verification#F9][ev:clawteam-probe-log#F12] |
| G-HB-07 (S) | CC S! | **6** persisted record (no substrate writes one for an external CLI); 1 emission; 3 fields on CT `CostEvent`/registry | CC `-p --output-format json`; HM `-z --usage-file`; Grok json; CX `--json` tokens; OC `audit` | d, low, any | [ev:harness-cli-capabilities-a#F10][ev:harness-cli-capabilities-b#F7] |
| G-HB-08 (S) | OC C?~; CT Xs! | **2** CT `register_backend` in-process; 3 plugin load on the `spawn` path (~10 lines); OC acpx alias `?` (no Hermes alias) | CT `spawn/__init__.py:10-29`, `plugins/manager.py` (MIT); OC `agents.list[].runtime.acp` | h–d, med (API), any | [ev:clawteam-spawn-platform#F8][ev:clawteam-spawn-platform#F17] |

### 2.6 AR — Artifact / dependency

| Gap (= Req) · P | Best existing | Rung | Candidate source (licence) | Cost, risk, platform | Evidence |
|---|---|---|---|---|---|
| G-AR-01 (M) | — | **6** | ATM ADR 0022 `requires.capabilities[]` vs `requires.artifacts[]` (owner-authorized) | d, low, any | [ev:atm-salvage#F10][ev:m0-product-architecture-review-2026-08-22#F7] |
| G-AR-02 (M) | OC S! | **6** cross-harness kind enum + "capability package" (small); 1 per-ecosystem kinds | OC skills/plugins/`requires.bins`; CC plugins; HM skills/distributions; CX skills/MCP | h, low, any | [ev:harness-cli-capabilities-b#F11][ev:claude-agent-teams-hermes-openbot#F14] |
| G-AR-03 (M) | HM S! | **4** patterns + 6 cross-harness manifest; 1 for Hermes targets | HM/DG patterns (MIT); ATM export-manifest (owner-authorized) | d–w, low, any | [ev:claude-agent-teams-hermes-openbot#F24][ev:dsh-agent-teams-and-gui#F20] |
| G-AR-04 (M) | HM S! | **1** env-name references — do **not** borrow CTF gateway-token propagation | OC SecretRef; HM `env_requires`; DG `.strict()` (MIT) | h, low, any | [ev:atm-salvage#F1][ev:claude-agent-teams-hermes-openbot#F24] |
| G-AR-05 (S) | OC S! | **6** per-capability report (small); 1 inputs | OC/HM/CT report inputs (MIT); ATM outcome vocabulary (owner-authorized) | d, low, any | [ev:harness-cli-capabilities-b#F11][ev:atm-salvage#F10][ev:atm-salvage#F7] |
| G-AR-06 (S) | — | **6** lock + fingerprint | ATM `ArtifactLock` (owner-authorized); HM distribution/ledger (MIT) | d, low, any | [ev:atm-salvage#F10][ev:claude-agent-teams-hermes-openbot#F24] |
| G-XC-01 (M) | CT S! | **1** verified (§7); ATM internal reuse authorized by owner | provenance + third-party notice audit | h, low | [ev:m0-product-architecture-review-2026-08-22#F7] |

### 2.7 MS — Messaging / surface

| Gap (= Req) · P | Best existing | Rung | Candidate source (licence) | Cost, risk, platform | Evidence |
|---|---|---|---|---|---|
| G-MS-01 (M) | CT S! | **1** (CT file-based; CC/CX/DC in-process; OC `agent --local`/HM `chat -q` as daemon-free workers) | — | —, low, no daemon on any OS | [ev:clawteam-probe-log#F2][ev:harness-cli-capabilities-b#F1] |
| G-MS-02 (C) | HM S! | **2** thin adapter presenting a TeamRun/Member over Hermes gateway platforms with profile routing (`hermes peer dm`; no Hermes `send` command is evidenced), OC `agent --deliver`, CC channels | HM gateway (20+ platforms); OC channels; CC channel plugins (MIT/prop.) | w, med (platform: daemons), daemon per surface | [ev:claude-agent-teams-hermes-openbot#F26][ev:openclaw-native-and-telegram-verification#F19] |
| G-MS-03 (S) | OC S! | **1** one bot account per visible Member; 6 Member↔identity binding record | OC `identity`; HM platform token per profile (MIT); OB `agent_profiles` (idea) | d, low, surface daemon | [ev:openclaw-native-and-telegram-verification#F3][ev:openclaw-native-and-telegram-verification#F20] |
| G-MS-04 (M) | CT S! | **1** nothing to build; OC bindings treated as presentation | — | —, low | [ev:openclaw-native-and-telegram-verification#F4][ev:atm-salvage#F5] |

### 2.8 LO — Long-running operations

| Gap (= Req) · P | Best existing | Rung | Candidate source (licence) | Cost, risk, platform | Evidence |
|---|---|---|---|---|---|
| G-LO-01 (S) | OC S! | **1** OS scheduler (cron/launchd/schtasks) or OC `cron add --session isolated` invoking a headless harness; HM cron `?` | OC cron; HM cron/kanban; CT `inbox watch --exec`→`spawn --no-keepalive` (`P~`) (MIT) | d, med (platform: scheduler per OS; OC Gateway), per-OS scheduler | [ev:openclaw-native-and-telegram-verification#F9][ev:clawteam-model#F19] |
| G-LO-02 (S) | OC S! | **6** job-level watchers (domain scripts outside any substrate); 1 trigger/scheduler/health infra | OC cron `--command`, hooks; CT `leader_watcher.py`, registry liveness (MIT); CC monitors `?` | d–w per job type, low, any | [ev:openclaw-native-and-telegram-verification#F9][ev:clawteam-model#F18] |
| G-LO-03 (S) | OC S! | **1** headless invocation with rendered definition; 2 trigger→invocation wiring | CC `--append-system-prompt`; HM `-p <profile> -q`; OC `--message` + workspace files (prop./MIT) | h–d, low, any | [ev:atm-salvage#F4][ev:harness-cli-capabilities-b#F19] |
| G-LO-04 (S) | OC S!; CT S! | **6** declarative resume/fresh policy (small enum); 1 substrate mechanisms; 4 CTF `AgentHealth`/`respawn.py` patterns | CT `should-keepalive`; CTF `respawn.py` (coupled), `registry.py:25-152` (MIT); DG `retryOf` (idea) | d, med (platform: keepalive POSIX-only), Windows has no keepalive loop | [ev:clawteam-probe-log#F14][ev:clawteam-spawn-platform#F20] |
| G-XC-04 (S) | OC S! | **6** cross-system invocation record (= G-HB-07), proposal audit (= G-EV-05); 1 per-system audit; 2/3 CT output/exit-code fidelity | as cited | d, low, any | [ev:openclaw-native-and-telegram-verification#F22][ev:clawteam-spawn-platform#F21] |

**Reading across (bold rungs, 54 gaps, under the §1 rule).** Rung 1: 17 (G-AD-06/07, G-TE-01/02/03/04/06/08, G-HB-02/06, G-AR-04, G-XC-01, G-MS-01/03/04, G-LO-01/03) · rung 2: 7 (G-AD-08, G-TE-05, G-TE-07, G-HB-04, G-HB-05, G-HB-08, G-MS-02) · rung 3: 0 · rung 4: 1 (G-AR-03) · rung 5: 0 · rung 6: 28 (G-AD-01/02/03/04/05/09, G-EV-01/02/03/04/05, G-TC-01/02/03/04/05/06, G-XC-02, G-HB-01/03/07, G-AR-01/02/05/06, G-LO-02/04, G-XC-04) · meta: 1 (G-XC-03). (Previous draft: 20/7/2/1/0/23/1 — the change is the uniform bolding rule: G-AD-03, G-AD-05, G-EV-04, G-TC-03, G-TC-04 are new fields on new objects → 6; G-TE-08 is satisfied by configuration + wrapper → 1.) Rung 5 is never cheapest; rung 3 is never cheapest either, and every ClawTeam PR listed in §5 has its rung-1/2 twin shown in its own §2 row, which matters given merge risk. Most rung-6 items are data objects or fields on them (definition, template fields, policy, records, lock, Proposal), not runtime machinery; how they group is for `architecture-options.md` (cite the object list of §6, not the count).

### 2.9 ClawTeam four-mode verdict (brief item 12)

Read off the CT/CTF entries in §2 (rung 1 = as-is or configured, 2 = wrapped, 3 = extended upstream; rung 5 forking is ruled out in §3):

- **As-is** (used with its defaults, unchanged): file-based team/task DAG/inbox/transport, `--session-id` per spawn, spawn registry + `leader_watcher`, snapshot, `spawn` for dynamic members — G-TE-02, G-TE-04, G-TE-06, G-MS-01, G-MS-04, G-LO-02 (infra part), G-XC-01 [ev:clawteam-probe-log#F2][ev:clawteam-spawn-platform#F19][ev:clawteam-model#F18].
- **Configured** (layer-written config, template keys or explicit argv; no ClawTeam change): per-Member `command` (no `--task`), `skip_permissions: false`, `default_backend: subprocess`, `template.leader`, harness/backend keys, `should-keepalive`, N commands for fan-out — G-TE-01, G-TE-03, G-TE-08, G-TC-02 (lead), G-TC-06, G-HB-03 (resolved command passed in), G-HB-05, G-LO-04 [ev:clawteam-probe-log#F16][ev:clawteam-probe-log#F17][ev:clawteam-spawn-platform#F20].
- **Wrapped** (rung 2a: driven through its CLI from outside, unchanged): the TeamRun compiler/wrapper — G-TE-05 (compose, wait, collect, stop, cleanup), G-TE-07 (capture output/exit code), G-TC-01 (render to TOML only if `launch` were used; otherwise direct `spawn` calls), G-TC-04 (filtered roster), G-TC-05 (gate before `spawn`), G-HB-04 (`--replace`/retry), G-HB-06 (`spawn subprocess -- <exe>`), G-EV-03 (plan round-trip as optional transport); rung 2b (library import) only for G-HB-08 `register_backend` [ev:clawteam-probe-log#F18][ev:clawteam-probe-log#F21][ev:clawteam-spawn-platform#F8].
- **Extended upstream** (rung 3): not the cheapest rung for any gap — the nine PRs of §5 are goodwill with a rung-1/2 twin each; nothing in §2 depends on a merge [ev:clawteam-spawn-platform#F24].
- **Not forked** (rung 5): nothing in either tree justifies it (§3).

**Selected implementation scope.** The four-mode verdict above is retained as comparative evidence, not as a commitment to a CLI-first runtime. The selected path uses ClawTeam only as an optional rung-2b coordination provider through its in-process Python seams. AgentTeam owns harness launching and never uses ClawTeam's `SubprocessBackend` (`shell=True`). M1a must qualify the import boundary, namespace behavior, and event translation without making the direct core depend on ClawTeam; team execution enters in M1b and the dynamic-member and nesting claims are proved in M1c and M2.

## 3. ClawTeam-OpenClaw fork-only features classified

Classes from [ev:clawteam-openclaw-fork-delta#F34] (112 fork-only commits [ev:clawteam-openclaw-fork-delta#F1], 88 files [ev:clawteam-openclaw-fork-delta#F2]; both trees MIT [ev:clawteam-openclaw-fork-delta#F30]).

| Feature (fork anchor) | Class | Reqs | Note |
|---|---|---|---|
| Bare `openclaw`→`tui` default + `clawteam-T-A` session key | partly already-upstream (adapter `tui --session` branch); default fork-only | HB-01, HB-02 | `--model` on `tui` invalid on 2026.7.1-2; subprocess path emits `--session-id` [ev:clawteam-openclaw-fork-delta#F5][ev:clawteam-openclaw-fork-delta#F6] |
| Worker-workspace isolation (`OPENCLAW_WORKSPACE`); circuit-breaker health (`AgentHealth`); per-agent model resolution (`model_resolution.py`) | worth-selective-reuse (idea / model only / pure function) | TE-02, AD-05, LO-04, HB-03, AD-04 | env name wrong for 2026.7.1-2; admission never consulted; no user-level layer [ev:harness-cli-capabilities-b#F4][ev:clawteam-openclaw-fork-delta#F12][ev:clawteam-openclaw-fork-delta#F15] |
| Gateway-token propagation; `--agent` probe; Gateway (A2A) APIs; dropped wsh backend | irrelevant (token conflicts AR-04; probe no-op; A2A router demoted; wsh out of scope) | AR-04 | [ev:clawteam-openclaw-fork-delta#F8][ev:clawteam-openclaw-fork-delta#F9][ev:clawteam-openclaw-fork-delta#F17][ev:clawteam-openclaw-fork-delta#F26] |
| Auto-respawn (`trap EXIT`, `respawn.py`, `subprocess_wrapper.py`) | fork-only (divergent from upstream keepalive) | LO-04, TE-06 | re-runs argv, max 2 [ev:clawteam-openclaw-fork-delta#F11] |
| Retry/backoff + idempotency keys; Hermes spawn target + `skills/hermes/SKILL.md`; `platform_compat.py` + Windows defaults | worth-upstreaming / selective-reuse | TE-06, XC-04, HB-08, HB-01, TE-03, TE-08, XC-02 | Hermes flags valid on 0.20.4; root guard lost in fork backends [ev:clawteam-openclaw-fork-delta#F13][ev:harness-cli-capabilities-b#F6][ev:clawteam-openclaw-fork-delta#F19] |
| Approvals allowlist hint; cost dashboard; prompt research blocks; subproject overlay; `alive` column; max-4 warning; defaults flipped to OpenClaw | fork-only, small/partial (`alive` worth-upstreaming) | HB-01, AR-05, HB-07, AD-01, TE-01, TE-06, HB-03 | cost self-reported, `board cost` missing [ev:clawteam-openclaw-fork-delta#F10][ev:clawteam-openclaw-fork-delta#F16][ev:clawteam-openclaw-fork-delta#F32] |
| kimi/qwen/opencode/pi; `--skill`; runtime inject; session capture; subprocess mode; CI | already-upstream | HB-08, HB-02, TE-06, TE-02, TE-08 | [ev:clawteam-openclaw-fork-delta#F20][ev:clawteam-openclaw-fork-delta#F25] |

Rung 5 verdict: nothing here justifies forking either tree — reusable parts are standalone modules (rung 4) or PR-sized deltas (rung 3); the rest is irrelevant or divergent [ev:clawteam-openclaw-fork-delta#F27][ev:clawteam-openclaw-fork-delta#F28].

## 4. Candidate selective-reuse modules and extension seams

| Candidate | Isolation (imports) | Lic | Merge/adapt cost | Would satisfy |
|---|---|---|---|---|
| CTF `clawteam/model_resolution.py` (70 lines) | none (stdlib) [ev:clawteam-openclaw-fork-delta#F28] | MIT (no SPDX header; attribute HKUDS) | h vendor; d to re-model precedence user > Assistant > default | HB-03, AD-04 pattern |
| CTF `clawteam/platform_compat.py` (130 lines) | stdlib [ev:clawteam-openclaw-fork-delta#F19] | MIT | h | TE-08, XC-02 (Windows default backend, file lock, `pid_alive`, `shell_join`) |
| CTF `spawn_with_retry` (25 lines); `subprocess_wrapper.py` (66); idempotency keys | protocol only; 1 helper + shells out to `lifecycle on-exit`; keys coupled to CT models | MIT | h–d; keys via upstream PR | HB-04, TE-06; LO-04/TE-07 exit hook without `shell=True`; XC-04 [ev:clawteam-openclaw-fork-delta#F13] |
| CTF `spawn/respawn.py` (86); `registry.py` health block (~130) | coupled to registry/TeamManager; partial | MIT | d (rewrite against own records) | LO-04 patterns [ev:clawteam-openclaw-fork-delta#F11][ev:clawteam-openclaw-fork-delta#F12] |
| CTF Hermes adapter (`adapters.py:64-82,242`; `command_validation.py:368-385`; `skills/hermes/SKILL.md` 262 lines) | inside the adapter chain | MIT (SKILL.md `license: MIT`) | d to port upstream or into a HarnessProfile | HB-08, HB-01, TE-03 [ev:clawteam-openclaw-fork-delta#F14] |
| CT CLI used in place (rung 2a): `team spawn-team/status/snapshot/cleanup`, `spawn [--replace]`, `task create/update/wait`, `inbox send/receive`, `lifecycle check-zombies`, global `--json`/`--data-dir`; stop = `spawn --replace` or SIGTERM to `teams/<T>/spawn_registry.json` pids | subprocess calls; 23 command groups; `mcp<2` pin for the MCP server only | MIT | h to call; risk = flag drift only | TE-01/05/06/07, TC-04 roster, HB-04/06, EV-03 transport [ev:clawteam-probe-log#F2][ev:clawteam-probe-log#F20][ev:clawteam-probe-log#F21] |
| CT library seams (rung 2b): `get_backend/register_backend`, `SpawnBackend`, `TeamManager`, `FileTaskStore`, `MailboxManager`, `build_agent_prompt`, snapshot, `registry.stop_agent/is_agent_alive`, MCP server (26 tools), event bus/hooks, `session_capture.py` + `session_locators/*` | plain Python; "Alpha", no `__all__`; `mcp<2` pin needed | MIT | h to call; risk = API drift (no stability promise) | HB-08 in-process backend; HB-01 resume capability; same TE rows as 2a if a library route is chosen [ev:clawteam-spawn-platform#F15][ev:clawteam-spawn-platform#F18][ev:clawteam-spawn-platform#F19] |
| Hermes `hermes_cli/profile_distribution.py` (782 lines, `wc -l` on `~/.hermes/hermes-agent/hermes_cli/profile_distribution.py`) + `distribution.yaml`; kanban dispatcher argv (`kanban_db.py:10828-10905`) | Hermes-coupled; format/argv are data | MIT | pattern d; rung 1 for Hermes targets | AR-03, AR-04, EV-02 two-layer split; HB-02/LO-03 headless Hermes worker form [ev:claude-agent-teams-hermes-openbot#F24][ev:harness-cli-capabilities-b#F19] |
| DG `src/tools/{recipes.ts 122, storage-transaction.ts 42, run-history.ts 275, orchestration.ts 173}`, `types.ts`/`spec.ts` zod records; DT `src/state.ts` (882), `types.ts` (104) (line counts = `wc -l` on `dsh-agent-team-gui/src/tools/*.ts`, `dsh-agent-teams/src/{state,types}.ts`) | pure (DG: only a `KvTable` type; DT: node only) [ev:dsh-agent-teams-and-gui#F31] | MIT | d to re-express selected schema/mechanism ideas in Python/JSON Schema; no TypeScript vendoring into core | AR-03 export/import preview+rollback, TC-02 bounded handoffs, TE-06 plan validation, TE-07/HB-07 run records; TE-06/TE-07 JSONL mailbox, atomic write with Windows retry, archive-on-delete; a later native TypeScript edge package remains possible |
| ATM ADR 0022 + `schemas/{artifact-spec,artifact-lock,requirement-resolution,role-template,management-proposal,approval-record}` | strict JSON Schema | owner-authorized internal reuse; preserve provenance/third-party terms | d to adapt and audit provenance | AR-01…AR-06, EV-03/05, XC-02 [ev:atm-salvage#F10][ev:m0-product-architecture-review-2026-08-22#F7] |

## 5. Upstream-friendly extension candidates (HKUDS/ClawTeam)

Nine candidates, priced for `architecture-options.md` (its §5 "Deferred" list enumerates the same nine). Sizes include tests. Shared risk: no upstream commit since 2026-05-09, PRs #159/#165/#167 unanswered [ev:clawteam-spawn-platform#F24]; none is required — each has a rung-1/2 twin shown in its §2 row, and the interim rule is "layer-side sidecars by default; PRs filed as goodwill if the owner says so" (answers `team-execution-model.md` §13 Q2).

| # | PR | Content | Size | Closes (twin in §2) |
|---|---|---|---|---|
| 1 | Windows guard | `adapters.py:53` `os.getuid()` behind a platform check (PR #159, open, reports "os.getuid() is Unix-only"; a one-line form would be `hasattr(os,"getuid") and os.getuid()==0` — wording ours, not the PR's) | 1 line (+ test) | G-TE-08 (twin: `skip_permissions: false`, rung 1) [ev:clawteam-spawn-platform#F20] |
| 2 | Packaging pin | `mcp>=1,<2` in `pyproject.toml` | 1 line | `clawteam-mcp` startup (twin: pin in the layer's install step) [ev:clawteam-probe-log#F1] |
| 3 | Output + exit code | `~/.clawteam/logs/<team>/<agent>.log` instead of DEVNULL; read `CLAWTEAM_EXIT_CODE` in `lifecycle on-exit` | ~40–60 lines | G-TE-07, G-HB-07, G-XC-04 (twin: wrapper tee + exit code, rung 2) [ev:clawteam-probe-log#F14][ev:clawteam-spawn-platform#F21] |
| 4 | Parent-team linkage | `TeamConfig.created_by{team,agent}` + `spawn --parent-team` + `team discover --parent` | ~50–100 lines | G-TE-05 archive link (twin: parent link in the layer's run record) [ev:clawteam-model#F22][ev:clawteam-probe-log#F18] |
| 5 | Hermes/Grok adapter branches; system prompt for codex/grok | port CTF `is_hermes_command` (`chat -q --yolo --source tool`); Grok `--always-approve/--rules/-p`; Codex `-c developer_instructions=` | ~30–40 lines each | G-TE-03, G-HB-02 (twin: explicit per-Member argv, rung 1) [ev:clawteam-spawn-platform#F2][ev:harness-cli-capabilities-a#F18] |
| 6 | `launch` error surfacing + per-member profile + `TaskDef.blocked_by` | check `"Error"` results (PR #167), `AgentDef.profile`, DAG edges in templates | ~60–120 lines | G-TE-01, G-TE-06 (twin: never `launch`; per-Member `spawn` + `task create --blocked-by`, rung 1/2) [ev:clawteam-probe-log#F15][ev:clawteam-probe-log#F23] |
| 7 | `TeamMember.hidden` | field + `team status`/board filter | ~15–30 lines | G-TC-04, G-AD-07 (twin: layer-side visibility field + filtered roster, rung 6+2) [ev:clawteam-model#F1] |
| 8 | Cleanup semantics | `team cleanup` stops registered processes, archives instead of deleting; validate `--blocked-by` ids | ~30–50 lines | G-TE-05, G-TE-07, G-TE-06 (twin: wrapper stops before `cleanup`; ids validated by the layer) [ev:clawteam-probe-log#F20][ev:clawteam-probe-log#F7] |
| 9 | Inbox membership ACL | reject non-member recipients unless `--allow-external` | ~30 lines | G-TC-03 mechanical level (twin: advisory level by construction, rung 1) [ev:clawteam-model#F4] |
| — | *(superseded, not counted)* Pre-spawn mutation hook + plugin load in spawn path | emit `BeforeWorkerSpawn` on `spawn/launch/run` with `prompt`/`system_prompt`/`command` honoured after handlers; `PluginManager.load_all_from_config()` before `get_backend` | ~50–90 lines | G-HB-02, G-HB-08 from the CLI — needed only if the definition were injected *inside* ClawTeam; superseded when the caller renders the full argv before `spawn` (§2.4 G-TE-03, §2.5 G-HB-02) [ev:clawteam-spawn-platform#F16][ev:clawteam-spawn-platform#F17] |

## 6. Components that are new by evidence

No system offers these even partially (rung 6 in §2; the field-level rung-6 rows G-AD-03/05, G-EV-04, G-TC-03/04, G-XC-02 are fields on the objects of items 1, 2 and 4 — cite this list, not a count):

1. **Harness-neutral Assistant definition package** (persona/principles/preferences + capability/artifact vocabulary + harness policy + overlays; G-AD-01/02/04/09): every carrier is harness-native; grep negatives in ClawTeam, ATM, OpenClaw [ev:clawteam-model §3][ev:atm-salvage §3][ev:openclaw-native-and-telegram-verification §3].
2. **TeamTemplate composing portable Assistants by reference** with relationships, visibility, dynamic-member policy (G-TC-01/02/05/06): "TeamTemplate → 0" in Hermes, no pre-authorable team in Claude Code, DG DSH-bound [ev:claude-agent-teams-hermes-openbot §3][ev:claude-agent-teams-hermes-openbot#F4][ev:dsh-agent-teams-and-gui#F31].
3. **Overlay model + Proposal + review/provenance record** (G-EV-01/02/03/05): learning absent or ungated everywhere [ev:claude-agent-teams-hermes-openbot#F12][ev:claude-agent-teams-hermes-openbot#F28][ev:dsh-agent-teams-and-gui#F29].
4. **HarnessProfile/HarnessCapability model, user > Assistant > default policy, ensemble synthesis record, persisted HarnessInvocation** (G-HB-01/03/05/07): code-encoded knowledge only; no fan-out+synthesis; no cross-system record [ev:clawteam-spawn-platform#F12][ev:clawteam-probe-log#F14].
5. **Capability vs Artifact distinction, cross-harness artifact kinds, per-host resolution report, artifact lock/fingerprint** (G-AR-01/02/05/06): ATM idea only [ev:atm-salvage#F10]; no consumed lock anywhere.
6. **Nested-TeamRun glue** (parent link, result contract, enforced inner isolation, archive+cleanup; G-TE-05): no parent/child concept in CT, OC, HM, DT/DG [ev:clawteam-model §3][ev:dsh-agent-teams-and-gui#F14][ev:claude-agent-teams-hermes-openbot#F7].
7. **Job-level deterministic backends**, **declarative resume/fresh policy per Member** (G-LO-02/04); **Member↔visible-identity binding**, **TeamRun-presenting surface adapter** (G-MS-02/03; C/S priority).

## 7. Licence table

| System | Version evaluated | Licence (file) | Reuse permitted | Evidence |
|---|---|---|---|---|
| ClawTeam (CT) | 0.3.0 @ `0119833` (2026-05-09) | MIT — `LICENSE:1-5`, `pyproject.toml:7` | yes, attribution | [ev:clawteam-spawn-platform#F25] |
| ClawTeam-OpenClaw (CTF) | 0.3.0+openclaw2 @ `8dac3fc` | MIT — identical `LICENSE`; fork-only files unmarked | yes, attribution to HKUDS | [ev:clawteam-openclaw-fork-delta#F30][ev:clawteam-openclaw-fork-delta#F1] |
| OpenClaw (OC) + multi-agent-kit | 2026.7.1-2; kit @ `5d6418d` (2026-07-10) | MIT — `LICENSE`, `package.json`, npm; kit MIT — `openclaw-multi-agent-kit/LICENSE` (Raul Vidis 2026) | yes (`dist` only; V14: do not import plugin-sdk) | [ev:harness-cli-capabilities-b#F16][ev:openclaw-native-and-telegram-verification §4][ev:atm-salvage#F1] |
| Claude Code (CC) | 2.1.241 | proprietary — Commercial/Consumer terms | invocation/config only; owner-operated native runs use subscription OAuth | [ev:m0-product-architecture-review-2026-08-22#F1][ev:m0-product-architecture-review-2026-08-22#F2] |
| Codex CLI (CX) | 0.149.0 | Apache-2.0 — github.com/openai/codex README; LICENSE file unfetched | source reuse pending file check; native owner-host runs use ChatGPT login | [ev:m0-product-architecture-review-2026-08-22#F1][ev:m0-product-architecture-review-2026-08-22#F2] |
| Grok CLI | 1.0.5 | Apache-2.0 first-party, github.com/xai-org/grok-build (web, accessed 2026-08-21); "External contributions are not accepted" | invocation; ToS 403 | [ev:harness-cli-capabilities-a §4][ev:harness-cli-capabilities-a#F14] |
| Hermes (HM) | 0.20.4 (git `a9a4a04`) | MIT — `LICENSE:1-3`, `pyproject.toml:17` | yes | [ev:harness-cli-capabilities-b#F22][ev:claude-agent-teams-hermes-openbot#F21] |
| dsh-agent-teams / dsh-agent-team-gui | 0.1.8 / 1.0.0 | MIT — `LICENSE` each; DSH MIT (web, accessed 2026-08-22) | yes (pure modules) | [ev:dsh-agent-teams-and-gui §4][ev:dsh-agent-teams-and-gui#F32] |
| OpenBot (OB) | @ `6c365f4` | MIT — `LICENSE` (CopilotKit 2026) | yes (ideas) | [ev:claude-agent-teams-hermes-openbot §4] |
| ATM | `agent-team-manager-dev@12a727e` (0.0.0, private) | no public licence; **owner-authorized internal AgentTeam reuse** | copy/adapt allowed inside this project; preserve source provenance and third-party notices; no public relicensing implied | [ev:m0-product-architecture-review-2026-08-22#F7] |
| Agent Skills spec | agentskills.io (web, re-verified 2026-08-22) | public specification | format reuse | [ev:atm-salvage#F8] |

## 8. Mapping to substrates

Primitive per substrate at rung 1–4, or "no primitive — new".

| Concept | ClawTeam | Claude Code / Codex | OpenClaw | Hermes | dsh (DT/DG) | Verdict |
|---|---|---|---|---|---|---|
| Assistant definition (neutral) | `AgentDef.task` string (render target) | `.claude/agents/*.md`, `--agents` / `.codex/agents/*.toml` (render targets) | workspace `SOUL.md`/`AGENTS.md` (render target) | profile `SOUL.md` + `distribution.yaml` (render target) | DG `AgentRecord` (schema idea) | no primitive — new; materialization rung 1–2 |
| Ephemeral Assistant | `spawn` (no persona slot) | `--agents` JSON, background subagent / agents file | `sessions_spawn` (no SOUL for sub-agents) | `delegate_task`, `--source tool` | DT `add_member` | mechanism rung 1; hidden = layer-side visibility field (6) + filtered roster (2); CT flag rung 3 optional |
| TeamTemplate | TOML template (persona inline, no reference) | none (no pre-authored team) | none | kanban `swarm` roster (one-shot) | DG `SquadRecord` (DSH-bound) | no primitive — new; render to CT TOML rung 2 |
| TeamRun (fresh) | `launch`/`spawn` + data dir | session team (interactive only) / `multi_agent` `?` | agent session tree | kanban board run | DT team dir / DG run | rung 1 (CT best-probed; HM Hermes-only) |
| Nested TeamRun | inner team by composition (no link) | subagent depth ≤3 (no team) / `?` | `maxSpawnDepth` tree | `max_spawn_depth` tree; kanban `--parent` | prohibited | glue new; composition rung 2 |
| HarnessProfile; SelectionPolicy / Broker | adapter chain (code); per-agent `command` + profiles | `--help` facts; `--fallback-model` / `-p profile` | acpx alias registry; `runtime.acp`, `acp.fallbacks` `?` | `--help` facts; `hermes fallback`, MoA | DG route + fallback route | no primitive — new; seeds rung 1/4; fan-out rung 2 |
| HarnessInvocation record | registry + self-reported cost | `-p` json cost / rollout tokens | `audit` (in-gateway) | `--usage-file`, kanban runs | DG run record | emission rung 1; record new |
| Overlay / Proposal / review; Capability vs Artifact; lock | plan approval round-trip (transport); `--skill` inline, `skills-lock.json` (ClawTeam/skills-lock.json:1-10 — source+hash, no version/ref, no in-repo reader) | `memory` file (silent); plugins / skills+MCP | memory hooks; skills `requires`, eligibility | distribution vs user paths, curator ledger; `env_requires`, distribution version | DG versions/retrospective; recipe routes | no primitive — new (ATM idea for artifacts) |
| Deterministic backend; surfaces | `spawn subprocess -- <exe>` (mislabelled); — | hooks/monitors; channels (preview) / hooks | cron `--command`; `identity`, bindings | cron `?`; gateway + profile routes | — | rung 1–2; Member binding new |

## 9. What is new vs borrowed

| Concept | Borrowed from (system + mechanism) | New |
|---|---|---|
| Definition materialization; fresh-by-default | CC flags/agent files/`--safe-mode --no-session-persistence`; Grok flags/isolated state; CX config override/`--ephemeral`; OC workspace/session keys; HM profile; CT task/skill channels; DG strict schemas | renderer contract; schema rule |
| Harness-neutral Assistant definition; capability/artifact vocabulary | shape ideas: HM `distribution.yaml`, DG `AgentRecord`, kit SOUL/IDENTITY split, Agent Skills name, ATM role-template/ADR 0022 | **new** |
| Harness policy / precedence | CTF `model_resolution.py` pattern; OC `model.fallbacks` | **new** (user > Assistant > default) |
| Overlays + Proposal + review | HM ownership split; CT plan-approval transport; HM ledger; DG versions/import preview; ATM MAC'd decisions | **new** |
| TeamTemplate by reference; relationships; dynamic-member policy; reviewer independence | CT TOML (render target); DG `SquadRecord`, `contextMode`, DG/kit handoffs; OC `subagents.*`, HM/DT caps; separate invocations (CT/HM/CC) | **new** template object and fields |
| TeamRun instantiation, DAG, inbox, archive; nested TeamRun; Windows path | CT `spawn/task/inbox/snapshot` + composition path (never `launch`); HM kanban (`--parent`); DG runs; OC/HM/CC trees; CT `skip_permissions: false` config, CTF `platform_compat.py` (optional), PR #159 guard (optional) | output/exit-code capture; run record; nesting glue (parent link, result contract, isolation, cleanup) |
| HarnessProfile; fallback; ensemble; invocation record | CT adapter chain + locators, evidence checklists, ATM query names; CTF `spawn_with_retry`, native model fallbacks; CT/DC fan-out; CC/HM/Grok/CX emissions, OC audit | **new** data model, synthesis record, persisted record |
| Artifact model, lock, resolution report | OC eligibility report; HM `env_requires`/distribution; CT `profile test`; ATM schemas (idea) | **new** |
| Deterministic backends / schedulers; surfaces / identity | OC cron `--command`, OS schedulers, CT leader watcher; HM gateway, OC channels+`identity`, CC channels | job-level watchers (domain); Member binding; TeamRun-presenting adapter |

## 10. Open questions and resolved review items

1. Will HKUDS/ClawTeam accept any rung-3 PR (no commit since 2026-05-09)? This is the decision `team-execution-model.md` §13 Q2 delegates here (`created_by`, `visibility`, process-stopping cleanup: upstream or sidecar). Interim rule: layer-side sidecars by default (every §5 item has its rung-1/2 twin in §2); the PRs are filed as goodwill only if the owner says so. Open: whether to file at all. [ev:clawteam-spawn-platform#F24]
2. ATM internal reuse is resolved by owner authorization. AgentTeam's MIT choice does not retroactively relicense ATM; copied/adapted material still needs provenance and third-party-obligation review [ev:m0-product-architecture-review-2026-08-22#F7].
3. Is `codex exec -c developer_instructions=…` honoured on 0.149.0 (G-HB-02 `?`)? Decides rung 1 vs a temp-`AGENTS.md` workaround [ev:harness-cli-capabilities-a#F2].
4. OpenClaw `acpx` path (`runtime.acp`, `acp.fallbacks`, custom Hermes alias): rung 1 for HB-03/04/08 only if a disposable-profile probe confirms it [ev:openclaw-native-and-telegram-verification#F16]; likewise Hermes `--source tool` hiding on 0.20.4 (G-TC-04) [ev:clawteam-openclaw-fork-delta §5].
5. Implementation language is resolved: Python 3.11+ with `uv`. DG/DT TypeScript modules are evidence and schema/mechanism ideas, not code vendored into the core; a small native TypeScript adapter may be added later if DSH becomes a primary harness.
6. Cross-platform disposition is resolved: future GitHub-hosted Windows/macOS jobs verify deterministic direct-path plumbing and, separately, the optional ClawTeam import/coordination seam, without live credentials or live-behavior claims. AgentTeam does not adopt ClawTeam's subprocess backend. Remaining evidence question: who writes ClawTeam's `skills-lock.json`? The file exists — `ClawTeam/skills-lock.json:1-10` (`{"version":1,"skills":{"frontend-design":{"source":"anthropics/skills","sourceType":"github","computedHash":"063a0e…"}}}`; source + hash, no version/ref; no reader in `clawteam/` — `grep -rl skills-lock` over `*.py|*.md|*.toml` → the file only; added in commit `4dac180`) — so only the writer is open; until known it is a shape precedent for G-AR-06, not a reusable mechanism [ev:m0-product-architecture-review-2026-08-22#F5].

## 11. Inconsistencies noted

- (resolved in the W3 owner pass) Fit-gap G-AR-06 now cites `ClawTeam/skills-lock.json:1-10` directly; only the writer of that file is unverified.
- (resolved in the W3 fix pass) Fit-gap TC-04 now gives HM `C?~` for `--source tool` (storage behaviour on 0.20.4 unprobed, [ev:clawteam-openclaw-fork-delta §5]); §2.3 marks the rung-1 option `?` accordingly.
- Fit-gap TE-08 "best: CTF C!" rests on docs + `platform_compat.py`; [ev:clawteam-openclaw-fork-delta#F6] shows the fork's subprocess+OpenClaw argv is flag-mismatched, so the CTF advantage holds for non-OpenClaw workers only; "C!" is not a verified Windows path.
- No other cell is contradicted; `?`-suffixed OC cells (HB-03/04/08) stay `?`.

---

STOP — §4–§5 are candidates priced for `architecture-options.md`; no task is authorised here, and the smallest-layer answer is stated only there. Discovery STOPs after `architecture-options.md` for product/architecture review.
