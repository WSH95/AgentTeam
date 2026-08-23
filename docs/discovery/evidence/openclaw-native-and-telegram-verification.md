---
id: ev:openclaw-kit-native
topic: openclaw-multi-agent-kit conventions mapped to our layers; local verification against installed OpenClaw 2026.7.1-2; web verification of Telegram Bot API claims; ATM V11–V13 re-verdict
systems: [openclaw-multi-agent-kit, OpenClaw native multi-agent (installed 2026.7.1-2), Telegram Bot API]
sources:
  - {kind: repo, ref: /home/wsh/Documents/00000/openclaw-multi-agent-kit@5d6418d (commit date 2026-07-10), accessed: 2026-08-21, version: unversioned docs-only kit}
  - {kind: cli, ref: "openclaw --version; openclaw --help; openclaw agents|sessions|acp|tui|agent|config|cron|skills|channels|attach|tasks|audit|worktrees|message --help; openclaw config schema; openclaw config file; openclaw config validate; openclaw agents list --json; openclaw agents bindings; openclaw channels list; openclaw plugins list; openclaw skills list; openclaw docs <query>", accessed: 2026-08-21, version: OpenClaw 2026.7.1-2 (0790d9f)}
  - {kind: repo, ref: /home/wsh/.nvm/versions/node/v24.16.0/lib/node_modules/openclaw/{docs,dist} (installed package, MIT), accessed: 2026-08-21, version: 2026.7.1-2}
  - {kind: repo, ref: /home/wsh/Documents/00000/agent-team-manager-dev/docs/design/feasibility-report.md (V11–V13) and tests/fixtures/openclaw/2026.7.1-2-*.json, accessed: 2026-08-21}
  - {kind: web, ref: https://registry.npmjs.org/openclaw/latest, accessed: 2026-08-21, version: 2026.7.1-2}
  - {kind: web, ref: https://docs.openclaw.ai/tools/acp-agents | /tools/subagents | /channels/telegram | /concepts/multi-agent, accessed: 2026-08-21}
  - {kind: web, ref: https://github.com/openclaw/openclaw/issues/41004 | /issues/31671, accessed: 2026-08-21}
  - {kind: web, ref: https://core.telegram.org/bots/faq | /bots/api | /bots/api-changelog | /bots/features | /api/bots/bot-to-bot, accessed: 2026-08-21, version: Bot API 10.2 (2026-07-14)}
  - {kind: web, ref: https://core.telegram.org/api/bots/managed-bots | /api/bots/guest-mode | https://telegram.org/blog/ai-bot-revolution-11-new-features | /blog/communities-editor-invisible-messages, accessed: 2026-08-22}
  - {kind: repo, ref: /home/wsh/.nvm/versions/node/v24.16.0/lib/node_modules/openclaw/{docs,dist} negative feature-symbol recheck, accessed: 2026-08-22, version: 2026.7.1-2}
method: Read every kit doc/template/example with line numbers; grepped kit for term coverage; ran read-only OpenClaw CLI help/list/schema commands (no gateway start, no prompts sent); parsed `openclaw config schema` JSON (2.4 MB) with a masking script; read the version-matched docs shipped inside the installed npm package; grepped installed dist for error strings; fetched official Telegram and OpenClaw web pages; restated ATM V11–V13 and re-verified each.
platform: {os: Ubuntu (Linux 5.15), tmux: absent, cli_versions: {openclaw: "2026.7.1-2 (0790d9f)", acpx: "not installed (not on PATH; no acpx plugin in `openclaw plugins list`)", node: v24.16.0}}
author_agent: ev:openclaw-kit-native
date: 2026-08-21
confidence: high
status: current with 2026-08-22 Telegram/OpenClaw addendum
---
# openclaw-multi-agent-kit conventions, OpenClaw native multi-agent (installed), and Telegram Bot API — verification

## 1. Scope & questions

- Part A — Which kit conventions are markdown convention vs enforced by OpenClaw config, and which of our layers each informs (MS-01..MS-04, AD-06, TC-02, HB-02)?
- Part B — What does the *installed* OpenClaw 2026.7.1-2 actually offer: multi-agent (`agents.list`, `bindings`, per-agent workspace), session tools (`sessions_send`/`sessions_spawn`), ACP support, `threadBindings` keys, Telegram keys? (HB-01, HB-02, TE-03, TE-04, TE-05, MS-02, XC-02)
- Part C — Web verdicts on the kit's platform claims that matter for Surface/brokerage (MS-02, MS-03, MS-04, HB-02) and on Telegram Bot API facts (MS-02, MS-04).
- Part D — ATM feasibility rows V11–V13 restated with today's verdict (MS-02, MS-04, XC-02).
- Negative: what OpenClaw does NOT offer for TeamTemplates / Nested TeamRuns / reusable role packages (TC-01, TE-05, AD-08).

Terminology note: the kit and OpenClaw say "agent", "persona", "subagent", "channel"; this file quotes them verbatim but maps them to glossary terms (Assistant, Member, Ephemeral Assistant, Surface) in the Claim lines.

## 2. Findings

### Part A — Kit conventions mapped to our layers

### F1. The kit is docs-only; nothing executes, and every rule is convention unless it is an `openclaw.json` key
- Claim: "This is a **template/docs-only repo** (no runtime code)" and "**Not a library or app.** Nothing here executes — everything is markdown, JSON, and JSONC meant to be copied into an OpenClaw workspace." Only the `openclaw.json` snippets (agents, bindings, channels, acp, threadBindings, hooks) are enforced by OpenClaw; SOUL/IDENTITY/AGENTS/handoff rules are prompt conventions.
- Evidence: openclaw-multi-agent-kit/docs/architecture.md:11,17; openclaw-multi-agent-kit/AGENTS.md:11; README.md:5 ("OpenClaw-specific ... won't work out of the box" elsewhere).
- Level: observed
- Requirements: XC-03, MS-02, HB-02
- Suggested fit cell: openclaw-multi-agent-kit → C~ (reuse as conventions/config examples only; nothing to adapt at code level)

### F2. Three-file persona layering: SOUL.md (identity/rules) ≠ IDENTITY.md (metadata card) ≠ workspace AGENTS.md (runtime ops) — separation rule quoted
- Claim: The workspace AGENTS.md template states the separation rule verbatim: "It defines structure, escalation rules, and shared context for all agents. SOUL.md defines each agent's personality, behavior, and domain expertise. Both files serve different layers — AGENTS.md is runtime ops, SOUL.md is identity." IDENTITY.md is a fixed-field card: Name, Role, Vibe, Model, Emoji, Channel, Capabilities, Key Output Files, Escalation. OpenClaw itself loads all three at session start (see F14), so *injection* is enforced by OpenClaw but *content separation* is convention.
- Evidence: openclaw-multi-agent-kit/templates/workspace/AGENTS.md:3-6 (rule), :8 (retrieval order "SOUL.md > USER.md > memory files > MEMORY.md"), :25-43 (file map); templates/identity/agent-identity.md:3-23; templates/soul/orchestrator.md:1-3,40,96 ("Each session = fresh start. Files ARE my memory."); docs/agent-design-patterns.md:16-44 (10-section SOUL structure incl. "8. Team Integration — Which topic, which teammates").
- Level: observed
- Requirements: AD-01, AD-05, AD-06, MS-03, HB-02
- Suggested fit cell: openclaw-multi-agent-kit → C~ for AD-01 persona shape; M~ for AD-05 (IDENTITY.md carries `Channel: [Topic # and name]` and `Model:`; SOUL §8 embeds topic numbers and `sessions_send` agent IDs — project/surface facts inside the role definition)

### F3. Kit IDENTITY.md mixes visible identity with runtime facts; OpenClaw has a separate native identity object
- Claim: Kit IDENTITY.md fields `Model`, `Channel` (topic number) and `Escalation` live beside `Name/Vibe/Emoji`. Installed OpenClaw separately models visible identity as `agents.list[].identity {name, emoji, theme, avatar}` and can read it from IDENTITY.md via `openclaw agents set-identity --from-identity`.
- Evidence: openclaw-multi-agent-kit/templates/identity/agent-identity.md:3-8,21-23; CLI `openclaw agents set-identity --help` (flags `--name --emoji --theme --avatar --from-identity --identity-file`); `openclaw config schema` → `agents.list.identity` keys `['avatar','emoji','name','theme']`.
- Level: verified (CLI + schema)
- Requirements: AD-06, MS-03
- Suggested fit cell: OpenClaw → S! for AD-06/MS-03 (identity is a separable config object); openclaw-multi-agent-kit → M~ (card conflates)

### F4. Topology rule: "topic per flow, not per agent"; primary `requireMention:false` / secondary `requireMention:true`
- Claim: "Design channels as **workflow lanes**, not personality rooms. Bad: Topic per agent ... Good: Topic per flow (`Build`, `Research`, ...)". Ownership: "**Primary owner** (drives output, `requireMention: false`) / **Secondary specialists** (support only, `requireMention: true`) / Never set two bots to `requireMention: false` in one topic." Orchestrator must have `enabled: false` on topics owned by others. `requireMention`/`enabled` are real OpenClaw keys (enforced); the "one primary per lane" and "orchestrator disabled" policies are conventions the operator must keep consistent by hand.
- Evidence: openclaw-multi-agent-kit/docs/telegram-channel-architecture.md:12-20,32-39; INSTRUCTIONS.md:213,239,265-278; docs/architecture.md:116-120; examples/minimal-team.json:46-97 (three accounts, per-topic `requireMention`); examples/full-team.json default account topics `TOPIC_BUILD…TOPIC_OPS: {enabled:false}`; schema `channels.telegram.groups.*.topics.*` keys include `requireMention`, `enabled`, `agentId`, `skills`, `systemPrompt`.
- Level: verified (keys in schema) / observed (policy)
- Requirements: MS-02, MS-04, TC-02
- Suggested fit cell: OpenClaw → C! for MS-02 (surface routing is configuration); openclaw-multi-agent-kit → M~ for MS-04 (the kit derives team membership from topic/bot topology — exactly what MS-04 forbids for Core)

### F5. Handoff standard: required fields + ACK/DONE/BLOCKED lifecycle, carried by `sessions_send` + `message` tool
- Claim: "Use this standard for **all** agent-to-agent requests". Required HANDOFF fields: `from, to, task_id, priority (P0|P1|P2), summary, context, deliver_to (telegram:<group-id>:<topic-id>), deadline, max_retries (optional, default 3), done_when[]`. Lifecycle: `ACK <task_id> — accepted|rejected` within 2 minutes; optional progress preambles; pre-DONE check then `DONE <task_id> / Result / Evidence / Risks`; `BLOCKED <task_id> / Blocker / Impact / Need decision from / Options / Recommendation` if blocked >15 min. Transport: `sessions_send(agentId=…, message="HANDOFF…")`; receivers post lifecycle messages "explicitly via the `message` tool targeting the shared topic — not by reply". Entirely convention (free text inside a tool call); nothing validates fields.
- Evidence: openclaw-multi-agent-kit/docs/inter-agent-handoff-standard.md:10-21,37-53,59-70,96-103,109-118; INSTRUCTIONS.md:346-366; templates/workspace/AGENTS.md:69-81; README.md:182.
- Level: observed
- Requirements: TC-02, TE-06, AD-03, XC-04
- Suggested fit cell: openclaw-multi-agent-kit → C~ (handoff vocabulary reusable as a TeamTemplate handoff convention; `deliver_to` is surface-specific)

### F6. `sessions_send` caveat the kit designs around (#31671): one-way trigger, receiver re-anchors via `message` tool
- Claim: "calling it from one agent into another's session can rewrite the target session's stored `channel` from `telegram` to `webchat` ... Treat `sessions_send` as a one-way trigger, not a routing rewrite."
- Evidence: openclaw-multi-agent-kit/docs/inter-agent-handoff-standard.md:23-31; docs/architecture.md:100; docs/acpx-telegram.md:500. Web: issue #31671 "Closed as not planned", label `stale`, created 2026-03-02, version 2026.1.24-3 (accessed 2026-08-21). Installed docs add a related rule: "Thread-scoped chat sessions, such as keys ending in `:thread:<id>`, are not valid `sessions_send` targets" and messages are "marked as inter-session data ... `[Inter-session message ... isUser=false]`" (openclaw package docs/concepts/session-tool.md:68-70).
- Level: observed (kit) / web (issue) / observed (installed docs)
- Requirements: MS-02, TE-06
- Suggested fit cell: OpenClaw → S~ for intra-gateway messaging (with known caveat); verdict on the issue: **unverifiable** whether fixed (closed stale, no fix reference)

### F7. ACPX invocation forms in the kit: (a) `agents.list[].runtime {type:"acp", acp:{backend:"acpx", agent, mode, cwd}}`, (b) `/acp spawn <agent> --thread here|auto`, (c) `sessions_spawn(runtime="acp", ...)`
- Claim: Three forms are documented. Form (a) plus `bindings[] {type:"acp", agentId, match{channel:"telegram", accountId, peer{kind:"group", id:"<chat>:topic:<topic>"}}, acp{label, mode, cwd}}` and global `acp {enabled, backend:"acpx", defaultAgent, allowedAgents[]}` are config (enforced). Form (b) is a chat slash command. Form (c) is a tool call; the kit says it "can only be called from a `subagent:*` session — not directly from a Telegram channel session. This is a platform-level restriction." The kit's `mode` values are `"persistent"` / `"exec"`.
- Evidence: openclaw-multi-agent-kit/docs/acpx-telegram.md:104-135,140-164,218-230,242-254,269-289,293-316; INSTRUCTIONS.md:280-293,525-541 (`sessions_spawn(runtime="acp", agentId="claude", cwd="/path/to/repo")`); templates/skills/acpx-session/SKILL.md:126-129; docs/telegram-dm-topics.md:254-262.
- Level: observed
- Requirements: HB-02, HB-03, TE-03
- Suggested fit cell: OpenClaw → C! for HB-02 via ACP (schema confirms keys, F16) — but see F17 for value drift

### F8. Kit "never pin a model" rule
- Claim: "Model-agnostic: never pin model ids in templates or example configs; agents inherit the runtime default" and "Leave `model` unset on each agent ... Only pin a specific model on an individual agent if you have a concrete reason". Both example configs omit `model` entirely; IDENTITY.md `Model:` says "leave blank to inherit".
- Evidence: openclaw-multi-agent-kit/AGENTS.md:17,20; INSTRUCTIONS.md:159-168; docs/architecture.md:23; docs/scaling.md:38-52; templates/openclaw-config.jsonc:6-9; examples/minimal-team.json:3,10-23; templates/identity/agent-identity.md:6.
- Level: observed
- Requirements: AD-04, HB-03
- Suggested fit cell: openclaw-multi-agent-kit → C~ (matches "no permanent harness/model binding"; the kit's "two-speed model policy" is a per-agent override, not a policy object)

### F9. Cron routine pattern in the kit vs installed OpenClaw
- Claim: Kit shows `"cron": {"jobs": [{"agentId":"ops","schedule":"45 * * * *","message":"..."}]}` inside `openclaw.json`. Installed schema has **no** `cron.jobs` key (keys: `enabled, failureAlert, failureDestination, maxConcurrentRuns, retry, runLog, sessionRetention, store, triggers, webhook, webhookToken`); jobs are managed via `openclaw cron add|edit|rm` and stored in SQLite ("`cron.store` is a logical store key ... not a live JSON file to hand-edit"). `cron add` supports `--agent`, `--session isolated|main`, `--message`, `--command <shell>` (deterministic payload, no model call), `--at/--every/--cron`, `--on-exit`, event `triggers`.
- Evidence: openclaw-multi-agent-kit/INSTRUCTIONS.md:477-494; `openclaw config schema` cron keys; `openclaw cron add --help`; openclaw package docs/automation/cron-jobs.md:128-134,181-199,208-214,533-555,570; docs/cli/cron.md:135.
- Level: verified (schema + CLI)
- Requirements: LO-01, LO-02, LO-03, HB-06
- Suggested fit cell: OpenClaw → S! for LO-02/HB-06 (command payloads + triggers are deterministic backends); openclaw-multi-agent-kit → ?w (its `cron.jobs` form is **changed** relative to 2026.7.1-2)

### F10. Kit config format and key structure
- Claim: `templates/openclaw-config.jsonc` top-level keys: `agents.defaults{workspace,maxConcurrent}`, `skills.enabled`, `channels.telegram{enabled,dmPolicy,streaming,threadBindings{spawnSessions,idleHours}}`, `acp{enabled,backend,defaultAgent,allowedAgents}`, `messages.ackReactionScope`, `session.dmScope`, `hooks.internal.entries{boot-md,bootstrap-extra-files,session-memory}`. `examples/minimal-team.json`: `agents.list[]` entries carry only `id` + `workspace`; `bindings[] {agentId, match{channel:"telegram", accountId}}`; `channels.telegram.accounts.{default,coder,qa}` each with `botToken` placeholder, `dmPolicy`, `groups.<GROUP_ID>.{requireMention,groupPolicy,enabled,topics}`. `full-team.json` adds `agents.list[0].subagents.allowAgents ["*"]` and per-account `threadBindings.spawnSessions`. The kit workspace layout is `~/.openclaw/workspace/agents/<id>/{SOUL.md,IDENTITY.md,skills/}` + `shared-context/{THESIS,SIGNALS,FEEDBACK-LOG,SUPERGROUP-MAP}.md`.
- Evidence: openclaw-multi-agent-kit/templates/openclaw-config.jsonc:5-66; examples/minimal-team.json:5-99; examples/full-team.json (parsed: `agents.list[0] = {id:"orchestrator", workspace, subagents:{allowAgents:["*"]}}`; coder account keys `botToken,dmPolicy,threadBindings,groups`); INSTRUCTIONS.md:101-105,150-157.
- Level: observed
- Requirements: HB-02, MS-02, AR-04
- Suggested fit cell: OpenClaw → C! (all keys exist in the installed schema, F16)

### F11. Kit's own "what is human-only" statements (BotFather, supergroup, topic IDs)
- Claim: "For each agent, the human needs to do this in Telegram (you cannot do this programmatically): @BotFather `/newbot` ... `/setjoingroups` Enable ... `/setprivacy` Disable"; supergroup creation, enabling Topics, adding bots as admins, collecting group/topic IDs are human steps. Topic *creation* is automatable via the kit's `telegram-topic-setup` skill using OpenClaw's `topic-create` action (returns `topicId`).
- Evidence: openclaw-multi-agent-kit/INSTRUCTIONS.md:51-91; docs/supergroup-setup.md:20-60; templates/skills/telegram-topic-setup/SKILL.md:13-25; docs/telegram-dm-topics.md:26-47.
- Level: observed
- Requirements: MS-02, XC-02
- Suggested fit cell: n/a (surface provisioning facts; see F30 for web confirmation)

### F12. Kit version claims vs today
- Claim: Kit states "OpenClaw v2026.3.28 or later (adds `/acp spawn`...); v2026.3.31 is the latest known release", "Skills system (v2026.3.24+)", and "This guide assumes OpenClaw 2026.x". Installed and npm-latest are both 2026.7.1-2.
- Evidence: openclaw-multi-agent-kit/docs/acpx-telegram.md:39,244; docs/architecture.md:91; INSTRUCTIONS.md:570; `openclaw --version` → `OpenClaw 2026.7.1-2 (0790d9f)`; https://registry.npmjs.org/openclaw/latest → `"version":"2026.7.1-2"`, `"license":"MIT"` (accessed 2026-08-21).
- Level: verified
- Requirements: XC-02, HB-01
- Suggested fit cell: n/a — verdict **changed** (kit is ~3 months behind; several key names drifted, F17/F18)

### Part B — Installed OpenClaw 2026.7.1-2 (local, read-only)

### F13. Multi-agent support is native: `agents.list[]`, `bindings[]`, per-agent workspace/agentDir/session store; helper CLI
- Claim: "Run multiple _isolated_ agents in one Gateway process, each with its own workspace, state directory (`agentDir`), and session store ... Inbound messages route to the right agent through **bindings**." Paths: workspace `agents.list[].workspace` (default `<stateDir>/workspace-<agentId>` for non-default agents), agentDir `~/.openclaw/agents/<agentId>/agent`, sessions `~/.openclaw/agents/<agentId>/sessions`. CLI: `openclaw agents add [name] --workspace --model --agent-dir --bind <channel[:accountId]> --non-interactive --json`, `agents bind/unbind/bindings/list --bindings/set-identity/delete`. `agents.list[]` has 35 schema keys incl. `id, workspace, agentDir, model, models, identity, skills, tools, sandbox, subagents, runtime, contextInjection, heartbeat, memorySearch, default`. Local state: exactly one agent `main` (`bindings: 0`), `agents bindings` → "No routing bindings.", `channels list` → "no configured chat channels".
- Evidence: openclaw package docs/concepts/multi-agent.md:9-19,41-50,61-69; `openclaw agents --help`, `openclaw agents add --help`; `openclaw config schema` (`agents.list` keys); `openclaw agents list --json` (masked: `{id:"main", workspace:"~/.openclaw/workspace", agentDir:"~/.openclaw/agents/main/agent", model:"openai/<model>", bindings:0, isDefault:true}`).
- Level: verified
- Requirements: TE-03, HB-01, HB-02, MS-02
- Suggested fit cell: OpenClaw → S! for "many isolated agents in one process" (AssistantInstance hosting); C! for routing

### F14. Workspace bootstrap files are injected by OpenClaw itself (AGENTS.md, SOUL.md, USER.md, IDENTITY.md, TOOLS.md, HEARTBEAT.md, BOOT.md, BOOTSTRAP.md, MEMORY.md, skills/)
- Claim: "Standard files OpenClaw expects inside the workspace": AGENTS.md "Loaded at the start of every session", SOUL.md "Loaded every session", IDENTITY.md "Created/updated during the bootstrap ritual", `skills/` "Highest-precedence skill location"; missing files inject a marker; limits `agents.defaults.bootstrapMaxChars` (20000) / `bootstrapTotalMaxChars` (60000); `agents.defaults.skipBootstrap`; per-agent `contextInjection: always|continuation-skip|never`. Sub-agent children get only AGENTS.md + TOOLS.md ("no `SOUL.md`, `IDENTITY.md`, `USER.md`, `MEMORY.md`..."). The local default workspace contains `AGENTS.md BOOTSTRAP.md HEARTBEAT.md IDENTITY.md SOUL.md TOOLS.md USER.md openclaw-workspace-state.json .git`.
- Evidence: openclaw package docs/concepts/agent-workspace.md:62-107; docs/tools/subagents.md:649; schema `agents.list.contextInjection` enum; `ls -a ~/.openclaw/workspace`.
- Level: verified
- Requirements: HB-02, HB-01, AD-07
- Suggested fit cell: OpenClaw → S! for HB-02 "workspace instruction files" injection method; note the sub-agent SOUL/IDENTITY exclusion (an Ephemeral Assistant spawned as a native sub-agent does **not** receive a persona file — only task text)

### F15. Session tools: `sessions_list/history/send/spawn/yield`, `subagents`, `session_status`; gated by `tools.profile`, visibility, `tools.agentToAgent`
- Claim: Table of seven tools; "`tools.profile: \"coding\"` includes the full session orchestration set, including `sessions_spawn`, `sessions_yield`, and `subagents`. `tools.profile: \"messaging\"` ... does not include sub-agent spawning." `sessions_spawn` "creates an isolated session for a background task by default. It is always non-blocking; it returns immediately with a `runId` and `childSessionKey`." Options: `runtime: "subagent"` (default) | `"acp"`, `model`, `thinking`, `thread: true`, `sandbox: "require"`, `context: "fork"|"isolated"`. Visibility `tools.sessions.visibility` = `self|tree|agent|all` (default `tree`; "cross-agent still requires tools.agentToAgent"); `tools.agentToAgent {enabled, allow[]}` "Keep off in simple deployments"; `session.agentToAgent.maxPingPongTurns` 0–20 default 5. Local config has `tools.profile = 'coding'`.
- Evidence: openclaw package docs/concepts/session-tool.md:14-35,63-72,88-104,106-117; schema `tools.sessions.visibility` enum + `tools.agentToAgent` descriptions; masked `~/.openclaw/openclaw.json` key dump (`tools.profile = 'coding'`).
- Level: verified
- Requirements: TE-04, TE-06, TC-05, XC-04
- Suggested fit cell: OpenClaw → S! for in-gateway Ephemeral Assistant spawning (TE-04) with allowlists (`subagents.allowAgents`, `requireAgentId`)

### F16. ACP in the installed version: config keys, harness ids, runtime routing, CLI surface
- Claim: Schema `acp` keys: `allowedAgents, backend, defaultAgent, dispatch, enabled, fallbacks, maxConcurrentSessions, runtime, stream`; `agents.list[].runtime {type: "embedded"|"acp", acp{agent, backend, cwd, mode}}`; `bindings[] {type:"route"|"acp", agentId, match{accountId, channel, guildId, peer{id,kind}, roles, teamId}, acp{backend,cwd,label,mode}, session, comment}`. ACP backend is the `@openclaw/acpx` **plugin** (`openclaw plugins install @openclaw/acpx`), not a bundled runtime; acpx aliases: `claude, codex, copilot, cursor, droid, fast-agent, gemini, iflow, kilocode, kimi, kiro, mux, opencode, openclaw, pi, qoder, qwen, trae` (18). Decision order in docs: Codex → native `/codex` + `openai/*` app-server runtime; "Claude Code, Gemini CLI, OpenCode, Cursor, Droid, or another external harness → ACP/acpx, not the native sub-agent runtime." CLI `openclaw acp` = "Run an ACP bridge backed by the Gateway" (flags `--session <key>`, `--session-label`, `--provenance off|meta|meta+receipt`, `acp client --cwd --server`); there is **no** `openclaw acp spawn` CLI subcommand — `/acp spawn` is a chat command. `openclaw attach` "launches Claude Code with a strict temporary MCP config bound to one Gateway session". Locally: acpx plugin not installed, `acpx` not on PATH; codex harness plugin enabled; telegram plugin stock but disabled.
- Evidence: `openclaw config schema` (paths above; `agents.list.runtime.type` description "\"embedded\" (default OpenClaw runtime) or \"acp\" (ACP harness defaults)"); openclaw package docs/tools/acp-agents-setup.md:28-51 (aliases), :44-45; docs/concepts/agent-runtimes.md:21-35,91-96; docs/tools/acp-agents.md:229-233; `openclaw acp --help`; `openclaw attach --help` + docs/cli/attach.md; `openclaw plugins list` (grep: no acpx; `@openclaw/telegram` disabled; `Codex ... enabled`); `which acpx` → not found.
- Level: verified
- Requirements: HB-01, HB-02, HB-03, HB-04 (`acp.fallbacks`), TE-03
- Suggested fit cell: OpenClaw → C! for HB-02/HB-03 (harness routing through ACP is configuration once the plugin is installed); P! for HB-04 (`acp.fallbacks` "Ordered list of fallback ACP backend ids tried when the primary backend fails with UNAVAILABLE")

### F17. Kit ACP `mode: "exec"` is **changed**: installed enum is `persistent | oneshot`
- Claim: Schema `agents.list.runtime.acp.mode` enum = `['persistent','oneshot']` ("Optional ACP session mode default for this agent (persistent or oneshot)"); `bindings[].acp.mode` documented as `"persistent" | "oneshot"`; `/acp spawn` flag `--mode persistent|oneshot`. The kit documents `"exec"` for one-shot.
- Evidence: `openclaw config schema`; openclaw package docs/tools/acp-agents.md:347,497-508; web docs.openclaw.ai/tools/acp-agents (accessed 2026-08-21, same); openclaw-multi-agent-kit/docs/acpx-telegram.md:133,301-316.
- Level: verified
- Requirements: HB-02, XC-02
- Suggested fit cell: verdict **changed** (kit key value stale)

### F18. `threadBindings` keys: kit's "only `spawnSessions` and `idleHours`" is **changed**; seven keys exist for Telegram and a global `session.threadBindings` block exists
- Claim: Schema `channels.telegram.threadBindings` (and per-account `channels.telegram.accounts.*.threadBindings`) keys: `defaultSpawnContext (enum isolated|fork), enabled, idleHours, maxAgeHours, spawnAcpSessions, spawnSessions, spawnSubagentSessions`. Top-level `session.threadBindings` exists: "Shared defaults for thread-bound session routing behavior across providers"; field details: `enabled`, `idleHours` (default 24; `0` disables), `maxAgeHours` (default 0), `spawnSessions` ("default gate for creating thread-bound work sessions from `sessions_spawn` and ACP thread spawns. Defaults to `true`"), `defaultSpawnContext` (`fork` default). `spawnSubagentSessions`/`spawnAcpSessions` are **deprecated legacy keys** migrated into `spawnSessions` by `openclaw doctor --fix` (migration code present in dist). The kit asserts the opposite ("Keys like `enabled`, `maxAgeHours`, or `maxAgeDays` are not part of the current Telegram schema" and "They do NOT live at top-level `session`").
- Evidence: `openclaw config schema`; openclaw package docs/gateway/config-agents.md:1293-1297,1336-1343; docs/channels/discord.md:787 ("Deprecated `spawnSubagentSessions`/`spawnAcpSessions` keys are migrated by `openclaw doctor --fix`"); dist/legacy-config-migrations--PhUdsg4.js (`resolveMigratedSpawnSessions` deletes both keys, sets `spawnSessions`); openclaw-multi-agent-kit/INSTRUCTIONS.md:295-328; docs/acpx-telegram.md:194,216; web docs.openclaw.ai/channels/telegram lists the same seven keys (accessed 2026-08-21). ATM fixture `tests/fixtures/openclaw/2026.7.1-2-s1-config-schema.raw.json` already contains `spawnAcpSessions` ×7, `maxAgeHours` ×8 (same version).
- Level: verified
- Requirements: MS-02, XC-02
- Suggested fit cell: verdict **changed**

### F19. Telegram channel keys in the installed schema (structure only)
- Claim: `channels.telegram` has 56 keys incl. `accounts, botToken, tokenFile, dmPolicy (pairing|allowlist|open|disabled; default pairing), groupPolicy (open|disabled|allowlist; default allowlist), allowFrom, groupAllowFrom, groups, threadBindings, streaming, webhookUrl, webhookSecret, webhookPath, webhookHost, webhookPort, webhookCertPath, pollingStallThresholdMs, apiRoot, actions, capabilities, configWrites, mentionPatterns, replyToMode, defaultAccount`. `groups.*` keys: `allowFrom, enabled, groupPolicy, ingest, requireMention, skills, systemPrompt, tools, toolsBySender, topics, …`; `topics.*` adds `agentId` ("`agentId` is topic-only and does not inherit from group defaults"). Transport: "Long polling is the default transport; webhook mode is optional." Actions include `createForumTopic`/`topic-create` ("enabled by default with no dedicated toggle").
- Evidence: `openclaw config schema`; openclaw package docs/channels/telegram.md:8,512-516,537-544,701-708,898-908.
- Level: verified
- Requirements: MS-02, MS-04, AR-04 (`tokenFile`/`TELEGRAM_BOT_TOKEN` references instead of inline token)
- Suggested fit cell: OpenClaw → C! for MS-02 Telegram surface

### F20. `agentId` routes the brain, not the visible sender — confirmed by installed docs
- Claim: Installed docs: "Replies still come from the same WhatsApp number — there is no per-agent sender identity." and for Telegram per-topic routing "each topic can route to a different agent via `agentId` in the topic config, giving it its own workspace, memory, and session" (session key `agent:zu:telegram:group:-100…:topic:3`); the bot handle "addresses the selected OpenClaw agent, even when the agent persona name differs from the Telegram username." Multi-bot: "For multiple bots in the same Telegram group, invite each bot and mention the one that should answer."
- Evidence: openclaw package docs/concepts/multi-agent.md:164,306-310; docs/channels/telegram.md:115,544-564; web docs.openclaw.ai/concepts/multi-agent (same sentence, accessed 2026-08-21); kit statement at openclaw-multi-agent-kit/README.md:63-81.
- Level: verified (installed docs) / web
- Requirements: MS-03, AD-06, MS-04
- Suggested fit cell: kit claim verdict **confirmed**; OpenClaw → S! for MS-03 (visible identity = channel account, separable from agentId)

### F21. Native nesting is capped and sub-agent sessions are auto-archived; no team object
- Claim: Sub-agent session key `agent:<agentId>:subagent:<uuid>`; "By default, sub-agents cannot spawn their own sub-agents (`maxSpawnDepth: 1`). Set `maxSpawnDepth: 2` ... (default: 1, range 1-5)"; `maxChildrenPerAgent` 5 (1–20); "Depth 2 (leaf worker): no session tools — `sessions_spawn` is always denied at depth 2"; "Sub-agent sessions are automatically archived after `agents.defaults.subagents.archiveAfterMinutes` (default `60`)"; `cleanup: "delete"` archives immediately; announce step posts results to the requester. `subagents.allowAgents` must name configured `agents.list[]` ids; `requireAgentId` forces explicit selection; `delegationMode suggest|prefer` "controls prompt guidance only; it does not change tool policy".
- Evidence: openclaw package docs/tools/subagents.md:12,341-348,371-379,384-395,409-410,436-441; web docs.openclaw.ai/tools/subagents (same, accessed 2026-08-21); schema `agents.list.subagents` keys.
- Level: verified
- Requirements: TE-04, TE-05, TE-07, TC-05, AD-07
- Suggested fit cell: OpenClaw → S! for TE-04 and AD-07 (non-user-roster child + audit/archive; portable persona-object caveat belongs to AD-01); Xs~ for TE-05 (depth-2 orchestrator pattern gives a tree of sessions but no TeamRun boundary/result object; see §3)

### F22. Audit/recording surfaces exist: `openclaw audit`, `openclaw tasks`, `sessions export-trajectory`
- Claim: `openclaw audit` "Inspect metadata-only agent run and tool action records" (`--kind agent_run|tool_action`, `--agent`, `--run`, `--session`, `--status started|succeeded|failed|cancelled|timed_out|blocked`); `openclaw tasks` "Inspect durable background tasks and TaskFlow state" (`--runtime subagent|acp|cron|cli`); `openclaw sessions export-trajectory` "Export a redacted trajectory bundle for a stored session"; live docs: "For a child started through `sessions_spawn`, the child owns a new context; it never reuses or mutates the parent context. The lineage projection links the parent context".
- Evidence: `openclaw audit --help`; `openclaw tasks --help`; `openclaw sessions export-trajectory --help`; `openclaw docs "sessions_spawn acp telegram thread"` (probe log §6, Audit history result).
- Level: verified
- Requirements: HB-07, TE-07, XC-04
- Suggested fit cell: OpenClaw → S! for recording HarnessInvocations that run *inside* the gateway (not for Claude Code/Codex invoked outside it)

### F23. Other installed surfaces relevant to brokerage: CLI backends, worktrees, sandbox, `openclaw agent` headless turn
- Claim: CLI backends = "local AI CLI as a text-only fallback ... CLI backends are not ACP" (`agents.defaults.cliBackends`, e.g. `claude-cli`); `openclaw worktrees create|list|remove|restore|gc` ("Managed worktrees give an agent task its own git branch and checkout ... `<openclaw-state-dir>/worktrees/<repo-fingerprint>/<name>`, branch `openclaw/<name>`"); `openclaw sandbox` Docker isolation; `openclaw agent --agent <id> --message|--message-file --model --session-key agent:<id>:<key> --json --local --deliver --reply-channel` = headless single turn; `openclaw tui --session --message --local`.
- Evidence: openclaw package docs/gateway/cli-backends.md:10-18; docs/concepts/managed-worktrees.md:10-27; `openclaw worktrees --help`; `openclaw sandbox --help`; `openclaw agent --help`; `openclaw tui --help`.
- Level: verified
- Requirements: HB-01, HB-02, TE-08, HB-06
- Suggested fit cell: OpenClaw → S! as a Harness with headless mode + JSON output + session keys (HarnessProfile facts)

### F24. `~/.openclaw` layout on this host (structure only)
- Claim: `~/.openclaw/{agents/main/{agent/,sessions/}, completions/, crestodian/, devices/, identity/, logs/, npm/projects/, plugin-skills/, skill-workshop/proposals/ (empty), state/, tools/node/, tui/, workspace/ (.git), workspace-attestations/, openclaw.json, openclaw.json.bak*, openclaw.json.last-good}`. `openclaw.json` top-level keys: `agents.defaults{models,workspace,model}`, `meta{lastTouchedVersion="2026.7.1-2"}`, `tools{web,profile="coding"}`, `plugins.entries{codex,openai}`, `wizard`, `gateway{mode=local, auth{mode=token, token=<masked>}, port=18789, bind=loopback, tailscale, controlUi, nodes}`, `session.dmScope=per-channel-peer`, `auth.profiles.<provider:account> <masked>`, `skills.install.nodeManager=npm`, `hooks.internal.entries`. `openclaw config validate` → "Config valid". No `agents.list`, `bindings`, `channels`, `acp`, `cron` blocks present.
- Evidence: `ls -la ~/.openclaw`; `find ~/.openclaw -maxdepth 2 -type d`; masked key-dump script (§6); `openclaw config file`; `openclaw config validate`.
- Level: verified
- Requirements: XC-02, AR-04
- Suggested fit cell: n/a (host baseline: OpenClaw present but single-agent, no Telegram, no ACP)

### Part C — Web verdicts on kit claims

### F25. "Telegram bots cannot see each other's messages" — **changed (partially)**
- Claim: Telegram FAQ still says "bots will not be able to see messages from other bots regardless of mode"; but the Bots Features page says "On Telegram, bots generally **cannot see** messages from other bots. However, in specific contexts, Bot-to-Bot communication is **allowed**" and the Bot-to-Bot page documents an opt-in "Bot-to-Bot Communication Mode" in @BotFather: in groups a bot receives another bot's message if it "Contains a command mention addressed to it, such as `/command@TargetBot`" or "Is a direct reply to one of its messages", and receives all group messages if it "Is an admin in the group" with "Group Privacy Mode disabled"; private bot-to-bot needs both sides enabled (`USER_BOT_TO_BOT_DISABLED`); "Bot-to-bot communication can create infinite reply loops." OpenClaw's own docs still instruct per-bot mentions and `sessions_send`.
- Evidence: https://core.telegram.org/bots/faq; https://core.telegram.org/bots/features; https://core.telegram.org/api/bots/bot-to-bot (all accessed 2026-08-21); kit claim openclaw-multi-agent-kit/README.md:174, INSTRUCTIONS.md:342, docs/inter-agent-handoff-standard.md:12.
- Level: web
- Requirements: MS-02, MS-04
- Suggested fit cell: n/a — supports MS-04 (bot-to-bot visibility is surface capability, not a coordination bus)

### F26. Privacy mode and admin bots — **confirmed**
- Claim: "Bots with privacy mode enabled will receive: Commands explicitly meant for them (e.g., /command@this_bot). General commands from users (e.g. /start) if the bot was the last bot to send a message to the group"; "bot admins always receive **all messages**"; change via `/setprivacy` and "the bot will need to be re-added to the group for this change to take effect." OpenClaw installed docs match ("disable privacy mode via `/setprivacy`, or make the bot a group admin ... remove and re-add the bot").
- Evidence: https://core.telegram.org/bots/faq; https://core.telegram.org/bots/features (accessed 2026-08-21); openclaw package docs/channels/telegram.md:85-93,801; kit INSTRUCTIONS.md:57-61.
- Level: web + observed
- Requirements: MS-02
- Suggested fit cell: n/a

### F27. `requireMention` single-primary rule — **confirmed as OpenClaw semantics, convention as policy**
- Claim: "Plain group messages do not trigger the bot while `requireMention: true`"; "If `requireMention=false`, Telegram privacy mode must allow full visibility"; topic entries inherit group settings unless overridden; `topics."*"` sets defaults. Nothing in OpenClaw prevents two bots both at `requireMention:false` in one topic — the kit's rule is operator policy.
- Evidence: openclaw package docs/channels/telegram.md:189,542,801; kit docs/telegram-channel-architecture.md:39.
- Level: verified (installed docs) / observed
- Requirements: MS-02
- Suggested fit cell: n/a

### F28. `sessions_spawn(runtime="acp", thread:true)` on Telegram (#41004) — **changed**
- Claim: Issue #41004 "Telegram ACP mismatch: /acp spawn works in-topic, but sessions_spawn(runtime:"acp", thread:true) fails (child vs current placement)", created 2026-03-09, **Closed**; root cause: `sessions_spawn` expected `child` placement while Telegram's adapter advertised `placements: ["current"]`. In 2026.7.1-2: installed docs list Telegram among thread-supporting channels for both ACP ("**Telegram** topics (forum topics in groups/supergroups and DM topics)") and native sub-agents ("Telegram and iMessage default to binding the current conversation"); the dist error string is now generic: ``Thread bindings do not support ${placementToUse} placement for ${policy.channel}.`` (the kit-quoted literal "…ACP thread spawn for telegram" no longer exists in dist). Not reproduced here (no Telegram configured, no gateway started).
- Evidence: https://github.com/openclaw/openclaw/issues/41004 (accessed 2026-08-21); openclaw package docs/tools/acp-agents.md:316-318; docs/tools/subagents.md:290-297; dist/acp-spawn-qAw-bP3b.js, dist/lifecycle-CEK2d8iR.js (grep, §6); web docs.openclaw.ai/tools/acp-agents + /tools/subagents (accessed 2026-08-21); kit docs/acpx-telegram.md:499, docs/telegram-dm-topics.md:264.
- Level: web + observed (docs/dist); runtime behavior unverified
- Requirements: MS-02, HB-02
- Suggested fit cell: n/a

### F29. `--bind here` vs `--thread` on Telegram — **partially confirmed / unverifiable**
- Claim: Installed and web docs: "`--bind here` and `--thread ...` are mutually exclusive"; "`--bind here` only works on channels that advertise current-conversation binding; OpenClaw returns a clear unsupported message otherwise"; Telegram doc only documents `/acp spawn <agent> --thread here|auto` for topics. No document lists Telegram as supporting `--bind here`, but none states it is unsupported either (web telegram page: "does **not** mention `--bind here` as an unsupported Telegram option"). The kit's "`sessions_spawn(runtime=\"acp\")` can only be called from a `subagent:*` session" is **not** in installed/web docs; the documented restrictions are: advertised "only when ACP is enabled, the requester is not sandboxed, and an ACP runtime backend is loaded" and "If the requester session is sandboxed, ACP spawns are blocked for both `sessions_spawn({ runtime: \"acp\" })` and `/acp spawn`."
- Evidence: openclaw package docs/tools/acp-agents.md:207-211,287-289,746-749; docs/channels/telegram.md:568; web docs.openclaw.ai/tools/acp-agents, /channels/telegram (accessed 2026-08-21); kit docs/acpx-telegram.md:254,279, docs/telegram-dm-topics.md:256.
- Level: observed / web
- Requirements: HB-02, MS-02
- Suggested fit cell: n/a — "subagent-only" verdict **unverifiable** (undocumented in 2026.7.1-2; may have been version-specific behavior)

### F30. Telegram Bot API: topics exist (incl. private-chat topics), no group/bot creation, getUpdates/webhook exclusive — **confirmed**
- Claim: Bot API 10.2 (July 14, 2026). `createForumTopic/editForumTopic/closeForumTopic/reopenForumTopic/deleteForumTopic/unpinAllForumTopicMessages` added in Bot API 6.3 (Nov 5, 2022), requiring `can_manage_topics`; `message_thread_id` parameter added to `sendMessage` in 6.3; General-topic methods in 6.4; "Added support for topics in private chats" in Bot API 9.3 (Dec 31, 2025). `message_thread_id`: "Unique identifier of a message thread or forum topic to which the message belongs; for supergroups and private chats only". No `createChat`/group-creation or bot-creation method exists in the Bot API. getUpdates: "This method will not work if an outgoing webhook is set up."; setWebhook: "You will not be able to receive updates using getUpdates for as long as an outgoing webhook is set up."; FAQ: "it's not possible to get updates via long polling while an outgoing Webhook is set." Rate limits: ~1 msg/s per chat, 20 msg/min per group, ~30 msg/s broadcast. OpenClaw: "Persistent `getUpdates` 409 conflicts point to another OpenClaw gateway, script, or external poller using the same token."
- Evidence: https://core.telegram.org/bots/api; https://core.telegram.org/bots/api-changelog; https://core.telegram.org/bots/faq (accessed 2026-08-21); openclaw package docs/channels/telegram.md:269,272,512; kit docs/telegram-dm-topics.md:18-23 (DM topics) consistent with Bot API 9.3.
- Level: web + observed
- Requirements: MS-02, MS-04, XC-02
- Suggested fit cell: n/a

### F31. Kit's ACPX backend list (12) vs installed acpx aliases (18) — **changed (superset)**
- Claim: Kit lists `claude, codex, opencode, gemini, pi, copilot, cursor, droid, kimi, kiro, qwen, trae`; installed setup doc lists those plus `fast-agent, iflow, kilocode, mux, openclaw, qoder`.
- Evidence: openclaw-multi-agent-kit/docs/acpx-telegram.md:29, templates/skills/acpx-session/SKILL.md:131-146; openclaw package docs/tools/acp-agents-setup.md:28-51.
- Level: verified (installed docs)
- Requirements: HB-01, HB-08
- Suggested fit cell: n/a

### Part D — ATM V11–V13 restated with today's verdict

### F32. V11 "Telegram: can bots see other bots?" — ATM: corrected to Bot-to-Bot Communication Mode → today: **confirmed**
- Claim: ATM row: "the old FAQ ('bots will not be able to see messages from other bots') is superseded by **Bot-to-Bot Communication Mode** — opt-in per bot in BotFather; in groups delivery on `/command@TargetBot` mentions or replies; a mode-enabled **admin** bot with privacy off receives all." Today the bot-to-bot page says exactly that (F25); the FAQ sentence is still published unchanged, so official pages remain inconsistent. Note ATM's ADR 0012 treats it as "a *surface capability*, never the team coordination bus" — same stance as MS-04.
- Evidence: agent-team-manager-dev/docs/design/feasibility-report.md:34; F25 sources (accessed 2026-08-21).
- Level: web
- Requirements: MS-02, MS-04
- Suggested fit cell: n/a

### F33. V12 "What cannot be automated via Bot API?" → **Bot API confirmed; broader platform changed**
- Claim: The Bot API still has no group-creation or bot-creation method, while it does cover `promoteChatMember`, `setChatPermissions`, `createForumTopic`, invite links and pins. However, "bot creation is BotFather-only" is no longer true for the Telegram platform as a whole: a user-authorized MTProto managed-bot flow now lets an approved manager bot create and manage bots (F36). This does not add such a method to the Bot API.
- Evidence: agent-team-manager-dev/docs/design/feasibility-report.md:35; F30 sources; openclaw package docs/channels/telegram.md:512-516.
- Level: web + observed
- Requirements: MS-02, XC-02
- Suggested fit cell: n/a

### F34. V13 "Token consumption exclusivity?" → today: **confirmed**
- Claim: ATM row: "`getUpdates` and webhooks are mutually exclusive per token; one update queue per bot. **ATM provisioning must never poll a token the gateway owns** — validation uses `getMe`/`getWebhookInfo` only." Today: Bot API getUpdates/setWebhook texts unchanged (F30); OpenClaw 2026.7.1-2 guards "only one active poller can use a bot token at a time" per gateway and diagnoses 409s as an external poller.
- Evidence: agent-team-manager-dev/docs/design/feasibility-report.md:36; https://core.telegram.org/bots/api; https://core.telegram.org/bots/faq (accessed 2026-08-21); openclaw package docs/channels/telegram.md:272.
- Level: web + observed
- Requirements: MS-02, XC-02
- Suggested fit cell: n/a

### F35. ATM's recorded OpenClaw fixtures are for the same installed version
- Claim: `agent-team-manager-dev/tests/fixtures/openclaw/2026.7.1-2-s1-config-schema.raw.json` (2.46 MB) is the same schema the CLI prints today (contains `spawnAcpSessions`, `maxAgeHours`, `"oneshot"`), plus recorded `agents-list`, `skills-list`, `sessions`, `tools-effective`, `invocations`, `mcp-probe` fixtures (s1–s4). They are reusable as historical probe evidence without re-running anything.
- Evidence: fixture directory listing (§6); `openclaw config schema` size 2,476,055 bytes today vs 2,456,521 in the fixture.
- Level: verified
- Requirements: HB-01, XC-02
- Suggested fit cell: n/a

### F36. Managed bots add a user-authorized MTProto creation path — **new platform capability**
- Claim: Telegram documents managed bots that an approved manager bot can create and control after user authorization. This is an MTProto/user-authorized flow, not a Bot API method and not evidence that OpenClaw can provision managed bots.
- Evidence: https://core.telegram.org/api/bots/managed-bots; https://telegram.org/blog/ai-bot-revolution-11-new-features (accessed 2026-08-22).
- Level: web
- Requirements: MS-02, XC-02
- Suggested fit cell: no change — Telegram platform capability; OpenClaw adapter support unverified

### F37. Guest bots and bot-to-bot communication broaden Telegram delivery — **new/changed**
- Claim: Telegram documents guest bots that can be mentioned where they are not members, plus opt-in bot-to-bot communication. These affect surface reachability and bot deployment choices; they do not create a TeamRun, task DAG, or coordination substrate.
- Evidence: https://core.telegram.org/api/bots/guest-mode; https://core.telegram.org/api/bots/bot-to-bot; https://telegram.org/blog/ai-bot-revolution-11-new-features (accessed 2026-08-22).
- Level: web
- Requirements: MS-02, MS-04
- Suggested fit cell: no change

### F38. Communities and ephemeral messages are surface features — **new platform capability**
- Claim: Telegram Communities group channels, groups, and bots at the client/product layer. Telegram also documents commands/messages visible only to the bot and one group member. Neither feature is an ATS Team semantic, and Telegram's UI visibility is not proof of AD-07 hidden-Member behavior in ATS.
- Evidence: https://telegram.org/blog/communities-editor-invisible-messages; https://core.telegram.org/bots/api (accessed 2026-08-22).
- Level: web
- Requirements: AD-07, MS-02, MS-04
- Suggested fit cell: no change

### F39. Installed OpenClaw 2026.7.1-2 does not establish support for the newly checked features
- Claim: Read-only searches of installed OpenClaw docs and distribution found no guest-chat, managed-bot creation, or Telegram ephemeral-message handling symbols. The installed Telegram adapter documentation remains mature for DMs/groups, topics, multi-account routing, streaming, and rich messages. Therefore the new Telegram capabilities are recorded as platform-available/OpenClaw-support-unverified. They do not re-score MS-02, and MS-04 remains unchanged because surface topology must not define Team semantics.
- Evidence: installed OpenClaw 2026.7.1-2 `{docs,dist}` negative search; [ev:m0-product-architecture-review-2026-08-22#F6].
- Level: verified negative search + installed docs; runtime unverified
- Requirements: MS-02, MS-04, XC-02
- Suggested fit cell: no change

## 3. Negative findings

- **No team/template/nested-team object in OpenClaw.** Installed docs grep (ugrep, fixed strings, case-insensitive): `'team template' → 0 files`, `'TeamTemplate' → 0`, `'nested team' → 0`, `'sub-team' → 0`, `'role package' → 0`, `'agent template' → 0`; `'Nested sub-agents' → 2` (tools/subagents.md, docs_map) and `'maxSpawnDepth' → 3` — nesting is a per-agent *session* tree (depth 1–5) with announces, not a TeamRun with a result/archive boundary. `'team' → 83 files` but only as `bindings.match.teamId` ("team/workspace ID constraint used by providers", e.g. Slack) and prose. Web docs.openclaw.ai/concepts/multi-agent: "no mentions of 'team', 'template', or 'nested' agent concepts" (accessed 2026-08-21). `openclaw --help` has no `team*`/`template*` command (commands listed in §6).
- **No reusable role-package format in OpenClaw.** `'persona' → 109 files` but always meaning "the per-agent workspace files (`AGENTS.md`/`SOUL.md`/`USER.md`)"; `openclaw agents add` takes `--workspace --model --agent-dir --bind` only (no `--from-template`/`--persona`); skills are the only packaged unit (`openclaw skills install` from ClawHub/git/local; SKILL.md frontmatter). `openclaw migrate` imports from `hermes`/Codex, not from a role package.
- **Kit has no team or nested concept either.** grep over kit (`nested|sub-team|team template|parent team|ensemble`) → 0 relevant hits (only catalog prose: "Persona development", "Ensemble methods"); "team" in the kit = a topic lane + primary/secondary bots (docs/architecture.md:103-112). Orchestrator SOUL says "I orchestrate. I don't execute ... Subagents do the work" without any delegation API beyond `sessions_send`/`sessions_spawn`.
- **No per-agent sender identity when sharing one channel account** (installed docs/concepts/multi-agent.md:164) — so a hidden Member cannot be given a distinct Telegram face without its own bot token.
- **No Telegram/ACP on this host**: `openclaw channels list` → none; `@openclaw/telegram` plugin disabled; acpx plugin absent; `which acpx` → not found; `agents bindings` → none.
- **Kit literal error string not in dist**: `grep -rl -F "Thread bindings do not support ACP thread spawn" dist → 0`; generic template present in 3 files (§6).
- **Kit `cron.jobs` config key not in schema** (F9); **`mode:"exec"` not in enum** (F17); **`maxAgeDays`** not in schema (kit's own negative, confirmed).

## 4. Platform & license notes

- openclaw-multi-agent-kit: MIT, `openclaw-multi-agent-kit/LICENSE` ("Copyright (c) 2026 Raul Vidis"); last commit 2026-07-10 (`5d6418d`). Docs-only; platform-neutral text but assumes `~/.openclaw/...` POSIX paths and `npm install -g acpx`.
- OpenClaw 2026.7.1-2: MIT (`package.json` license field; `LICENSE` + `THIRD_PARTY_NOTICES.md` in the installed package; npm registry `"license":"MIT"`). Installed via npm (Node v24.16.0) on Ubuntu; `openclaw daemon` help mentions "launchd/systemd/schtasks" → macOS/Linux/Windows service install paths exist; `--container` flag for Podman/Docker; `sandbox` requires Docker. Not probed on Windows/macOS here.
- Telegram Bot API operations still do not create bots/groups; BotFather remains the ordinary human configuration route for tokens/privacy/bot-to-bot mode. Separately, Telegram now documents a user-authorized MTProto managed-bot flow (F36). Rate limits and single-poller token constraints remain as recorded.
- This host: Ubuntu, no tmux; OpenClaw gateway configured local/loopback (not started by this probe).

## 5. Open questions

1. Does `sessions_spawn({runtime:"acp", thread:true})` now succeed from a Telegram topic session in 2026.7.1-2 (F28)? Requires a configured bot + gateway run — out of scope for this read-only pass.
2. Is the kit's "only from `subagent:*` session" restriction (F29) a real 2026.3.x behavior that was lifted, or a misreading of the sandbox/visibility gates? No issue reference was given by the kit.
3. Is #31671 (`sessions_send` channel rewrite) still reproducible? Closed as stale, no fix commit cited.
4. How does `tools.sessions.visibility` interact with `tools.agentToAgent` for cross-agent `sessions_send` in multi-agent Telegram setups (needed before any Surface adapter relies on it)?
5. Whether `openclaw attach` (Claude Code with scoped gateway MCP) or ACP `claude` alias is the preferred path for running Claude Code *through* OpenClaw remains a design decision, not an evidence question.

## 6. Probe / CLI log

Full outputs saved under `/tmp/claude-1000/-home-wsh-Documents-assistant-team-system-dev/17fd77ac-75ce-402b-a1a9-5d1eebba9843/scratchpad/ev-openclaw-kit-native/` (`version.txt`, `help.txt`, `help-subcommands-1.txt`, `help-subcommands-2.txt`, `config-schema.json` [2,476,055 B], `plugins-list.txt`, `docs-probe.txt`). Trimmed:

```
$ openclaw --version
OpenClaw 2026.7.1-2 (0790d9f)
$ openclaw --help   # commands (trimmed): acp* agent agents* approvals* attach audit backup* capability*
  channels* chat config* configure cron* daemon* dashboard devices* directory* docs doctor gateway*
  health hooks* infer* logs mcp* memory* message* migrate* models* node* nodes* onboard pairing*
  plugins* sandbox* secrets* security* sessions* skills* status system* tasks* transcripts* tui
  update* webhooks* worktrees*
$ openclaw agents --help → add | bind | bindings | delete | list | set-identity | unbind
$ openclaw acp --help   → "Run an ACP bridge backed by the Gateway"; subcommand: client   (no `spawn`)
$ openclaw agent --help → --agent --message/--message-file --model --session-id --session-key --json --local --deliver --channel telegram|… --thinking
$ openclaw config --help → file | get | patch | schema | set | unset | validate
$ openclaw config schema | python3 (masked walker) →
  top-level keys (46): accessGroups acp agents approvals audio audit auth bindings broadcast browser
  channels cli commands commitments crestodian cron diagnostics discovery env gateway hooks logging
  marketplaces mcp media memory messages meta models nodeHost plugins proxy secrets security session
  skills surfaces talk tools transcripts tui ui update web wizard
  agents.list.runtime.acp.mode enum=['persistent','oneshot']
  channels.telegram.threadBindings keys: defaultSpawnContext enabled idleHours maxAgeHours spawnAcpSessions spawnSessions spawnSubagentSessions
  cron keys: enabled failureAlert failureDestination maxConcurrentRuns retry runLog sessionRetention store triggers webhook webhookToken
$ openclaw config file → ~/.openclaw/openclaw.json ; openclaw config validate → "Config valid"
$ openclaw agents list --json → [{"id":"main","workspace":"~/.openclaw/workspace","agentDir":"~/.openclaw/agents/main/agent","model":"openai/<model>","bindings":0,"isDefault":true}]
$ openclaw agents bindings → No routing bindings.
$ openclaw channels list → no configured chat channels
$ openclaw plugins list → Plugins (50/68 enabled); @openclaw/telegram disabled; Codex (app-server harness) enabled; no acpx entry
$ which acpx → not on PATH
$ openclaw skills list → Skills (23/57 ready) incl. bundled "coding-agent: Delegate coding work to Codex, Claude Code, or OpenCode as background workers" (needs setup)
$ openclaw docs "sessions_spawn acp telegram thread" → results incl. /gateway/config-channels, /automation/tasks, /gateway/audit ("For a child started through `sessions_spawn`, the child owns a new context...")
$ ls ~/.openclaw → agents completions crestodian devices identity logs npm openclaw.json(.bak*, .last-good) plugin-skills skill-workshop state tools tui workspace workspace-attestations
$ grep (python) installed dist → "Thread bindings do not support ${placementToUse} placement for ${policy.channel}." (dist/acp-spawn-*.js, dist/lifecycle-*.js); legacy migration deletes spawnSubagentSessions/spawnAcpSessions → spawnSessions (dist/legacy-config-migrations-*.js)
$ grep counts (installed docs): 'team template'→0 'TeamTemplate'→0 'nested team'→0 'sub-team'→0 'role package'→0 'agent template'→0 'Nested sub-agents'→2 'maxSpawnDepth'→3 'persona'→109 'team'→83
```

No gateway was started, no prompt was sent to any model, no file under `/home/wsh/Documents/00000/` or `~/.openclaw/` was modified, and no credential value was read or printed.
