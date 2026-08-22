---
id: ev:harness-caps-B
topic: HarnessCapability checklist + definition-injection matrix for OpenClaw 2026.7.1-2 and Hermes Agent v0.20.4 (worker-harness view + Surface nature)
systems: [OpenClaw, Hermes Agent, ClawTeam-OpenClaw (cross-check), ClawTeam (cross-check), agent-team-manager-dev (recorded fixtures)]
sources:
  - {kind: cli, ref: "openclaw --help / agent / tui / agents / sessions / acp / skills / hooks / approvals / mcp / config / models / audit / tasks / worktrees --help", accessed: 2026-08-22, version: "OpenClaw 2026.7.1-2 (0790d9f)"}
  - {kind: cli, ref: "hermes --help / chat / profile / config / tools / skills / sessions / kanban / hooks / approvals / mcp / acp / send / claw / import-agent --help", accessed: 2026-08-22, version: "Hermes Agent v0.20.4 (2026.8.18), git a9a4a04"}
  - {kind: repo, ref: "~/.nvm/versions/node/v24.16.0/lib/node_modules/openclaw/{docs,dist}@2026.7.1-2 (bundled, version-matched docs + built JS/.d.ts)", accessed: 2026-08-22, version: 2026.7.1-2}
  - {kind: repo, ref: "~/.hermes/hermes-agent@a9a4a04 (installed source checkout)", accessed: 2026-08-22, version: v0.20.4}
  - {kind: repo, ref: "ClawTeam-OpenClaw/clawteam/spawn/{tmux_backend,adapters,command_validation}.py, CHANGELOG.md, tests/test_openclaw_agent.py", accessed: 2026-08-22, version: v0.3.0+openclaw2}
  - {kind: repo, ref: "ClawTeam/clawteam/spawn/{adapters.py,session_locators/openclaw.py}", accessed: 2026-08-22, version: 0.3.0}
  - {kind: repo, ref: "agent-team-manager-dev/tests/fixtures/openclaw/2026.7.1-2-s{1,2,3,3b,4}-evidence.json", accessed: 2026-08-22, version: "recorded 2026-08-20 against OpenClaw 2026.7.1-2"}
  - {kind: web, ref: "https://docs.openclaw.ai/cli/agent", accessed: 2026-08-22}
  - {kind: web, ref: "https://docs.openclaw.ai/cli/tui", accessed: 2026-08-22}
  - {kind: web, ref: "https://github.com/openclaw/openclaw", accessed: 2026-08-22}
  - {kind: web, ref: "https://hermes-agent.nousresearch.com/docs/reference/cli-commands", accessed: 2026-08-22}
  - {kind: web, ref: "https://hermes-agent.nousresearch.com/docs/user-guide/profiles", accessed: 2026-08-22}
  - {kind: web, ref: "https://github.com/NousResearch/hermes-agent", accessed: 2026-08-22}
method: Read-only `--help` trees of both installed CLIs (no prompts sent, no gateway started); read the version-matched docs bundled in the OpenClaw npm package and the Hermes source checkout; grepped OpenClaw `dist/*.js|*.d.ts` option strings and env names; dumped `openclaw config schema` and extracted key sets; ran only listing commands (`agents list --json`, `skills list --json`, `hooks list`, `plugins list`, `models list --plain`, `hermes profile list`, `hermes skills list`); inspected ~/.openclaw and ~/.hermes structure with credential-like keys redacted; cross-checked the ClawTeam fork/upstream spawn forms against the installed flags; reused ATM's recorded OpenClaw fixtures; six WebFetch lookups for live-doc/licence confirmation.
platform: {os: Ubuntu (Linux 5.15), tmux: absent, cli_versions: {openclaw: "2026.7.1-2 (0790d9f)", hermes: "v0.20.4 (2026.8.18)", node: "v24.16.0", python(hermes venv): "3.11.16"}}
author_agent: ev:harness-caps-B
date: 2026-08-22
confidence: high
status: draft
---
# OpenClaw and Hermes Agent as worker harnesses — capability checklist and definition-injection matrix

## 1. Scope & questions

- Which of the 15 HarnessCapability rows does each harness support, with exact flag/config names? → HB-01, HB-02, HB-03, HB-05, HB-07, HB-08, TE-03.
- How would an Assistant definition reach each harness without being changed, what cannot be injected, and can each run be a fresh instance (vs. OpenClaw's persistent `agents.list` agents)? → HB-02, AD-04, AD-05, TE-02, AD-07.
- Do the spawn forms used by ClawTeam upstream (`openclaw agent --local --session-id --message`) and the fork (`openclaw tui --session … --message … --model --agent`; `hermes chat --yolo --source tool -q`) exist on the installed CLIs today? → HB-01, HB-08.
- What is each harness's Surface/bot nature and how separable is it from the worker role? → MS-01, MS-02, MS-03, MS-04, AD-06.
- Platform and licence facts. → TE-08, XC-01, XC-02.

## 2. Findings

### F1. OpenClaw has a one-turn headless command: `openclaw agent` (with `--local` for no-Gateway runs)
- Claim: `openclaw agent` runs exactly one agent turn; it needs one session selector (`--to`, `--session-key`, `--session-id`, or `--agent`), takes `-m/--message <text>` or `--message-file <path>` (exactly one), `--model <id>`, `--thinking <level>`, `--timeout <seconds>` (default 600), `--json`, `--local` ("Run the embedded agent locally (requires model provider API keys in your shell)"). `--json` reserves stdout for the JSON response; diagnostics go to stderr; embedded-fallback JSON carries `meta.transport:"embedded"`, `meta.fallbackFrom:"gateway"`. `--local` runs are one-shot: "bundled MCP loopback resources and warm Claude stdio sessions opened for the run are retired after the reply".
- Evidence: CLI log §6 (`openclaw agent --help`); OpenClaw docs `docs/cli/agent.md` (bundled, 2026.7.1-2) "## Options"/"## Notes"; https://docs.openclaw.ai/cli/agent (accessed 2026-08-22) lists the same 17 flags.
- Level: verified (CLI help) / observed (docs)
- Requirements: HB-01, HB-02, HB-07, MS-01
- Suggested fit cell: OpenClaw → S! (headless run)

### F2. `openclaw tui` has no `--agent` and no `--model` flag in 2026.7.1-2 (nor in the live docs)
- Claim: The full option set of `openclaw tui|terminal` is `--deliver --history-limit <n> --local --message <text> --password --session <key> --thinking <level> --timeout-ms <ms> --token --url`. Agent selection happens implicitly ("Launched from inside a configured agent workspace directory, TUI auto-selects that agent") or through a prefixed `--session agent:<id>:…`. `openclaw chat` = `tui --local`.
- Evidence: CLI log §6; dist grep `tui-cli-DI2ZjVRm.js` option strings `"--deliver" "--history-limit <n>" "--local" "--message <text>" "--password <password>" "--session <key>" "--thinking <level>" "--timeout-ms <ms>" "--token <token>" "--url <url>"`; https://docs.openclaw.ai/cli/tui (accessed 2026-08-22): "Neither `--agent` nor `--model` appear" (live page additionally lists `--tls-fingerprint`, i.e. docs are newer than the installed build).
- Level: verified
- Requirements: HB-01, HB-08
- Suggested fit cell: n/a (cross-check)

### F3. Fork spawn form: `--session`/`--message` valid, `--agent` correctly probe-gated, `--model` appended unguarded
- Claim: `ClawTeam-OpenClaw/clawteam/spawn/command_validation.py:302-307` normalizes bare `openclaw` to `[openclaw, "tui"]` (comment: "OpenClaw >= 2026.6 made `openclaw agent` a single-turn command that requires an explicit session target, so a resident worker must run the interactive TUI instead"). `tmux_backend.py:231-240` then appends `--session clawteam-<team>-<agent>`, `--model <model>` (if a model resolved), `--agent <id>` (only if `_openclaw_supports_agent_flag()` at `tmux_backend.py:52-63` found `--agent` in `openclaw tui --help`), `--message <prompt>`. On 2026.7.1-2 the `--agent` probe returns False (graceful drop, warning "worker isolation is handled via OPENCLAW_WORKSPACE instead"), but `--model` is not probed, so any model-resolved spawn yields `openclaw tui --session … --model …` with a flag the installed CLI does not define. The fork's own test only asserts `tui` + `--session` (`tests/test_openclaw_agent.py:50-80`); CHANGELOG says the form was "verified live on OpenClaw 2026.6.11" (`CHANGELOG.md:31`).
- Evidence: file:line above; F2.
- Level: observed (source) / inferred (runtime failure of `--model` not executed here)
- Requirements: HB-01, HB-08, XC-03
- Suggested fit cell: ClawTeam-OpenClaw → Xs~ (OpenClaw spawn adapter needs version probing for `--model`)

### F4. Correction to recon: `OPENCLAW_WORKSPACE` is not an OpenClaw env var; the override is `OPENCLAW_WORKSPACE_DIR`
- Claim: The fork sets `env_vars["OPENCLAW_WORKSPACE"] = worker_ws` (`tmux_backend.py:168`) to isolate workers from the user's SOUL.md/AGENTS.md. OpenClaw 2026.7.1-2 reads `OPENCLAW_WORKSPACE_DIR` (docs: "`OPENCLAW_WORKSPACE_DIR` overrides both of the above when set"); a grep of all `dist/*.js` for `OPENCLAW_WORKSPACE[A-Z_]*` finds only `OPENCLAW_WORKSPACE_DIR` (3 hits, 2 files) and zero hits for the bare name. So the fork's worker-workspace isolation is a no-op on this version and workers inherit the default agent's bootstrap files. The recon appendix wording "worker-workspace isolation (`~/.clawteam/worker-workspace`, `OPENCLAW_WORKSPACE`)" should read "…intended via `OPENCLAW_WORKSPACE`, which OpenClaw 2026.7.1-2 does not read".
- Evidence: `docs/concepts/agent-workspace.md` "## Default location"; `docs/concepts/multi-agent.md` "## Paths" table; dist grep (§6); `ClawTeam-OpenClaw/clawteam/spawn/tmux_backend.py:66-75,164-168`.
- Level: verified (grep) / observed
- Requirements: HB-02, TE-02, AD-05
- Suggested fit cell: ClawTeam-OpenClaw → Xs~

### F5. Upstream ClawTeam form `openclaw agent --local --session-id <agent> --message <prompt>` exists but is single-turn
- Claim: `ClawTeam/clawteam/spawn/adapters.py:104-115` emits `agent --local --session-id <agent_name> --message <prompt>` (or `--session <agent_name> --message` for non-`agent` subcommands). All flags exist (F1). Because `openclaw agent` returns after one turn, a ClawTeam "resident worker" built on it exits immediately (the fork's stated reason for switching to `tui`). Upstream's session locator resumes with `--session agent:main:resume:<id>` or `--session-id <id>` (`session_locators/openclaw.py:72-78`) and discovers sessions from `~/.openclaw/agents/*/sessions/*.jsonl` + `sessions.json` (`:53-60`).
- Evidence: file:line above; `ClawTeam-OpenClaw/CHANGELOG.md:31`.
- Level: observed
- Requirements: HB-01, TE-02
- Suggested fit cell: ClawTeam → C~ (one-shot OpenClaw invocation works; resident worker does not)

### F6. Fork Hermes form `hermes chat --yolo --source tool -q <prompt>` is valid on Hermes 0.20.4
- Claim: `hermes chat` accepts `-q/--query`, `--yolo`, `--source SOURCE` ("Session source tag for filtering (default: cli). Use 'tool' for third-party integrations that should not appear in user session lists"), `-m/--model`, `--provider`, `-Q/--quiet`, `--in DIR`, `--worktree`, `--max-turns N`, `--accept-hooks`, `--resume`, `-c/--continue [NAME]`, `--create-if-missing`, `--ignore-rules`, `--ignore-user-config`, `--safe-mode`, `-s/--skills`, `-t/--toolsets`, `--reasoning`. The fork inserts `chat`, appends `--source tool`, `-m <model>`, `-q <prompt>`, and `--yolo` when skip-permissions (`ClawTeam-OpenClaw/clawteam/spawn/adapters.py:59-80`, `tmux_backend.py:251-268`); it deliberately never passes `--continue`. Hermes is absent from upstream ClawTeam (`grep -rn -i hermes ClawTeam/clawteam/` → 0).
- Evidence: CLI log §6 (`hermes chat --help`); `hermes-agent/hermes_cli/_parser.py:304,487-490`; https://hermes-agent.nousresearch.com/docs/reference/cli-commands (accessed 2026-08-22).
- Level: verified
- Requirements: HB-01, HB-08
- Suggested fit cell: ClawTeam-OpenClaw → S! (Hermes spawn flags)

### F7. Hermes has a pure one-shot mode with a machine-readable usage report
- Claim: `hermes -z/--oneshot PROMPT` prints only the final response text to stdout ("No banner, no spinner, no tool previews, no session_id line… approvals are auto-bypassed"); `--usage-file PATH` writes a JSON usage report "(estimated cost, token counts, model, api_calls)… even when the run fails". In `-q` mode without `--yolo`, dangerous commands are refused with the message "BLOCKED: Command flagged as dangerous … single-query mode (-q) runs without a user present to approve it … set approvals.single_query_mode: approve in config.yaml"; plugin-gated actions "fail CLOSED" in non-interactive non-gateway contexts.
- Evidence: `hermes --help` (§6); `hermes-agent/tools/approval.py:3780-3789, 3834-3838`; `cli.py:15755-15762` (report keys `final_response, messages, api_calls, completed, failed, error`).
- Level: verified (help) / observed (source)
- Requirements: HB-01, HB-07, AD-03
- Suggested fit cell: Hermes → S! (headless + cost record)

### F8. OpenClaw definition injection = workspace bootstrap files; there is no system-prompt CLI flag
- Claim: OpenClaw "builds its own system prompt for every agent run; there is no runtime default prompt." Workspace files injected on every run: `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `IDENTITY.md`, `USER.md`, `HEARTBEAT.md`, `BOOTSTRAP.md` (new workspaces only), `MEMORY.md` (when present); limits `agents.defaults.bootstrapMaxChars` (20000) / `bootstrapTotalMaxChars` (60000); `agents.defaults.contextInjection` `always|continuation-skip|never`; `agents.defaults.skipBootstrap` stops auto-creation; the `agent:bootstrap` internal hook exposes `context.bootstrapFiles` (mutable) "for example swapping SOUL.md for an alternate persona"; bundled hook `bootstrap-extra-files` injects extra files but "Only recognized bootstrap basenames are loaded". Sub-agent sessions inject only `AGENTS.md` and `TOOLS.md`. The only per-invocation text channel is `--message`/`--message-file` (user turn), i.e. a prompt prefix, not a system prompt. Neither `agent` nor `tui` exposes `--system-prompt`/`--append-system-prompt` (dist option-string grep, §6).
- Evidence: `docs/concepts/system-prompt.md` (intro, "## Workspace bootstrap injection"); `docs/automation/hooks.md:65,158,226,262`; `docs/gateway/config-agents.md:64-102`; F1/F2 option lists.
- Level: observed / verified (flags)
- Requirements: HB-02, AD-01, AD-09
- Suggested fit cell: OpenClaw → C~ (definition via files in a per-run workspace) / Xs~ if a per-run system prompt is required

### F9. `agents.list[]` is the per-agent unit; its schema keys define what can be bound per Assistant
- Claim: `openclaw config schema` → `agents.list[]` keys: `agentDir, bootstrapMaxChars, bootstrapTotalMaxChars, contextInjection, contextLimits, contextTokens, default, description, embeddedAgent, experimental, fastModeDefault, groupChat, heartbeat, humanDelay, id, identity{avatar,emoji,name,theme}, memorySearch, model, models, name, params, reasoningDefault, runRetries, runtime{type: "embedded"|"acp"}, sandbox{backend,mode,scope,workspaceAccess,workspaceRoot,…}, skills[] (allowlist; non-empty list is final), skillsLimits, subagents{allowAgents,delegationMode,model,requireAgentId,thinking}, thinkingDefault, toolProgressDetail, tools{allow,alsoAllow,deny,profile,exec,fs,elevated,sandbox,…}, tts, utilityModel, verboseDefault, workspace`. Per-agent paths: workspace `<stateDir>/workspace-<agentId>` (or `agents.list[].workspace`), state `~/.openclaw/agents/<agentId>/agent`, sessions `~/.openclaw/agents/<agentId>/sessions`. Agent ids are normalized to `^[a-z0-9][a-z0-9_-]{0,63}$` (ATM probe). `agents.entries` is rejected by the schema.
- Evidence: schema dump (§6); `dist/agent-scope-COpr6UvA.d.ts:11-40` (`ResolvedAgentConfig`); `docs/concepts/multi-agent.md` "## Paths"; `agent-team-manager-dev/tests/fixtures/openclaw/2026.7.1-2-s1-evidence.json` (`u11.observedConstraints`, `u1.dryRun.agentsEntries.errors`).
- Level: verified (schema) / observed
- Requirements: HB-02, AD-04, AD-06, TC-04
- Suggested fit cell: OpenClaw → C!

### F10. OpenClaw agents are persistent, config-materialized entities; per-run freshness is achievable by session key or disposable profile, not by an ephemeral-agent primitive
- Claim: `openclaw agents add <name> --workspace <dir> [--model] [--agent-dir] [--bind] --non-interactive --json` writes `agents.list` and also creates the workspace, `git init`s it, seeds bootstrap files and creates `agents/<id>/sessions` (ATM s2: 41 added paths; "agentsAddPerformsOtherNonConfigProvisioning: true"); the added agent was visible to the running Gateway before restart and persisted after. `openclaw agents delete <id> --force` prunes workspace/state. Fresh context on an existing agent = a new session key (`--session-key agent:<id>:<run-key>`; ATM s3: "distinctTuplesLandedInDistinctContexts: true, sameTuplePreservedState: true, restartSurvival: true"). A disposable whole instance = `openclaw --profile <name>` (isolates `OPENCLAW_STATE_DIR`/`OPENCLAW_CONFIG_PATH` under `~/.openclaw-<name>`) or `--dev`. No schema key expresses an ephemeral/TTL agent (grep `ephemeral|ttl` under `agents.list` → 0). Sub-agent sessions (F12) are the only runtime-created, auto-archived unit.
- Evidence: `openclaw agents add/delete --help`; `agent-team-manager-dev/tests/fixtures/openclaw/2026.7.1-2-s2-evidence.json` (`u4.*`), `…-s3-evidence.json` (`u9.*`, candidates A/B); `openclaw --help` (`--profile`, `--dev`); `docs/concepts/multi-agent.md`.
- Level: observed (ATM recorded probe) / verified (help)
- Requirements: TE-02, AD-05, AD-07, TE-07
- Suggested fit cell: OpenClaw → P~ (fresh run by composition: profile or session key) / M~ for "Assistant = agent id" mapping

### F11. OpenClaw skills: AgentSkills `SKILL.md`, six load roots, per-agent allowlist, shared `~/.agents/skills` visible to OpenClaw
- Claim: Load order (highest first): `<workspace>/skills`, `<workspace>/.agents/skills`, `~/.agents/skills`, `~/.openclaw/skills`, bundled, `skills.load.extraDirs` + plugin skills. Visibility is controlled separately by `agents.defaults.skills` / `agents.list[].skills` ("A non-empty `agents.list[].skills` list is the final set"). Gating via `metadata.openclaw.requires` (bins/env/config/OS). `openclaw skills install` from ClawHub, git or local dir (`--global` → `~/.openclaw/skills`). On this host `openclaw skills list --json` returns 57 skills: 51 `openclaw-bundled`, 2 `openclaw-extra`, 4 `agents-skills-personal` (`code-review`, `design-taste-frontend`, `find-skills`, `frontend-design` — i.e. the user's `~/.agents/skills` shared with other harnesses), all 4 eligible.
- Evidence: `docs/tools/skills.md:32-75,77-110,235-300`; CLI log §6 (`skills list --json` summary); `openclaw skills --help`.
- Level: verified (listing) / observed
- Requirements: AR-02, AR-03, HB-02, AD-02
- Suggested fit cell: OpenClaw → S!

### F12. OpenClaw sub-agents: `sessions_spawn` tool, isolated sessions, depth/children limits, ACP runtime for external harnesses
- Claim: Sub-agents run in `agent:<agentId>:subagent:<uuid>` sessions, are tracked as background tasks (`openclaw tasks list --runtime subagent|acp|cron|cli`), announce completion back to the requester, and by default "do **not** get session or message tools". `context: "isolated"` (default) or `"fork"`. `promptMode=minimal` for sub-agents. Config: `agents.defaults.subagents.{maxSpawnDepth ("1 = no nesting (default)"), maxChildrenPerAgent (default 5), maxConcurrent, model, thinking, delegationMode suggest|prefer, runTimeoutSeconds, archiveAfterMinutes, allowAgents, requireAgentId}`; per-agent override `agents.list[].subagents`; `tools.subagents.tools` narrows child tools; `tools.sessions.visibility` `self|tree|agent|all`. `sessions_spawn` requires tool profile `coding`/`full` or `tools.alsoAllow`. `runtime: "acp"` dispatches to external harnesses via the `acpx` plugin (`claude`, `codex`, `gemini`, `opencode`, `cursor`, `droid`, `pi`…; Hermes is not in the list); `agents.list[].runtime.type="acp"` maps an agent to an ACP harness.
- Evidence: `docs/tools/subagents.md` (intro, "Spawn behavior", "Context modes", "Tool: sessions_spawn", "Delegation prompt mode"); `docs/tools/acp-agents.md:90-120`; schema dump (§6); `openclaw tasks --help`.
- Level: observed (docs + schema)
- Requirements: TE-04, TE-05, AD-07, TC-05, HB-08
- Suggested fit cell: OpenClaw → C~ (dynamic hidden member within one OpenClaw agent) / P~ (nested run via acp)

### F13. OpenClaw session/archive/audit surfaces
- Claim: Session store `~/.openclaw/agents/<agentId>/sessions/sessions.json` + `<sessionId>.jsonl`; `openclaw sessions [list] --json --agent|--all-agents --active --store`; `sessions export-trajectory --session-key … --json` ("redacted trajectory bundle"); `openclaw transcripts list|path|show`; `openclaw audit --json --kind agent_run|tool_action --agent --session --run --status started|succeeded|failed|cancelled|timed_out|blocked`; `openclaw tasks show <id> --json`. `sessions` "Shows token usage per session when the agent reports it".
- Evidence: CLI log §6; `docs/concepts/session.md:114-128`.
- Level: verified (help)
- Requirements: TE-07, HB-07, XC-04
- Suggested fit cell: OpenClaw → S!

### F14. OpenClaw cwd, permission, model and hook controls
- Claim: cwd: the workspace "is the **default cwd**, not a hard sandbox"; set via `agents.list[].workspace` / `agents.defaults.workspace` / `OPENCLAW_WORKSPACE_DIR`; no `--cwd` on `agent`/`tui` (only `acp client --cwd`); `openclaw worktrees create <repoRoot> --name --base-ref --json`. Permissions: `tools.exec.mode` `deny|allowlist|ask|auto|full` (default `security: full` on gateway/node hosts, `deny` in sandbox); approvals file per execution host; `openclaw approvals allowlist add --agent "*" "/abs/path"`; per-agent `tools.{allow,deny,profile}`; "Plugin approval gates still apply in local mode". Model: `--model provider/model` per run; `agents.list[].model`; `agents.defaults.model {primary, fallbacks}`; model-scoped `agentRuntime.id` (`codex`, `claude-cli`); CLI backends (`agents.defaults.cliBackends`, e.g. `--model claude-cli/claude-sonnet-4-6`) run a local CLI as a text-only fallback. Hooks: `hooks.internal.entries.<name>.enabled`; bundled `boot-md` (`gateway:startup` → `BOOT.md`), `bootstrap-extra-files`, `session-memory`, `command-logger`, `compaction-notifier`; events include `agent:bootstrap`, `command:*`, `session:patch`, `gateway:shutdown`; hooks "run inside the Gateway". On this host: `session-memory` enabled, 5/5 hooks ready, 50/68 plugins enabled.
- Evidence: `docs/concepts/agent-workspace.md` (warning block); `docs/tools/exec-approvals.md:129-160`; `docs/tools/permission-modes.md`; `docs/gateway/config-agents.md:353-484`; `docs/gateway/cli-backends.md`; `docs/automation/hooks.md:9,46-65,198-229`; CLI log §6; `~/.openclaw/openclaw.json` key dump (§6).
- Level: observed / verified (help, config keys)
- Requirements: HB-01, HB-03, HB-04, AD-03
- Suggested fit cell: OpenClaw → S! (model/permissions) / C~ (cwd)

### F15. OpenClaw is Gateway/channel-centric, but the worker path needs no Gateway
- Claim: Product framing: "The Gateway is just the control plane — the product is the assistant"; agents bind to channel accounts via `bindings` (Telegram/Discord/WhatsApp…: "one bot per agent"); visible identity is `agents.list[].identity {name, emoji, avatar, theme}` / `IDENTITY.md` (`openclaw agents set-identity --from-identity`), separate from `id`. `openclaw agent --local` and `openclaw tui --local` run the embedded runtime without a Gateway; `openclaw agent` without `--local` "Falls back to the embedded agent if the Gateway request fails". Cross-agent messaging is governed by `tools.agentToAgent {enabled, allow[]}` (global allowlist; ATM U10: not project-confinable) and `session.agentToAgent`.
- Evidence: `README.md:22,33`; `docs/concepts/multi-agent.md`; `docs/cli/agent.md` intro; schema dump; `agent-team-manager-dev/tests/fixtures/openclaw/2026.7.1-2-s3-evidence.json` (`a2aConfinement: false`).
- Level: observed
- Requirements: MS-01, MS-02, MS-03, MS-04, AD-06, TC-03
- Suggested fit cell: OpenClaw → S! (MS-02 surface adapter) / M~ (MS-04 if agent ids were team semantics)

### F16. OpenClaw platform and licence
- Claim: MIT (LICENSE: "Copyright (c) 2026 OpenClaw Foundation"); `engines.node ">=22.22.3 <23 || >=24.15.0 <25 || >=25.9.0"`; Linux "fully supported… requires Node" (systemd user unit via `openclaw gateway install`); macOS menu-bar app + launchd; Windows: "native **Windows Hub** companion app plus Windows CLI support", PowerShell installer `install.ps1`, managed startup via Scheduled Tasks, "WSL2 remains the most Linux-compatible Gateway runtime on Windows"; `dist` has 85 files branching on `process.platform === "win32"`. Live GitHub page states platforms "macOS, Linux, Windows (via WSL2)".
- Evidence: `openclaw/package.json`, `openclaw/LICENSE`; `docs/platforms/{linux,macos,windows}.md`; dist grep (§6); https://github.com/openclaw/openclaw (accessed 2026-08-22).
- Level: verified (files) / observed
- Requirements: TE-08, XC-01, XC-02
- Suggested fit cell: OpenClaw → S~ (Ubuntu/macOS) / C~ (Windows native CLI)

### F17. Hermes system-prompt injection: `SOUL.md` (profile home), `agent.system_prompt`/`display.personality` overlay, `HERMES_EPHEMERAL_SYSTEM_PROMPT` env; no CLI flag
- Claim: `build_system_prompt_parts` assembles `stable` (identity = `SOUL.md` from the agent's own HERMES_HOME or `DEFAULT_AGENT_IDENTITY`, tool docs, platform hints), context files, and `volatile` (skills index, memory snapshot, USER.md, timestamp). The session overlay is resolved as `HERMES_EPHEMERAL_SYSTEM_PROMPT` env > `display.personality` (named built-in/user personality) > `agent.system_prompt` ("the user-owned manual overlay"); it "is NOT included here. It's injected at API-call time only so it stays out of the cached/stored system prompt". `--ignore-rules` skips "AGENTS.md, SOUL.md, .cursorrules, memory, and preloaded skills"; `--safe-mode` also disables user config, plugins, MCP. No `--system-prompt`/`--append-system-prompt` flag exists on `hermes`/`hermes chat` (help + `_parser.py`).
- Evidence: `hermes-agent/agent/system_prompt.py:12-21,375-390,741-744`; `agent/prompt_builder.py:2258-2290`; `hermes_cli/personality.py:1-60,150-161`; `cli.py:5155-5170`; CLI log §6.
- Level: observed (source) / verified (flags)
- Requirements: HB-02, AD-01, AD-09
- Suggested fit cell: Hermes → C! (SOUL.md in a per-run profile + env overlay)

### F18. Hermes workspace instruction files: AGENTS.md directory chain, CLAUDE.md, .cursorrules, `.hermes.md`
- Claim: Context files are loaded from the cwd (`TERMINAL_CWD` in gateway mode, `terminal.cwd`/`--in DIR` otherwise): `AGENTS.override.md` / `AGENTS.md` / `agents.md` merged along the directory chain from git root down to cwd ("`AGENTS.override.md` wins over `AGENTS.md`"), `CLAUDE.md`, `.cursorrules`, and `.hermes.md`/`HERMES.md` ("walk to git root"); content is scanned for prompt injection and head/tail-truncated at `context_file_max_chars`. `skip_context_files=True` with `load_soul_identity=True` keeps SOUL.md but drops project files.
- Evidence: `agent/prompt_builder.py:2211-2330` (`_load_hermes_md`, `_agents_md_directory_chain`, `_load_agents_md`); `agent/agent_init.py:612-618`; `agent/coding_context.py:82-86`.
- Level: observed
- Requirements: HB-02
- Suggested fit cell: Hermes → S~

### F19. Hermes profiles are the isolation unit; the kanban dispatcher already spawns one headless Hermes per task per profile
- Claim: A profile "is a separate Hermes home directory" (`~/.hermes/profiles/<name>`: `config.yaml`, `.env`, `SOUL.md`, `memories/`, `sessions/`, `skills/`, cron, `state.db`); selected by `-p/--profile <name>` (consumed before argparse, hence absent from `hermes --help`; `_parser.py:11-19`) which sets `HERMES_HOME`; wrapper alias `~/.local/bin/<name>`; `hermes profile create <name> [--clone (config.yaml, .env, SOUL.md, skills) | --clone-all | --clone-from SRC] [--description "<role>" — "Used by the kanban decomposer to route tasks based on role"] [--no-skills]`; `profile export/import` (.tar.gz); `profile install <git-url|dir>`/`update` via `distribution.yaml` (`name`, `version`, `hermes_requires`, `env_requires[]`; `.env`, `auth.json`, `memories/`, `sessions/`, `state.db*` hard-excluded). Docs: "Never point two agent processes at the same profile"; "Profiles do **not** sandbox the agent". The kanban dispatcher spawns workers as `hermes -p <profile> --cli --accept-hooks [-m …] [--provider …] [--reasoning …] [--toolsets …] [--skills …]* -q <prompt> [-Q]` with `cwd=workspace`, `stdin=DEVNULL`, `HERMES_PROFILE=<profile>` (`kanban_db.py:10828-10905`); `hermes kanban create … --workspace scratch|worktree|worktree:<path>|dir:<path> --assignee <profile> --parent <id> --model --provider --skill --max-runtime --idempotency-key --json`. On this host: one profile (`default`, 82 skills).
- Evidence: `hermes profile --help`, `profile create --help`, `kanban create --help` (§6); `hermes_cli/profiles.py:5-15,44-75,117-126`; `website/docs/user-guide/profiles.md:7-19,51-57,98-107,129-152`; `website/docs/user-guide/profile-distributions.md:31-62,117-140`; https://hermes-agent.nousresearch.com/docs/user-guide/profiles (accessed 2026-08-22).
- Level: verified (help, listing) / observed (source, docs)
- Requirements: AD-05, TE-02, HB-02, TE-04, TE-06
- Suggested fit cell: Hermes → C! (fresh profile per Assistant/run) / S~ (kanban = in-harness task DAG)

### F20. Hermes skills, MCP, sub-agents, resume, cwd, structured output
- Claim: Skills: `~/.hermes/skills/<category>/<name>/SKILL.md` (82 installed; `hermes skills list --source all|hub|builtin|local`), `hermes skills install <id|SKILL.md URL>` (skills.sh/GitHub/ClawHub), repo-local `./.hermes/skills` and `./.agents/skills` after `hermes skills trust`, preload `-s/--skills`, `hermes bundles`. MCP: `hermes mcp add <name> --url|--command --args … --env` → config key `mcp_servers` (`hermes_cli/config.py:1955`); `hermes mcp serve`; none configured locally. Sub-agents: `delegate_task` ("Spawn one or more subagents in isolated contexts"); `DELEGATE_BLOCKED_TOOLS = {delegate_task (no recursive delegation), clarify, memory, send_message, cronjob}`; shared `IterationBudget` (`delegation.max_iterations: 250` here); `--worktree` isolation. Resume: `--resume <id>|latest`, `-c/--continue [name]`, `--create-if-missing`, `--in DIR`; SQLite `state.db`; `hermes sessions list --source … --workspace …`, `sessions export` (JSONL/Markdown/QMD). cwd: `--in DIR`, `terminal.cwd`, `--worktree`. Structured output: only `-z --usage-file` JSON and `hermes send --json`; `chat` has no `--json`.
- Evidence: CLI log §6; `tools/delegate_tool.py:50-58,4731-4760`; `agent/skill_utils.py:624-631`; `~/.hermes/config.yaml` key dump (§6).
- Level: verified (help) / observed
- Requirements: AR-02, AR-03, HB-01, TE-04, TE-02, HB-07
- Suggested fit cell: Hermes → S! (skills, MCP, resume) / C~ (structured output)

### F21. Hermes permissions, model selection, hooks
- Claim: `--yolo` sets `HERMES_YOLO_MODE=1` before plugin discovery (`main.py:11599-11607`); `hermes approvals suggest|test` mine/dry-run the `command_allowlist`; `--accept-hooks` auto-approves unseen shell hooks declared in `config.yaml` (`hooks:`), which "can block or fail closed" on `pre_tool_call`; gateway hooks `~/.hermes/hooks/<name>/{HOOK.yaml,handler.py}` with events `session:start|end|reset|compress`, `agent:start|step`, `command:*`; plugin hooks `pre_tool_call`, `post_tool_call`, `on_session_start`, `on_session_end`; outbound webhooks. Model: `-m`, `--provider` (built-in or user-defined `providers:`), `--reasoning none…ultra`, `hermes fallback add/remove` (chain tried when the primary fails), `hermes moa`. None of the hook kinds are configured on this host.
- Evidence: CLI log §6; `website/docs/user-guide/features/hooks.md:13-20,74-88,361-440`; `tools/approval.py:37`.
- Level: verified (help) / observed
- Requirements: HB-01, HB-03, HB-04, AD-03
- Suggested fit cell: Hermes → S!

### F22. Hermes platform, licence, Surface nature
- Claim: MIT ("Copyright (c) 2025 Nous Research"; `pyproject.toml` `license = "MIT"`); Python 3.11 (installed venv 3.11.16); README: "Linux, macOS, WSL2, Termux" and "Windows (native, PowerShell)… CLI, gateway, TUI, and tools all work natively… Native Windows install lives under `%LOCALAPPDATA%\hermes`"; 75 source files branch on `sys.platform`; kanban uses `CREATE_NO_WINDOW` on Windows. Surfaces: `hermes gateway` (Telegram, Discord, Slack, WhatsApp, Signal, Weixin, …), `profile_routes` (route inbound platform/guild/chat/thread to a profile), `hermes send --to platform[:chat_id[:thread_id]]`, `hermes peer` (bot-to-bot DMs), `--source` tag separating tool-originated sessions from user sessions, `hermes acp` (ACP server for editors), `hermes serve` (headless backend). Hermes also imports other harnesses' setups (`hermes import-agent claude-code|codex`, `hermes claw migrate` from OpenClaw) and OpenClaw imports Hermes (`openclaw migrate hermes`).
- Evidence: `hermes-agent/LICENSE`, `pyproject.toml:17`, `README.md:37-59`; `docs/profile-routing.md`; CLI log §6; `openclaw/docs/install/migrating-hermes.md`; https://github.com/NousResearch/hermes-agent (accessed 2026-08-22).
- Level: verified (files) / observed
- Requirements: TE-08, XC-01, XC-02, MS-01, MS-02, MS-03
- Suggested fit cell: Hermes → S~ (all three OS) / S! (MS-02 surface)

### F23. HarnessCapability checklist (15 rows)

| # | Capability | OpenClaw 2026.7.1-2 | Hermes v0.20.4 |
|---|---|---|---|
| 1 | Headless run | `openclaw agent --local -m/--message-file … --session-key/--session-id/--agent` (one turn) — **S!** | `hermes chat -q … [-Q] [--yolo]`; `hermes -z … --usage-file` — **S!** |
| 2 | System-prompt injection | No flag; workspace `SOUL.md`/`AGENTS.md` etc. injected per run; `agent:bootstrap` hook — **C~** | No flag; `SOUL.md` in HERMES_HOME + `HERMES_EPHEMERAL_SYSTEM_PROMPT` / `agent.system_prompt` / `display.personality` — **C!** |
| 3 | Prompt prefix | `--message`/`--message-file` (user turn) — **S!** | `-q`/`-z` text; `agent.prefill_messages_file` — **S!** |
| 4 | Workspace instruction files | `AGENTS.md, SOUL.md, TOOLS.md, IDENTITY.md, USER.md, HEARTBEAT.md, BOOTSTRAP.md, MEMORY.md` (workspace only) — **S!** | `AGENTS(.override).md` chain, `CLAUDE.md`, `.cursorrules`, `.hermes.md` (cwd→git root) — **S~** |
| 5 | Skills | AgentSkills `SKILL.md`; 6 roots incl. `~/.agents/skills`; `agents.list[].skills` allowlist — **S!** | `~/.hermes/skills`, repo `./.agents/skills` (trusted), `-s`, bundles — **S!** |
| 6 | MCP config | `mcp.servers` + `openclaw mcp add/set/probe`; `openclaw attach` (Claude Code grant) — **S!** | `mcp_servers` + `hermes mcp add`; `hermes mcp serve` — **S!** |
| 7 | Sub-agents | `sessions_spawn` (depth/children limits, `runtime:"acp"`) — **S!** | `delegate_task` (no recursion), kanban swarm — **S!** |
| 8 | Session resume | `--session-id`/`--session-key`; `sessions list --json` — **S!** | `--resume ID|latest`, `-c [name]`, `--create-if-missing` — **S!** |
| 9 | cwd control | workspace = default cwd (`agents.list[].workspace`, `OPENCLAW_WORKSPACE_DIR`); no `--cwd` — **C~** | `--in DIR`, `terminal.cwd`, `--worktree` — **S!** |
| 10 | Structured output | `agent --json` (payloads, meta, deliveryStatus); `audit --json`; `sessions --json` — **S!** | `-z --usage-file` JSON; `chat` has no `--json` — **C~** |
| 11 | Permission/approval | `tools.exec.mode deny|allowlist|ask|auto|full`; per-agent `tools.allow/deny`; `approvals allowlist add` — **S!** | `--yolo`; `-q` blocks dangerous cmds unless `approvals.single_query_mode: approve`; `command_allowlist`; `pre_tool_call` hooks — **S!** |
| 12 | Model selection | `--model provider/model`; `agents.list[].model`; fallbacks; `agentRuntime` codex/claude-cli; CLI backends — **S!** | `-m`, `--provider`, `--reasoning`; `hermes fallback`; `moa` — **S!** |
| 13 | Hooks | `hooks.internal.entries.*` (Gateway-side), `agent:bootstrap`, `boot-md` — **S!** (Gateway only) | shell hooks in `config.yaml`, gateway hooks dir, plugin hooks — **S!** |
| 14 | Version/platform | MIT; Node ≥22.22.3; Linux/macOS/Windows(native CLI + WSL2) — **S~** | MIT; Python 3.11; Linux/macOS/WSL2/Termux/Windows native — **S~** |
| 15 | Provider config / automation terms | `models.providers.*`, per-agent `auth-profiles.json`, SecretRefs; automation via CLI/Gateway is documented first-class — **S!** | `config.yaml` `model.provider`, `.env`, `hermes auth` pools; `-z` "Intended for scripts / pipes" — **S!** |

- Level: as per F1–F22.
- Requirements: HB-01 (whole table), HB-02, HB-07.

### F24. Definition-injection matrix (what reaches each harness without changing the Assistant definition)

| Assistant component | OpenClaw path | Hermes path | Cannot be injected |
|---|---|---|---|
| Persona / judgment principles / preferences | Per-run workspace `SOUL.md` (+`AGENTS.md` for operating rules, `USER.md` for user prefs) in `agents.list[].workspace` or `OPENCLAW_WORKSPACE_DIR`; or `agent:bootstrap` hook replacing `bootstrapFiles` | `SOUL.md` in a per-run HERMES_HOME (`-p <profile>` or `HERMES_HOME=…`); `HERMES_EPHEMERAL_SYSTEM_PROMPT` env for a run-scoped overlay | A per-invocation system prompt via flag (neither CLI has one); OpenClaw only accepts the fixed bootstrap basenames |
| Task / project context | `--message-file task.md` (user turn) | `-q`/`-z` text; project `AGENTS.md` chain in cwd | — |
| Visible identity | `agents.list[].identity {name,emoji,avatar}` / `IDENTITY.md` | none per profile beyond SOUL.md (gateway bot identity is the platform token) | Hermes has no agent-level display identity field (unverified beyond help/docs) |
| Skills | copy/symlink into `<workspace>/skills` or `~/.agents/skills`; restrict with `agents.list[].skills` | `<HERMES_HOME>/skills/<cat>/<name>/SKILL.md`, or repo `./.agents/skills` + `hermes skills trust`; `-s name` | — |
| MCP servers | `mcp.servers` (config patch, `openclaw mcp set <name> <json>`) | `mcp_servers` in profile `config.yaml` (`hermes mcp add`) | — |
| Permissions | `agents.list[].tools.{allow,deny,profile,exec}`; `tools.exec.mode`; approvals allowlist | `--yolo` / `command_allowlist` / `approvals.*` in profile config; `--toolsets` | Fine-grained per-invocation tool allowlists on OpenClaw require a config entry (agent or profile), not a flag |
| Harness preference / model | `--model`, `agents.list[].model`, `agentRuntime` | `-m`, `--provider`, `--reasoning` | — |
| Fresh instance per run | new `--session-key` on an agent, or `--profile <run>` disposable state dir, or `agents add`/`delete --force` | fresh profile (`hermes profile create --clone`) or `HERMES_HOME=<tmp>`; `--ignore-rules` drops memory/SOUL injection on a shared profile | OpenClaw has no ephemeral-agent primitive; Hermes warns against two processes on one profile (memory writes) |

- Level: inferred composition from F8–F21.
- Requirements: HB-02, AD-04, AD-05, TE-02, AD-07.

## 3. Negative findings

OpenClaw (2026.7.1-2):
- No `--system-prompt` / `--append-system-prompt` / `--cwd` on `agent` or `tui`: `grep -oE '"--[a-z-]+( <[a-z-]+>)?"' dist/register.agent-turn-DkKoME6y.js dist/tui-cli-DI2ZjVRm.js` → option lists in F1/F2 only.
- No `--agent` / `--model` on `tui` (F2); live docs agree.
- `OPENCLAW_WORKSPACE` env not read: `grep -hoE "OPENCLAW_WORKSPACE[A-Z_]*" dist/*.js | sort | uniq -c` → `3 OPENCLAW_WORKSPACE_DIR` only (F4).
- No ephemeral/TTL agent key: schema extract of `agents.list[]` (F9) contains no `ephemeral|ttl|expires` key.
- `agents.entries` rejected ("Unrecognized key: entries") and `message send` has no `--agent` selector — ATM fixtures `…-s1-evidence.json`, `…-s2-evidence.json`.
- Hermes is not an acpx harness target (`docs/tools/acp-agents.md:90-120` lists claude/codex/cursor/gemini/opencode/droid/pi…).
- `openclaw/src/` in the npm package contains only `agents/templates/HEARTBEAT.md`; TypeScript sources are not shipped (only `dist`), so source-line citations here are to bundled `docs/` and `dist/*.d.ts`.
- No per-run cost/token field documented for `agent --json` (`docs/cli/agent.md` JSON sections list `payloads`, `meta.durationMs`, `deliveryStatus` only).

Hermes (v0.20.4):
- No `--system-prompt`/`--append-system-prompt` flag: `grep -n -E '"--system-prompt"|append-system' hermes_cli/_parser.py hermes_cli/main.py` → 0.
- `-p/--profile` is absent from `hermes --help` (pre-argparse; `hermes_cli/_parser.py:11-19`); `hermes profiles` is not a command (only `profile`).
- `hermes chat` has no `--json`/`--output-format` (`_parser.py` chat args; help).
- `hermes tools list --summary` refuses non-interactive use ("requires an interactive terminal"), so tool inventory cannot be scripted that way.
- No MCP servers, no hooks, no non-default profiles configured on this host (`hermes mcp list`, `hermes hooks list`, `hermes profile list`).
- Personal `~/.agents/skills` (as opposed to repo-local `./.agents/skills`) not found in Hermes skill loading: `grep -rn -E "\.agents/skills|~/.agents" agent/skill_utils.py agent/prompt_builder.py` → only repo-local `<root>/.agents/skills` mentions.
- `hermes` does not appear anywhere in upstream ClawTeam (`grep -rn -i hermes ClawTeam/clawteam/` → 0).
- No documented "fresh instance" flag other than `--ignore-rules`/`--safe-mode`; `delegation.max_spawn_depth` / `max_concurrent_children` are referenced in `tools/delegate_tool.py:4735-4740` but not present in `~/.hermes/config.yaml` (only `delegation.max_iterations`).

## 4. Platform & license notes

- OpenClaw: MIT (`LICENSE`, OpenClaw Foundation 2026); Node `>=22.22.3 <23 || >=24.15.0 <25 || >=25.9.0`; Linux Gateway + systemd user unit; macOS app/launchd; Windows native CLI/Gateway (PowerShell installer, Scheduled Tasks, VBS hidden launcher) with WSL2 "most Linux-compatible"; `--local` embedded runs need provider keys in the shell; Gateway-side features (hooks, cron, channels, `sessions_spawn` announce delivery) require a running Gateway. Terms: no usage-policy text found in the package beyond MIT; model-provider terms are external.
- Hermes Agent: MIT (`LICENSE`, Nous Research 2025; `pyproject.toml`); Python 3.11 via bundled `uv`; Linux/macOS/WSL2/Termux and native Windows (`%LOCALAPPDATA%\hermes`); Windows caveats in `hermes update --force/--force-venv`; gateway service via systemd/launchd; `-z` explicitly "Intended for scripts / pipes". Terms: MIT only; Nous Portal login is optional.
- Both expose ACP (`openclaw acp`, `hermes acp`) and MCP server modes, and both ship cross-harness importers (OpenClaw↔Hermes, Hermes←Claude Code/Codex).

## 5. Open questions

1. Does `openclaw tui --session … --model …` fail with an unknown-option error on 2026.7.1-2 (commander default) — i.e. is every model-resolved fork spawn broken on this version? Not executed (would start an interactive session).
2. Does `openclaw agent --local` honour `tools.exec.mode`/approvals identically to Gateway runs? `docs/cli/tui.md` says plugin approval gates apply in local mode; exec-approvals docs do not mention `--local`.
3. Exact allowed values of Hermes `approvals.single_query_mode` (only `approve` is quoted in the deny message).
4. Does Hermes `--ignore-rules` also suppress memory *writes* (MEMORY.md/USER.md) for a run on a shared profile, or only injection?
5. Whether `openclaw agent --json` can be made to report token/cost per run (only `sessions --json` shows token usage when "the agent reports it").
6. Whether OpenClaw's `acpx` plugin can be configured with a custom Hermes ACP alias (`docs/tools/acp-agents.md:118-120` mentions custom acpx aliases must be mapped via `agents.list[].runtime.acp.agent`).

## 6. Probe / CLI log

Full outputs: `/tmp/claude-1000/-home-wsh-Documents-assistant-team-system-dev/17fd77ac-75ce-402b-a1a9-5d1eebba9843/scratchpad/ev-harness-caps-B/{openclaw-help.txt,openclaw-subhelp.txt,hermes-help.txt,hermes-help2.txt,openclaw-config-schema.json,skills-list.json}`.

```
$ openclaw --version → 2026.7.1-2 (0790d9f);  $ hermes --version → v0.20.4 (2026.8.18), Python 3.11.16
$ openclaw agent --help   → flags in F1 (incl. --local --session-id --session-key --agent --model --message-file --json)
$ openclaw tui --help     → flags in F2 (no --agent, no --model)
$ openclaw agents list --json → [{"id":"main","workspace":"~/.openclaw/workspace","agentDir":"~/.openclaw/agents/main/agent","model":"openai/gpt-5.6-sol","bindings":0,"isDefault":true}]
$ openclaw skills list --json → 57 skills (bundled 51, extra 2, agents-skills-personal 4);  hooks list → 5/5 ready;  plugins list → 50/68 enabled
$ openclaw config schema > openclaw-config-schema.json (2.4 MB) → key extraction in F9/F12
$ grep -oE '"--[a-z-]+( <[a-z-]+>)?"' dist/tui-cli-DI2ZjVRm.js dist/register.agent-turn-DkKoME6y.js   (F1/F2)
$ grep -hoE "OPENCLAW_WORKSPACE[A-Z_]*" dist/*.js | sort | uniq -c → 3 OPENCLAW_WORKSPACE_DIR ;  win32 branch files → 85
$ hermes --help / hermes chat --help → flags in F6/F7;  hermes profile list → default only;  hermes profile → 82 skills
$ hermes hooks list / hermes mcp list → none configured;  hermes config get agent.personalities → {}
$ ~/.openclaw/openclaw.json keys (redacted) → agents.defaults.{workspace,model.primary}, hooks.internal.entries.session-memory.enabled=true, tools.profile="coding"
$ ~/.hermes/config.yaml keys (redacted) → model.provider=openai-codex, agent.max_turns=500, delegation.max_iterations=250, terminal.cwd='.'
```
