---
title: Reuse-vs-build analysis — cheapest reuse rung per gap
status: draft
date: 2026-08-22
owns: per-gap cheapest reuse rung (source, licence, cost/risk, platform); fork-only feature classification; selective-reuse modules; upstream-friendly extension candidates; components new by evidence; licence table
depends_on: product-intent.md (register), existing-systems-fit-gap.md (G-ids, cells), evidence/*.md; consumed by architecture-options.md (which alone states the smallest-layer answer)
---

# Reuse-vs-build analysis

> Reading guide: for every gap `G-*` in `existing-systems-fit-gap.md` §"Consolidated gap list" this document names the **cheapest rung** on the reuse ladder (XC-03) that closes it, a candidate source, its licence (XC-01), cost/risk and a platform note (XC-02). It never ranks architecture options and never says which layer to build — that is `architecture-options.md`. Requirements are cited by ID from `product-intent.md` §3.

## 1. Method

**Ladder.** 1 configuration/composition · 2 thin adapter (wrapper over existing CLIs/seams, unchanged) · 3 upstream-friendly extension (bounded PR) · 4 selective licensed module reuse · 5 fork only when necessary · 6 new implementation only if nothing else satisfies. The bold rung per gap is the **lowest rung at which the requirement is actually satisfied**, not the lowest at which something related exists; when a gap splits into a borrowed mechanism and a new object, all rungs are listed ("**6** object; 1 to materialize").

**Evidence standard.** Claims cite `[ev:<file>#Fn]` or `Repo/path:line`; fit-gap cells are taken as given (disagreements only in §"Inconsistencies noted"); a rung resting on an unverified cell carries `?`.

**Cost** (borrow/adapt step only): `h` hours · `d` ≤5 working days · `w` 1–4 weeks. **Risk** `low|med|high (factor)` — *merge*: rung 3 depends on HKUDS/ClawTeam (no commit since 2026-05-09, 22 open PRs [ev:clawteam-spawn-platform#F24]); rung 2 on seams without a stability promise ("Alpha", no `__all__` [ev:clawteam-spawn-platform#F15]); fork backends bypass `adapter.prepare_command` (5 `xfail`) [ev:clawteam-openclaw-fork-delta#F27]. *platform*: tmux, Gateway daemon, POSIX-only shell, Windows untested (no Windows CI in CT/CTF/DT/DG [ev:clawteam-spawn-platform#F20][ev:dsh-agent-teams-and-gui §4]). *verif.*: enabling cell is `~`/`?`. **Platform**: needs on Ubuntu (this host, no tmux), macOS, Windows; "any" = pure data. Licences: MIT · Apache · prop. (Claude Code, invocation only) · none (ATM; ideas citable, text not copyable until licensed).

## 2. Per-gap table

### 2.1 AD — Assistant definition

| Gap (= Req) · P | Best existing | Rung | Candidate source (licence) | Cost, risk, platform | Evidence |
|---|---|---|---|---|---|
| G-AD-01 (M) | HM S! | **6** neutral object; 1 to materialize | shape ideas: Hermes `distribution.yaml`+`SOUL.md`, DG `AgentRecord`, kit SOUL/IDENTITY/AGENTS split (MIT); ATM role-template (none) | d, low, any | [ev:claude-agent-teams-hermes-openbot#F24][ev:dsh-agent-teams-and-gui#F18] |
| G-AD-02 (M) | CT Xs!; ATM idea | **6** vocabulary; 1 Agent Skills name; 3 fields on CT `AgentDef` | Agent Skills spec (public); ADR 0022 `requires.capabilities/artifacts` (none) | d, low, any | [ev:atm-salvage#F8][ev:atm-salvage#F10] |
| G-AD-03 (S) | DG S! | **1** permissions via harness flags; 4 collaboration-schema ideas; escalation = new field | CC `--permission-mode`, CX `--sandbox`, Grok `--allow/--deny`, HM `--yolo`, OC `tools.allow/deny` (prop./Apache/MIT); DG `qualityGate`/handoff, kit HANDOFF/ACK/DONE/BLOCKED (MIT) | d, low, any | [ev:harness-cli-capabilities-a#F11][ev:dsh-agent-teams-and-gui#F25] |
| G-AD-04 (M) | OC C! | **6** policy object; 4 precedence-chain pattern | CTF `model_resolution.py` (70 lines, stdlib; MIT); OC `model{primary,fallbacks}` | d, low, any | [ev:clawteam-openclaw-fork-delta#F15][ev:clawteam-openclaw-fork-delta#F28] |
| G-AD-05 (M) | DG S! | **1** run-side isolation knobs + strict schema on the new object | CC `--bare`; CX `--ephemeral`/`CODEX_HOME`; Grok `GROK_HOME`; HM fresh profile/`--ignore-rules`; OC `--profile`/session key; DG `.strict()` | h, low, any | [ev:harness-cli-capabilities-a#F19][ev:harness-cli-capabilities-b#F24] |
| G-AD-06 (C) | OC S! | **1** | OC `agents.list[].identity{name,emoji,avatar,theme}`, `set-identity --from-identity` (MIT); Member binding → G-MS-03 | h, low, OC (Gateway for channels) | [ev:openclaw-native-and-telegram-verification#F3] |
| G-AD-07 (M) | HM S! | **1** spawn mechanism; 3 hidden flag (G-TC-04); object = G-AD-01 | HM `delegate_task`/`--source tool`; CC `--agents` + background subagents; OC `sessions_spawn`; CT `spawn` (MIT/prop.) | d, med (merge), OC needs Gateway | [ev:claude-agent-teams-hermes-openbot#F22][ev:harness-cli-capabilities-b#F12] |
| G-AD-08 (M) | DG S! | **2** renderer from one definition into each harness format | CC `.claude/agents/*.md`/`--agents`; HM profile `SOUL.md`; OC workspace files; CT `AgentDef.task`/`--skill` | d/harness, med (flag drift), any | [ev:harness-cli-capabilities-a#F17][ev:harness-cli-capabilities-b#F24] |
| G-AD-09 (M) | OC S! | **6** composite (with G-AD-01); 1 inside each harness; harness composition = G-HB-05 | as G-AD-08 | —, low, any | [ev:harness-cli-capabilities-b#F9][ev:clawteam-model#F15] |

### 2.2 EV — Evolution

| Gap (= Req) · P | Best existing | Rung | Candidate source (licence) | Cost, risk, platform | Evidence |
|---|---|---|---|---|---|
| G-EV-01 (M) | HM Xs! | **6** project-independence filter; 1 interception point `?` | HM `pre_tool_call` hooks/curator ledger; CC `PreToolUse`; OC `session-memory` hook (MIT/prop.) | d, med (verif.), any | [ev:claude-agent-teams-hermes-openbot#F28][ev:harness-cli-capabilities-b#F21] |
| G-EV-02 (M) | HM Xs! | **6** 3-layer merge/conflict rules; borrow the 2-layer ownership split | HM distribution-owned vs user-owned paths; CT whole-file override (MIT) | d, low, any | [ev:claude-agent-teams-hermes-openbot#F24][ev:clawteam-probe-log#F4] |
| G-EV-03 (M) | DG Xs!; ATM idea | **6** Proposal object; 2 approval transport | CT `plan_submit/approve/reject` (MCP + messages + `plans/`) (MIT); DG retrospective text; ATM typed proposal (none) | d, low, CT file-based | [ev:clawteam-model#F17][ev:clawteam-model#F21] |
| G-EV-04 (M) | HM S! | **1** + schema rule | G-AD-05 knobs; HM export hard-excludes `memories/ sessions/ .env` (MIT) | h, low, any | [ev:claude-agent-teams-hermes-openbot#F24][ev:harness-cli-capabilities-a#F19] |
| G-EV-05 (S) | DG Xs!; ATM idea | **6** review workflow with provenance; 4 ledger/version/preview patterns | HM curator `ledger`; DG `squad_versions`, import preview, `StorageUnitOfWork` (MIT); ATM MAC'd decision + plan-hash (none) | d–w, low, any | [ev:claude-agent-teams-hermes-openbot#F28][ev:dsh-agent-teams-and-gui#F20] |
| G-XC-03 (M) | HM C! | meta: 1 materialize into OC/HM/CC/CX/Grok; 2/4 render into CT templates / lift DG schemas; **6** three new objects | rows above | — | fit-gap §XC-03 |

### 2.3 TC — Team composition

| Gap (= Req) · P | Best existing | Rung | Candidate source (licence) | Cost, risk, platform | Evidence |
|---|---|---|---|---|---|
| G-TC-01 (M) | DG S! | **6** template object; 2 render into CT TOML for execution; 4 schema idea | CT `~/.clawteam/templates/*.toml` (`leader/agents[]/tasks[]`, per-agent `command`); DG `SquadRecord→AgentRecord` (MIT) | d, low, CT file-based | [ev:clawteam-probe-log#F4][ev:clawteam-model#F13] |
| G-TC-02 (M) | DG S!; CT C! | **6** relationship/handoff fields (small); 1 lead via CT `template.leader`; 4 schema ideas | DG `executionOrder/contextMode/qualityGate`, bounded `SquadMemberHandoff`; kit handoff standard (MIT); ATM `topology.allow` (none) | d, low, any | [ev:dsh-agent-teams-and-gui#F24][ev:openclaw-native-and-telegram-verification#F5] |
| G-TC-03 (S) | DG C!; OC C! | **1** by construction (reviewer = own HarnessInvocation, fresh context, no inbox); 3 CT inbox ACL; 6 enforcement-level field | CT subprocess workers; HM profiles; CC `isolation: worktree`; DG `contextMode=spawn` (MIT); ATM ADR 0026 (none) | d, med (merge for ACL), any | [ev:clawteam-model#F4][ev:dsh-agent-teams-and-gui#F25] |
| G-TC-04 (S) | HM C! | **3** `TeamMember.hidden` + board filter on CT; 1 HM `--source tool` (Hermes-only `?`) | CT `team/models.py:65-87`; HM `chat --source tool` (MIT) | d, med (merge; HM unverified), any | [ev:clawteam-model#F1][ev:harness-cli-capabilities-b#F6] |
| G-TC-05 (M) | OC C! | **6** policy fields; 2 enforce in the caller before `spawn`; 1 inside OC/HM/DT | OC `subagents.{maxSpawnDepth,maxChildrenPerAgent,allowAgents}`; HM `delegation.max_spawn_depth`; DT `maxMembers/memberMaxDepth` (MIT); ATM `spawn{intraRole,maxDepth}` (none) | d, low, OC Gateway, others none | [ev:openclaw-native-and-telegram-verification#F21][ev:claude-agent-teams-hermes-openbot#F22] |
| G-TC-06 (M) | DG S!; CT C! | **6** team-preference field (small); 1 harness/backend keys in CT template | CT `TemplateDef.command/backend`; DG record (MIT) | h, low, any | [ev:clawteam-probe-log#F4][ev:dsh-agent-teams-and-gui#F18] |

### 2.4 TE — Team execution

| Gap (= Req) · P | Best existing | Rung | Candidate source (licence) | Cost, risk, platform | Evidence |
|---|---|---|---|---|---|
| G-TE-01 (M) | CT S! | **1** CT `launch`/`spawn`; 3 surface spawn failures (PR #167) + `TaskDef.blocked_by`, or 2 wrapper checking `"Error"` per member; alt 1 HM `kanban create` (Hermes-only) | CT `commands.py:4034-4215`; HM kanban (MIT) | d, med (merge), CT subprocess any OS; HM kanban needs gateway | [ev:clawteam-probe-log#F15][ev:clawteam-probe-log#F23] |
| G-TE-02 (M) | CT S! | **1** (CT/CC/CX/DC fresh; OC session key; HM fresh profile); 3 CTF `OPENCLAW_WORKSPACE`→`_DIR` fix | CT `--session-id` per spawn, opt-in `--resume`; G-AD-05 knobs | h, low, any | [ev:clawteam-spawn-platform#F19][ev:harness-cli-capabilities-b#F4] |
| G-TE-03 (M) | CT C! | **1** per-agent `command`; 2 in-process custom backend (`register_backend`) for Hermes/Grok argv; or 3 adapter branches | CT `spawn/__init__.py:10-29`, `AgentDef.command`; CTF `adapters.py:64-82` (MIT) | d, med (merge/API), subprocess any OS | [ev:clawteam-probe-log#F16][ev:clawteam-spawn-platform#F17] |
| G-TE-04 (M) | OC S! | **1** spawn (CT/OC/CC/HM); 3 hidden flag (G-TC-04); OC sub-agent persona only as `--message-file` prefix | as G-AD-07 | d, med (merge), OC Gateway, others none | [ev:openclaw-native-and-telegram-verification#F14][ev:clawteam-model#F1] |
| G-TE-05 (M) | CT P! | **2** wrapper over CT seams (`spawn-team B -n <self>`→`spawn --team B`→`task wait B --agent <self>`→`inbox receive B`→`snapshot`→`stop_agent`→`cleanup`); 3 `TeamConfig.created_by` parent link; 6 result-contract/isolation record | CT `manager.py`, `waiter.py`, `snapshot.py`, `registry.py` (MIT); HM kanban `--parent` (links only) | d–w, med (merge/API), CT file-based, no tmux | [ev:clawteam-model#F22][ev:clawteam-probe-log#F18] |
| G-TE-06 (S) | CT S! | **1** CT DAG/inbox/watcher; 3 `--blocked-by` validation + liveness column (CTF has it); alt 1 HM kanban, DG (DSH) | CT `store/file.py`, `mailbox.py`, `leader_watcher.py`; CTF `commands.py:1598-1629` (MIT) | h–d, low, any (CT); HM gateway | [ev:clawteam-probe-log#F7][ev:clawteam-probe-log#F10] |
| G-TE-07 (M) | DG S!; CT P! | **2** caller captures stdout/exit code and writes the run record; 1 CT snapshot/events/registry + harness transcripts; 3 logs dir + read `CLAWTEAM_EXIT_CODE` (PR #159) | CT `snapshot.py:123-183`, `session_locators/*`; CTF last-80-lines capture (MIT) | d, med (merge), any | [ev:clawteam-spawn-platform#F21][ev:clawteam-probe-log#F14] |
| G-TE-08 (M) | CTF C! | **3** one-line `os.getuid` guard (PR #159 open) + 4 CTF `platform_compat.py`; 1 harness CLIs on Windows (docs `~`) | CT `adapters.py:53`; CTF `platform_compat.py` (130 lines) (MIT) | h–d, high (platform: no Windows CI anywhere), Windows = subprocess only | [ev:clawteam-spawn-platform#F20][ev:clawteam-openclaw-fork-delta#F19] |
| G-XC-02 (M) | OC S! | **6** two independent dimensions in the HarnessProfile (tiny); 1 OC docs/`requires`; ATM `compatibility{runtimes,platforms}` idea | OC skills `metadata.openclaw.requires` (MIT); ADR 0022 (none) | h, low, any | [ev:harness-cli-capabilities-b#F11][ev:atm-salvage#F10] |

### 2.5 HB — Harness brokerage

| Gap (= Req) · P | Best existing | Rung | Candidate source (licence) | Cost, risk, platform | Evidence |
|---|---|---|---|---|---|
| G-HB-01 (M) | CT Xs! | **6** data model; 4 extract flag knowledge from CT adapters/keepalive/locators; 1 seed from evidence checklists | CT `adapters.py:49-140`, `keepalive.py:11-35`, `session_locators/*` (MIT); ATM adapter-contract query names (none) | d, low, any | [ev:clawteam-spawn-platform#F1][ev:harness-cli-capabilities-a#F16] |
| G-HB-02 (M) | CC S! | **1** per-harness channels; 2 renderer; CT's system-prompt drop for non-claude avoided by rung-2 backend or fixed at 3 (~20 lines) | CC `--append-system-prompt[-file]`, `--add-dir`, `--mcp-config`; Grok `--rules`; CX `-c developer_instructions` `?`; OC per-run workspace; HM `SOUL.md`/env overlay | d, med (CX verif.), any | [ev:harness-cli-capabilities-a#F17][ev:harness-cli-capabilities-b#F24] |
| G-HB-03 (M) | OC C?~; CT Xs! | **6** user>role>default policy; 4 CTF `model_resolution.py` pattern; 1 pass the resolved command to CT `spawn` | CTF `model_resolution.py:29-70`; CT command precedence (MIT) | d, low, any | [ev:clawteam-openclaw-fork-delta#F15][ev:clawteam-probe-log#F17] |
| G-HB-04 (S) | OC C?~; CT/DC P! | **2** caller retries with the next harness; 4 CTF `spawn_with_retry` backoff; 1 model-level fallbacks | CTF `spawn/__init__.py:46-70`; CT `--replace`; CC `--fallback-model`, OC `model.fallbacks`, HM `hermes fallback` (MIT/prop.) | h–d, low, any | [ev:clawteam-openclaw-fork-delta#F13][ev:clawteam-probe-log#F21] |
| G-HB-05 (M) | CT P!; DC | **2** fan-out (N invocations); 6 synthesis record with per-harness attribution; synthesis step = one more invocation (1) | CT template with N commands; DC scripts; CC workflows, HM MoA (same-runtime precedents) | d, low, any | [ev:clawteam-probe-log#F16][ev:harness-cli-capabilities-a#F10] |
| G-HB-06 (S) | OC S! | **1** OC cron `--command`/hooks; 2 caller invokes the executable directly (avoids CT's `-p` append and DEVNULL) | OC `cron add --command`; CC hooks/monitors `?`; CT `spawn subprocess -- <exe>` | h, low, OC Gateway; direct call any | [ev:openclaw-native-and-telegram-verification#F9][ev:clawteam-probe-log#F12] |
| G-HB-07 (S) | CC S! | **6** persisted record (no substrate writes one for an external CLI); 1 emission; 3 fields on CT `CostEvent`/registry | CC `-p --output-format json`; HM `-z --usage-file`; Grok json; CX `--json` tokens; OC `audit` | d, low, any | [ev:harness-cli-capabilities-a#F10][ev:harness-cli-capabilities-b#F7] |
| G-HB-08 (S) | OC C?~; CT Xs! | **2** CT `register_backend` in-process; 3 plugin load on the `spawn` path (~10 lines); OC acpx alias `?` (no Hermes alias) | CT `spawn/__init__.py:10-29`, `plugins/manager.py` (MIT); OC `agents.list[].runtime.acp` | h–d, med (API), any | [ev:clawteam-spawn-platform#F8][ev:clawteam-spawn-platform#F17] |

### 2.6 AR — Artifact / dependency

| Gap (= Req) · P | Best existing | Rung | Candidate source (licence) | Cost, risk, platform | Evidence |
|---|---|---|---|---|---|
| G-AR-01 (M) | — | **6** | ADR 0022 `requires.capabilities[]` vs `requires.artifacts[]` (none) | d, low, any | [ev:atm-salvage#F10] |
| G-AR-02 (M) | OC S! | **6** cross-harness kind enum + "capability package" (small); 1 per-ecosystem kinds | OC skills/plugins/`requires.bins`; CC plugins; HM skills/distributions; CX skills/MCP | h, low, any | [ev:harness-cli-capabilities-b#F11][ev:claude-agent-teams-hermes-openbot#F14] |
| G-AR-03 (M) | HM S! | **4** patterns + 6 cross-harness manifest; 1 for Hermes targets | HM `distribution.yaml`, `profile install|export|import`; DG `recipes.ts` + strict import preview (MIT); ATM export-manifest (none) | d–w, low, any | [ev:claude-agent-teams-hermes-openbot#F24][ev:dsh-agent-teams-and-gui#F20] |
| G-AR-04 (M) | HM S! | **1** env-name references — do **not** borrow CTF gateway-token propagation | OC SecretRef; HM `env_requires`; DG `.strict()` (MIT) | h, low, any | [ev:atm-salvage#F1][ev:claude-agent-teams-hermes-openbot#F24] |
| G-AR-05 (S) | OC S! | **6** per-capability report (small); 1 inputs | OC `skills list --json` eligibility; HM `env_requires`; CT `profile test` (MIT); ATM outcome vocabulary (none) | d, low, any | [ev:harness-cli-capabilities-b#F11][ev:atm-salvage#F7] |
| G-AR-06 (S) | — | **6** lock + fingerprint | ATM `ArtifactLock` (none); HM distribution `version` (no hash/ref), curator ledger (skills only) (MIT) | d, low, any | [ev:atm-salvage#F10][ev:claude-agent-teams-hermes-openbot#F24] |
| G-XC-01 (M) | CT S! | **1** verified (§7); ATM needs an owner licence statement | — | h, low | fit-gap §XC-01 |

### 2.7 MS — Messaging / surface

| Gap (= Req) · P | Best existing | Rung | Candidate source (licence) | Cost, risk, platform | Evidence |
|---|---|---|---|---|---|
| G-MS-01 (M) | CT S! | **1** (CT file-based; CC/CX/DC in-process; OC `agent --local`/HM `chat -q` as daemon-free workers) | — | —, low, no daemon on any OS | [ev:clawteam-probe-log#F2][ev:harness-cli-capabilities-b#F1] |
| G-MS-02 (C) | HM S! | **2** thin adapter presenting a TeamRun/Member over HM `hermes send --to`, OC `agent --deliver`, CC channels | HM gateway (20+ platforms); OC channels; CC channel plugins (MIT/prop.) | w, med (platform: daemons), daemon per surface | [ev:claude-agent-teams-hermes-openbot#F26][ev:openclaw-native-and-telegram-verification#F19] |
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

**Reading across (primary rungs, 54 gaps).** Rung 1: 20 · rung 2: 7 · rung 3: 2 (G-TC-04, G-TE-08) · rung 4: 1 (G-AR-03) · rung 5: 0 · rung 6: 23 · meta: 1. Rung 5 is never cheapest; rung 3 is never the only path (every ClawTeam fix has a rung-2 equivalent, which matters given merge risk). Most rung-6 items are data objects (definition, template fields, policy, records, lock, Proposal), not runtime machinery; how they group is for `architecture-options.md`.

## 3. ClawTeam-OpenClaw fork-only features classified

From [ev:clawteam-openclaw-fork-delta#F34] (112 fork-only commits, 88 files [ev:clawteam-openclaw-fork-delta#F2]; both trees MIT [ev:clawteam-openclaw-fork-delta#F30]).

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
| CTF `clawteam/model_resolution.py` (70 lines) | none (stdlib) [ev:clawteam-openclaw-fork-delta#F28] | MIT (no SPDX header; attribute HKUDS) | h vendor; d to re-model precedence user>role>default | HB-03, AD-04 pattern |
| CTF `clawteam/platform_compat.py` (130 lines) | stdlib [ev:clawteam-openclaw-fork-delta#F19] | MIT | h | TE-08, XC-02 (Windows default backend, file lock, `pid_alive`, `shell_join`) |
| CTF `spawn_with_retry` (25 lines); `subprocess_wrapper.py` (66); idempotency keys | protocol only; 1 helper + shells out to `lifecycle on-exit`; keys coupled to CT models | MIT | h–d; keys via upstream PR | HB-04, TE-06; LO-04/TE-07 exit hook without `shell=True`; XC-04 [ev:clawteam-openclaw-fork-delta#F13] |
| CTF `spawn/respawn.py` (86); `registry.py` health block (~130) | coupled to registry/TeamManager; partial | MIT | d (rewrite against own records) | LO-04 patterns [ev:clawteam-openclaw-fork-delta#F11][ev:clawteam-openclaw-fork-delta#F12] |
| CTF Hermes adapter (`adapters.py:64-82,242`; `command_validation.py:368-385`; `skills/hermes/SKILL.md` 262 lines) | inside the adapter chain | MIT (SKILL.md `license: MIT`) | d to port upstream or into a HarnessProfile | HB-08, HB-01, TE-03 [ev:clawteam-openclaw-fork-delta#F14] |
| CT seams used in place (rung 2): `get_backend/register_backend`, `SpawnBackend`, `TeamManager`, `FileTaskStore`, `MailboxManager`, `build_agent_prompt`, snapshot, `registry.stop_agent/is_agent_alive`, MCP server (26 tools), event bus/hooks, `session_capture.py` + `session_locators/*` | plain Python; "Alpha", no `__all__`; `mcp<2` pin needed | MIT | h to call; risk = API drift | TE-01/05/06/07, HB-08, EV-03 transport, HB-01 resume capability [ev:clawteam-spawn-platform#F15][ev:clawteam-spawn-platform#F18][ev:clawteam-spawn-platform#F19] |
| Hermes `hermes_cli/profile_distribution.py` (782 lines) + `distribution.yaml`; kanban dispatcher argv (`kanban_db.py:10828-10905`) | Hermes-coupled; format/argv are data | MIT | pattern d; rung 1 for Hermes targets | AR-03, AR-04, EV-02 two-layer split; HB-02/LO-03 headless Hermes worker form [ev:claude-agent-teams-hermes-openbot#F24][ev:harness-cli-capabilities-b#F19] |
| DG `src/tools/{recipes.ts 122, storage-transaction.ts 42, run-history.ts 275, orchestration.ts 173}`, `types.ts`/`spec.ts` zod records; DT `src/state.ts` (882), `types.ts` (104) | pure (DG: only a `KvTable` type; DT: node only) [ev:dsh-agent-teams-and-gui#F31] | MIT | d (TypeScript; language TBD) | AR-03 export/import preview+rollback, TC-02 bounded handoffs, TE-06 plan validation, TE-07/HB-07 run records; TE-06/TE-07 JSONL mailbox, atomic write with Windows retry, archive-on-delete |
| ATM ADR 0022 + `schemas/{artifact-spec,artifact-lock,requirement-resolution,role-template,management-proposal,approval-record}` | strict JSON Schema | **none declared** — ideas only | d once licensed | AR-01…AR-06, EV-03/05, XC-02 [ev:atm-salvage#F10][ev:atm-salvage#F11] |

## 5. Upstream-friendly extension candidates (HKUDS/ClawTeam)

Sizes include tests. Shared risk: no upstream commit since 2026-05-09, PRs #159/#165/#167 unanswered [ev:clawteam-spawn-platform#F24]; each item has a rung-2 fallback (§2).

| PR | Content | Size | Closes |
|---|---|---|---|
| Windows guard; packaging pin | `adapters.py:53` `os.getuid()` → `hasattr(os,"getuid") and os.getuid()==0` (PR #159 proposes); `mcp>=1,<2` in `pyproject.toml` | 1 line each (+ test) | G-TE-08; `clawteam-mcp` startup [ev:clawteam-spawn-platform#F20][ev:clawteam-probe-log#F1] |
| Output + exit code | `~/.clawteam/logs/<team>/<agent>.log` instead of DEVNULL; read `CLAWTEAM_EXIT_CODE` in `lifecycle on-exit` | ~40–60 lines | G-TE-07, G-HB-07, G-XC-04 [ev:clawteam-probe-log#F14][ev:clawteam-spawn-platform#F21] |
| Parent-team linkage | `TeamConfig.created_by{team,agent}` + `spawn --parent-team` + `team discover --parent` | ~50–100 lines | G-TE-05 archive link [ev:clawteam-model#F22][ev:clawteam-probe-log#F18] |
| Pre-spawn mutation hook + plugin load in spawn path | emit `BeforeWorkerSpawn` on `spawn/launch/run` with `prompt`/`system_prompt`/`command` honoured after handlers; `PluginManager.load_all_from_config()` before `get_backend` | ~50–90 lines | G-HB-02, G-HB-08 (from the CLI) [ev:clawteam-spawn-platform#F16][ev:clawteam-spawn-platform#F17] |
| Hermes/Grok adapter branches; system prompt for codex/grok | port CTF `is_hermes_command` (`chat -q --yolo --source tool`); Grok `--always-approve/--rules/-p`; Codex `-c developer_instructions=` | ~30–40 lines each | G-TE-03, G-HB-02 [ev:clawteam-spawn-platform#F2][ev:harness-cli-capabilities-a#F18] |
| `launch` error surfacing + per-member profile + `TaskDef.blocked_by` | check `"Error"` results (PR #167), `AgentDef.profile`, DAG edges in templates | ~60–120 lines | G-TE-01, G-TE-06 [ev:clawteam-probe-log#F15][ev:clawteam-probe-log#F23] |
| `TeamMember.hidden` | field + `team status`/board filter | ~15–30 lines | G-TC-04, G-AD-07 [ev:clawteam-model#F1] |
| Cleanup semantics | `team cleanup` stops registered processes, archives instead of deleting; validate `--blocked-by` ids | ~30–50 lines | G-TE-05, G-TE-07, G-TE-06 [ev:clawteam-probe-log#F20][ev:clawteam-probe-log#F7] |
| Inbox membership ACL | reject non-member recipients unless `--allow-external` | ~30 lines | G-TC-03 mechanical level [ev:clawteam-model#F4] |

## 6. Components that are new by evidence

No system offers these even partially (rung 6 in §2):

1. **Harness-neutral Assistant definition package** (persona/principles/preferences + capability/artifact vocabulary + harness policy + overlays; G-AD-01/02/04/09): every carrier is harness-native; grep negatives in ClawTeam, ATM, OpenClaw [ev:clawteam-model §3][ev:atm-salvage §3][ev:openclaw-native-and-telegram-verification §3].
2. **TeamTemplate composing portable Assistants by reference** with relationships, visibility, dynamic-member policy (G-TC-01/02/05/06): "TeamTemplate → 0" in Hermes, no pre-authorable team in Claude Code, DG DSH-bound [ev:claude-agent-teams-hermes-openbot §3][ev:claude-agent-teams-hermes-openbot#F4][ev:dsh-agent-teams-and-gui#F31].
3. **Overlay model + Proposal + review/provenance record** (G-EV-01/02/03/05): learning absent or ungated everywhere [ev:claude-agent-teams-hermes-openbot#F12][ev:claude-agent-teams-hermes-openbot#F28][ev:dsh-agent-teams-and-gui#F29].
4. **HarnessProfile/HarnessCapability model, user>role>default policy, ensemble synthesis record, persisted HarnessInvocation** (G-HB-01/03/05/07): code-encoded knowledge only; no fan-out+synthesis; no cross-system record [ev:clawteam-spawn-platform#F12][ev:clawteam-probe-log#F14].
5. **Capability vs Artifact distinction, cross-harness artifact kinds, per-host resolution report, artifact lock/fingerprint** (G-AR-01/02/05/06): ATM idea only [ev:atm-salvage#F10]; no consumed lock anywhere.
6. **Nested-TeamRun glue** (parent link, result contract, enforced inner isolation, archive+cleanup; G-TE-05): no parent/child concept in CT, OC, HM, DT/DG [ev:clawteam-model §3][ev:dsh-agent-teams-and-gui#F14][ev:claude-agent-teams-hermes-openbot#F7].
7. **Job-level deterministic backends**, **declarative resume/fresh policy per Member** (G-LO-02/04); **Member↔visible-identity binding**, **TeamRun-presenting surface adapter** (G-MS-02/03; C/S priority).

## 7. Licence table

| System | Licence (file) | Reuse permitted | Evidence |
|---|---|---|---|
| ClawTeam (CT) | MIT — `LICENSE:1-5`, `pyproject.toml:7` | yes, attribution | [ev:clawteam-spawn-platform#F25] |
| ClawTeam-OpenClaw (CTF) | MIT — identical `LICENSE`; fork-only files unmarked | yes, attribution to HKUDS | [ev:clawteam-openclaw-fork-delta#F30] |
| OpenClaw (OC) + multi-agent-kit | MIT — `LICENSE`, `package.json`, npm; kit MIT | yes (`dist` only; V14: do not import plugin-sdk) | [ev:harness-cli-capabilities-b#F16][ev:atm-salvage#F1] |
| Claude Code (CC) | proprietary — Commercial/Consumer terms (web, 2026-08-21) | invocation/config only; API key for automation | [ev:harness-cli-capabilities-a#F15] |
| Codex CLI (CX) | Apache-2.0 — README (web); LICENSE file unfetched | yes (pending file) | [ev:harness-cli-capabilities-a#F14] |
| Grok CLI | Apache-2.0 first-party (web); "External contributions are not accepted" | invocation; ToS 403 | [ev:harness-cli-capabilities-a §4] |
| Hermes (HM) | MIT — `LICENSE:1-3`, `pyproject.toml:17` | yes | [ev:harness-cli-capabilities-b#F22][ev:claude-agent-teams-hermes-openbot#F21] |
| dsh-agent-teams / dsh-agent-team-gui | MIT — `LICENSE` each; DSH MIT (web) | yes (pure modules) | [ev:dsh-agent-teams-and-gui §4][ev:dsh-agent-teams-and-gui#F32] |
| OpenBot (OB) | MIT — `LICENSE` (CopilotKit 2026) | yes (ideas) | [ev:claude-agent-teams-hermes-openbot §4] |
| ATM | **none** — no `LICENSE`, no `license` field | text blocked until the owner states one; ideas citable | [ev:atm-salvage §3] |
| Agent Skills spec | public specification | format reuse | [ev:atm-salvage#F8] |

## Mapping to substrates

Primitive per substrate at rung 1–4, or "no primitive — new".

| Concept | ClawTeam | Claude Code / Codex | OpenClaw | Hermes | dsh (DT/DG) | Verdict |
|---|---|---|---|---|---|---|
| Assistant definition (neutral) | `AgentDef.task` string (render target) | `.claude/agents/*.md`, `--agents` / `.codex/agents/*.toml` (render targets) | workspace `SOUL.md`/`AGENTS.md` (render target) | profile `SOUL.md` + `distribution.yaml` (render target) | DG `AgentRecord` (schema idea) | no primitive — new; materialization rung 1–2 |
| Ephemeral Assistant | `spawn` (no persona slot) | `--agents` JSON, background subagent / agents file | `sessions_spawn` (no SOUL for sub-agents) | `delegate_task`, `--source tool` | DT `add_member` | mechanism rung 1; hidden flag rung 3 (CT) |
| TeamTemplate | TOML template (persona inline, no reference) | none (no pre-authored team) | none | kanban `swarm` roster (one-shot) | DG `SquadRecord` (DSH-bound) | no primitive — new; render to CT TOML rung 2 |
| TeamRun (fresh) | `launch`/`spawn` + data dir | session team (interactive only) / `multi_agent` `?` | agent session tree | kanban board run | DT team dir / DG run | rung 1 (CT best-probed; HM Hermes-only) |
| Nested TeamRun | inner team by composition (no link) | subagent depth ≤3 (no team) / `?` | `maxSpawnDepth` tree | `max_spawn_depth` tree; kanban `--parent` | prohibited | glue new; composition rung 2 |
| HarnessProfile; SelectionPolicy / Broker | adapter chain (code); per-agent `command` + profiles | `--help` facts; `--fallback-model` / `-p profile` | acpx alias registry; `runtime.acp`, `acp.fallbacks` `?` | `--help` facts; `hermes fallback`, MoA | DG route + fallback route | no primitive — new; seeds rung 1/4; fan-out rung 2 |
| HarnessInvocation record | registry + self-reported cost | `-p` json cost / rollout tokens | `audit` (in-gateway) | `--usage-file`, kanban runs | DG run record | emission rung 1; record new |
| Overlay / Proposal / review; Capability vs Artifact; lock | plan approval round-trip (transport); `--skill` inline, `skills-lock.json` `?` | `memory` file (silent); plugins / skills+MCP | memory hooks; skills `requires`, eligibility | distribution vs user paths, curator ledger; `env_requires`, distribution version | DG versions/retrospective; recipe routes | no primitive — new (ATM idea for artifacts) |
| Deterministic backend; surfaces | `spawn subprocess -- <exe>` (mislabelled); — | hooks/monitors; channels (preview) / hooks | cron `--command`; `identity`, bindings | cron `?`; gateway + profile routes | — | rung 1–2; Member binding new |

## What is new vs borrowed

| Concept | Borrowed from (system + mechanism) | New |
|---|---|---|
| Definition materialization; fresh-by-default | CC flags/agent files/`--bare`; Grok flags; CX config override/`--ephemeral`; OC workspace files/session keys; HM profile/SOUL/env overlay; CT `--task`/`--skill`; DG strict schemas | renderer contract; schema rule |
| Harness-neutral Assistant definition; capability/artifact vocabulary | shape ideas: HM `distribution.yaml`, DG `AgentRecord`, kit SOUL/IDENTITY split, Agent Skills name, ATM role-template/ADR 0022 | **new** |
| Harness policy / precedence | CTF `model_resolution.py` pattern; OC `model.fallbacks` | **new** (user>role>default) |
| Overlays + Proposal + review | HM ownership split; CT plan-approval transport; HM ledger; DG versions/import preview; ATM MAC'd decisions | **new** |
| TeamTemplate by reference; relationships; dynamic-member policy; reviewer independence | CT TOML (render target); DG `SquadRecord`, `contextMode`, DG/kit handoffs; OC `subagents.*`, HM/DT caps; separate invocations (CT/HM/CC) | **new** template object and fields |
| TeamRun instantiation, DAG, inbox, archive; nested TeamRun; Windows path | CT `launch/spawn/task/inbox/snapshot` + composition path; HM kanban (`--parent`); DG runs; OC/HM/CC trees; CTF `platform_compat.py`, PR #159 guard | output/exit-code capture; run record; nesting glue (parent link, result contract, isolation, cleanup) |
| HarnessProfile; fallback; ensemble; invocation record | CT adapter chain + locators, evidence checklists, ATM query names; CTF `spawn_with_retry`, native model fallbacks; CT/DC fan-out; CC/HM/Grok/CX emissions, OC audit | **new** data model, synthesis record, persisted record |
| Artifact model, lock, resolution report | OC eligibility report; HM `env_requires`/distribution; CT `profile test`; ATM schemas (idea) | **new** |
| Deterministic backends / schedulers; surfaces / identity | OC cron `--command`, OS schedulers, CT leader watcher; HM gateway, OC channels+`identity`, CC channels | job-level watchers (domain); Member binding; TeamRun-presenting adapter |

## Open questions

1. Will HKUDS/ClawTeam accept any rung-3 PR (no commit since 2026-05-09)? If not, rung-3 items revert to rung-2 equivalents; file the PRs anyway? [ev:clawteam-spawn-platform#F24]
2. ATM licence: will the owner add a LICENSE (or written permission) so ADR 0022 schema text can be reused at rung 4 rather than re-derived? [ev:atm-salvage §3]
3. Is `codex exec -c developer_instructions=…` honoured on 0.148.0 (G-HB-02 `?`)? Decides rung 1 vs a temp-`AGENTS.md` workaround [ev:harness-cli-capabilities-a#F2].
4. OpenClaw `acpx` path (`runtime.acp`, `acp.fallbacks`, custom Hermes alias): rung 1 for HB-03/04/08 only if a disposable-profile probe confirms it [ev:openclaw-native-and-telegram-verification#F16]; likewise Hermes `--source tool` hiding on 0.20.4 (G-TC-04) [ev:clawteam-openclaw-fork-delta §5].
5. The implementation language (TBD) decides whether DG/DT TypeScript modules are vendored (rung 4) or used only as schema ideas.
6. No candidate has Windows CI: is a Windows/macOS probe a precondition for the rung-3+4 answer to G-TE-08? Who writes ClawTeam's `skills-lock.json` (the only in-substrate lock precedent for G-AR-06, if real)?

## Inconsistencies noted

- Fit-gap G-AR-06 cites CT `skills-lock.json` (source+hash, no reader) with `[ev:harness-cli-capabilities-b#F10]`, but no evidence file documents that file; the claim traces only to [recon] and the fit-gap's own evidence-gap note asks to confirm the writer. Treated here as UNVERIFIED.
- Fit-gap TC-04 gives HM `C!` for `--source tool`, while [ev:clawteam-openclaw-fork-delta §5] records that storage behaviour on 0.20.4 was not probed (no-op on ≤0.8.0). Cell kept; the rung-1 option is marked `?` in §2.3.
- Fit-gap TE-08 "best: CTF C!" rests on docs + `platform_compat.py`; [ev:clawteam-openclaw-fork-delta#F6] shows the fork's subprocess+OpenClaw argv is flag-mismatched, so the CTF advantage holds for non-OpenClaw workers only; "C!" is not a verified Windows path.
- No other cell is contradicted; `?`-suffixed OC cells (HB-03/04/08) stay `?`.
