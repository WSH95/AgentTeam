---
id: ev:clawteam-model
topic: ClawTeam team/task/mailbox/lifecycle model and leader/worker protocol (incl. nested-team walk-through)
systems: [ClawTeam, ClawTeam-OpenClaw]
sources:
  - {kind: repo, ref: /home/wsh/Documents/00000/ClawTeam@0119833 (tag v0.2.0-99-g0119833, pyproject 0.3.0, 2026-05-09), accessed: 2026-08-21, version: 0.3.0}
  - {kind: repo, ref: /home/wsh/Documents/00000/ClawTeam-OpenClaw@8dac3fc (v0.3.0+openclaw2, 2026-07-04), accessed: 2026-08-21, version: 0.3.0+openclaw2}
  - {kind: cli, ref: "command -v clawteam clawteam-mcp tmux; python3 --version; uv --version; claude --version; codex --version", accessed: 2026-08-21}
method: Static read of every file in clawteam/{team,store,transport,templates,events,plugins,harness,mcp,identity,config}.py plus targeted reads of cli/commands.py (4672 lines), spawn/{tmux,subprocess}_backend.py, spawn/{prompt,registry,keepalive}.py, skills/clawteam/*; grep negative searches; diff of model files against the fork. No ClawTeam code was executed (not installed; rules forbid installing).
platform: {os: Ubuntu (Linux 5.15), tmux: absent, cli_versions: {clawteam: not installed, python3: 3.8.10 (system; ClawTeam needs >=3.10 via uv 0.11.26), claude: 2.1.239, codex: 0.148.0}}
author_agent: ev:clawteam-model
date: 2026-08-21
confidence: high
status: draft
---
# ClawTeam model and leader/worker protocol

## 1. Scope & questions
- (a) What is a team/member on disk and how is identity carried? — TC-01, TC-02, TE-01, TE-07, AD-05
- (b) Task DAG semantics (statuses, locks, cycles, unblock, `task wait`) — TE-06
- (c) Mailbox/transport/events/shutdown protocol — TE-06, MS-01, LO-04
- (d) Template model and `launch` — TC-01, TC-02, TC-06, TE-01, AD-08
- (e) What leader and workers are actually told; HITL — AD-01, AD-09, HB-02, TE-04, XC-04
- (f) Leader dynamics (watcher, router, Ralph loop, context recovery) — LO-02, LO-03, LO-04, TE-06
- (g) MCP programmatic surface — HB-02, MS-01, XC-03
- (h) Nested-team walk-through on paper — TE-05, TE-07, EV-04
- (i) Extension points for a wrapping layer — XC-03, XC-04, HB-08
- CLI tree + version confirmation; fork model deltas — XC-02, XC-03

## 2. Findings

### F1. TeamConfig / TeamMember are 6 + 5 fields; role is a free string
- Claim: `TeamConfig{name, description, leadAgentId, createdAt, members[], budgetCents}`; `TeamMember{name, user, agentId(hex12), agentType="general-purpose", joinedAt}`. No parent/child, no visibility, no relationships.
- Evidence: ClawTeam/clawteam/team/models.py:65-87. Sample `teams/{team}/config.json` (by_alias, written atomically at manager.py:39-47):
  ```json
  {"name":"A","description":"Auto-created by clawteam spawn","leadAgentId":"3f2c...","createdAt":"2026-...Z",
   "members":[{"name":"w1","user":"","agentId":"3f2c...","agentType":"general-purpose","joinedAt":"..."}],"budgetCents":0.0}
  ```
- Level: observed. Requirements: TC-01, TC-02, TC-04, AD-05. Fit: ClawTeam → Xs~ (TC-04), S~ (TC-02 lead only).

### F2. Data-dir layout (all paths derived from code)
- Claim: `get_data_dir()` = `$CLAWTEAM_DATA_DIR` > config `data_dir` > `~/.clawteam` (models.py:15-23); `config.json` is *always* `~/.clawteam/config.json` regardless of data_dir (config.py:179-181).

| Path | Writer | Evidence |
|---|---|---|
| `teams/{team}/config.json` | TeamManager | manager.py:24-47 |
| `teams/{team}/inboxes/{user_}{agent}/msg-{ms}-{uid8}.json` (+`.consumed`) | FileTransport | transport/file.py:373-381,458-471 |
| `teams/{team}/dead_letters/{agent}/...+.meta.json` | FileTransport | transport/file.py:384-392,512-544 |
| `teams/{team}/events/evt-{ms}-{uid8}.json` (never consumed) | MailboxManager | mailbox.py:48-59 |
| `teams/{team}/spawn_registry.json` | spawn/registry | registry.py:18-47 |
| `teams/{team}/peers/{agent}.json` (p2p) | P2PTransport | transport/p2p.py:22-25 |
| `teams/{team}/leader_watch_state.json`, `runtime_state.json` | LeaderWatcher / routing policy | leader_watcher.py:279-284; routing_policy.py:46-47 |
| `tasks/{team}/task-{id8}.json` + `.tasks.lock` | FileTaskStore | store/file.py:120-134 |
| `costs/{team}/cost-*.json`, `sessions/{team}/{agent}.json`, `plans/{team}/{agent}-{planid}.md`, `snapshots/{team}/snap-*.json`, `workspaces/{team}/{agent}` + `workspace-registry.json`, `harness/{team}/{harness_id}/{state.json,exit-journal.jsonl}`, `plugins/*/plugin.json`; user templates `~/.clawteam/templates/*.toml` | various | costs.py:76-79; sessions.py:33-44; plan.py:20-38; snapshot.py:30-33; workspace/manager.py:26-31,73-74; harness/phases.py:409-417; exit_journal.py:181-185; plugins/manager.py:98-103; templates/__init__.py:52 |
- Level: observed. Requirements: TE-07, AD-05, XC-04. Fit: ClawTeam → S~ (run archive raw material exists).

### F3. Identity = 7 env-derived fields; `to_env()` is dead code; spawn backends build child env themselves
- Claim: `AgentIdentity{agent_id, agent_name, user, agent_type, team_name, is_leader, plan_mode_required}`; `from_env()` precedence `CLAWTEAM_*` > `OH_*` > `CLAUDE_CODE_*` > default (identity.py:10-36,64-85). `to_env()` (docstring "for spawning sub-agents") has **0 callers** outside identity.py. Backends do `os.environ.copy()` then override `CLAWTEAM_AGENT_ID/NAME/TYPE/TEAM_NAME/AGENT_LEADER` (tmux_backend.py:66-79; subprocess_backend.py:45-56), add `CLAWTEAM_WORKSPACE_DIR` only if `cwd` (tmux:80-81), `CLAWTEAM_CONTEXT_ENABLED=1`, `CLAWTEAM_DATA_DIR` (setdefault), `CLAWTEAM_BIN`, and `unset CLAUDECODE CLAUDE_CODE_ENTRYPOINT CLAUDE_CODE_SESSION` (tmux:166).
- Level: observed. Requirements: AD-05, TE-02, HB-02. Fit: ClawTeam → S~ (per-instance identity), corrects recon wording ("to_env() for spawning sub-agents" is aspirational, unused).

### F4. Membership is not enforced on message delivery
- Claim: `resolve_inbox()` returns the raw recipient string when no member matches (manager.py:236-244); `FileTransport.deliver` `mkdir`s the inbox (transport/file.py:373-381,458-460). So `clawteam inbox send <team> <anyname>` from any process delivers and creates a stray inbox; `broadcast()` later iterates *all* inbox dirs (mailbox.py:160; transport/file.py:574-578) — including `_pending_*` join dirs upstream (fork filters them: ClawTeam-OpenClaw/clawteam/transport/file.py:260-264).
- Level: observed. Requirements: TE-05, TE-06, TC-03. Fit: ClawTeam → P~/Xs~ (isolation by convention only).

### F5. Leader = member with `agentId == leadAgentId`; first `spawn` into a new team makes the spawned agent the leader
- Claim: `get_leader_name` falls back to first member (manager.py:181-189). `clawteam spawn --team X` auto-creates X with `leader_name=_name, leader_id=_id, leader_agent_type=agent_type` (cli/commands.py:3223-3233), `is_leader = _name == leader_name` (3247-3248) → env `CLAWTEAM_AGENT_LEADER=1` + tmux `remain-on-exit` (tmux_backend.py:200-204). `team spawn-team` takes leader id from the caller's env identity (commands.py:1164-1179). `team add-member` / `approve-join` add with `agent_type="general-purpose"` (commands.py:1414-1420,1456-1462) — role/capabilities text from `request-join` is not persisted.
- Level: observed. Requirements: TC-02, TE-04, TE-05. Fit: ClawTeam → S~ (dynamic members), Xs~ (role on join).

### F6. TaskItem = 14 fields; `blocked` is set automatically; `blocks[]` is write-only
- Claim: `TaskItem{id(hex8), subject, description, status ∈ {pending,in_progress,completed,blocked}, priority ∈ {low,medium,high,urgent}, owner, lockedBy, lockedAt, blocks[], blockedBy[], startedAt, createdAt, updatedAt, metadata{}}` (models.py:124-142, 36-47). Create with `blocked_by` → status `blocked` (store/file.py:192-194). Dependents resolve only via `blockedBy`; `blocks` is appended but never read for resolution (file.py:282-285,458-470; grep `.blocks` → only append).
- Evidence sample `tasks/A/task-1a2b3c4d.json`: `{"id":"1a2b3c4d","subject":"Deploy","description":"","status":"blocked","priority":"medium","owner":"","lockedBy":"","lockedAt":"","blocks":[],"blockedBy":["aaa11111"],"startedAt":"","createdAt":"...","updatedAt":"...","metadata":{}}`
- Level: observed. Requirements: TE-06. Fit: ClawTeam → S!~ (DAG primitives exist).

### F7. Claiming = advisory lock keyed on env identity; refuses when owner liveness is unknown
- Claim: `update(status=in_progress, caller)` acquires `lockedBy=caller`; if already locked by another name and `is_agent_alive()` is `True` **or `None`** (no spawn-registry entry) → `TaskLockError` unless `--force` (file.py:337-347). `caller` = `CLAWTEAM_AGENT_NAME` in CLI (commands.py:2204) or explicit param in MCP (`task_update(caller=...)`, mcp/tools/task.py:294-307). `completed`/`pending` clear the lock; `release_stale_locks()` frees locks of dead agents (file.py:259-261,349-364). Whole-team serialisation via `fcntl.flock`/`msvcrt.locking` on `.tasks.lock` (file.py:150-171); writes are mkstemp+`os.replace` (442-456). Events `AfterTaskUpdate`/`TaskCompleted` emitted async outside the lock (304-321).
- Level: observed. Requirements: TE-06, LO-04. Fit: ClawTeam → S~.

### F8. Cycle check is DFS over all tasks of the team; `task wait` is a polling waiter that drains an inbox
- Claim: `_validate_blocked_by_unlocked` rejects self-block and any cycle over the whole team graph (file.py:412-440). `TaskWaiter` loop: receive(limit=50) on monitored inbox → dead-agent check resets `in_progress`→`pending` → count → return `completed` when `completed == total` (0 tasks → immediate) | `timeout` | `interrupted` (waiter.py:148-157,184-309). CLI default inbox = **team leader's** (commands.py:2481-2483), `--agent` overrides; exit code 1 unless completed (2603-2604). `receive` is destructive (mailbox.py:216-237).
- Level: observed. Requirements: TE-05, TE-06, LO-01. Fit: ClawTeam → S~ (wait), caveat: waiting on another team's tasks consumes that team's leader inbox unless `--agent` is given.

### F9. Message model: 12 `MessageType`s, one JSON file per message, non-consumed event log
- Claim: `MessageType ∈ {message, join_request, join_approved, join_rejected, plan_approval_request, plan_approved, plan_rejected, shutdown_request, shutdown_approved, shutdown_rejected, idle, broadcast}` (models.py:50-62). `TeamMessage{type, from, to, content, requestId(hex12 default), timestamp, key, proposedName, capabilities, assignedName, agentId, teamName, planFile, summary, plan, feedback, reason, lastTask, status}` serialised `exclude_none` (models.py:90-121; mailbox.py:116). Sample file `teams/A/inboxes/leader/msg-1755770000123-9f8e7d6c.json`: `{"type":"idle","from":"w1","to":"leader","requestId":"c0ffee...","timestamp":"...","agentId":"3f2c...","lastTask":"1a2b3c4d","status":"completed"}`. Every send/broadcast also appends `events/evt-*.json` (mailbox.py:118,173).
- Level: observed. Requirements: TE-06, TE-07, MS-01. Fit: ClawTeam → S~.

### F10. Transport interface and claim semantics
- Claim: `Transport{deliver(recipient, bytes), fetch(agent, limit, consume), count, list_recipients, close}` + `register_transport(name, cls)` (transport/base.py:253-279; transport/__init__.py:301-317). FileTransport claim = rename `.json`→`.consumed`, `flock` non-blocking, ack unlinks, parse failure → quarantine (transport/file.py:473-510; mailbox.py:204-214). `peek` = non-consuming fetch (skips locked `.consumed`). p2p = ZeroMQ PUSH/PULL with `peers/{agent}.json` lease (5 s) and FileTransport fallback (p2p.py:28-64,100-109). Optional Redis wakeup publishes on `clawteam:{team}:tasks|events|agent:{name}`; best-effort, never raises (redis_wakeup.py:31-38,74-98; store/file.py:197-208; mailbox.py:119-131).
- Level: observed. Requirements: TE-06, TE-08, HB-08. Fit: ClawTeam → S~.

### F11. Shutdown / idle / exit protocol is message-based plus process hooks
- Claim: `request_shutdown`→`shutdown_request`; `approve_shutdown`/`reject_shutdown` reply to requester (lifecycle.py:19-62; CLI commands.py:2826-2890, approver's name from env). `lifecycle idle` sends `idle` to `get_leader_name(team)` + `AgentIdle` event (lifecycle.py:64-88; commands.py:2893-2925). `lifecycle should-keepalive` exits 1 iff a `shutdown_approved` message is *peeked* in the agent's inbox (commands.py:3007-3026). `lifecycle on-exit --team --agent`: write exit journal, clear session file, reset owner's `in_progress`→`pending`, message leader "exited unexpectedly…", emit `WorkerExit` (2928-3004); `on-crash` = on-exit + `WorkerCrash` (3029-3046). Wiring: tmux `set-hook pane-exited/pane-died` (tmux_backend.py:206-225) and the POSIX keepalive shell loop `while true; do eval "$__ct_cmd"; … lifecycle on-exit …; if [ $? -eq 0 ] && lifecycle should-keepalive; then resume; fi` (keepalive.py:53-91; subprocess_backend.py:122-137, Windows path `cmd & on-exit` 124-128).
- Level: observed. Requirements: LO-04, TE-06, XC-04. Fit: ClawTeam → S~.

### F12. Join protocol
- Claim: `team request-join` sends `join_request` to the leader inbox and polls `_pending_{name}` (commands.py:1226-1319); `approve-join` adds member and replies `join_approved{assignedName, agentId, teamName}` (1379-1438). `capabilities` is free text in the message only.
- Level: observed. Requirements: TC-05, TE-04. Fit: ClawTeam → S~.

### F13. Template model: `AgentDef = {name, type, task, command?}` confirmed; `TemplateDef` has 7 fields; harness keys are ignored
- Claim: `AgentDef{name, type="general-purpose", task="", command: list[str]|None}`; `TaskDef{subject, description, owner}`; `TemplateDef{name, description, command=["claude"], backend="tmux", leader: AgentDef, agents[], tasks[]}` (templates/__init__.py:24-44). `_parse_toml` reads only `name, description, command, backend, leader, agents, tasks` (75-100) — `harness = true` and `[template.harness]` in `harness-default.toml` are **inert** (grep `harness` in templates/__init__.py → 0). `render_task` substitutes `{goal}`, `{team_name}`, `{agent_name}`; unknown `{x}` kept (59-68). Search order: `~/.clawteam/templates/{name}.toml` then builtin (103-124). Builtins: `code-review, harness-default, hedge-fund, research-paper, software-dev, strategy-room` (ls clawteam/templates). `clawteam template list|show` (commands.py:3964-4027; `show` dumps the model JSON).
- Evidence (verbatim `clawteam/templates/harness-default.toml`):
  ```toml
  [template]
  name = "harness-default"
  description = "Default plan-then-execute harness with planner, executors, and evaluator"
  command = ["claude"]
  backend = "tmux"
  harness = true

  [template.harness]
  phases = ["discuss", "plan", "execute", "verify", "ship"]
  human_gates = ["plan"]
  wave_parallelism = 3
  evaluator_count = 1

  [template.leader]
  name = "planner"
  type = "planner"
  task = "Analyze the user's goal, discuss requirements, and produce a structured specification with sprint contracts. Each contract must have testable success criteria."

  [[template.agents]]
  name = "evaluator"
  type = "evaluator"
  task = "Review the implementation against the sprint contract success criteria. Test thoroughly and report specific, actionable findings for each criterion."
  ```
- Level: observed. Requirements: TC-01, TC-02, TC-06, AD-08, AD-09. Fit: ClawTeam → C~ for "whole-team preset", M~ for "compose Assistants by reference" (persona = inline `task` string; no reference to a reusable definition).

### F14. `clawteam launch` flow
- Claim (commands.py:4034-4215): load template → team name `{tmpl.name}-{hex6}` or `--team` → `create_team(leader)` → `add_member` per agent (type from AgentDef) → `TaskStore.create(subject, description, owner)` per TaskDef (no deps/priority possible) → backend → `skip_permissions` from config → optional worktrees (`--workspace`) → spawn leader first then agents with `build_agent_prompt(task=render_task(...))`, `is_leader=(name==leader)`, `keepalive=True`, one `--profile` for all. `TeamLaunch` event is never emitted (grep `TeamLaunch(` → only the dataclass).
- Level: observed. Requirements: TE-01, TE-03, HB-03. Fit: ClawTeam → S~ (TE-01), Xs~ (TE-03: one command/profile per launch; per-agent `command` override exists in AgentDef).

### F15. The worker prompt has no persona slot; it is Identity + Task + protocol boilerplate
- Claim: `build_agent_prompt` (spawn/prompt.py:27-108) emits `## Identity` (Name, ID, [User], Type, Team, Leader), optional `## Workspace`, `## Task` (the raw `--task`/template text), optional `## Context` (git overlap), `## Coordination Protocol`, `## Worker Loop Protocol`. "Type" is the only role signal (`agent_type` string). Docstring: "Coordination knowledge … is provided by the ClawTeam Skill, not duplicated here" (prompt.py:1-5). Verbatim Worker Loop Protocol (prompt.py:98-106):
  ```
  ## Worker Loop Protocol
  - For ongoing jobs, do not start a detached daemon/watch loop and then immediately exit.
  - Keep the monitoring/reporting loop in the foreground, or keep a foreground watchdog alive that continues checking health and sending updates.
  - After finishing your current task batch, re-check `clawteam task list {team} --owner {agent}`.
  - If that still shows no tasks, scan `clawteam task list {team}` for pending work that matches your assignment before you go idle.
  - Then check for new instructions with `clawteam inbox receive {team} --agent {agent}`.
  - If you become idle, notify the leader with `clawteam lifecycle idle {team}` and continue checking for new work.
  - Repeat this loop until the leader confirms shutdown or there is truly no more work to do.
  ```
  Prompt delivery: tmux paste-buffer after CLI-ready detection (tmux_backend.py:256-262) or `-p` headless via adapter; `--skill <name>` loads `~/.claude/skills/<name>/SKILL.md` into `--append-system-prompt` (claude/pi only) (commands.py:98-117,3284-3296; tmux_backend.py:110-112).
- Level: observed. Requirements: AD-01, AD-09, HB-02, TE-04. Fit: ClawTeam → Xs~ (HB-02 prompt/system-prompt injection exists for claude/pi; other CLIs get prompt only), M~ (AD-09: persona collapses to one task string).

### F16. The leader is told the same thing; leader-ness is env flag + template text + the Skill
- Claim: `launch` builds the leader prompt with the same function (`leader_name=tmpl.leader.name` → "Leader: <self>", coordination lines tell it to message itself) (commands.py:4163-4174). Distinguishers: `CLAWTEAM_AGENT_LEADER=1`, tmux `remain-on-exit`, and the template's leader `task` (e.g. code-review: "WAIT … `sleep 45 && clawteam board show {team_name}`", code-review.toml:193-210). The real leader playbook is `skills/clawteam/SKILL.md` (v0.3.1) + `references/workflows.md` (Workflows 1-6: create team/tasks, spawn+coordinate, join, plan approval, graceful shutdown, monitoring) + `cli-reference.md`. SKILL.md "Worker Loop Protocol" (lines 163-178) repeats: task list → inbox receive → `lifecycle idle` → "Repeat the loop until the leader explicitly shuts the worker down."
- Level: observed. Requirements: TC-02, AD-01, TE-04. Fit: ClawTeam → C~ (lead behaviour is a Skill + template text).

### F17. `harness/roles.py` roles and HITL gates
- Claim: `DEFAULT_ROLES = {planner, executor, evaluator}` with `RoleConfig{role, system_prompt_addon, phase_affinity}`; `LEADER` constant has no config (roles.py:116-159). Addons are used only by `PhaseRoleSpawner` (spawner.py:27,51,75-77), appended to `build_harness_system_prompt` (harness/prompts.py:165-197) and injected via `--append-system-prompt` (claude/pi). HITL: `HumanApprovalGate(phase)` requires artifact `approval-{phase}.json` (phases.py:323-335); default human gate on `plan` (orchestrator.py:59-61); `clawteam harness approve <team>` writes it (commands.py:4478-4496). Plan approval = message round-trip (`plan_approval_request` with `planFile`, `plan_approved/rejected` with `feedback`) and file `plans/{team}/{agent}-{planid}.md` (team/plan.py:109-161); MCP `plan_submit/get/approve/reject`. `PhaseState{harness_id, team_name, current_phase, phases, phase_roles, phase_history, artifacts, goal, cli, agent_count}` (phases.py:271-285); `SprintContract{id,title,description,tasks[],success_criteria[SuccessCriterion{description,test_command,verified,verified_by,verified_at}],assigned_to[],wave,depends_on[],status}` (contracts.py:439-462).
- Level: observed. Requirements: AD-01, TC-02, EV-03, XC-04. Fit: ClawTeam → C~ (roles), S~ (plan HITL).

### F18. LeaderWatcher injects a "Scheduler check" summary on state change or heartbeat
- Claim: every `interval` (60 s default; or Redis event) compute signature over completed/blocked/leader-inbox-count/dead agents; if changed or heartbeat (300 s) due → `RuntimeEnvelope(source="scheduler", message_type="scheduler_check")` → `backend.inject_runtime_message` (tmux pane paste; subprocess backend re-routes to inbox; wsh) else inbox message from `scheduler` (leader_watcher.py:87-122,165-277). State in `teams/{team}/leader_watch_state.json`.
- Level: observed. Requirements: LO-02, LO-03, TE-06. Fit: ClawTeam → S~ (deterministic poller nudging an LLM).

### F19. RuntimeRouter + DefaultRoutingPolicy (30 s same-pair throttle, aggregation)
- Claim: `inbox watch`/`runtime watch` normalise messages to `RuntimeEnvelope{source,target,channel,priority,message_type,summary,evidence[],recommended_next_action,payload,requires_injection,dedupe_key,created_at}`; `decide()` → `inject` or `aggregate` (throttled) with state in `runtime_state.json`; priority `high` for shutdown/idle/plan messages (router.py:14-138; routing_policy.py:50-140). `inbox watch --exec` runs a shell per message with `CLAWTEAM_MSG_FROM/TO/TYPE/CONTENT/TIMESTAMP/JSON` env (watcher.py:413-441).
- Level: observed. Requirements: LO-02, LO-03, MS-01. Fit: ClawTeam → S~.

### F20. Ralph loop + ContextRecovery only work under `clawteam harness conduct`
- Claim: `RalphLoopPlugin.on_register` subscribes `WorkerExit` (priority -10); `_on_exit` re-spawns via `ctx.spawner.respawn(resume=True, extra_prompt=recovery)` only `if self._ctx.spawner` (ralph_loop_plugin.py:238-282). `PluginManager._build_context()` gives `HarnessContext(bus=...)` with **no spawner** (plugins/manager.py:187-191); `load_all_from_config()` is called only from `harness conduct` (commands.py:4528-4536; grep → 1 caller). `ContextRecovery.build_recovery_prompt` = iteration header + own/all tasks by role + `git log --author={agent}` + artifact (executor: sprint-contract mentioning agent; evaluator/planner: spec.md) + teammate done/total + unread count (context_recovery.py:23-161). `FileExitJournal`: `on-exit` writes `harness/{team}/exit-journal.jsonl` (commands.py:2946; exit_journal.py:181-185) while the conductor reads `harness/{team}/{harness_id}/exit-journal.jsonl` (conductor.py:65-67) — different paths.
- Level: observed. Requirements: LO-04, EV-04, TE-06. Fit: ClawTeam → Xs~ (within-run memory exists; not reusable across runs; project facts only).

### F21. MCP server exposes 26 tools; no spawn/lifecycle/wait/cleanup/launch
- Claim: `clawteam-mcp` = FastMCP("clawteam") registering `TOOL_FUNCTIONS` (mcp/server.py:13-33; tools/__init__.py:138-165); errors surfaced as `MCPToolError` (helpers.py:50-65).

| Tool | Parameters |
|---|---|
| `team_list()` · `team_get(team_name)` · `team_members_list(team_name)` | — |
| `team_create(team_name, leader_name, leader_id, description="", user="", leader_agent_type="leader")` · `team_member_add(team_name, member_name, agent_id, agent_type="general-purpose", user="")` | tools/team.py:176-229 |
| `task_list(team_name, status?, owner?, priority?, sort_by_priority=False)` · `task_get(team_name, task_id)` · `task_stats(team_name)` · `task_create(team_name, subject, description="", owner="", priority?, blocks?, blocked_by?, metadata?)` · `task_update(team_name, task_id, status?, owner?, subject?, description?, priority?, add_blocks?, add_blocked_by?, metadata?, caller="", force=False)` | tools/task.py:238-327 |
| `mailbox_send(team_name, from_agent, to, content?, msg_type?, request_id?, key?, proposed_name?, capabilities?, feedback?, reason?, assigned_name?, agent_id?, message_team_name?, plan_file?, summary?, plan?, last_task?, status?)` · `mailbox_broadcast(team_name, from_agent, content, msg_type?, key?, exclude?)` · `mailbox_receive(team_name, agent_name, limit=10)` · `mailbox_peek(team_name, agent_name)` · `mailbox_peek_count(team_name, agent_name)` | tools/mailbox.py:337-415 |
| `plan_submit(team_name, agent_name, leader_name, plan_content, summary="")` · `plan_get(team_name, plan_id, agent_name)` · `plan_approve/plan_reject(team_name, leader_name, plan_id, agent_name, feedback="")` | tools/plan.py:424-468 |
| `board_overview()` · `board_team(team_name)` · `cost_summary(team_name)` · `workspace_agent_diff(team_name, agent_name, repo?)` · `workspace_file_owners(team_name, repo?)` · `workspace_cross_branch_log(team_name, limit=50, repo?)` · `workspace_agent_summary(team_name, agent_name, repo?)` | tools/board.py, cost.py, workspace.py |
- Level: observed. Requirements: HB-02, MS-01, XC-03. Fit: ClawTeam → P~ (a thin layer can do team/task/mailbox via MCP; spawning/lifecycle only via CLI).

### F22. Nested-team walk-through (A/w1 spawns B/child1) — step table
- Claim: a worker can create another team; nothing links B to A; results and exit notices stay inside B unless the worker also registers itself in B or B's agents send cross-team.

| Step | What happens | Evidence |
|---|---|---|
| 1 | w1 (env `CLAWTEAM_TEAM_NAME=A, CLAWTEAM_AGENT_NAME=w1, CLAWTEAM_AGENT_LEADER=0`) runs `clawteam spawn --team B --agent-name child1 --task …`. Caller identity is not read except `CLAWTEAM_USER`; names/ids come from flags or are generated. | commands.py:3132-3135 |
| 2 | `is_agent_alive(B, child1)` → `None`; `get_team(B)` → `None` → `create_team(B, leader_name=child1, leader_id=<new>, description="Auto-created by clawteam spawn", leader_agent_type=<--agent-type>)`. **child1 becomes B's leader; w1 is not a member of B.** `is_leader=True` → `CLAWTEAM_AGENT_LEADER=1`, `remain-on-exit`. | commands.py:3139-3141,3223-3248; tmux_backend.py:200-204 |
| 3 | Child env = w1's `os.environ` copy + overrides of the 5 identity keys → `CLAWTEAM_TEAM_NAME=B, CLAWTEAM_AGENT_NAME=child1`. Inherited unchanged: `CLAWTEAM_USER`, `CLAWTEAM_DATA_DIR`, `CLAWTEAM_TRANSPORT`, and `CLAWTEAM_WORKSPACE_DIR` (w1's worktree) when no `cwd` is given. Precedence: CLI flag/generated > caller env; caller env never wins for identity keys. | tmux_backend.py:66-85; subprocess_backend.py:45-68 |
| 4 | Prompt to child1: `## Identity … Team: B, Leader: child1`; protocol says "send a summary to the leader: `clawteam inbox send B child1 …`" → results land in `teams/B/inboxes/child1`, invisible to A. | prompt.py:41-52,91-92 |
| 5 | Parent/child linkage: none. `grep -rn -i "parent\|nested\|child\|subteam" clawteam/` → only `Path.parent`, `--cgroup-parent`, "trust parent folder"; `TeamConfig` has no such field; no event carries a creator team. | models.py:77-87; §3 |
| 6 | Workspace (default `auto`): `get_workspace_manager(None)` uses `Path.cwd()`; `repo_root = git rev-parse --show-toplevel`, `base_branch = current branch`. If w1 runs from its worktree `workspaces/A/w1`, child1 gets branch `clawteam/B/child1` based on `clawteam/A/w1`, worktree `workspaces/B/child1`; `workspace merge` targets `base_branch` (the parent's branch). | workspace/manager.py:56-59,73-90,157-166,274 |
| 7 | Alternative: w1 first runs `clawteam team spawn-team B -n w1` (leader id = w1's env `CLAWTEAM_AGENT_ID`), then `spawn --team B --agent-name child1` → w1 is B's leader; child1's `idle`, "All tasks completed", `on-exit` notices go to `teams/B/inboxes/w1`. w1 must poll **explicitly** `clawteam inbox receive B --agent w1` (team is a required positional; `identity.team_name` is never used as a default team). | commands.py:1156-1179,2907,2972-2981; grep `identity.team_name` → 3352 only |
| 8 | `lifecycle on-exit --team B --agent child1` → exit journal `harness/B/…`, `sessions/B/child1.json` cleared, B's `in_progress` tasks owned by child1 → `pending`, message to `get_leader_name(B)`, `WorkerExit(team_name=B)`. Nothing is written under A. | commands.py:2928-2992 |
| 9 | `clawteam team cleanup B` → `rmtree(teams/B, tasks/B, costs/B, sessions/B, plans/B)` + git worktrees of B; **A untouched**; **does not stop B's processes** (no `stop_agent` call) — a still-running child1 recreates `tasks/B` on its next `task update` (`_tasks_root` mkdir). `snapshots/B` is not deleted. `TeamShutdown` is emitted only by `LifecycleManager.cleanup_team`, which has 0 callers; CLI uses `TeamManager.cleanup`. | manager.py:192-221; store/file.py:120-126; commands.py:1515-1530; lifecycle.py:90-118 |
| 10 | `clawteam task wait B --agent w1 [--timeout]` from w1 blocks until all B tasks are `completed` and drains `teams/B/inboxes/w1`; without `--agent` it drains **B's leader inbox** (child1's in step 2). Zero tasks in B → returns `completed` immediately. | commands.py:2467-2491; waiter.py:184-245 |
| 11 | Cross-team send works both ways without membership: `clawteam inbox send A w1 "result"` from child1 (sender from env = child1) delivers to `teams/A/inboxes/w1` and logs in `teams/A/events`; `clawteam inbox send B <nonmember>` creates a stray inbox dir. Transports are constructed per team name (`MailboxManager(team)`), so "scope" is whatever team string the caller passes. | commands.py:1756-1788; mailbox.py:41-46,72-118; transport/file.py:373-381 |
| 12 | Archive of B: `clawteam team snapshot B` bundles config, tasks, events, sessions, costs, pending inboxes into `snapshots/B/snap-{ts}[-tag].json` and survives `team cleanup B`. | snapshot.py:123-183; manager.py:203-213 |
- Level: observed (file:line for every step; step 6 inferred for git behaviour; none probed). Requirements: TE-05, TE-07, EV-04, TC-03. Fit: ClawTeam → P~ (nested run achievable by CLI convention: spawn-team B as self, spawn children, `task wait B --agent self`, read B inbox, snapshot B, cleanup B) / Xs~ (no creator link, no result-return contract, no process stop on cleanup). Corrects recon: "Nested delegation: no API" stands, but the walk-through shows the *composition* path and its two traps (leader auto-assignment to the first spawned child; `task wait` default inbox).

### F23. Event catalogue (18 event types + base); `BeforeWorkerSpawn` is veto-only in practice and not emitted by `clawteam spawn`
- Claim: all events subclass `HarnessEvent{team_name, timestamp}` (events/types.py:342-523):

| Event | Extra fields | Emitted by |
|---|---|---|
| `BeforeWorkerSpawn` | `agent_name, agent_type, command[], veto` | harness/spawner.py:34-42 only (sync `emit`); CLI `spawn`/`launch` never emit it; the handler may mutate `command` in place but the spawner ignores the event's command afterwards (uses `self._cli`) |
| `AfterWorkerSpawn` | `agent_name, agent_id, backend, target` | tmux_backend.py:320 (async) |
| `WorkerExit` | `agent_name, exit_code, abandoned_tasks[]` | commands.py:2987 (sync) |
| `WorkerCrash` | `agent_name, error` | commands.py:3042 |
| `BeforeTaskCreate` | `subject, owner` | store/file.py:212 (async, **after** save — not a veto) |
| `AfterTaskUpdate` | `task_id, old_status, new_status, owner` | store/file.py:309 |
| `TaskCompleted` | `task_id, owner, duration_seconds` | store/file.py:315 |
| `BeforeInboxSend` | `from_agent, to, msg_type` | mailbox.py:135 (async, after delivery) |
| `AfterInboxReceive` | `agent_name, count` | mailbox.py:232 |
| `BeforeWorkspaceMerge` | `agent_name, branch` | workspace/manager.py:266 |
| `AfterWorkspaceCleanup` | `agent_name` | workspace/manager.py:232 |
| `TeamLaunch` | `template, agent_count` | never |
| `TeamShutdown` | — | lifecycle.py:115 (dead path) |
| `AgentIdle` | `agent_name, last_task` | lifecycle.py:84 |
| `HeartbeatTimeout` | `agent_name, last_seen` | never |
| `PhaseTransition` | `from_phase, to_phase, artifacts[]` | harness/phases.py:151 |
| `TransportFallback` | `transport, fallback, reason` | never (grep) |
| `BoardAttach` | — | never (grep) |
  Bus: sync `emit()` in priority order, exceptions swallowed; `emit_async()` = 2-thread pool; `register_event_type()` for plugins (events/bus.py:60-169). Global bus loads config hooks once per process (global_bus.py:179-214).
- Level: observed. Requirements: XC-04, HB-08, EV-03. Fit: ClawTeam → Xs~ (hooks are observational; no pre-spawn mutation point in the CLI spawn path).

### F24. Hooks and plugins
- Claim: `HookDef{event, action ∈ {shell, python}, command, priority, enabled}` (events/hooks.py:232-240; config.py:143-150). Shell hooks get `CLAWTEAM_EVENT_TYPE` + `CLAWTEAM_{FIELD}` (+`OH_`) env, `capture_output`, 30 s timeout (hooks.py:291-317); python = dotted callable (320-329). CLI `hook list|add|remove|test` (commands.py:4224-4306). Plugins: `HarnessPlugin{name, version, description, on_register(ctx), on_unregister, contribute_gates, contribute_prompts}` (plugins/base.py:13-41; `contribute_*` have 0 callers); discovery via entry-point group `clawteam.plugins`, `config.plugins` dotted modules, `data_dir/plugins/*/plugin.json` (manifest listed but never loaded from that path) (plugins/manager.py:62-123,132-178).
- Level: observed. Requirements: XC-03, XC-04, HB-08. Fit: ClawTeam → Xs~.

### F25. `ClawTeamConfig` fields and precedence
- Claim: `data_dir, user, default_team, default_profile, transport, task_store, workspace="auto", default_backend="tmux", skip_permissions=True, timezone, gource_*, profiles{AgentProfile}, presets{AgentPreset}, spawn_prompt_delay=2.0, spawn_ready_timeout=30.0, hooks[HookDef], plugins[str]` (config.py:153-172); env > file > default via `get_effective` map `CLAWTEAM_DATA_DIR/USER/TEAM_NAME/DEFAULT_PROFILE/TRANSPORT/TASK_STORE/WORKSPACE/DEFAULT_BACKEND/SKIP_PERMISSIONS/…` (201-237). `AgentProfile{description, agent, command[], model, base_url, base_url_env, api_key_env, api_key_target_env, env{}, env_map{}, args[]}` (117-130) — credentials by env-name reference only.
- Level: observed. Requirements: AR-04, HB-03, XC-02. Fit: ClawTeam → S~ (AR-04 for profiles), C~ (HB-03 user-level default only; no role-level policy upstream).

### F26. CLI tree (typer) and version facts
- Claim: root `clawteam` (`--version --json --data-dir --transport`; commands.py:22-70) with sub-apps `config, preset, profile, team{spawn-team,discover,request-join,join-status,approve-join,add-member,reject-join,cleanup,status,watch,snapshot,snapshots,restore,snapshot-delete}, inbox{send,broadcast,receive,peek,log,watch}, runtime{inject,watch,state}, task{create,get,update,list,stats,wait}, cost{report,show,budget}, session{save,show,clear}, plan{submit,approve,reject}, lifecycle{request-shutdown,approve-shutdown,reject-shutdown,idle,on-exit,should-keepalive,on-crash,check-zombies}, identity{show,set}, board{show,update,overview,live,serve,attach,gource}, workspace{list,checkpoint,merge,cleanup,status}, context{diff,files,conflicts,log,inject}, template{list,show}, hook{list,add,remove,test}, plugin{list,info}, harness{start,status,advance,contracts,abort,approve,conduct}` + top-level `spawn`, `launch`, `run` (grep `add_typer|@.*command` commands.py:174-4550). Version: pyproject `0.3.0`; git describe `v0.2.0-99-g0119833` (no 0.3.0 tag in clone); SKILL.md frontmatter `version: 0.3.1`.
- Level: observed. Requirements: XC-03. Fit: n/a.

### F27. Fork (ClawTeam-OpenClaw) model deltas relevant to this slice
- Claim (diff upstream→fork): `TeamMember.modelName` (models.py:+75); `TeamMessage.confidence`, `.idempotencyKey`; `TaskItem.idempotencyKey` (+148) with store/mailbox dedupe; `AgentIdentity.model` + `OPENCLAW_*` env prefix (identity.py:+31-34,+61,+88); `AgentDef += task_type, intent, end_state, constraints[], retry{max_retries,backoff_*}, model, model_tier ∈ {strong,balanced,cheap}`; `TemplateDef += model, model_strategy ∈ {auto,none}, max_agents=4`, `command` default `["openclaw"]`, `backend` default via `platform_compat.default_spawn_backend()`; prompt adds `## Mission` (intent/end_state/constraints), `## Shared Memory` (`memory_store/recall` scope), `BOIDS_RULES`, `METACOGNITION_BLOCK` when `team_size>1` (spawn/prompt.py:+9-35,+85-118); lifecycle adds gateway notify + `handle_agent_exit()`; file transport filters `_pending_*`. Same 26 MCP tools, same events/types.py, still no parent/child field (fork grep → only `OPENCLAW_NESTED` unset).
- Level: observed. Requirements: AD-01, HB-03, XC-03. Fit: ClawTeam-OpenClaw → C~ (mission/constraints per AgentDef), still M~ for Assistant-by-reference.

### F28. Cost / session / snapshot records (run-archive raw material)
- Claim: `CostEvent{id, agentName, provider, model, inputTokens, outputTokens, costCents, reportedAt}` (costs.py:21-33; reported by the agent itself via `clawteam cost report`); `SessionState{agentName, teamName, sessionId, lastTaskId, savedAt, state{}}` (sessions.py:20-30; `state.client` used for resume); `SnapshotMeta{id, teamName, tag, createdAt, memberCount, taskCount, eventCount, sessionCount, costEventCount}` + bundle keys `config, tasks, events, sessions, costs, inboxes` (snapshot.py:36-49,171-179). `spawn_registry.json[agent] = {backend, tmux_target, block_id, pid, command[], spawned_at}` (registry.py:39-46).
- Level: observed. Requirements: TE-07, HB-07, XC-04. Fit: ClawTeam → Xs~ (HB-07: harness/model/cost are self-reported, not recorded by the spawner).

## 3. Negative findings
- No parent/child/nested team concept: `grep -rn -i "parent\b\|nested\|\bchild\|subteam\|sub-team\|sub_team" clawteam/` → hits only `Path.parent`, `--cgroup-parent` (command_validation.py:14,74), "trust parent folder" (tmux_backend.py:534, wsh_backend.py:184), "nested structures" docstring (config.py:138), CSS. Same in fork (only `OPENCLAW_NESTED` in an `unset` clause).
- `AgentIdentity.to_env()` has no callers: `grep -rn "to_env()" clawteam/ | grep -v identity.py` → 0.
- `TeamLaunch`, `HeartbeatTimeout`, `TransportFallback`, `BoardAttach` are never emitted (`grep -rn "<Name>(" clawteam/` → only types.py).
- `BeforeWorkerSpawn` is not emitted on the CLI `spawn`/`launch` path (`grep -rn BeforeWorkerSpawn clawteam/` → events/*, harness/spawner.py:30-42 only).
- `LifecycleManager.cleanup_team` has 0 callers (`grep -rn "cleanup_team(" clawteam/` → only def + `ws_mgr.cleanup_team`); CLI cleanup never emits `TeamShutdown`.
- `contribute_prompts`/`contribute_gates` plugin hooks have 0 callers.
- `PluginManager.load_all_from_config` is called only in `harness conduct` (commands.py:4534).
- Template `harness`/`[template.harness]` keys are not read (`grep -n harness clawteam/templates/__init__.py` → 0).
- No persona/role file format, no reusable agent package, no per-role harness policy, no cross-run memory in upstream: searched `grep -rn -i "persona\|soul\|role_file\|agent_package\|memory" clawteam/` → only `harness/roles.py` addons and fork-only "Shared Memory" prompt lines.
- `task wait` cannot target a task subset or another team's tasks by id; only whole-team completion (waiter.py:213-245).
- MCP has no `spawn`, `launch`, `lifecycle_*`, `task_wait`, `team_cleanup`, `template_*` tools (tools/__init__.py:138-165).
- No tests for cross-team or nested behaviour: `grep -rln -i "nested\|subteam\|cross-team" tests/` → only a `tmp_path/"deep"/"nested"` filesystem fixture (test_registry.py:178).

## 4. Platform & license notes
- License: MIT — `ClawTeam/LICENSE` ("Copyright (c) 2025 HKUDS"); pyproject `license = {text = "MIT"}`; fork also MIT (recon). No automation-flag terms in-repo; `skip_permissions=True` default passes `--dangerously-skip-permissions` to claude (config.py:162; SKILL.md:106,255).
- OS paths: file locks `fcntl` vs `msvcrt` in store/file.py:110-113,155-171, transport/file.py:327-336, snapshot.py:7-10, fileutil.py; `_pid_alive` uses `ctypes` on win32 (registry.py:195-218). Keepalive/exit-hook shell is POSIX (`while true … eval`) in tmux and subprocess backends; Windows subprocess uses `cmd & on-exit` without keepalive (subprocess_backend.py:122-137). tmux backend requires tmux (absent on this host; `command -v tmux` → not found). `is_agent_alive` returns `None` for unregistered agents → lock refusals (F7). Python >=3.10 required; host system Python is 3.8.10 (uv provides newer).
- Not exercised here: ClawTeam is not installed (`command -v clawteam` → not found) and installing/running was out of scope for this analyst; every "Level: observed" above is source-read, none probe-verified.

## 5. Open questions
1. Does `git worktree add` from inside a linked worktree (step 6 of F22) behave as inferred on this host's git version? (probe agent)
2. Does a `clawteam spawn` issued by a tmux-spawned worker inherit the worker's `CLAWTEAM_WORKSPACE_DIR` and does any code path read it downstream (grep shows it is only set, never read in upstream — confirm)?
3. Is the exit-journal path mismatch (F20) already fixed upstream after 0119833 (2026-05-09)? Needs a web check of HKUDS/ClawTeam main.
4. Would upstream accept a `created_by{team,agent}` field on `TeamConfig` / a `--parent-team` spawn flag (reuse rung 3)? Unknown; no CONTRIBUTING.md upstream (fork has one).
5. Fork default backend on Windows/macOS via `platform_compat.default_spawn_backend()` — value not read in this slice.

## 6. Probe / CLI log
```
$ cd /home/wsh/Documents/00000/ClawTeam && git log -1 --format='%H %ad %s' --date=short && git describe --tags
01198332ef9270c32c5460b8a178f964fc0df451 2026-05-09 Merge pull request #156 from HKUDS/feat/install-skills-from-scripts
v0.2.0-99-g0119833
$ grep -n '^version' pyproject.toml            → version = "0.3.0"
$ cd ../ClawTeam-OpenClaw && git log -1 --format='%H %ad %s' --date=short; git describe --tags
8dac3fc9774df98f5fea7ba6b5d77bdf6d47d482 2026-07-04 chore(release): v0.3.0+openclaw2
v0.3.0+openclaw2
$ command -v clawteam || echo "clawteam: not found"      → clawteam: not found
$ command -v clawteam-mcp || echo "not found"             → clawteam-mcp: not found
$ command -v tmux || echo "tmux: not found"               → tmux: not found
$ python3 --version                                        → Python 3.8.10
$ uv --version; claude --version; codex --version          → uv 0.11.26; 2.1.239 (Claude Code); codex-cli 0.148.0
$ find clawteam -name '*.py' | xargs wc -l | tail -1       → 18966 total (.py only)
$ grep -rn -i "parent\b\|nested\|\bchild\|subteam\|sub-team\|sub_team" clawteam/ | grep -v "path.parent\|\.parent\b\|parents=True\|Path(__file__).parent"
   → config.py:138 (docstring), tmux_backend.py:534, command_validation.py:14,74, wsh_backend.py:184, board/static/index.html (CSS)
$ grep -rn "to_env()" clawteam/ | grep -v identity.py       → (none)
$ grep -rn "BeforeWorkerSpawn" clawteam/ | grep -v events/   → harness/spawner.py:30,33,34
$ grep -rn "TeamLaunch(" clawteam/                           → events/types.py:133 only
$ grep -rn "cleanup_team(" clawteam/ | grep -v "def cleanup_team\|ws_mgr.cleanup_team" → (none)
$ grep -rn "load_all_from_config\|load_from_module\|load_from_entry_point" clawteam/ | grep -v plugins/manager.py → cli/commands.py:4534
$ grep -rn "contribute_prompts\|contribute_gates" clawteam/ | grep -v plugins/base.py → (none)
$ diff <upstream> <fork> on 10 model files → see F27 (mcp/tools/__init__.py and events/types.py identical)
```
