---
id: ev:cc-teams-hermes-openbot
topic: Claude Code native multi-agent features (subagents, agent teams, background sessions, workflows, channels), Hermes Agent as a multi-agent/bot system (profiles, delegation, kanban, gateway), OpenBot governance platform — what each solves for AD/TC/TE/HB/AR/EV/MS/LO
systems: [Claude Code 2.1.239, Hermes Agent 0.20.4, OpenBot (CopilotKit, commit 6c365f4)]
sources:
  - {kind: cli, ref: "claude --version; claude --help; claude agents|plugin|project|mcp --help", accessed: 2026-08-22, version: 2.1.239}
  - {kind: web, ref: "https://code.claude.com/docs/en/{agent-teams,sub-agents,cross-session-messaging,headless,hooks,plugins,agents,agent-view,workflows,channels,tools-reference}", accessed: 2026-08-22, version: "agent-teams page 'as of v2.1.178' with notes through v2.1.239"}
  - {kind: cli, ref: "hermes --version; hermes --help; hermes {profile,peer,kanban,gateway,moa,skills,acp,cron,tools,memory,plugins,hooks,import-agent,sessions,curator,journey,mcp,sync,chat} --help; hermes profile list", accessed: 2026-08-22, version: "0.20.4 (2026.8.18)"}
  - {kind: repo, ref: "~/.hermes/hermes-agent (installed source, read-only): tools/delegate_tool.py, hermes_cli/profile_distribution.py, hermes_cli/kanban_db.py, hermes_cli/main.py, gateway/platforms/, plugins/platforms/, docs/profile-routing.md, docs/kanban/multi-gateway.md, agent/moa_loop.py, LICENSE, README.md", accessed: 2026-08-22, version: 0.20.4}
  - {kind: web, ref: "https://hermes-agent.nousresearch.com/docs/user-guide/{features/kanban,profiles,profile-distributions,features/delegation,messaging}", accessed: 2026-08-22}
  - {kind: repo, ref: "OpenBot@6c365f492cc84d3aeacd68ff4bee78dd9b87d02a (2026-08-20): docs/{architecture,coworkers,deployment}.md, README.md, examples/fintech/{agents,channels,model}.yaml, server/src/computer/policy.ts, server/src/db/schema/plugins.ts, server/src/audit.ts, server/package.json, LICENSE", accessed: 2026-08-22}
method: Read-only local CLI help inspection (no sessions started, no prompts sent); read-only inspection of installed Hermes source and of OpenBot; official docs via WebFetch; ~/.claude and ~/.hermes inspected for directory/key names only (no credential values). Glossary terms used as defined.
platform: {os: Ubuntu (Linux 5.15), tmux: absent, cli_versions: {claude: 2.1.239, hermes: 0.20.4 (2026.8.18), python-for-hermes: 3.11.16}}
author_agent: ev:cc-teams-hermes-openbot
date: 2026-08-22
confidence: high
status: draft
---
# Claude Code native multi-agent features, Hermes Agent as a system, and OpenBot — evidence

## 1. Scope & questions

- **Decisive question (TE-03, TE-05, HB-05):** does Claude Code 2.1.239 natively provide teams of Claude agents with task list + mailbox + teammates on different models, and can a team include non-Claude harnesses? Exactly what is solved / not solved?
- Claude Code for reusable role packages (AD-01/02/08/09, AR-02), team execution (TE-01..08), hooks/plugins (AR-02/03, XC-04), headless invocation (HB-01/02/07), surfaces (MS-01/02), long-running work (LO-01..04).
- Hermes 0.20.4 as a multi-agent/bot system: delegation (TE-04/05), profiles & distributions (AD-01..05, AR-03/04), kanban (TE-03/06/07, HB-03), gateway surfaces (MS-02/03), MoA (HB-05), skills/curator (EV-01..05), platform (TE-08).
- OpenBot: Bot/coworker model (AD-01/06, MS-03), skills-as-instructions (AD-09), policy gateway + audit (XC-04, TE-07), per-Bot container (TE-08), surfaces (MS-02), provider assumptions (HB-01).
- Negative findings per system: persistent Assistant packages, nested TeamRuns, cross-vendor brokerage, evolution Proposals.

## 2. Findings

### Claude Code 2.1.239 (installed)

### F1. Installed CLI exposes `--agents`, `--agent`, `--bg`, `claude agents`, `-p` JSON output; no team flag in `--help`
- Claim: `claude --help` lists `--agents <json>` ("JSON object defining custom agents"), `--agent <agent>`, `--bg/--background` ("manage with `claude agents`"), `--append-system-prompt`, `--system-prompt[-file]`, `--output-format text|json|stream-json`, `--json-schema`, `--max-budget-usd`, `--fallback-model`, `--permission-mode`, `--plugin-dir`, `--mcp-config`, `--bare`, `--worktree`, `--tmux`, `--forward-subagent-text`. No `--teammate-mode` or `--channels` (docs: both hidden).
- Evidence: `claude --help` (§6); agent-teams doc ("The `--teammate-mode` flag is experimental and doesn't appear in `claude --help`").
- Level: verified
- Requirements: HB-01, HB-02, HB-07
- Suggested fit cell: Claude Code → S! (HB-01/02 for the Claude harness)

### F2. Agent teams exist but are experimental, off by default: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- Claim: "Agent teams are experimental and disabled by default. Enable them by setting `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` ... Without that variable, no team is set up at session start, no team directories are written, and Claude does not spawn or propose teammates." Locally `~/.claude/teams/` is absent; `~/.claude/tasks/<session-id>/N.json` exist with keys `activeForm, blockedBy, blocks, description, id, status, subject`.
- Evidence: https://code.claude.com/docs/en/agent-teams (2026-08-22); `ls ~/.claude/teams` → absent (§6).
- Level: verified (local) / observed (docs)
- Requirements: TE-06, TE-03
- Suggested fit cell: Claude Code → C~ (all-Claude team execution)

### F3. Teams form via the Agent tool `name` input; `TeamCreate`/`TeamDelete` no longer exist; one team per session
- Claim: "Claude launches a teammate when it calls the Agent tool with a `name` while agent teams are enabled"; "Both tools no longer exist. The `team_name` input on the Agent tool is accepted but ignored"; team name = `session-` + first 8 chars of session ID; "One team per session ... You can't create additional named teams or share a team across sessions."
- Evidence: agent-teams doc §How Claude starts agent teams, §Architecture, §Limitations.
- Level: observed
- Requirements: TE-01, TC-01, TE-05
- Suggested fit cell: Claude Code → M~ (TC-01 persistent TeamTemplate), Xs~ (TE-01)

### F4. Team substrate = shared task list + JSON mailboxes + `config.json` under `~/.claude`; not pre-authorable
- Claim: "Team config: `~/.claude/teams/{team-name}/config.json`; Task list: `~/.claude/tasks/{team-name}/`"; mailbox "JSON file at `~/.claude/teams/{team-name}/inboxes/{agent-name}.json`"; tasks pending/in progress/completed with dependencies, "Task claiming uses file locking"; `config.json` `members` array (name, agent ID, agent type; lead = `team-lead`). "The team config directory is removed when the session ends. The task list directory persists locally." "don't edit it by hand or pre-author it"; "There is no project-level equivalent of the team config."
- Evidence: agent-teams doc §Architecture; hooks doc rows `TaskCreated` (`team_name, task_id, task_title, task_description`), `TaskCompleted`, `TeammateIdle`.
- Level: observed
- Requirements: TE-06, TE-07, TC-06
- Suggested fit cell: Claude Code → S~ (TE-06 all-Claude), Xs~ (TE-07: no unified run archive; team config deleted)

### F5. Teammates may run different Claude models; permission mode inherited at spawn
- Claim: model per teammate via prompt or `CLAUDE_CODE_SUBAGENT_MODEL`; `teammateDefaultModel` removed in v2.1.234; "Teammates inherit the lead's effort level"; "you can't set per-teammate modes at spawn time."
- Evidence: agent-teams doc §Specify teammates and models, §Permissions.
- Level: observed
- Requirements: TE-03 (models only), HB-03
- Suggested fit cell: Claude Code → S~ (multi-model), M~ (multi-harness)

### F6. Teammates are Claude Code sessions only; non-Claude harnesses cannot be members
- Claim: "Each teammate is a full, independent Claude Code session"; "Teammates | Separate Claude Code instances"; comparison page: "In every approach the workers are Claude sessions. To involve a different tool, expose it to Claude as an MCP server." No teammate command/harness input exists in `claude --help`, the Agent tool, or docs.
- Evidence: agent-teams doc; https://code.claude.com/docs/en/agents (2026-08-22); `claude --help`.
- Level: observed / verified (absence in CLI)
- Requirements: TE-03, HB-05, HB-08
- Suggested fit cell: Claude Code → M~ (mixed-harness TeamRun), P~ (foreign harness only as MCP tool)

### F7. No nested teams; lead fixed; teammates cannot background subagents
- Claim: "No nested teams: teammates cannot spawn their own teammates. Only the lead can manage the team."; "Lead is fixed"; teammate subagents "run in the foreground ... Claude Code returns an error when a teammate spawns a subagent whose definition sets `background: true`."
- Evidence: agent-teams doc §Limitations.
- Level: observed
- Requirements: TE-05, TE-04
- Suggested fit cell: Claude Code → M~ (TE-05 via teams; see F11 for subagent nesting)

### F8. Teams require an interactive session; `-p`/Agent SDK never spawns teammates
- Claim: "Spawning teammates also requires an interactive session. In non-interactive mode with the `-p` flag, including Agent SDK sessions, Claude doesn't spawn teammates".
- Evidence: agent-teams doc §Enable agent teams.
- Level: observed
- Requirements: TE-01, LO-01, MS-01
- Suggested fit cell: Claude Code → M~ (scripted/unattended TeamRun)

### F9. No resumption of in-process teammates; task status can lag; message-based shutdown
- Claim: "`/resume` and `/rewind` do not restore in-process teammates"; "Task status can lag"; shutdown request can be approved or rejected; idle notification "doesn't carry the teammate's output".
- Evidence: agent-teams doc §Limitations, §Shut down teammates, §Context and communication.
- Level: observed
- Requirements: TE-02, LO-04, TE-06
- Suggested fit cell: Claude Code → S~ (fresh-by-default), Xs~ (recovery)

### F10. Reusable role = subagent definition; skills/mcpServers frontmatter ignored for teammates
- Claim: "To define reusable teammate roles, use subagent definitions instead." A teammate "honors that definition's `tools` allowlist and `model`, and the definition's body is appended to the teammate's system prompt"; "`skills` and `mcpServers` frontmatter fields ... are not applied when that definition runs as a teammate."
- Evidence: agent-teams doc §Use subagent definitions for teammates.
- Level: observed
- Requirements: AD-08, TC-01, AD-02
- Suggested fit cell: Claude Code → S~ (AD-08 within Claude), M~ (TC-01)

### F11. Subagent definitions: format, scopes, nesting depth 3, 20 concurrent
- Claim: Markdown + YAML frontmatter; required `name`, `description`; optional `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory` (`user|project|local`), `background`, `effort`, `isolation: worktree`, `color`, `initialPrompt`. Scope priority: managed settings > `--agents` CLI JSON (session only) > `.claude/agents/` > `~/.claude/agents/` > plugin `agents/`. Nesting "up to 3 layers" (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`), "max 20 subagents running simultaneously" (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`); `Agent(type1, type2)` restricts spawnable types; named subagents addressable via `SendMessage`, resumable; transcripts `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`.
- Evidence: https://code.claude.com/docs/en/sub-agents (2026-08-22); `claude --help` `--agents`.
- Level: observed
- Requirements: AD-01, AD-02, AD-07, AD-09, TE-04, TE-05, EV-01
- Suggested fit cell: Claude Code → S~ (AD-01 for Claude only; TE-04 hidden temporary worker), C~ (AD-07 via `--agents`), Xs~ (TE-05: nested subagents, not isolated TeamRuns)

### F12. Subagent `memory` is an agent-written persistent file — silent mutation, no review gate
- Claim: with `memory:` the subagent "gets instructions for reading/writing memory files" and "first 200 lines or 25KB of `MEMORY.md` in context".
- Evidence: sub-agents doc §Persistent Memory.
- Level: observed
- Requirements: EV-01, EV-03, EV-04
- Suggested fit cell: Claude Code → M~ (EV-03), Xs~ (EV-01 storage slot)

### F13. Hooks: 30 events incl. `SubagentStart/Stop`, `TeammateIdle`, `TaskCreated/Completed`, `WorktreeCreate`; types `command, http, mcp_tool, prompt, agent`; configurable in settings, plugins, subagent/skill frontmatter
- Claim: exit-2 semantics (`TaskCompleted` → "prevents completion", `TeammateIdle` → "prevents idle"); common payload `session_id, transcript_path, cwd, permission_mode, hook_event_name, agent_id, agent_type`.
- Evidence: https://code.claude.com/docs/en/hooks (2026-08-22).
- Level: observed
- Requirements: XC-04, TE-06, HB-06, LO-02
- Suggested fit cell: Claude Code → S~ (XC-04), P~ (HB-06 deterministic checks as hooks)

### F14. Plugins package skills/agents/hooks/MCP/LSP/monitors/workflows; `claude plugin validate|eval|tag`
- Claim: plugin root has `.claude-plugin/plugin.json` (`name, version, description, author`), `skills/`, `commands/`, `agents/`, `hooks/hooks.json`, `.mcp.json`, `.lsp.json`, `monitors/monitors.json` ("Each stdout line from `command` is delivered to Claude as a notification"), `bin/`, `settings.json` (`agent`, `subagentStatusLine` only); namespaced `/plugin:skill`, `plugin:agent`; `--plugin-dir`, `--plugin-url`; local subcommands `details, eval, init, install, list, marketplace, tag, validate`.
- Evidence: https://code.claude.com/docs/en/plugins (2026-08-22); `claude plugin --help` (§6).
- Level: verified (CLI) / observed
- Requirements: AR-02, AR-03, AD-02, LO-02
- Suggested fit cell: Claude Code → S~ (AR-02/03 Claude-format artifacts), C~ (LO-02 monitors)

### F15. Headless `-p`: JSON `result`, `session_id`, `total_cost_usd`, `structured_output`; `--bare`; cross-directory `--resume`
- Claim: `--output-format json` includes `total_cost_usd` "and a per-model cost breakdown"; `--json-schema` → `structured_output`; `stream-json` `system/init` carries `model, tools, mcp_servers, plugins, plugin_errors, capabilities`; `--bare` skips hooks/plugins/CLAUDE.md and takes context only from `--system-prompt[-file]`, `--append-system-prompt[-file]`, `--add-dir`, `--mcp-config`, `--settings`, `--agents`, `--plugin-dir` ("will become the default for `-p`"); `--resume <id>` works from any directory (v2.1.223+); SIGTERM → exit 143.
- Evidence: https://code.claude.com/docs/en/headless (2026-08-22); `claude --help`.
- Level: observed / verified (flags)
- Requirements: HB-01, HB-02, HB-07, TE-02
- Suggested fit cell: Claude Code → S! (HB-02 injection paths; HB-07 cost/outcome)

### F16. Cross-session messaging: `ListAgents` + `SendMessage` across local sessions (Unix socket), Remote Control, cloud; plain text; inbound controls
- Claim: on by default v2.1.224+ (Linux/macOS), v2.1.234+ native Windows; local delivery "Over a per-session socket ... never through Anthropic servers"; `-p` sessions bind an inbox unless `--bare`; `crossSessionInbound: accept|hold|refuse`, `isolatePeerMachines`; "Plain text only"; socket exported as `CLAUDE_CODE_MESSAGING_SOCKET` so "a script or hook [can] post into a session"; not on Bedrock/Vertex/Foundry.
- Evidence: https://code.claude.com/docs/en/cross-session-messaging (2026-08-22).
- Level: observed
- Requirements: TE-06, MS-01, HB-06
- Suggested fit cell: Claude Code → S~ (Claude↔Claude), P~ (deterministic backend posting via socket)

### F17. Background sessions (`claude --bg`, `claude agents`, supervisor): per-session model, worktrees, persistence without a terminal; research preview; Claude-only
- Claim: "Background sessions are hosted by a per-user supervisor process"; "Each background session can run on a different model"; `claude --bg --model opus ...`, `--agent <name> --bg`, `--exec '<shell>'`; worktrees under `.claude/worktrees/`; sessions "stop if the machine shuts down"; `claude agents --json`.
- Evidence: https://code.claude.com/docs/en/agent-view (2026-08-22); `claude agents --help`.
- Level: observed / verified (flags)
- Requirements: LO-01, LO-04, TE-02, TE-08
- Suggested fit cell: Claude Code → S~ (LO-01 Claude-driven), n/a (mixed harness)

### F18. Dynamic workflows: JavaScript `agent()`/`pipeline()` orchestrating subagents with cross-checks; resumable in-session; Claude-only workers
- Claim: "A dynamic workflow is a JavaScript script that orchestrates subagents at scale"; `agent(prompt, {schema, label})`; "Up to 16 concurrent agents", "1,000 agents total per run"; saved to `.claude/workflows/` or `~/.claude/workflows/`; "If you exit Claude Code while a workflow is running, the next session starts the workflow fresh"; per-stage model routing possible.
- Evidence: https://code.claude.com/docs/en/workflows (2026-08-22).
- Level: observed
- Requirements: HB-05, TE-06
- Suggested fit cell: Claude Code → S~ (multi-model Claude ensemble+synthesis), M~ (cross-harness)

### F19. Channels: Telegram/Discord/iMessage plugins push events into a running session; hidden `--channels`; research preview
- Claim: "A channel is an MCP server that pushes events into your running Claude Code session"; `claude --channels plugin:telegram@claude-plugins-official` (also `discord`, `imessage` macOS, `fakechat`); pairing + allowlist; "Events only arrive while the session is open"; requires Bun; not on Bedrock/Vertex/Foundry.
- Evidence: https://code.claude.com/docs/en/channels (2026-08-22).
- Level: observed
- Requirements: MS-02, MS-03, MS-04
- Suggested fit cell: Claude Code → C~ (MS-02), S~ (MS-04)

### F20. Display/platform: in-process default "Works in any terminal"; split panes need tmux/iTerm2, unsupported in Windows Terminal/VS Code/Ghostty; Task tools opt-in on Fable 5
- Claim: "The default is `"in-process"`"; `teammateMode` / `--teammate-mode`; "Split-pane mode isn't supported in VS Code's integrated terminal, Windows Terminal, or Ghostty". Tools reference: "In Claude Code v2.1.233 and later, the following tools aren't available on Opus 4.8, Sonnet 5, Fable 5, Mythos 5 ... unless you opt in: `TodoWrite`, `TaskCreate`, `TaskGet`, `TaskUpdate`, and `TaskList`" (`CLAUDE_CODE_ENABLE_TODO_TOOLS=1` or `--allowedTools TaskCreate`); without them teams "coordinate through messages instead of the shared task list".
- Evidence: agent-teams doc §Choose a display mode, §Limitations; https://code.claude.com/docs/en/tools-reference (2026-08-22).
- Level: observed
- Requirements: TE-08, XC-02, TE-06
- Suggested fit cell: Claude Code → S~ (TE-08 no tmux), C~ (TE-06 task tools)

### Hermes Agent 0.20.4 (installed)

### F21. Hermes is a Python agent platform (MIT, Nous Research) with 70+ subcommands: gateway, profiles, kanban, delegation, skills, memory, cron, plugins, MCP, ACP
- Claim: `hermes --version` → "Hermes Agent v0.20.4 (2026.8.18), Install directory: /home/wsh/.hermes/hermes-agent, Python: 3.11.16"; subcommands include `profile, peer, kanban, gateway, moa, skills, bundles, plugins, curator, journey, memory, cron, hooks, mcp, acp, import-agent, sessions, project, verify, approvals`. LICENSE: "MIT License, Copyright (c) 2025 Nous Research".
- Evidence: `hermes --help` (§6); `~/.hermes/hermes-agent/LICENSE:1-3`.
- Level: verified
- Requirements: XC-01, HB-01
- Suggested fit cell: Hermes → n/a (license OK)

### F22. `delegate_task`: fresh-context subagents, flat by default (`MAX_DEPTH = 1`), opt-in nesting via `delegation.max_spawn_depth` + `role="orchestrator"`, per-task `output_schema`, `list/steer/stop`; children cannot target other profiles/harnesses
- Claim: docstring "Spawns child AIAgent instances with isolated context, inherited toolsets ... A fresh conversation (no parent history)"; `DELEGATE_BLOCKED_TOOLS = {"delegate_task", "clarify", "memory", "send_message", "cronjob"}`; `MAX_DEPTH = 1  # flat by default: parent (0) -> child (1); grandchild rejected unless max_spawn_depth raised.`; `_DEFAULT_MAX_CONCURRENT_CHILDREN = 10` (web docs say 3); schema `goal, context, tasks[]{goal, context, role: leaf|orchestrator, output_schema}, role, output_schema, action: spawn|list|steer|stop`; child model via global `delegation.model/provider`; docs: "Subagents cannot target other profiles or harnesses — they inherit parent's API key and provider"; live logs `<hermes_home>/cache/delegation/live/<id>/task-<n>.log`; optional `delegation.worktree_isolation`.
- Evidence: `~/.hermes/hermes-agent/tools/delegate_tool.py:1-18,50-58,118-135,4651,4730-4835`; delegation doc (2026-08-22).
- Level: verified (source) / observed (docs)
- Requirements: TE-04, TE-05, AD-07, XC-04
- Suggested fit cell: Hermes → S! (TE-04), Xs~ (TE-05: subagent tree, single harness, not isolated TeamRun)

### F23. Profiles = isolated Hermes homes (`~/.hermes/profiles/<name>/`: `config.yaml, .env, SOUL.md, memories, sessions, skills, state.db`) selected by `hermes -p <name>` (pre-parsed into `HERMES_HOME`); one gateway per profile; `--description` drives kanban routing
- Claim: `hermes profile create NAME [--clone|--clone-all|--clone-from] [--description ...]` ("Used by the kanban decomposer to route tasks based on role"); `export/import` archives strip keys; `-p` pre-parsed in `hermes_cli/main.py:512-596` ("Pre-parse --profile/-p and set HERMES_HOME before imports"), hence absent from argparse help; docs: "A profile does not stop it from accessing folders outside the profile directory." Local `hermes profile list`: one profile `default`.
- Evidence: `hermes profile --help`, `hermes profile create --help` (§6); `hermes_cli/main.py:512-596`; profiles doc (2026-08-22).
- Level: verified / observed
- Requirements: AD-01, AD-05, TC-04, MS-03
- Suggested fit cell: Hermes → S! (persona+config+skills bundle), M~ (AD-05: sessions/memories/.env live inside the reusable unit)

### F24. Profile distributions: git-installable agent package with `distribution.yaml`; no secrets; distribution-owned vs user-owned paths on update
- Claim: manifest `name, version, description, hermes_requires, author, license, env_requires[{name, description, required, default}], distribution_owned[]`; `hermes profile install <git URL|dir>`, `update`, `info`; "Distribution-owned paths (SOUL.md, mcp.json, skills/, cron/, distribution.yaml) are replaced from the new source"; "`config.yaml` ... preserved on update unless `--force-config`"; "User-owned paths (memories/, sessions/, state.db, auth.json, .env, logs/, workspace/, ...) are never touched"; "Git ref pinning (`#v1.2.0`) is planned but not in the initial release".
- Evidence: `~/.hermes/hermes-agent/hermes_cli/profile_distribution.py:20-75`; `hermes profile install --help`; profile-distributions doc (2026-08-22).
- Level: verified / observed
- Requirements: AD-08, AR-03, AR-04, EV-02
- Suggested fit cell: Hermes → S! (AR-03/04 Hermes-only packages), Xs~ (2-layer base/user split; no reviewed evolution layer)

### F25. Kanban: durable SQLite board across profiles; dispatcher spawns `hermes -p <profile>` workers in isolated workspaces; per-task model/provider; swarm workers→verifier→synthesizer; runs/events audit; single-host; no nested boards
- Claim: `VALID_STATUSES = {"triage","todo","scheduled","ready","running","blocked","review","done","archived"}`; tables `tasks, task_links, task_comments, task_events, task_runs, task_attachments, kanban_notify_subs`; `kanban create --assignee PROFILE --parent ID --workspace scratch|worktree|dir:<path> --model --provider --max-runtime --max-retries --skill`; `kanban swarm --worker PROFILE:TITLE[:SKILL] --verifier P --synthesizer P goal`; `decompose` ("Profile roster with user-authored descriptions"); `daemon` "DEPRECATED — dispatcher now runs in the gateway"; docs: workers spawned as `hermes -p <profile>` with `HERMES_KANBAN_TASK`; "Kanban is deliberately single-host"; "Nesting (Subtasks): Not supported ... cannot spawn a board within a board"; per-task log `~/.hermes/kanban/logs/<task_id>.log`, `task_runs` attempt history.
- Evidence: `hermes kanban --help`, `kanban create/swarm/decompose/dispatch --help` (§6); `hermes_cli/kanban_db.py:102-103,1333-1501`; kanban doc (2026-08-22); `docs/kanban/multi-gateway.md:1-25`.
- Level: verified / observed
- Requirements: TE-06, TE-07, TE-03, HB-03, HB-07, TC-02, LO-04
- Suggested fit cell: Hermes → S! (TE-06/07 Hermes-only; per-task model policy), M~ (TE-03 cross-harness members; TE-05), Xs~ (TC-02 roles = profile descriptions)

### F26. Gateway surfaces: 20+ adapters (core: api_server, signal, weixin, whatsapp_cloud, yuanbao, qqbot, bluebubbles, webhook, msgraph; plugins: telegram, discord, slack, matrix, mattermost, email, feishu, teams, irc, line, sms, a2a, …); profile routing; `peer` bot-to-bot; A2A v1.0
- Claim: `docs/profile-routing.md`: "one gateway instance serve[s] multiple isolated profiles, selecting which profile handles an inbound message based on ... the platform, server (`guild_id`), channel (`chat_id`), and/or thread (`thread_id`)"; `hermes peer dm <peer>[/<agent>]` "the cross-machine twin of `hermes -p <bot> chat`"; A2A README: "Works with any A2A-compliant peer (another Hermes, LangChain, CrewAI, Google ADK, OpenClaw, …)"; `hermes gateway install` = systemd/launchd service.
- Evidence: `gateway/platforms/`, `plugins/platforms/` listings (§6); `docs/profile-routing.md:1-30`; `plugins/platforms/a2a/README.md:1-10`; `hermes peer|gateway --help`; messaging doc (2026-08-22).
- Level: verified / observed
- Requirements: MS-02, MS-03, MS-04
- Suggested fit cell: Hermes → S! (MS-02), C~ (MS-03 per-profile bot identity), n/a (MS-04: routing is surface→profile)

### F27. MoA (`/moa`, `hermes moa`) = per-turn mixture-of-agents with reference models feeding the main loop — same-runtime multi-model ensemble, not multi-harness
- Claim: `hermes moa` "Configure Mixture of Agents provider/model slots"; `agent/moa_loop.py`: "It marks one user turn as MoA-enabled; the normal Hermes agent loop still owns tool calling ... this module gathers reference-model context before each model iteration."
- Evidence: `hermes moa --help` (§6); `~/.hermes/hermes-agent/agent/moa_loop.py:1-8`.
- Level: verified
- Requirements: HB-05
- Suggested fit cell: Hermes → P~ (multi-model within one harness), M~ (cross-harness ensemble)

### F28. Skills: `SKILL.md` (frontmatter `name, description, version, author, license, tags, platforms`), registries, `bundles`, `sync propose`, `curator` (auto-maintenance with ledger/rollback), `journey`
- Claim: `hermes skills`: "from skills.sh, well-known agent skill endpoints, GitHub, ClawHub, and other registries"; `hermes curator`: "auxiliary-model background task that periodically reviews agent-created skills, prunes stale ones, consolidates overlaps, and archives obsolete skills ... auto-deletion never happens ... `ledger` List the per-mutation skill audit ledger (all actors: curator/agent/user)"; `hermes sync propose` "Share a skill with your organisation"; sample frontmatter `skills/mlops/huggingface-hub/SKILL.md:1-9`.
- Evidence: CLI help (§6); installed skills tree.
- Level: verified
- Requirements: AR-02, AR-03, EV-01, EV-03, EV-05
- Suggested fit cell: Hermes → S! (AR-02/03), Xs~ (EV-03: auto-mutation with ledger, no human Proposal gate; EV-05 ledger for skills only)

### F29. Headless `-z/--oneshot` + `--usage-file` JSON (cost, tokens, model, api_calls); `--worktree`; `import-agent claude-code|codex`; `acp`; `mcp serve`
- Claim: `-z PROMPT` "print ONLY the final response text"; `--usage-file PATH` "JSON usage report (estimated cost, token counts, model, api_calls)"; `import-agent` "Maps CLAUDE.md/AGENTS.md instructions, permission allowlists, MCP servers, skills, and memories into their Hermes equivalents ... API keys and credentials are never imported"; `hermes acp` ACP server; `hermes mcp serve`.
- Evidence: `hermes --help`, `hermes import-agent|acp|mcp --help` (§6).
- Level: verified
- Requirements: HB-01, HB-02, HB-07, AR-05
- Suggested fit cell: Hermes → S! (as Harness: headless+cost), P~ (HB-02 via SOUL.md/AGENTS.md/`--skills`)

### F30. Hermes platform: Linux, macOS, WSL2, Termux, native Windows; kanban runtime caps use SIGTERM/SIGKILL
- Claim: README "### Linux, macOS, WSL2, Termux" / "### Windows (native, PowerShell) ... CLI, gateway, TUI, and tools all work natively"; `--max-runtime`: "the dispatcher SIGTERMs (then SIGKILLs) the worker".
- Evidence: `~/.hermes/hermes-agent/README.md:37-59`; `hermes kanban create --help`.
- Level: verified (text) / unverified (Windows kanban)
- Requirements: TE-08, XC-02
- Suggested fit cell: Hermes → S~ (TE-08), ? (kanban on Windows)

### OpenBot (CopilotKit, MIT, commit 6c365f4 2026-08-20)

### F31. Bots are AG-UI endpoints in tenant `agents.yaml` (`id, name, title, role_description, avatar_seed, type: built-in|remote-ag-ui, endpoint, system_prompt`); coworkers carry a durable "standing role" injected as AG-UI system content
- Claim: `agents.yaml:21-27` `type: remote-ag-ui`, `endpoint: ${MANAGED_AGENT_AG_UI_URL:-http://localhost:4201/ag-ui}`; coworkers.md: "A coworker is a Bot with a durable profile and standing role ... `You are Expense Manager, Finance Operations. ... This standing role applies in every channel.`"; tables `agents` (endpoint/key ref), `agent_profiles` (name, title, role, avatar seed, owner, visibility, soft deletion), `agent_preferences`; visibility `private|public`; "Package-provided agents cannot be edited or deleted through the product."
- Evidence: `OpenBot/examples/fintech/agents.yaml:3-27`; `OpenBot/docs/coworkers.md:1-40`; `OpenBot/docs/architecture.md:88-98`.
- Level: observed
- Requirements: AD-01, AD-06, MS-03, HB-08
- Suggested fit cell: OpenBot → S~ (AD-06 identity separate from endpoint), Xs~ (AD-01 role text only), P~ (HB-08 any AG-UI endpoint)

### F32. "Skills are instructions, not capabilities" — `/`-invoked prose; personal skills attach only to owned Bots
- Claim: README: "**Skills are instructions, not capabilities**: personal skills attach only to Bots their author owns, deployment skills are admin-owned, and both are invoked with `/` in the composer."; schema: "A tool is something a Bot calls; a skill is something a Bot is told. Writing one adds no capability at all ... The firewall is at the tool call, not at the prose".
- Evidence: `OpenBot/README.md:151`; `OpenBot/server/src/db/schema/plugins.ts:100-107`; `OpenBot/docs/architecture.md:118-127`.
- Level: observed
- Requirements: AD-09, AR-01, AR-02
- Suggested fit cell: OpenBot → S~ (AD-09 conceptual), n/a (AR-02 prose + MCP only)

### F33. Governance gateway: CEL (`cel-js` 0.8.2), deny-before-allow, fail-closed, audit row before action, per-Bot container, audited human takeover, secrets never in transcript
- Claim: "Rules use CEL expressions ... Deny rules are evaluated before allow rules. The policy engine fails closed: a missing or empty policy permits nothing, a broken deny rule denies ... A malformed configured policy stops server startup"; context `tool.name, intent, bot.id, actor.id, page.url, page.host, element.*, key, file.*, mcp.server, mcp.tool, mcp.effect`; "write an audit row for the decision; call the computer only when the decision forwards"; `auditEvents` table; "each Bot gets its own computer container, workspace volume, and browser profile" (Docker socket; optional gVisor); `computer.help_requested/control_taken/control_released`; "records that a secret was requested or supplied and the character count, not the secret value."
- Evidence: `OpenBot/docs/architecture.md:38-86`; `server/src/computer/policy.ts:1-33`; `server/package.json:20`; `server/src/audit.ts:3,255`.
- Level: observed
- Requirements: XC-04, TE-07, AR-04, AD-03
- Suggested fit cell: OpenBot → S~ (XC-04, AD-03), P~ (reference design; browser-action domain)

### F34. Surfaces are in-app only: `channels.yaml` (`id, permitted_agents, allowed_groups`), one coworker per channel; no Telegram/Discord/WhatsApp; Slack only as MCP connector
- Claim: `grep -rniE 'telegram|discord|whatsapp'` over `*.ts,*.tsx,*.md,*.yaml` (excl. node_modules) → **0 files**; "Slack" only in "The curated MCP catalogue contains Atlassian, Box, Slack, Salesforce, and ServiceNow"; "A channel is a conversation with one coworker and a CopilotKit Intelligence thread mapping."
- Evidence: §6 grep; `OpenBot/docs/architecture.md:96,125`; `examples/fintech/channels.yaml:1-16`.
- Level: verified (grep) / observed
- Requirements: MS-02, MS-04
- Suggested fit cell: OpenBot → n/a (MS-02), S~ (MS-04)

### F35. Assumptions: one provider per deployment (`model.yaml: provider, credential_secret_ref, default_model`), persistent Bots/threads (CopilotKit Intelligence), single Docker host, Bun/TypeScript, PostgreSQL+pgvector
- Claim: `model.yaml` `provider: openai`, `credential_secret_ref: openai-api-key`, `default_model: gpt-4.1`; "conversations survive restarts through CopilotKit Intelligence"; deployment.md: "OpenBot ships as one container ... The supervisor ... needs a Docker socket, which no serverless container platform permits"; `packageManager: bun@1.3.14`; no OS matrix in docs.
- Evidence: `examples/fintech/model.yaml:1-4`; `README.md:157`; `docs/deployment.md:1-40`; `package.json:5`.
- Level: observed
- Requirements: HB-01, TE-02, TE-08, AR-04
- Suggested fit cell: OpenBot → M~ (TE-02 fresh instances; HB-03 multi-harness), S~ (AR-04 credential refs)

## 3. Negative findings

**Claude Code** — No persistent TeamTemplate/team config file ("There is no project-level equivalent of the team config. A file like `.claude/teams/teams.json` ... is not recognized"; must not pre-author; `ls ~/.claude/teams` absent). No nested teams ("teammates cannot spawn their own teammates"); subagent nesting ≤3 yields subagents, not isolated TeamRuns. No non-Claude teammates / harness brokerage (no teammate command/harness input in `claude --help`, Agent tool, or docs; "In every approach the workers are Claude sessions"). No evolution Proposals: subagent `memory`/auto-memory are agent-written files; docs searched (sub-agents, hooks, plugins) mention approval only for teammate plans and permissions. Teams unavailable under `-p`/SDK.

**Hermes** — No TeamTemplate object: `grep -rn "team_template\|TeamTemplate" ~/.hermes/hermes-agent/hermes_cli ~/.hermes/hermes-agent/tools` → 0 (kanban `swarm` is a one-shot graph builder; profiles are per-agent). No nested TeamRun ("Kanban has no recursive board mechanism"; delegation nesting only in-process, children "cannot target other profiles or harnesses"). No cross-vendor brokerage: `delegate_task`/kanban `--model/--provider` pick models for Hermes workers; grep `"claude"`/`"codex"` in `hermes_cli/kanban*.py`, `tools/delegate_tool.py` → only import/session-import references, no spawn targets. No human-gated Proposal model: curator auto-mutates agent-created skills (ledger/rollback); `sync propose` shares to an org, not an overlay review.

**OpenBot** — No multi-agent orchestration/delegation/team: `grep -rniE "multi-agent|sub-?agent|delegat|handoff|orchestrat|team"` over README + docs → 1 hit (deployment.md, human "team trusts its own Bots"). No nested runs, no harness brokerage (one `model.yaml` provider; Bots are endpoints), no evolution mechanism (grep "proposal|learn" in docs → 0 relevant). No external messaging surfaces (F34).

## 4. Platform & license notes

| System | License (file) | OS support (evidence) | Automation-flag notes |
|---|---|---|---|
| Claude Code 2.1.239 | Proprietary CLI (behavioral reference only, not source reuse) | Teams in-process "Works in any terminal"; split panes need tmux/iTerm2, "not supported in VS Code's integrated terminal, Windows Terminal, or Ghostty"; cross-session messaging macOS/Linux/WSL2 v2.1.224+, native Windows v2.1.234+ (WSL2↔native isolated); channels/messaging not on Bedrock/Vertex/Foundry; background sessions stop on shutdown | `--dangerously-skip-permissions` "Recommended only for sandboxes"; `-p` skips trust dialog; `--bare` recommended for scripts; teams experimental |
| Hermes 0.20.4 | MIT (`~/.hermes/hermes-agent/LICENSE`) | README: Linux, macOS, WSL2, Termux, native Windows "fully supported"; gateway via systemd/launchd; kanban single-host SQLite | `--yolo`, `--accept-hooks`, `delegation.subagent_auto_approve` (default false, "opt-in YOLO for cron/batch"); `-z` "approvals are auto-bypassed" |
| OpenBot @6c365f4 | MIT (`OpenBot/LICENSE`, "Copyright (c) 2026 CopilotKit") | Docker-first single image; supervisor needs Docker socket; gVisor optional; Bun 1.3.14; no OS matrix | `OPENBOT_DEV_NO_AUTH=true` local only; default policy `deny: []`, `allow: ["true"]` unless replaced |

## 5. Open questions

1. Will the Agent SDK expose the team mailbox/task list for non-interactive orchestration? As of 2026-08-22 teams need an interactive session — relevant if a Lead is a headless Claude process.
2. Task tools on Fable 5 require opt-in (F20) and "Task status can lag" — is the shared task list a reliable TeamRun substrate?
3. Hermes kanban on native Windows (SIGTERM/SIGKILL caps, worker spawn) unverified.
4. Hermes delegation web docs say "No per-task model parameter" and omit `output_schema`; installed 0.20.4 source has per-task `output_schema` and `role` but a global `delegation.model`. Which is canonical next release?
5. Can Hermes kanban dispatch a task to a Claude Code or Codex worker? No hook found in 0.20.4.

## 6. Probe / CLI log

All commands read-only; transcript at `/tmp/claude-1000/-home-wsh-Documents-assistant-team-system-dev/17fd77ac-75ce-402b-a1a9-5d1eebba9843/scratchpad/ev-cc-teams-hermes-openbot/probe-log.md`.

```
$ claude --version → 2.1.239 (Claude Code)
$ claude --help | grep -E "^\s+--(agents|agent|bg|bare|teammate|channels)" → --agent, --agents, --bare, --bg  (no --teammate-mode / --channels)
$ ls ~/.claude/teams → No such file ; ls ~/.claude/tasks → <session-uuid>/{N.json,.lock,.highwatermark}
$ hermes --version → Hermes Agent v0.20.4 (2026.8.18) ... Python: 3.11.16
$ hermes profile list → default | gpt-5.6-sol | gateway stopped
$ grep -n "MAX_DEPTH = 1" ~/.hermes/hermes-agent/tools/delegate_tool.py → 129
$ grep -n "VALID_STATUSES" ~/.hermes/hermes-agent/hermes_cli/kanban_db.py → 102
$ ls ~/.hermes/hermes-agent/plugins/platforms → a2a buzz dingtalk discord email feishu google_chat homeassistant irc line matrix mattermost ntfy photon raft simplex slack sms teams telegram wecom whatsapp
$ git -C OpenBot log -1 --format='%H %ad' --date=short → 6c365f49... 2026-08-20
$ grep -rniE 'telegram|discord|whatsapp' OpenBot --include=*.ts --include=*.tsx --include=*.md --include=*.yaml -l | grep -v node_modules | wc -l → 0
```
