---
id: ev:clawteam-probe
topic: ClawTeam upstream 0.3.0 installed and exercised in isolation (subprocess backend, shell no-op workers, no tmux) — observed runtime behavior for team execution, per-member harness selection, nested-run simulation, lifecycle hooks
systems: [ClawTeam]
sources:
  - {kind: repo, ref: ClawTeam@01198332ef9270c32c5460b8a178f964fc0df451 (2026-05-09, "Merge pull request #156"), accessed: 2026-08-21, version: 0.3.0}
  - {kind: probe, ref: "uv venv -p 3.11 + uv pip install <copy of repo>; clawteam ... under isolated HOME/CLAWTEAM_DATA_DIR", accessed: 2026-08-21, version: clawteam v0.3.0}
  - {kind: cli, ref: "clawteam --help / <group> --help / <cmd> --help", accessed: 2026-08-21, version: 0.3.0}
method: Copied the repo (excluding .git) to a scratch dir, installed into a Python 3.11 uv venv, ran every command with HOME, CLAWTEAM_DATA_DIR, CLAWTEAM_DEFAULT_BACKEND=subprocess and CLAWTEAM_USER pointing at the scratch dir; spawned only shell no-ops (a script that records its env/args and sleeps); read source to explain observed behavior; killed/verified no leftover processes. Full transcripts in scratchpad probe/log/*.txt (see §6).
platform: {os: Ubuntu (Linux 5.15), tmux: absent, cli_versions: {clawteam: 0.3.0, python: 3.11.16, uv: 0.11.26, mcp: "1.29.0 (2.0.0 breaks clawteam-mcp)", typer: 0.27.1, pydantic: 2.13.4}}
author_agent: ev:clawteam-probe
date: 2026-08-21
confidence: high
status: draft
---
# ClawTeam upstream — isolated install & runtime probe log

## 1. Scope & questions

- §1 Does ClawTeam 0.3.0 install and run on Python 3.11; what CLI/MCP surface exists? → HB-02, TE-06, TE-08, XC-02
- §2 Config resolution and on-disk layout with no prior config → TE-08, XC-02, AD-04
- §3 Templates/presets/profiles as they exist on disk → TC-01, TC-02, TE-01, HB-01, HB-03
- §4 Team, task DAG, inbox semantics with no agent process at all → TE-06, TE-07, MS-01
- §5 Subprocess backend with a shell no-op: prompt injection, env, liveness, on-exit → HB-02, TE-02, TE-06, TE-07, LO-04, XC-04
- §6 Can two Members of one TeamRun run different commands purely by configuration? Precedence CLI vs template vs profile → **TE-03**, TC-05, HB-03, AD-04
- §7 Simulated Nested TeamRun (worker of team A spawns into team B): identity, isolation, cleanup → **TE-05**, TE-07
- §8 Windows/macOS branches touched but not testable here → TE-08, XC-02
- §9 Crashes/unexpected behavior → XC-02

Conventions: `$P` = `/tmp/claude-1000/-home-wsh-Documents-assistant-team-system-dev/17fd77ac-75ce-402b-a1a9-5d1eebba9843/scratchpad/probe`. All commands were run as `env HOME=$P/home CLAWTEAM_DATA_DIR=$P/data CLAWTEAM_DEFAULT_BACKEND=subprocess CLAWTEAM_USER=probe $P/venv/bin/clawteam …` (wrapper `$P/ct.sh`). The no-op worker `$P/bin/noop.sh` writes `hello from $CLAWTEAM_AGENT_NAME …`, argv, cwd and all `CLAWTEAM_*` env to `$P/log/run-<team>-<agent>.out`, then `sleep ${NOOP_SLEEP:-3}`.

## 2. Findings

### F1. Installs on Python 3.11 with uv; `clawteam-mcp` is broken by the unpinned `mcp` dependency
- Claim: `uv pip install $P/src` succeeds on CPython 3.11.16; `clawteam --version` → `clawteam v0.3.0`. But `pyproject.toml` declares `mcp>=1.0.0` with no upper bound; uv resolved `mcp==2.0.0`, whose package has no `mcp.server.fastmcp`, so `clawteam-mcp --help` dies with `ModuleNotFoundError: No module named 'mcp.server.fastmcp'` (ClawTeam/clawteam/mcp/server.py:8). Installing `mcp<2` (resolved 1.29.0) fixes it.
- Evidence: probe §1 (`uv pip install …` exit 0; traceback verbatim in §6); ClawTeam/pyproject.toml:27.
- Level: verified
- Requirements: TE-08, XC-02, HB-02
- Suggested fit cell: ClawTeam → Xs! (packaging pin)

### F2. CLI surface: 23 command groups; MCP server exposes 26 tools but no spawn/launch/lifecycle/template tool
- Claim: Top level: `spawn launch run config preset profile team inbox runtime task cost session plan lifecycle identity board workspace context template hook plugin harness`. Global flags `--json --data-dir --transport`. FastMCP tools (after mcp pin): `team_list team_get team_members_list team_create team_member_add task_list task_get task_stats task_create task_update mailbox_send mailbox_broadcast mailbox_receive mailbox_peek mailbox_peek_count plan_submit plan_get plan_approve plan_reject board_overview board_team cost_summary workspace_agent_diff workspace_file_owners workspace_cross_branch_log workspace_agent_summary`. Process creation exists only in the CLI.
- Evidence: `clawteam --help`; `$P/py.sh $P/list_mcp.py` (mcp.list_tools(), 26 entries) — probe log 01-help-tree.txt, 01c-mcp-tools.txt.
- Level: verified
- Requirements: TE-06, HB-02, MS-01
- Suggested fit cell: ClawTeam → S! (coordination via CLI/MCP), P~ (spawn via CLI only)

### F3. Config: env > file > default; nothing is written until `profile set`/`config set`; the written file bakes in tmux/auto defaults
- Claim: `config show` with no file prints 17 keys with sources (`data_dir env`, `user env`, `default_backend subprocess env`, `workspace auto default`, `skip_permissions True default`, `hooks []`, `plugins []`). `config health` reports data dir exists/writable/latency/mount/teams count. No `$HOME/.clawteam` is created by read commands. `profile set p1 …` then writes `$HOME/.clawteam/config.json` containing every key with its *default* (`"default_backend": "tmux"`, `"workspace": "auto"`, `"data_dir": ""`), plus `profiles`/`presets`; env still wins afterwards (`default_backend subprocess env`).
- Evidence: probe §2 and §6P.2 (file verbatim in log 06p-profiles.txt).
- Level: verified
- Requirements: TE-08, XC-02, HB-03, AD-04
- Suggested fit cell: ClawTeam → C!

### F4. Templates are whole-team TOML presets with a per-agent `command` field; user templates override builtins by name; one builtin is unloadable
- Claim: `template list` shows 5 builtins (`code-review hedge-fund research-paper software-dev strategy-room`); user files `$HOME/.clawteam/templates/*.toml` appear with `Source user` and override by `name`. Schema (`TemplateDef`): `name, description, command: list[str]=["claude"], backend, leader{name,type,task,command|null}, agents[]{name,type,task,command|null}, tasks[]{subject,description,owner}`; placeholders `{goal} {team_name} {agent_name}`. The builtin `harness-default.toml` is *invalid TOML* (`harness = true` followed by `[template.harness]`): `template list` silently skips it (`except Exception: continue`, ClawTeam/clawteam/templates/__init__.py:134-141) and `template show harness-default` crashes with an unhandled `TOMLDecodeError: Cannot overwrite a value (at line 8, column 18)`.
- Evidence: `template show software-dev --json`; `$P/src/clawteam/templates/software-dev.toml`; ClawTeam/clawteam/templates/__init__.py:24-40,103-146; probe §9 traceback.
- Level: verified
- Requirements: TC-01, TC-02, TE-01, TE-03
- Suggested fit cell: ClawTeam → C! (team composition by config), M~ (no Assistant-by-reference; `task` is an inline prompt)

### F5. Presets = provider endpoints; profiles = reusable runtime command+env, may point at any executable
- Claim: 13 builtin presets (`anthropic-official bailian bailian-coding deepseek gemini-vertex google-ai-studio minimax-cn minimax-global moonshot-cn openai-official openrouter zhipu-cn zhipu-global`), each listing client CLIs (`claude/codex/gemini/kimi`) and an `*_API_KEY` *env var name* (never a value). A profile is `{description, agent, command[], model, base_url, base_url_env, api_key_env, api_key_target_env, env{}, env_map{}, args[]}`; `profile set p1 --command "$P/bin/noopA.sh" --env NOOP_FROM_PROFILE=p1` stores `command: ["$P/bin/noopA.sh"]` and is accepted by `spawn --profile p1`.
- Evidence: `preset list`; `profile show p1 --json`; ClawTeam/clawteam/spawn/profiles.py:86-140 (`apply_profile`).
- Level: verified
- Requirements: HB-01, HB-03, AR-04, AD-04
- Suggested fit cell: ClawTeam → C! (harness/provider selection as config), Xs~ (no capability description of a harness)

### F6. Team record on disk has no parent/child field; leader is whoever created the team
- Claim: `teams/{T}/config.json` = `{name, description, leadAgentId, createdAt, members[{name,user,agentId,agentType,joinedAt}], budgetCents}`. Agent IDs are `uuid4().hex[:12]`. `team spawn-team` makes `--agent-name` (default `leader`) the leader; `spawn --team X` into a non-existent team creates X with the spawned agent as leader and description `"Auto-created by clawteam spawn"`.
- Evidence: probe §4b.9 (file verbatim), §7.3; ClawTeam/clawteam/team/models.py:72; ClawTeam/clawteam/cli/commands.py:3221-3231.
- Level: verified
- Requirements: TE-05, TE-07, TC-02
- Suggested fit cell: ClawTeam → Xs~ (TE-05 parent link absent)

### F7. Task DAG: 8-hex ids, `--blocked-by` is not validated, dependents auto-unblock on completion
- Claim: `task create T4 "Task two" --blocked-by 1` succeeded and produced `status: blocked, blockedBy: ["1"]` although no task `1` exists (ids are `uuid4().hex[:8]`, e.g. `6a752549`); that task stays blocked forever. With a real id, completing `6a752549` moved `92edb718` from `blocked` to `pending` automatically. Task JSON fields: `id subject description status priority owner lockedBy lockedAt blocks blockedBy startedAt createdAt updatedAt metadata`. `task wait --timeout` emits `{"event":"progress"…}` lines then `{"event":"result","status":"timeout|completed",…}` and exits 1 on timeout.
- Evidence: probe §4.4–4.6, §4b.1, §4b.7, §4.24; ClawTeam/clawteam/team/models.py:129.
- Level: verified
- Requirements: TE-06
- Suggested fit cell: ClawTeam → S! (DAG), Xs! (dangling-dependency validation)

### F8. Claim/lock semantics: an in_progress task is locked to the caller; others are refused unless the holder is *known dead*
- Claim: `env CLAWTEAM_AGENT_NAME=w1 clawteam task update T4 <id> --status in_progress` sets `lockedBy: "w1", lockedAt, startedAt`. `env CLAWTEAM_AGENT_NAME=w2 … --status in_progress --owner w2` → `"error": "Task '6a752549' is locked by 'w1' (since …). Use --force to override."` even though w1 had never been spawned (registry unknown). Source: `alive = is_agent_alive(team, locked_by); if alive is not False: raise TaskLockError` (ClawTeam/clawteam/store/file.py:241-249) — unknown (`None`) counts as alive. `--force` bypasses; `completed` clears `lockedBy`.
- Evidence: probe §4b.2–4b.6.
- Level: verified
- Requirements: TE-06, TE-04
- Suggested fit cell: ClawTeam → S!
- Correction to recon: "claim refuses if locked by a *live* agent" is imprecise — it refuses unless the holder is provably dead.

### F9. Messaging: no membership check on recipients; inbox dir naming depends on membership; events log is non-consuming
- Claim: `inbox send T4 nobody "x"` succeeds and creates `teams/T4/inboxes/nobody/`. Members resolve to `{user}_{name}` (`probe_w1`), non-members to the bare name (`TeamManager.resolve_inbox`, ClawTeam/clawteam/team/manager.py). Without identity env `from` is `"agent"`. Message file `msg-<epoch-ms>-<hex>.json` = `{type, from, to, content, requestId, timestamp[, key]}`; `receive` deletes the file, `peek` does not; every send is mirrored to `teams/T/events/evt-*.json` (`inbox log`). `broadcast` returns `recipients: ["probe_w1"]` (all members except sender). `MessageType` = `message join_request join_approved join_rejected plan_approval_request plan_approved plan_rejected shutdown_request shutdown_approved shutdown_rejected idle broadcast`.
- Evidence: probe §4.13–4.23, §4b.8, §4b.11; ClawTeam/clawteam/team/models.py:50-62.
- Level: verified
- Requirements: TE-06, TE-07, MS-01
- Suggested fit cell: ClawTeam → S! (local messaging), Xs~ (no addressing boundary)

### F10. `team status` / `board show` do not display liveness
- Claim: While `w2` was running, `team status T5` listed `Name User ID Type Joined` only; `board show T5` adds an `Inbox` count and the task board; neither shows alive/dead. Liveness is only available via `spawn.registry.is_agent_alive` and `lifecycle check-zombies --team T [--max-hours 2.0]`.
- Evidence: probe §5.6, §5.6b; `lifecycle check-zombies --help`.
- Level: verified
- Requirements: TE-06, LO-04
- Suggested fit cell: ClawTeam → Xs!

### F11. `spawn` argument parsing: first positional must be the backend name; `-c` must be protected with `--`
- Claim: `clawteam spawn $P/bin/noop.sh --team T5t` → `"Unknown spawn backend: $P/bin/noop.sh. Available: subprocess, tmux, wsh"` — when any command is given positionally, the backend must also be given positionally (config `default_backend` cannot be combined with a custom command). `clawteam spawn subprocess sh -c "…"` → typer `No such option: -c` (exit 2). Both `clawteam spawn subprocess --team T5 -n w1 … -- sh -c "…"` and `clawteam spawn subprocess $P/bin/noop.sh …` work.
- Evidence: probe §5.3, §5.3b, §5.3c, tmux-missing log; ClawTeam/clawteam/cli/commands.py:3095-3096.
- Level: verified
- Requirements: HB-02, TE-03
- Suggested fit cell: ClawTeam → C! (any executable is spawnable), Xs~ (ergonomics)

### F12. Subprocess backend runs any executable; fallback adapter appends `-p <prompt>`; stdout/stderr discarded
- Claim: For a non-recognised command the adapter appends `["-p", prompt]` (ClawTeam/clawteam/spawn/adapters.py:139-140); `noop.sh` received `argc=2 args=-p|## Identity …`. The prompt (`build_agent_prompt`) contains sections `## Identity` (Name/ID/User/Type/Team/Leader), `## Task`, `## Coordination Protocol` (exact `clawteam task list/update`, `inbox send`, `cost report` commands), `## Worker Loop Protocol`. Env injected: `CLAWTEAM_AGENT_ID AGENT_NAME AGENT_TYPE AGENT_LEADER(0/1) TEAM_NAME DATA_DIR USER BIN` (+`WORKSPACE_DIR` when a worktree exists). Wrapper (POSIX): `<cmd>; __ct_status=$?; CLAWTEAM_EXIT_CODE="$__ct_status" $P/venv/bin/clawteam lifecycle on-exit --team T --agent w; exit $__ct_status` (keepalive loop only when `build_resume_command` knows the CLI). `Popen(shell=True, stdout=DEVNULL, stderr=DEVNULL, cwd=cwd)`; cwd = spawner's cwd when no worktree.
- Evidence: probe §5.9 (`run-T5-w2.out` verbatim in log 05b), `ps` showing `/bin/sh -c $P/bin/noop.sh -p '## Identity…'`; ClawTeam/clawteam/spawn/subprocess_backend.py:45-71,139-147; keepalive.py:53-86.
- Level: verified
- Requirements: HB-02, TE-02, TE-07, XC-04, LO-02
- Suggested fit cell: ClawTeam → S! (HB-02 injection for generic CLIs = argv only), Xs! (no output capture/audit)

### F13. Spawn registry & liveness: pid-based; dead entries persist
- Claim: `teams/T/spawn_registry.json` = `{"<agent>": {backend, tmux_target, block_id, pid, command[], spawned_at}}` (command includes the full prompt). `is_agent_alive` → `True` while sleeping, `False` after exit (`os.kill(pid,0)`), `None` if no entry; `list_dead_agents('T5')` → `['w1','w2']`; entries are never removed on exit.
- Evidence: probe §5.4–5.8; ClawTeam/clawteam/spawn/registry.py:55-80,195-218.
- Level: verified
- Requirements: TE-06, LO-04, XC-04
- Suggested fit cell: ClawTeam → S!

### F14. `lifecycle on-exit` fires after clean exit: resets tasks, messages leader "exited unexpectedly", writes exit journal without exit code
- Claim: After `noop.sh` exited 0: task `3c4d37f1` went `in_progress/lockedBy w1` → `pending/lockedBy ""`; leader inbox received `"Agent 'w1' exited unexpectedly. Reset 1 task(s) to pending: w1 job"` (same text for exit 0); `harness/T5/exit-journal.jsonl` got `{"agent_name":"w1","exit_code":null,"abandoned_tasks":[],"timestamp":…}` — `exit_code` is `null` because `CLAWTEAM_EXIT_CODE` is set by the wrapper but never read (`journal.record_exit(agent_name=agent)`, commands.py:2947) and the journal line is written before abandoned tasks are computed; `costs/T5/summary.json` is created as a side effect.
- Evidence: probe §5.10–5.14; ClawTeam/clawteam/cli/commands.py:2928-3003.
- Level: verified
- Requirements: TE-06, TE-07, LO-04
- Suggested fit cell: ClawTeam → S! (recovery), Xs! (audit fidelity)

### F15. Without tmux: `spawn tmux` fails cleanly and rolls back; `launch` of a tmux template reports success with zero processes
- Claim: `spawn tmux …` → `{"error": "Error: tmux not installed"}`, team `T5t` not created. `launch software-dev --team-name T5L` (template `backend="tmux"`) printed `"status": "launched"`, exit 0, created the team, 5 members and 5 tasks, but no `spawn_registry.json` — per-agent `result` strings (`Error: tmux not installed`) are collected into `spawned[]` and never output (commands.py:4181-4205). Same for `launch probe-two --backend tmux`.
- Evidence: probe 05c-tmux-missing.txt; ClawTeam/clawteam/spawn/tmux_backend.py:61-62.
- Level: verified
- Requirements: TE-08, XC-02, TE-01
- Suggested fit cell: ClawTeam → C! (subprocess path viable without tmux), Xs! (launch error surfacing)

### F16. TE-03 via template: two Members of one TeamRun run different commands purely by TOML configuration
- Claim: User template `probe-two.toml` with `command=["$P/bin/noop.sh"]`, `backend="subprocess"`, agents `alpha.command=["$P/bin/noopA.sh"]`, `beta.command=["$P/bin/noopB.sh"]`, `gamma` (no command). `launch probe-two --team-name T6L --no-workspace` spawned 4 processes; outputs: `alpha NOOP_MARK=A`, `beta NOOP_MARK=B`, `lead/gamma` ran `noop.sh`; registry `cmd0` per agent matches. `launch … --command $P/bin/noopB.sh` changed lead/gamma to noopB but alpha stayed noopA (`a_cmd = agent.command or cmd`, commands.py:4061,4127). `launch … --profile p1` changed lead/gamma to noopA (profile command) but beta stayed noopB; profile env `NOOP_FROM_PROFILE=p1` reached all four.
- Evidence: probe 06-template-launch.txt, 06p-profiles.txt §6P.9; ClawTeam/clawteam/cli/commands.py:4125-4130.
- Level: verified
- Requirements: TE-03, TC-01, TC-05, HB-03
- Suggested fit cell: ClawTeam → C! (per-member harness command by configuration)

### F17. TE-03 via `spawn --profile`: precedence CLI command > profile command > `claude` default; profile env always merges
- Claim: `spawn subprocess --profile p1 … -n a` → noopA; `--profile p2 … -n b` → noopB; `spawn subprocess $P/bin/noopB.sh --profile p1 … -n c` → ran noopB with `NOOP_FROM_PROFILE=p1`; `env CLAWTEAM_DEFAULT_PROFILE=p2 clawteam spawn subprocess --team T6P -n d` → noopB (config `default_profile` honoured). Resolution order in `resolve_profile_name`: `--profile` > configured `default_profile` > single configured profile; multiple profiles without default → error (profiles.py:46-84).
- Evidence: probe 06p-profiles.txt §6P.4–6P.8; ClawTeam/clawteam/spawn/profiles.py:86-110.
- Level: verified
- Requirements: TE-03, HB-03, AD-04
- Suggested fit cell: ClawTeam → C!

| Launch/spawn input | Resulting command | Resulting env |
|---|---|---|
| template agent `command` | wins over everything | + profile env |
| `launch --command X` | replaces template-level default only | — |
| `launch --profile p` | replaces template-level default only | profile env for all agents |
| `spawn <cmd> --profile p` | `<cmd>` | profile env |
| `spawn --profile p` (no cmd) | profile `command` (or `agent`) | profile env |
| `spawn` (nothing) | `claude` | — |

### F18. Simulated Nested TeamRun: inner team auto-created, the spawned child becomes *leader* of it; no link to the creator
- Claim: With `CLAWTEAM_TEAM_NAME=A CLAWTEAM_AGENT_NAME=w1 CLAWTEAM_AGENT_ID=<w1 id>` in the environment, `spawn subprocess $P/bin/noop.sh --team B --agent-name child1` created `B` with `leadAgentId = child1's id`; child1's process saw `CLAWTEAM_AGENT_LEADER=1 CLAWTEAM_TEAM_NAME=B`; `child2` joined as a member. `B/config.json` and `B/spawn_registry.json` contain no mention of `A`, `w1` or a parent; `A/config.json` members (`lead1, w1`) and `A/spawn_registry.json` (`w1`) were unchanged. `team discover` lists `A` and `B` flat. The spawning CLI never reads the caller's identity env.
- Evidence: probe 07-nested.txt §7.2–7.5, §7.11; ClawTeam/clawteam/cli/commands.py:3118-3122.
- Level: verified
- Requirements: TE-05, TE-07, AD-07
- Suggested fit cell: ClawTeam → Xs! (inner-run creation works; parent/result linkage and leader semantics must be added)

### F19. Cross-team messaging and waiting work from anywhere: no isolation boundary between teams
- Claim: `env CLAWTEAM_TEAM_NAME=B CLAWTEAM_AGENT_NAME=child1 clawteam inbox send A w1 "result from inner run"` was delivered and consumed by `inbox receive A --agent w1`. `inbox send B w1 …` (w1 not a member of B) created `B/inboxes/w1/` and was receivable. `task wait B --timeout 2` from A's identity works (`status: completed` with 0 tasks; `timeout` with a pending task).
- Evidence: probe §7.6–7.10.
- Level: verified
- Requirements: TE-05, TE-07
- Suggested fit cell: ClawTeam → P! (result return by message is possible), M~ (isolation of inner task/message space is not enforced by the substrate)

### F20. `team cleanup` deletes data but not processes; an orphaned worker later resurrects directories
- Claim: `team cleanup B --force` removed `teams/B tasks/B costs/B sessions/B` (and plans) but left `harness/B/exit-journal.jsonl`; team A and A/w1 (still alive) were untouched. `team cleanup C --force` while `c1` (sleep 30) was running returned `cleaned` and **did not stop the process** (`ps -p <pid>` alive afterwards); when c1 exited, its `on-exit` hook recreated `harness/C`, `sessions/C`, `tasks/C` (not `teams/C`). `TeamManager.cleanup` (manager.py:192-216) only rmtree's dirs and best-effort worktrees; it never consults the registry.
- Evidence: probe §7.13–7.15 and 08b-misc.txt "C zombie check".
- Level: verified
- Requirements: TE-05, TE-07, LO-04
- Suggested fit cell: ClawTeam → Xs! (archive instead of delete; stop processes on cleanup)

### F21. `--replace` stops and replaces a running same-name Member
- Claim: Spawning `r1` twice → `"Agent 'r1' is already running in team 'T8'. Use --replace to stop it and spawn a new instance."`; with `--replace` the old pid received SIGTERM (gone 1 s later), registry pid updated, member list unchanged (`['r1']`).
- Evidence: probe 08b-misc.txt §8b; ClawTeam/clawteam/spawn/registry.py:121-160.
- Level: verified
- Requirements: TE-04, TE-02
- Suggested fit cell: ClawTeam → S!

### F22. Workspace supplied at run time: `--repo` creates a per-Member worktree under the data dir; cleanup from a non-repo cwd leaves it behind
- Claim: `spawn subprocess noop.sh --team T9 -n ws1 --repo $P/repo` (workspace mode `auto`) printed `Workspace: $P/data/workspaces/T9/ws1 (branch: clawteam/T9/ws1)`; the process ran with `cwd` = worktree and `CLAWTEAM_WORKSPACE_DIR` set; `workspaces/T9/workspace-registry.json` records `{team_name, repo_root, workspaces[{agent_name, agent_id, branch_name, worktree_path, repo_root, base_branch, created_at}]}`. In a non-git cwd with no `--repo`, `auto` silently runs without a worktree (`cwd=$P`). After `team cleanup T9 --force` (run from `$P`, not a repo) `git worktree list` and branch `clawteam/T9/ws1` still existed.
- Evidence: probe 09-misc2.txt; ClawTeam/clawteam/cli/commands.py:3177-3200.
- Level: verified
- Requirements: TE-01, TE-07, AD-05
- Suggested fit cell: ClawTeam → S! (workspace is execution-time input), Xs! (cleanup completeness)

### F23. `launch` = create team + members + tasks + spawn (keepalive on); `spawn` = auto-register + build prompt + spawn
- Claim: `launch` creates the team (leader = template leader), adds members, creates template tasks (`TaskStore.create`), resolves backend `--backend or tmpl.backend`, then spawns leader first then agents with `keepalive=True`; no DAG edges from templates (no `blocked_by` in `TaskDef`). `spawn` resolves backend (`default_backend` or tmux), profile, workspace, auto-creates team/member, builds the prompt only when `--task` is given, optional `--resume` (session store) and `--skill` (reads `~/.claude/skills/<name>`; injected with `--append-system-prompt` for claude/pi only, subprocess_backend.py:92-94).
- Evidence: ClawTeam/clawteam/cli/commands.py:3093-3302, 4034-4185; probe §5/§6.
- Level: verified (paths exercised) / observed (claude/pi branches)
- Requirements: TE-01, TE-02, HB-02
- Suggested fit cell: ClawTeam → S! (TE-01 instantiation), C~ (HB-02 for claude via `--append-system-prompt`)

### F24. Identity is purely environment-based
- Claim: `identity show` reads `CLAWTEAM_AGENT_ID/NAME/TYPE/TEAM_NAME/USER/LEADER`; `identity set` prints `export` lines. All CLI sender/claimer semantics derive from these vars (e.g. `from: "agent"` when unset). Nothing binds an identity to a persistent definition.
- Evidence: `identity --help`; probe §4.14; ClawTeam/clawteam/cli/commands.py:3308-3360.
- Level: verified
- Requirements: AD-05, TE-02, TE-05
- Suggested fit cell: ClawTeam → S! (identity is run-scoped, matches AD-05)

### F25. Windows/macOS code paths: which were exercised in their POSIX form only
- Claim: Exercised here (POSIX branch): advisory locks `fcntl.flock` in `fileutil.py:73`, `store/file.py:65`, `transport/file.py:43`, `team/snapshot.py:92` (win32 uses `msvcrt.locking`); liveness `os.kill(pid,0)` (`registry.py:212`; win32 `ctypes.windll.kernel32.OpenProcess`, :200-210); subprocess wrapper `;`-chain with `CLAWTEAM_EXIT_CODE` and optional `while true` keepalive (`subprocess_backend.py:129-137`; win32 builds `cmd & clawteam lifecycle on-exit …` with no keepalive and no exit code, :124-128); `adapters.py:53 os.getuid()` runs for every spawn with `skip_permissions` (default true) before the claude check → `AttributeError` on Windows (source-only). `stop_agent` uses `signal.SIGTERM`. CI matrix: `ubuntu-latest, macos-latest` only (`.github/workflows/ci.yml:24`). macOS not tested here.
- Evidence: probe 08b-misc.txt (grep table: `win32` 13 sites, `msvcrt` 13, `fcntl` 13, `ctypes` 5, `getuid` 1); source lines cited.
- Level: verified (POSIX), observed (win32 branches)
- Requirements: TE-08, XC-02
- Suggested fit cell: ClawTeam → C! (Ubuntu, subprocess), ?w (Windows), C~ (macOS)

### F26. Crashes and surprises (summary; details in §6)
- Claim: (a) `clawteam-mcp` ImportError with mcp 2.0.0 (F1); (b) `template show harness-default` unhandled `TOMLDecodeError` traceback (F4); (c) `launch` swallows all spawn errors (F15); (d) `spawn … sh -c` parsed as an option (F11); (e) `--blocked-by` accepts unknown ids (F7); (f) `team cleanup` leaves live processes and `harness/` dir, and orphans recreate dirs (F20); (g) exit journal `exit_code: null` (F14); (h) `clawteam run --profile` imports a non-existent `resolve_profile_env` (commands.py:4627; `'resolve_profile_env' in dir(clawteam.spawn.profiles)` → `False`) — confirms recon, not executed; (i) `profile set` persists `default_backend: "tmux"` into a fresh config file (F3).
- Level: verified (a–g, i), observed (h)
- Requirements: XC-02, TE-08
- Suggested fit cell: ClawTeam → Xs!

## 3. Negative findings

- No parent/child team field: `grep -n "parent" $P/src/clawteam/team/models.py` → 0 hits; B's `config.json`/`spawn_registry.json` contain no `A`/`w1`/`parent` (probe §7.3). 
- No MCP tool for spawn/launch/lifecycle/template: `list_tools()` 26 names, none matching `spawn|launch|lifecycle|template` (01c-mcp-tools.txt).
- No liveness in `team status`/`board show` output (probe §5.6/§5.6b).
- No stdout/stderr capture for subprocess workers: `grep -n "DEVNULL" subprocess_backend.py` → lines 144-145; no log file path anywhere in `$P/data` after runs (`find $P/data -name '*.log'` → none).
- No membership check on `inbox send` recipient (probe §4.23) and no team-scoping of callers (`task wait`, `inbox receive` from another team's identity, §7.7–7.10).
- No per-template or per-agent DAG edges: `grep -n "blocked" $P/src/clawteam/templates/__init__.py` → 0 hits (`TaskDef` = subject/description/owner).
- `CLAWTEAM_EXIT_CODE` consumer: `grep -rn CLAWTEAM_EXIT_CODE clawteam/` → only `spawn/keepalive.py:66` (set, never read).
- `harness-default` in `template list` output → absent (invalid TOML).
- No `$HOME/.clawteam` created by read-only commands (`find $P/home` empty until `profile set`).
- No leftover processes after the probe (`ps -eo pid,cmd | grep -E "/bin/sh .*probe/bin/noop|probe/venv/bin/clawteam"` → 0).

## 4. Platform & license notes

- License: MIT — `ClawTeam/LICENSE` ("MIT License, Copyright (c) 2025 HKUDS"); `pyproject.toml` `license = {text = "MIT"}`. No terms-of-use constraints on automation flags found in the repo; the adapter adds `--dangerously-skip-permissions` / `--dangerously-bypass-approvals-and-sandbox` / `--yolo` for known CLIs by default (`skip_permissions=True`), which is a policy concern for those harnesses' own ToS, not ClawTeam's.
- Ubuntu (this host): install, subprocess backend, tasks, inbox, lifecycle, profiles, templates, worktrees all verified; tmux backend unavailable (`which tmux` → none) and fails cleanly.
- Windows: `fileutil/store/transport/snapshot` have `msvcrt` branches, `registry._pid_alive` has a ctypes branch, `subprocess_backend` builds a `cmd & hook` chain (no keepalive loop, no exit code), `adapters.py:53 os.getuid()` is executed unconditionally when `skip_permissions` is true → spawn would raise on Windows until changed (source-only, untested). `tests/test_windows_compat.py` exists.
- macOS: same POSIX branches as Linux; in CI matrix; untested here.
- `mcp` must be pinned `<2` for `clawteam-mcp` to start (F1).

## 5. Open questions

1. Does `clawteam launch` ever surface per-agent spawn failures (e.g. via hooks/events), or is `board show`/registry inspection the only way to notice zero processes? (not found; F15)
2. Is the `probe_w1` vs `w1` inbox-dir split intentional (multi-user namespace) and does `mailbox_receive(agent_name=…)` over MCP follow the same resolution?
3. How would a Nested TeamRun's *result* be returned in ClawTeam terms — only via `inbox send <outer-team> <member>` from the inner run (F19), or via `task update --metadata`? Untested with real agents. *[Owner note 2026-08-23: `clawteam task update` has no `--metadata` option (ClawTeam/clawteam/cli/commands.py:2184-2191); the carrier was decided in `architecture-options.md` §5 — `inbox send` + layer-owned `run.json`, task closed by `--status completed`.]*
4. Does the tmux backend's keepalive/`pane-died` path behave differently from the subprocess wrapper on clean exits (the "exited unexpectedly" wording, F14)? Not testable here.
5. `harness-default.toml`/`clawteam harness` subsystem (plan-then-execute) was not probed beyond the TOML parse failure.
6. Windows: is the `os.getuid()` crash confirmed by upstream tests? (`tests/test_windows_compat.py` not executed.)

## 6. Probe / CLI log

Full transcripts (trimmed tables, verbatim JSON): `$P/log/01-help-tree.txt`, `01b-subhelp.txt`, `01c-mcp-tools.txt`, `04-team-tasks-inbox.txt`, `04b-claims-files.txt`, `05-subprocess-spawn.txt` (failed `-c` attempt), `05b-subprocess-spawn.txt`, `05c-tmux-missing.txt`, `06-template-launch.txt`, `06p-profiles.txt`, `07-nested.txt`, `08-source-checks.txt`, `08b-misc.txt`, `09-misc2.txt`, worker outputs `run-<team>-<agent>.out`. Helper scripts: `$P/ct.sh`, `$P/py.sh`, `$P/bin/noop.sh`, `$P/bin/noopA.sh`, `$P/bin/noopB.sh`, `$P/home/.clawteam/templates/probe-two.toml`, `$P/list_mcp.py`.

Key commands and trimmed outputs:

```
# §1
rsync -a --exclude .git /home/wsh/Documents/00000/ClawTeam/ $P/src/        # RSYNC_OK
uv venv -p 3.11 $P/venv                                                     # CPython 3.11.16
uv pip install --python $P/venv/bin/python $P/src                           # EXIT=0 (mcp==2.0.0 resolved)
$P/ct.sh --version                                                          # clawteam v0.3.0
$P/venv/bin/clawteam-mcp --help
#   ModuleNotFoundError: No module named 'mcp.server.fastmcp'  (server.py:8)
uv pip install --python $P/venv/bin/python "mcp<2"                          # - mcp==2.0.0 + mcp==1.29.0
$P/py.sh $P/list_mcp.py                                                     # TOOL COUNT: 26

# §2
$P/ct.sh config show      # data_dir env | user probe env | default_backend subprocess env | workspace auto default | skip_permissions True default
$P/ct.sh config health    # Exists: yes  Writable: yes  Latency: 0.1 ms  Mount point: no (local)  Teams: 0  User: probe (env)
find $P/home $P/data      # only $P/data/teams created

# §3
$P/ct.sh template list    # code-review hedge-fund research-paper software-dev strategy-room (builtin)
$P/ct.sh template show harness-default   # TOMLDecodeError: Cannot overwrite a value (at line 8, column 18)
$P/ct.sh preset list      # 13 builtin presets
$P/ct.sh profile list     # No profiles configured.

# §4
$P/ct.sh --json team spawn-team T4 -d "probe team" --agent-name lead1 --agent-type leader   # created, leadAgentId 289cc10c9b9d
$P/ct.sh --json task create T4 "Task two" --blocked-by 1 -o w1        # status blocked, blockedBy ["1"] (no task "1")
env CLAWTEAM_AGENT_NAME=w2 $P/ct.sh --json task update T4 6a752549 --status in_progress --owner w2
#   {"error": "Task '6a752549' is locked by 'w1' (since …). Use --force to override."}
$P/ct.sh --json inbox send T4 nobody "x"                              # ok, creates inboxes/nobody/
$P/ct.sh --json inbox broadcast T4 "all hands" (as lead1)             # {"count": 1, "recipients": ["probe_w1"]}
$P/ct.sh --json task wait T4 --timeout 3 --poll-interval 1            # {"event":"result","status":"timeout",...} exit=1

# §5
$P/ct.sh --json spawn subprocess sh -c "echo hi; sleep 3" --team T5 -n w1      # No such option: -c (exit 2)
$P/ct.sh --json spawn subprocess --team T5 -n w1 --no-workspace --task "probe task" -- sh -c "echo hi > …; sleep 2"   # spawned pid=48973
$P/ct.sh --json spawn subprocess $P/bin/noop.sh --team T5 -n w2 --no-workspace --task "probe task"                      # spawned pid=48980
cat $P/data/teams/T5/spawn_registry.json   # {"w2": {"backend":"subprocess","tmux_target":"","block_id":"","pid":48980,"command":["$P/bin/noop.sh","-p","## Identity\n\n- Name: w2 …"],"spawned_at":…}}
$P/py.sh -c "from clawteam.spawn.registry import is_agent_alive,list_dead_agents; …"   # alive: True dead: []   → after exit: alive: False dead: ['w1','w2']
ps -o pid,ppid,stat,cmd -p 48980           # /bin/sh -c $P/bin/noop.sh -p '## Identity …' ; child 48981 /bin/sh $P/bin/noop.sh -p …
cat $P/log/run-T5-w2.out                   # hello from w2 in T5 … argc=2 args=-p|## Identity … cwd=$P  CLAWTEAM_AGENT_ID=… CLAWTEAM_AGENT_LEADER=0 … CLAWTEAM_BIN=$P/venv/bin/clawteam CLAWTEAM_DATA_DIR=$P/data
$P/ct.sh --json task list T5               # 3c4d37f1 pending w1 ""   (was in_progress/locked w1)
$P/ct.sh --json inbox peek T5 --agent lead1  # "Agent 'w1' exited unexpectedly. Reset 1 task(s) to pending: w1 job"
cat $P/data/harness/T5/exit-journal.jsonl  # {"agent_name": "w1", "exit_code": null, "abandoned_tasks": [], "timestamp": …}
$P/ct.sh --json spawn tmux $P/bin/noop.sh --team T5t -n w1 --no-workspace     # {"error": "Error: tmux not installed"}; T5t not created
$P/ct.sh --json launch software-dev --team-name T5L --goal g --no-workspace   # "status": "launched" (5 agents) — no spawn_registry.json

# §6
$P/ct.sh --json launch probe-two --team-name T6L --goal G1 --no-workspace
#   registry: lead noop.sh | alpha noopA.sh | beta noopB.sh | gamma noop.sh ; outputs NOOP_MARK=A / B
$P/ct.sh --json launch probe-two --team-name T6L2 --no-workspace --command $P/bin/noopB.sh   # lead/beta/gamma noopB, alpha noopA
$P/ct.sh profile set p1 --command "$P/bin/noopA.sh" --env NOOP_FROM_PROFILE=p1 ; … p2 …   # OK Saved profile; writes $P/home/.clawteam/config.json
$P/ct.sh --json spawn subprocess --profile p1 --team T6P -n a …  # a→noopA(p1); b→noopB(p2); c (explicit noopB + --profile p1)→noopB with NOOP_FROM_PROFILE=p1; d (CLAWTEAM_DEFAULT_PROFILE=p2)→noopB
$P/ct.sh --json launch probe-two --team-name T6LP --no-workspace --profile p1   # lead/alpha/gamma noopA, beta noopB; all NOOP_FROM_PROFILE=p1

# §7
env CLAWTEAM_TEAM_NAME=A CLAWTEAM_AGENT_NAME=w1 CLAWTEAM_AGENT_ID=599000813fc5 $P/ct.sh --json spawn subprocess $P/bin/noop.sh --team B -n child1 --agent-type child --no-workspace --task "inner task"
#   B created, leadAgentId = child1 id; child1 env CLAWTEAM_AGENT_LEADER=1 CLAWTEAM_TEAM_NAME=B ; A members unchanged ['lead1','w1']
env CLAWTEAM_TEAM_NAME=B CLAWTEAM_AGENT_NAME=child1 $P/ct.sh --json inbox send A w1 "result from inner run"   # delivered; inbox receive A --agent w1 → content
$P/ct.sh --json inbox send B w1 "msg in B for w1" ; inbox receive B --agent w1    # works; B/inboxes/{probe_child1,probe_child2,w1}
$P/ct.sh --json team cleanup B --force     # cleaned; teams/tasks/costs/sessions/B gone; harness/B remains; A intact, A/w1 alive True
$P/ct.sh --json team cleanup C --force (c1 sleeping 30s)   # cleaned; "c1 pid 51641 STILL RUNNING after cleanup"; later harness/C sessions/C tasks/C recreated

# §8b / §9
spawn r1 twice → error "already running … Use --replace"; --replace → old pid gone, registry pid updated
spawn … --repo $P/repo (throwaway git repo) → Workspace: $P/data/workspaces/T9/ws1 (branch: clawteam/T9/ws1); cleanup leaves worktree+branch
ps -eo pid,cmd | grep -E "/bin/sh .*probe/bin/noop|probe/venv/bin/clawteam" | grep -v grep   # count=0 (no leftovers)
```
