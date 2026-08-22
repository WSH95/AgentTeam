---
id: ev:clawteam-spawn-platform
topic: ClawTeam upstream — spawning, harness adapters, definition injection, resume, liveness, library seams, platform support, quality, license
systems: [ClawTeam]
sources:
  - {kind: repo, ref: /home/wsh/Documents/00000/ClawTeam@01198332 (origin https://github.com/HKUDS/ClawTeam.git, v0.3.0, HEAD 2026-05-09), accessed: 2026-08-21, version: 0.3.0}
  - {kind: cli, ref: "gh issue list / gh pr list / gh api repos/HKUDS/ClawTeam (read-only)", accessed: 2026-08-21, version: gh 2.97.0}
  - {kind: cli, ref: "claude --help; codex --help; codex exec --help; codex resume --help; openclaw agent --help; openclaw tui --help; hermes --help; hermes chat --help; grok --help", accessed: 2026-08-21, version: "claude 2.1.239, codex-cli 0.148.0, OpenClaw 2026.7.1-2, Hermes 0.20.4, grok 1.0.5"}
method: Static reading of ClawTeam source with line numbers (no ClawTeam code executed, nothing installed); argv derived by hand-tracing NativeCliAdapter.prepare_command + backend post-processing; local `--help` of installed harness CLIs to verify flag existence; `gh` read-only queries for issue/PR/commit statistics; `git log` statistics on the local clone.
platform: {os: Ubuntu 20.04.6 (Linux 5.15.0-139), tmux: absent, cli_versions: {claude: 2.1.239, codex: 0.148.0, openclaw: 2026.7.1-2, hermes: 0.20.4, grok: 1.0.5, gemini: absent, kimi: absent, qwen: absent, opencode: absent, nanobot: absent, pi: absent, wsh: absent, docker: 28.1.1, python3 (system): 3.8.10, uv: 0.11.26 (3.11.16/3.13.14 available), gh: 2.97.0}}
author_agent: ev:clawteam-spawn-platform
date: 2026-08-21
confidence: high
status: draft
---
# ClawTeam upstream — spawn, adapters, injection, liveness, seams, platform, quality

## 1. Scope & questions

- (a) What exact argv does ClawTeam build per harness CLI, interactive vs headless, and how is the definition/prompt injected? → HB-01, HB-02, HB-08, AD-04
- (b) Which shorthand commands are normalized / rejected? → HB-01, HB-08
- (c) `clawteam spawn` / `launch` / `run` options and how the harness command is resolved → HB-03, TE-03, HB-02
- (d) Backend contract (tmux / subprocess / wsh), `get_backend` / `register_backend` → HB-08, TE-08, HB-06
- (e) Profiles / presets — is there any per-Member or per-TeamTemplate harness/model policy? → HB-03, HB-04, AD-04, TC-05
- (f) Registry, liveness, keepalive, on-exit/on-crash → LO-04, TE-06, HB-07, XC-04
- (g) Library-vs-CLI seams: can another program import and call the pieces; can a plugin/hook mutate prompt/command; MCP server use → XC-03, HB-02, HB-08
- (h) Platform support per code path → TE-08, XC-02
- (i) Quality: tests, logging, known bugs, roadmap, cadence, license → XC-01, XC-03

## 2. Findings

### F1. Adapter layer is a single if/elif chain keyed on executable basename; argv per harness (interactive vs headless)
- Claim: `NativeCliAdapter.prepare_command(command, *, prompt, cwd, skip_permissions, interactive, agent_name, container_env) -> PreparedCommand(normalized_command, final_command, post_launch_prompt)` (ClawTeam/clawteam/spawn/adapters.py:22-46). Detection is by `Path(command[0]).name.lower()` (adapters.py:149-222); the per-CLI argv is hard-coded in one chain (adapters.py:49-140). Backends then add `--append-system-prompt` only for claude/pi (tmux_backend.py:110-112, subprocess_backend.py:92-94, wsh_backend.py:285-290). The table below is derived by hand-tracing (P = worker prompt from `build_agent_prompt`; S = system-prompt text; `[skip]` = flag added when `skip_permissions` is true, which is the config default, config.py:59).

| CLI | interactive argv (tmux backend, `interactive=True`) | headless argv (subprocess backend, `interactive=False`) | perm flag `[skip]` | system prompt S | keepalive resume argv (`keepalive.py:11-35`) | `--resume` session argv (session_locators) | session locator |
|---|---|---|---|---|---|---|---|
| claude / claude-code | `claude --session-id <uuid4> [skip] [--append-system-prompt S]`; P pasted after launch via tmux `load-buffer`/`paste-buffer` + Enter×2 (adapters.py:132-133; tmux_backend.py:256-262, 687-734) | `claude --session-id <uuid4> [skip] --append-system-prompt S -p P` (adapters.py:140; subprocess_backend.py:92-94 inserts S before `-p`) | `--dangerously-skip-permissions`, omitted when `os.getuid()==0` (adapters.py:53-55) | yes (both backends + wsh) | `claude --continue [skip] [--append-system-prompt S]`; subprocess adds `-p <keepalive resume prompt>` (subprocess_backend.py:99-100; keepalive.py:38-50) | `claude ... --resume <id>` (session_locators/claude.py:103-107) | `--session-id` generated at spawn (claude.py:64-74); transcripts `~/.claude/projects/<encoded cwd>/*.jsonl` (claude.py:114-117); env `CLAUDE_CODE_SESSION`/`CLAUDE_SESSION_ID` (claude.py:90) |
| codex / codex-cli | `codex [skip]`; P pasted post-launch unless sub-command is non-interactive (`exec`, `review`, `resume`, …, adapters.py:134-136, 166-187) | `codex [skip] P` — P appended **positionally**, i.e. TUI-with-initial-prompt, not `codex exec` (adapters.py:137-138) | `--dangerously-bypass-approvals-and-sandbox` (adapters.py:56-57) | **no** | `codex resume --last [skip]` (keepalive.py:23-24) | `codex ... resume <id>` (codex.py:80-84) | `~/.codex/sessions/**/*.jsonl` (codex.py:128-129); env `CODEX_THREAD_ID`/`CODEX_SESSION_ID` (codex.py:49) |
| gemini | `gemini [skip] -i P` (adapters.py:127-128) | `gemini [skip] -p P` (adapters.py:129-130) | `--yolo` (adapters.py:58-64) | no | `gemini --resume latest [skip]` (keepalive.py:25-26) | `gemini ... --resume <id>` (gemini.py:74-78) | `$GEMINI_CLI_HOME/.gemini` or `$GEMINI_HOME` or `~/.gemini` → `projects/*/chats/*.json` (gemini.py:48-65, 81-88) |
| kimi | `kimi [skip] [-w cwd] --print -p P` — **always print mode, even in tmux** (adapters.py:66-70) | same | `--yolo` | no | `kimi --continue [skip] [-w cwd]` (keepalive.py:27-28) | none (no locator) | none |
| qwen / qwen-code | `qwen [skip] -p P` (generic branch, adapters.py:139-140) | same | `--yolo` | no | `qwen --continue [skip]` (keepalive.py:29-30) | none | none |
| opencode | `opencode [skip] -p P` (generic branch) | same | `--yolo` | no | `opencode --continue [skip]` (keepalive.py:31-32) | `opencode ... --session <id>` (opencode.py:70-74) | `opencode session list --format json` filtered by cwd (opencode.py:41-68) |
| openclaw | bare `openclaw` → `openclaw agent --local`; then `openclaw agent --local --session-id <agent_name> --message P` (command_validation.py:302-303; adapters.py:104-111); if user passes `openclaw tui …`: `openclaw tui --session <agent_name> --message P` (adapters.py:112-116) | same (no interactive distinction) | none | no | **none** → keepalive loop disabled (keepalive.py:35 returns `[]`; subprocess_backend.py:133-134 / keepalive.py:70-71 emit plain `cmd; on-exit; exit`) | `openclaw agent --local ... --session-id <id>`; tui: `--session agent:main:resume:<id>` (openclaw.py:72-77) | `~/.openclaw/agents/*/sessions/*.jsonl` + `sessions.json` (openclaw.py:47-60) |
| nanobot (incl. `docker run … nanobot`) | bare `nanobot` → `nanobot agent`; `nanobot agent [-w cwd] -m P` (command_validation.py:292-301; adapters.py:100-103); docker-wrapped: adds `-w cwd -v cwd:cwd`, `-v <CLAWTEAM_DATA_DIR>`, clawteam bootstrap mounts and `-e CLAWTEAM_*/OH_*/*_API_KEY/*_BASE_URL/*_API_BASE/GOOGLE_CLOUD_PROJECT` (adapters.py:72-99; cli_env.py:137-186) | same | none | no | none (docker nanobot explicitly `[]`, keepalive.py:17-18) | `nanobot agent ... --session <id>` (nanobot.py:49-53) | `$NANOBOT_HOME/workspace/sessions/*.jsonl` (nanobot.py:39-47) |
| pi | `pi P` (positional, adapters.py:121-122) then `--append-system-prompt S` appended (insert_at = len) | `pi --append-system-prompt S -p P` (adapters.py:123-124) | none (“minimal by design”, adapters.py:118) | yes | `pi --continue` (keepalive.py:33-34) | none | none |
| **generic fallback** (any other executable: `cursor`, `python`, `hermes`, `grok`, …) | `<cmd…> -p P` (adapters.py:139-140) | same | none | no | none → no keepalive loop | none | none |

- tmux quirk: for openclaw, pi and the generic fallback the prompt is delivered **twice** — in argv and again typed into the pane via `tmux send-keys P Enter` after `_wait_for_tui_ready` (tmux_backend.py:263-283; the exclusion list names codex/nanobot/gemini/kimi/qwen/opencode only). Codex and Claude use the paste-buffer path only.
- Startup-dialog automation exists only for claude/codex/gemini trust prompts and the Claude skip-permissions "Yes, I accept" dialog (tmux_backend.py:435-551) and the Codex update gate (566-598).
- Level: observed (argv traced from source; not executed)
- Requirements: HB-01, HB-02, HB-08, TE-03
- Suggested fit cell: ClawTeam → HB-02 claude/pi `S!`; HB-02 codex/gemini/openclaw/others `Xs!` (system-prompt injection absent for 8 of 10 CLIs); HB-08 `Xs!` (adding a CLI = editing the if/elif chain, no adapter registry)

### F2. Hermes, Cursor and Grok are absent from the adapter code; the generic fallback is only viable where the CLI accepts `-p <prompt>`
- Claim: `grep -rni 'hermes\|cursor\|grok' clawteam/` → 5 hits, all CSS/`gource` cursor (none are harness code). Cursor appears only in README.md:550 ("🔮 Experimental", `clawteam spawn subprocess cursor`) and in the skill-install target list (scripts/install_clawteam.sh:61). Locally verified flags (`--help`, 2026-08-21): **Hermes 0.20.4 has no `-p`** (`hermes -z PROMPT`, `hermes chat -q QUERY`, `--resume`, `--continue`, `--yolo`, `--skills`, `--tui/--cli`) → the fallback `hermes -p P` would not be a valid invocation; **grok 1.0.5 has `-p, --single <PROMPT>`**, `--system-prompt-override`, `--output-format`, `-c/--continue`, `--cwd`, `--always-approve` → fallback `grok -p P` is plausibly a working headless run.
- Level: verified (flag existence via `--help`); consequence for Hermes inferred
- Requirements: HB-01, HB-08
- Suggested fit cell: ClawTeam → Hermes `Xs!`, Grok `C~` (fallback works by accident), Cursor `?`

### F3. `normalize_spawn_command` has exactly three rewrite rules and rejects nothing; `validate_spawn_command` only checks executability
- Claim: rules (command_validation.py:285-305): (1) bare `nanobot` → `[nanobot, agent]`; (2) `docker|podman run … <image>` with no remainder or remainder `nanobot` and image name containing "nanobot" → `… nanobot agent`; (3) bare `openclaw` → `[openclaw, agent, --local]`. Everything else is returned unchanged. `validate_spawn_command` (254-282) errors only when the executable is not found on PATH (`shutil.which`) or a path-like executable is not an executable file. No allow/deny list of CLIs exists.
- Level: observed
- Requirements: HB-01, HB-08
- Suggested fit cell: ClawTeam → `S!`

### F4. `clawteam spawn` option surface: `--profile` yes, `--command` no (backend and command are positional); `launch` has `--command` and `--backend`
- Claim: `spawn` signature (cli/commands.py:3093-3108): positional `backend` ("tmux (default) or subprocess") and `command: list[str]`; options `--team/-t`, `--agent-name/-n`, `--profile`, `--agent-type`, `--task`, `--workspace/--no-workspace/-w`, `--repo`, `--skip-permissions/--no-skip-permissions`, `--resume/-r`, `--replace`, `--keepalive/--no-keepalive` (default on), `--skill` (repeatable, help text says "claude only"). There is **no** `--command` and **no** `--backend` option on `spawn` (backend is the first positional). `launch` (4034-4043) has `--goal/-g`, `--backend/-b`, `--profile`, `--team-name/--team/-t`, `--workspace/--no-workspace/-w`, `--repo`, `--command` (list). `run` (4550-4559) has positional `cli`, `goal`, options `--team`, `--profile/-P`, `--workspace/-w`, `--skill/-s`, `--resume`, `--keepalive`.
- Level: observed
- Requirements: HB-03, TE-03
- Suggested fit cell: ClawTeam → `S!`

### F5. Harness command resolution order in `spawn`
- Claim: (1) explicit positional command wins; `resolve_profile_name(explicit, command=…)` returns `None` when a command is given so no implicit profile is applied (profiles.py:46-65, commands.py:3127); (2) else `--profile` / `default_profile` / the single configured profile → `apply_profile` fills the command from `profile.command` or `[profile.agent]` and adds `--model` (claude/codex/gemini/kimi/pi only, profiles.py:156-159) + `profile.args` + env mapping (profiles.py:86-142; commands.py:3205-3215); (3) else `command = ["claude"]` (commands.py:3216-3217). Backend: positional → `default_backend` config → `"tmux"` (3123-3125). `launch`: `--command` → template `command` (default `["claude"]`, templates/__init__.py:40) → per-agent `AgentDef.command` overrides (templates/__init__.py:28; commands.py:4066, 4138). `run`: command is always `[cli]` (4635).
- Level: observed
- Requirements: HB-03, AD-04
- Suggested fit cell: ClawTeam → static per-Member harness via TOML `AgentDef.command` `C!`; precedence policy (user > role > default) `Xs~` (must be computed by a wrapper and passed as the explicit command)

### F6. `--skill` injection reads `~/.claude/skills/<name>/SKILL.md` (or `<name>.md`) and becomes `--append-system-prompt`, applied only to claude and pi
- Claim: `_load_skill_content` (commands.py:98-117) reads Claude Code's user skill dir only; joined content is passed as `system_prompt` to `be.spawn` (3284-3296, 3307). All three backends apply it only when `is_claude_command or is_pi_command` (tmux_backend.py:110-112; subprocess_backend.py:92-94; wsh claude only, wsh_backend.py:285-290); for codex/gemini/openclaw/… the system prompt is **silently dropped** (test `test_subprocess_backend_skips_system_prompt_for_non_claude`, tests/test_spawn_backends.py:1243). `run` additionally prepends `build_harness_system_prompt` (harness/prompts.py:6-39: a "## ClawTeam Runtime" command cheat-sheet) to the skill text (commands.py:4612-4622).
- Level: observed
- Requirements: HB-02, AD-02, AR-02
- Suggested fit cell: ClawTeam → claude `S!`; others `Xs!`

### F7. `runtime inject` works on all three backends but with different delivery semantics; backend method is duck-typed
- Claim: `clawteam runtime inject <team> <agent> --summary … [--source --channel --priority --evidence --recommended-next-action]` (commands.py:1967-2008) resolves the backend from `spawn_registry.json` and requires `hasattr(backend, "inject_runtime_message")` (1996). tmux: paste-buffer into the pane (tmux_backend.py:338-361); subprocess: **queues a mailbox message** to the agent inbox instead (subprocess_backend.py:177-193); wsh: JSON-RPC `send_input` (wsh_backend.py:407-426). Payload is `<clawteam_notification>` XML-ish text (runtime_notification.py:8-43).
- Level: observed
- Requirements: TE-06, LO-03, MS-01
- Suggested fit cell: ClawTeam → `S!` (tmux/wsh live), `P~` (subprocess: inbox poll)

### F8. Backend contract: `SpawnBackend.spawn(...)` + `list_running()`; no liveness method on the backend; `get_backend` consults the registry first
- Claim: `SpawnBackend` ABC (spawn/base.py:8-31) declares `spawn(command, agent_name, agent_id, agent_type, team_name, prompt=None, env=None, cwd=None, skip_permissions=False, system_prompt=None, is_leader=False, keepalive=False) -> str` (a status string; errors are strings starting with `"Error"`, checked by callers commands.py:3313) and `list_running() -> list[dict[str,str]]`. `inject_runtime_message(team, agent_name, envelope) -> tuple[bool,str]` exists on all three built-ins but is not in the ABC. Liveness lives in module functions `registry.is_agent_alive(team, agent)` (registry.py:55-79), not on backends. `register_backend(name, cls)` / `get_backend(name="tmux")` (spawn/__init__.py:10-29): registry lookup first, then `subprocess|tmux|wsh`, else `ValueError("Unknown spawn backend: … Available: subprocess, tmux, wsh")` (registered names are not listed). The TmuxBackend additionally has static `session_name`, `tile_panes`, `attach_all` (tmux_backend.py:363-433).
- Level: observed
- Requirements: HB-08, HB-06, TE-08
- Suggested fit cell: ClawTeam → `S!` for in-process custom backends; see F18 for the CLI-process limitation

### F9. tmux backend mechanics (env file, CLAUDECODE unset, hooks, readiness)
- Claim: env exported via a temp `clawteam-env-*.env.sh` sourced by the pane shell, filtered to shell-safe names, self-deleting (`rm -f`) (tmux_backend.py:140-154); `unset CLAUDECODE CLAUDE_CODE_ENTRYPOINT CLAUDE_CODE_SESSION` prefix so a Claude leader can spawn Claude workers (166); `TERM=dumb` rewritten to `xterm-256color` (70-71); `CLAWTEAM_CONTEXT_ENABLED=1` (83); `tmux new-session -d -s clawteam-<team> -n <agent>` / `new-window` (181-192); `remain-on-exit on` only for the leader (200-204); `set-hook pane-exited → clawteam lifecycle on-exit`, `pane-died → lifecycle on-crash` (206-225); `_wait_for_tmux_pane` (timeout `min(spawn_ready_timeout, max(4, spawn_prompt_delay+2))`, 229-240); `_wait_for_cli_ready` heuristics: last-10-line prompt chars `❯ > ›`, "Try … write a test", or two identical consecutive captures (601-654). Pane PID captured via `#{pane_pid}` for fallback liveness (288-297). `AfterWorkerSpawn` is emitted **only** by this backend (316-328; `grep -rn 'AfterWorkerSpawn(' clawteam/` → tmux_backend.py:320 only).
- Level: observed
- Requirements: TE-06, TE-08, XC-04
- Suggested fit cell: ClawTeam → `S!` on Linux/macOS with tmux; `n/a` on this host (tmux absent)

### F10. subprocess backend: `Popen(shell=True)`, stdout/stderr → DEVNULL, POSIX keepalive wrapper, separate cmd.exe branch on Windows
- Claim: subprocess_backend.py:139-147 — `subprocess.Popen(shell_cmd, shell=True, env=spawn_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=cwd)` ("fire-and-forget; unread pipes can block"). On POSIX `shell_cmd = build_keepalive_shell_command(...)` (130-137) = `cmd; __ct_status=$?; CLAWTEAM_EXIT_CODE="$__ct_status" clawteam lifecycle on-exit --team T --agent A; exit $__ct_status`, or a `while true; do eval "$__ct_cmd"; …; clawteam lifecycle should-keepalive …; __ct_cmd="$__ct_resume"; sleep 1; continue …` loop when keepalive and a resume command exist (keepalive.py:53-91, docstring "POSIX shell"). On `sys.platform == "win32"`: `subprocess.list2cmdline(final_command)` + `" & " + exit_hook` — **no keepalive/resume loop and no `$?` propagation** (124-128). Registry entry records `pid` (151-158). Tested by `test_subprocess_backend_discards_output_and_preserves_exit_hook_and_registry` (tests/test_spawn_backends.py:77).
- Level: observed
- Requirements: TE-08, LO-04, XC-02
- Suggested fit cell: ClawTeam → Ubuntu-without-tmux `C!`; Windows `Xs~` (see F21)

### F11. wsh backend (TideTerm/WaveTerm) is POSIX-shell + Unix-socket based
- Claim: `wsh run -X -c "<export …; cd …&& wrapped>" --cwd …` (wsh_backend.py:325-339); docstring "Input is injected via JSON-RPC over Unix socket" (211); binary discovered at `~/.local/share/tideterm/bin/wsh` or `~/.local/state/waveterm/bin/wsh` (registry.py:228-231); prompt appended positionally for claude only (282-283).
- Level: observed
- Requirements: TE-08
- Suggested fit cell: ClawTeam → `n/a` on this host; `?` Windows

### F12. Profiles/presets are provider/model/env routing for one spawn; no per-Member or per-TeamTemplate harness policy, no fallback, no ensemble
- Claim: `AgentProfile` fields consumed by `apply_profile`: `command|agent`, `env`, `env_map`, `base_url(+_env)`, `api_key_env(+_target_env)`, `model`, `args` (profiles.py:86-142); `_base_url_env_var`/`_api_key_target_env` know only claude/codex/gemini/kimi (162-183). `resolve_profile_name` order: explicit `--profile` > none-if-command > `default_profile` > single profile > `None`, raising on multiple profiles without default (46-83). Presets (presets.py:12-197) are a catalog of provider bundles (`anthropic-official`, `openai-official`, Moonshot/MiniMax/… `claude_compatible_preset`) with `client_overrides` per CLI; `generate_profile_from_preset` (281). `launch --profile` applies **one** profile to **all** agents (commands.py:4129-4142). Nothing in `ClawTeamConfig` (config.py:50-69) or `TeamConfig`/`TeamMember` binds a profile/harness to a member, and nothing implements fallback or multi-harness fan-out (`grep -rn "fallback\|ensemble" clawteam/spawn clawteam/team` → 0 relevant hits).
- Level: observed
- Requirements: HB-03, HB-04, HB-05, AD-04, TC-05
- Suggested fit cell: ClawTeam → HB-03 `Xs~`, HB-04 `XL~`, HB-05 `XL~` (caller-side orchestration; ClawTeam only spawns one process per call)

### F13. Registry record and liveness per backend; zombie/dead listing
- Claim: `register_agent` stores `{backend, tmux_target, block_id, pid, command[], spawned_at}` under `~/.clawteam/teams/<team>/spawn_registry.json` with `file_locked` + `atomic_write_text` (registry.py:26-47, 18-23). `is_agent_alive` → tmux: `tmux list-panes -F '#{pane_dead} #{pane_current_command}'`, dead if `pane_dead==1` or current command is a shell; falls back to pid (55-79, 171-192); subprocess: `_pid_alive` (`os.kill(pid,0)`; Windows `ctypes.windll.kernel32.OpenProcess/GetExitCodeProcess==259`, 195-218); wsh: `wsh blocks list --json` (221-255). `list_dead_agents` (82-90), `list_zombie_agents(max_hours=2.0)` (93-118), `stop_agent` (kill-window / SIGTERM / deleteblock, 121-168). `clawteam lifecycle check-zombies` exits 1 when zombies exist (commands.py:3049-3086).
- Level: observed
- Requirements: TE-06, LO-04, HB-07, XC-04
- Suggested fit cell: ClawTeam → `S!`; HB-07 `Xs~` (no harness version/model/cost/outcome in the record)

### F14. Lifecycle on-exit / on-crash / should-keepalive
- Claim: `lifecycle on-exit` (commands.py:2928-3004): exit-journal record, `SessionStore.clear(agent)`, reset the agent's `in_progress` tasks to `pending`, message the leader, emit `WorkerExit`. `on-crash` = on-exit + `WorkerCrash(error="pane-died")` (3029-3046). `should-keepalive` exits 1 iff a `shutdown_approved` message is in the inbox (3007-3026). Keepalive resume is only attempted when exit status is 0 (keepalive.py:86-88).
- Level: observed
- Requirements: LO-04, TE-06
- Suggested fit cell: ClawTeam → `S!` (POSIX), `n/a` Windows subprocess

### F15. Library seams — importable entry points with stable-looking signatures, but no declared public API
- Claim: `clawteam/__init__.py` exports only `__version__` (no `__all__`, no API doc; README has zero mentions of "plugin", "hook", "register_backend" — `grep -n -i "plugin\|hook\|register_backend" README.md` → 0). Usable seams found:
  - `TeamManager` (all `@staticmethod`, team/manager.py:50-247): `create_team(name, leader_name, leader_id, description="", user="", leader_agent_type="leader") -> TeamConfig`, `add_member(team_name, member_name, agent_id, agent_type="general-purpose", user="") -> TeamMember`, `get_team`, `remove_member`, `get_leader_name`, `cleanup`, `list_members`, `resolve_inbox`, `discover_teams`.
  - `FileTaskStore(team_name)` (store/file.py:45; `TaskStore = FileTaskStore`, team/tasks.py:12): `create(subject, description="", owner="", priority=None, blocks=None, blocked_by=None, metadata=None) -> TaskItem`, `update(task_id, status=None, owner=None, subject=None, description=None, priority=None, add_blocks=None, add_blocked_by=None, metadata=None, caller="", force=False)`, `get`, `list_tasks`, `release_stale_locks`.
  - `MailboxManager(team_name, transport=None)` (team/mailbox.py:32-41): `send(from_agent, to, content=None, msg_type=MessageType.message, request_id=None, key=None, …, summary=None, plan=None, last_task=None, …)`, `broadcast`, `receive(agent_name, limit=10)`, `peek`, `peek_count`.
  - `get_backend(name).spawn(...)` (F8) and `register_backend`.
  - `build_agent_prompt(agent_name, agent_id, agent_type, team_name, leader_name, task, user="", workspace_dir="", workspace_branch="", isolated_workspace=False, repo_path=None) -> str` (spawn/prompt.py:27-39), producing `## Identity / ## Workspace / ## Task / ## Context / ## Coordination Protocol / ## Worker Loop Protocol` sections (42-98).
  All are plain Python; none carry a semver/stability promise; the package is "Development Status :: 3 - Alpha" (pyproject.toml:13).
- Level: observed
- Requirements: XC-03, HB-08, TE-06
- Suggested fit cell: ClawTeam → rung 2 (thin adapter) `P~` — importable today, stability unguaranteed

### F16. Hooks and `BeforeWorkerSpawn` can veto but cannot mutate prompt or command; the event does not even fire on the `spawn`/`launch`/`run` paths
- Claim: `BeforeWorkerSpawn(team_name, agent_name, agent_type, command, veto=False)` (events/types.py:24-31); `EventBus.emit` runs handlers synchronously and "handlers can set event.veto = True … (caller must check)" (events/bus.py:86-101). The only emitter is `PhaseRoleSpawner.spawn_for_phase` (harness/spawner.py:30-44), which then spawns with `command=[self._cli]` (84) — i.e. even an in-place mutation of `event.command` is ignored; `prompt`/`system_prompt` are not on the event at all. `clawteam spawn`, `launch`, `run` never emit it (`grep -n BeforeWorkerSpawn clawteam/cli/commands.py` → 0). Shell hooks receive event fields as `CLAWTEAM_<FIELD>` env vars and return only an exit code (events/hooks.py:77-103); config hooks are loaded lazily on first `get_event_bus()` (events/global_bus.py:22,35-44). `HarnessPlugin` (plugins/base.py:13-41) offers `on_register(ctx)`, `contribute_gates`, `contribute_prompts(phase, role)` — the latter is consulted only by the harness conductor, not by `spawn`.
- Level: observed
- Requirements: HB-02, XC-04, EV-03
- Suggested fit cell: ClawTeam → hook/plugin mutation of the injected definition `M!` for the spawn CLI path; `Xs~` if injection is done by the caller before `spawn()`

### F17. Plugins are loaded only by `clawteam harness conduct`; a plugin's `register_backend` cannot reach a `clawteam spawn` process
- Claim: `PluginManager.load_all_from_config()` is called only in `harness_conduct` (cli/commands.py:4532-4534); `spawn`/`launch`/`run` never instantiate `PluginManager`. Plugin discovery: entry-point group `clawteam.plugins`, `ClawTeamConfig.plugins: list[str]` dotted module paths, and `~/.clawteam/plugins/*` (plugins/manager.py:21-60). The context handed to config-loaded plugins is `HarnessContext(bus=…)` only — `spawner`, `team_name` unset (manager.py:146-150); only the conductor builds a context with a spawner (harness/conductor.py:73-81). A custom backend registered via `register_backend` receives the **full** `spawn(...)` kwargs including `prompt` and `system_prompt` (F8), so a wrapping backend can transform them — but only in the same Python process that called `register_backend`.
- Level: observed
- Requirements: HB-08, HB-02, XC-03
- Suggested fit cell: ClawTeam → custom-backend-from-library `S!`; custom-backend-from-`clawteam spawn` CLI `Xs!` (needs a plugin-load call in the spawn path)

### F18. MCP server exposes 26 coordination tools (team/task/mailbox/plan/board/cost/workspace) over stdio; **no spawn tool**
- Claim: `clawteam-mcp = clawteam.mcp.server:main` (pyproject.toml:44) → `FastMCP("clawteam")`, `mcp.run()` (mcp/server.py:13,32-33; FastMCP default transport is stdio — inferred from the mcp SDK default, not from ClawTeam code). `TOOL_FUNCTIONS` (mcp/tools/__init__.py:28-55): `team_list/get/members_list/create/member_add`, `task_list/get/stats/create/update`, `mailbox_send/broadcast/receive/peek/peek_count`, `plan_submit/get/approve/reject`, `board_overview/team`, `cost_summary`, `workspace_agent_diff/file_owners/cross_branch_log/agent_summary`. `grep -rn "spawn\|get_backend" clawteam/mcp/` → 0. Any MCP client (non-agent program included) can use these.
- Level: observed
- Requirements: TE-06, MS-01, HB-06
- Suggested fit cell: ClawTeam → coordination-over-MCP `S!`; spawn-over-MCP `Xs!`

### F19. Session capture gives claude an explicit `--session-id` per spawn; resume is opt-in (`--resume`); `SessionStore` is cleared on exit
- Claim: `prepare_session_capture` (session_capture.py:34-64) → `ClaudeSessionLocator.prepare` appends `--session-id <uuid4>` unless `--session-id/--resume/-r/--continue/-c/--no-session-persistence` already present (claude.py:30-74); other locators capture asynchronously after launch. `spawn --resume` loads `SessionStore(team).load(agent)` and rewrites the command via `build_resume_command(command, session_id, client=…)` (commands.py:3269-3282; session_capture.py:139-152). `lifecycle on-exit` always `SessionStore.clear(agent)` (commands.py:2954). Locators registered: claude, codex, gemini, opencode, openclaw, nanobot (session_locators/__init__.py:21-28) — none for kimi/qwen/pi.
- Level: observed
- Requirements: TE-02, LO-04, HB-01
- Suggested fit cell: ClawTeam → TE-02 `S!`

### F20. Per-feature OS support matrix (code-path evidence)

| Feature | Ubuntu | macOS | Windows (native) | Evidence |
|---|---|---|---|---|
| tmux backend (default) | yes | yes (CI) | no — returns `"Error: tmux not installed"` | tmux_backend.py:61-62; README.md:382 "Requires … tmux" |
| subprocess backend | yes | yes | partial: cmd.exe branch, no keepalive, no exit-code env | subprocess_backend.py:124-128 |
| `NativeCliAdapter` with `skip_permissions=True` (config default) | yes | yes | **AttributeError `os.getuid`** for every CLI (the call precedes the claude check) | adapters.py:49-53; config.py:59; PR #159 (open) "os.getuid() is Unix-only" |
| keepalive/resume loop | yes (`sh`) | yes | no | keepalive.py:62 "POSIX shell"; subprocess_backend.py:124 |
| tmux env-file / `unset` / `cd &&` | yes | yes | n/a | tmux_backend.py:146-170 |
| wsh backend | yes (TideTerm/WaveTerm) | likely | Unix-socket RPC + POSIX `export` → no | wsh_backend.py:211, 325-332 |
| file locking (fileutil, store, snapshot, transport) | `fcntl.flock` | same | `msvcrt.locking` | fileutil.py:22-25,67-83; store/file.py:14-17,59-75; team/snapshot.py:7-10,84-92; transport/file.py:7-16 |
| atomic write | `os.replace` | same | same (issue #81 fix) | fileutil.py:42-46 |
| pid liveness | `os.kill(pid,0)` | same | `ctypes` OpenProcess | registry.py:195-218 |
| stop agent | SIGTERM | same | `os.kill(SIGTERM)` (TerminateProcess semantics) | registry.py:143-151 |
| executable validation | `shutil.which`, `os.sep/os.altsep` | same | same | command_validation.py:254-282 |
| session locators | `Path.home()` based | same | same paths under `%USERPROFILE%` | session_locators/*.py |
| docker-wrapped nanobot volume specs | yes | yes | broken on `C:\` paths (issue #163, PR #165 open) | command_validation.py:222-226 `spec.split(":")` |
| long prompts via `-p` in subprocess | fine | fine | cmd.exe truncation at newlines reported (PR #159 body) | subprocess_backend.py:125 `list2cmdline` |
| CI coverage | ubuntu-latest | macos-latest | **none** | .github/workflows/ci.yml (matrix os × py 3.10/3.11/3.12) |
| Windows tests | — | — | 1 import-shim test only | tests/test_windows_compat.py:32-48 (fileutil, store/file, snapshot, transport/file import without `fcntl`) |

- Level: observed (code); Windows runtime behaviour inferred from code + PR/issue text, not executed
- Requirements: TE-08, XC-02
- Suggested fit cell: ClawTeam → Ubuntu `S!`, macOS `S~` (CI only), Windows `XL~` (subprocess-only, blocked by `os.getuid` unless `skip_permissions=false`)

### F21. Worker output is not logged anywhere by ClawTeam
- Claim: `grep -rn "import logging\|getLogger" clawteam/spawn/ clawteam/cli/commands.py` → 0. subprocess: stdout/stderr → DEVNULL (F10). tmux/wsh: output exists only in the live pane/block; nothing is persisted by ClawTeam (the harness's own transcript files under `~/.claude/projects`, `~/.codex/sessions`, … are the only record, indexed by session locators). PR #159 (open) proposes `~/.clawteam/logs/`.
- Level: observed
- Requirements: TE-07, HB-07, XC-04
- Suggested fit cell: ClawTeam → `Xs!`

### F22. Known bugs confirmed with line numbers
- Claim:
  1. `clawteam run --profile X` → `from clawteam.spawn.profiles import resolve_profile_env` (commands.py:4627-4628); `grep -rn resolve_profile_env clawteam/ tests/` → only those two lines; the function does not exist → `ImportError` at runtime.
  2. `clawteam run --workspace` → `ws_mgr.create_workspace(team, agent_name)` (commands.py:4605) but the signature is `create_workspace(self, team_name, agent_name, agent_id)` (workspace/manager.py:65-69) → `TypeError`, swallowed by `except Exception: pass` (4607-4608) → silent no-op.
  3. Cleanup duplication: `TeamManager.cleanup` (team/manager.py:191-222; also removes plans + legacy plan paths) vs `LifecycleManager.cleanup_team` (team/lifecycle.py:91-119; emits `TeamShutdown`, does not remove plans).
  4. `launch` appends every spawn result without checking for `"Error"` and prints a success table (commands.py:4176-4189, 4200-4215) — open issue #166, open PR #167.
  5. subprocess/wsh backends never emit `AfterWorkerSpawn` (F9).
  6. `get_backend` error message lists only built-ins even when custom backends are registered (spawn/__init__.py:29).
- Level: observed
- Requirements: XC-03, TE-08
- Suggested fit cell: n/a (quality facts)

### F23. Tests: 39 `test_*.py` files, 564 test functions; what the spawn-relevant ones cover
- Claim: counts via `grep -c "^def test_\|^    def test_"`. Spawn-relevant: `test_adapters.py` (22: detection, `--yolo`, `-p`/`-i`, post-launch prompt for claude/codex, docker nanobot, pi), `test_spawn_backends.py` (50: PATH propagation, DEVNULL+exit hook, tmux env export, trust-prompt confirmation, pane wait, nanobot/docker, gemini/kimi/qwen/opencode flags, system prompt injection claude/pi, keepalive watchdog prompt, `_wait_for_cli_ready`, paste-buffer, runtime injection on 3 backends, `_load_skill_content`), `test_spawn_cli.py` (20: rollback on failure, profile application, skills → system prompt, replace, keepalive default, leader marking, `--repo` cwd), `test_registry.py` (22), `test_session_capture.py` (8), `test_wsh_backend.py` (3), `test_windows_compat.py` (1), `test_profiles.py` (9), `test_presets.py` (8), `test_event_bus.py` (16), `test_lifecycle.py` (7), `test_runtime_routing.py` (11); the remaining 25 files cover tasks (46), mailbox (30), manager (29), harness (34), templates (25), snapshots (21), board, CLI, config, costs, models, paths, store, waiter, MCP, etc. All backend tests mock `subprocess`/`tmux`; none execute a real harness.
- Level: observed
- Requirements: XC-03
- Suggested fit cell: n/a

### F24. Maintenance cadence and community signal
- Claim: local clone = upstream HEAD `01198332` (gh api `repos/HKUDS/ClawTeam/commits?per_page=1` → same SHA, 2026-05-09; `pushed_at` 2026-05-09). 217 commits total; per month: 2026-03: 183, 2026-04: 28, 2026-05: 6, **none in Jun/Jul/Aug 2026** (as of 2026-08-21). Authors: tjb-tech 124, who96 20, Jiabin Tang 12, Yufeng He 8, xzq.xu 8. Tags: v0.1.1, v0.1.2, v0.2.0 (no v0.3.0 tag although pyproject says 0.3.0). GitHub: 5513 stars, 760 forks; issues 15 open / 46 closed; PRs 22 open / 58 merged / 22 closed-unmerged; newest open PR #167 (2026-08-17) and issues #163/#166 (Jul 2026) unanswered by commits. Unmerged PRs touching this scope: #150 (openclaw keepalive), #158 (agent_name substitution + openclaw keepalive), #159 (Windows subprocess), #165 (Windows docker paths), #167 (launch failures).
- Level: verified (gh/git commands)
- Requirements: XC-03, XC-01
- Suggested fit cell: n/a

### F25. ROADMAP and license
- Claim: ROADMAP.md (Chinese) — Phase 1 Transport abstraction (v0.3, done), Phase 2 Redis transport (v0.4), Phase 3 shared state via NFS or Redis (v0.5), then multi-user/Web UI; nothing about harness brokerage, per-member harness policy, or portable assistant definitions. LICENSE: first lines "MIT License / Copyright (c) 2025 HKUDS / Permission is hereby granted, free of charge…" (LICENSE:1-5); `license = {text = "MIT"}` (pyproject.toml:7); GitHub `license.spdx_id = MIT`. Automation-relevant harness flags ClawTeam uses by default (`--dangerously-skip-permissions`, `--dangerously-bypass-approvals-and-sandbox`, `--yolo`) are harness-side terms, not ClawTeam license terms.
- Level: verified
- Requirements: XC-01
- Suggested fit cell: ClawTeam → XC-01 `S!` (MIT permits selective reuse with attribution)

### F26. Every flag ClawTeam emits for claude/codex/openclaw exists in the locally installed versions
- Claim: verified by `--help` (see §6): claude 2.1.239 has `--append-system-prompt`, `--session-id <uuid>`, `-r/--resume [value]`, `-c/--continue`, `--dangerously-skip-permissions`, `-p/--print`; codex-cli 0.148.0 has `exec`, `resume [SESSION_ID] [PROMPT] --last`, `--dangerously-bypass-approvals-and-sandbox`, and **`-p` = `--profile`** (so ClawTeam's positional prompt for codex is correct); OpenClaw 2026.7.1-2 has `agent --local --session-id -m/--message` and `tui --session --message`.
- Level: verified
- Requirements: HB-01, HB-02
- Suggested fit cell: n/a (input for harness-profile evidence)

## 3. Negative findings

- No Hermes/Cursor/Grok adapter: `grep -rni 'hermes\|cursor\|grok' clawteam/` → 5 non-harness hits (gource.py, static/index.html CSS). Cursor only in README.md:28,384,550 and scripts/install_clawteam.sh:61.
- No `--command` option on `spawn`: `grep -n '"--command"' clawteam/cli/commands.py` → only launch (4043).
- No `BeforeWorkerSpawn` emission on spawn/launch/run paths: `grep -rn BeforeWorkerSpawn clawteam/` → types.py, events/__init__.py, harness/spawner.py only.
- No `AfterWorkerSpawn` from subprocess/wsh: `grep -rn 'AfterWorkerSpawn(' clawteam/` → tmux_backend.py:320 only.
- No spawn tool in MCP: `grep -rn 'spawn\|get_backend' clawteam/mcp/` → 0.
- No logging in spawn layer: `grep -rn 'import logging\|getLogger' clawteam/spawn/ clawteam/cli/commands.py` → 0.
- No `resolve_profile_env`: `grep -rn resolve_profile_env clawteam/ tests/` → commands.py:4627-4628 only (call sites, no definition).
- No per-member profile/harness field: `grep -n "profile\|command\|harness" clawteam/team/models.py` → 0 in `TeamMember`/`TeamConfig` (only `TemplateDef.command`/`AgentDef.command` in templates/__init__.py:28,40).
- No fallback/ensemble: `grep -rn "fallback" clawteam/spawn/` → only `resolve_clawteam_executable` docstring/comments; `grep -rn "ensemble" clawteam/` → 0.
- No plugin/hook/backend-API documentation: `grep -n -i "plugin\|hook\|register_backend" README.md` → 0; `docs/` contains only `transport-architecture.md` + site assets.
- No "AgentDefinition" feature in this repo (issue #146 refers to `~/.openharness/agents/*.md`): `grep -rn AgentDefinition clawteam/` → 0.
- No Windows CI job: `.github/workflows/ci.yml` matrix `os: [ubuntu-latest, macos-latest]`.
- No `is_alive` on `SpawnBackend`: `grep -n "def is_alive" clawteam/spawn/*.py` → 0 (liveness is `registry.is_agent_alive`).

## 4. Platform & license notes

- Host facts: Ubuntu 20.04.6 / Linux 5.15, **tmux absent**, wsh absent; system Python 3.8 (ClawTeam requires >=3.10, pyproject.toml:6), uv provides 3.11/3.13. On this host only the `subprocess` backend is runnable (F10, F20); `tmux` default must be overridden via positional `backend` or `default_backend` config.
- Windows: see F20 matrix. Net: subprocess-only, `skip_permissions` must be set false to avoid `os.getuid` (adapters.py:53), no keepalive/resume, no exit-code env, prompt length/newline truncation reported (PR #159), docker path bug (#163). Windows is not in CI; one import-shim test exists.
- macOS: covered by CI (macos-latest × 3.10–3.12) for unit tests; all POSIX paths apply.
- License: MIT (LICENSE:1-3, "Copyright (c) 2025 HKUDS"); pyproject `license = {text = "MIT"}`; GitHub SPDX MIT. No additional terms of use found in the repo. Harness automation flags ClawTeam enables by default (`--dangerously-skip-permissions`, `--dangerously-bypass-approvals-and-sandbox`, `--yolo`) are governed by each harness's own terms, outside this repo.

## 5. Open questions

1. Does `codex <positional prompt>` (subprocess headless argv, F1) actually start without a TTY under `Popen(stdout=DEVNULL)`? Not executed here; README's "Adding a Different Agent" contract (README.md:519-536) only says an agent "must accept an initial task, either by command-line argument or interactive input" and never mentions `codex exec` — needs a probe.
2. FastMCP `mcp.run()` default transport assumed stdio (mcp SDK behaviour, not in ClawTeam source) — confirm against the installed `mcp` version if MCP use is proposed.
3. Will upstream merge PR #159/#165/#167 (Windows + launch failures)? No commits since 2026-05-09; affects whether a Windows path is "configuration" or "extension".
4. Session capture for claude relies on `~/.claude/projects/<encoded cwd>` naming (claude.py:110-117); stability across Claude Code versions is unverified.
5. Whether the double prompt delivery for openclaw/pi/generic in tmux (F1) is intentional or a bug — not documented.

## 6. Probe / CLI log

(Trimmed; nothing from ClawTeam was executed or installed.)

```
$ git -C /home/wsh/Documents/00000/ClawTeam log -1 --format='%H %ad %s' --date=iso
01198332ef9270c32c5460b8a178f964fc0df451 2026-05-09 15:25:55 +0800 Merge pull request #156 …
$ git rev-list --count HEAD → 217 ; git log --format='%ad' --date=format:'%Y-%m' | sort | uniq -c → 183 2026-03 / 28 2026-04 / 6 2026-05 ; git tag → v0.1.1 v0.1.2 v0.2.0
$ gh api 'repos/HKUDS/ClawTeam/commits?per_page=1' → 01198332… 2026-05-09T07:25:55Z
$ gh api repos/HKUDS/ClawTeam → stars=5513 forks=760 license=MIT pushed_at=2026-05-09 open_issues=37
$ gh issue list --state open|closed → 15 | 46 ; gh pr list open|merged|closed-unmerged → 22 | 58 | 22
$ gh pr view 159 → "adapters.py: os.getuid() is Unix-only … CMD.exe truncates long prompts at newlines … redirect stdout/stderr to log files … instead of DEVNULL"
$ gh issue view 81 → "Missing fcntl module on Windows … Path.rename() not atomic" (closed 2026-03-30) ; gh issue view 166 → launch reports success on 100% spawn failure (open)
$ grep -c "^def test_\|^    def test_" tests/test_*.py → 564 across 39 files
$ cat .github/workflows/ci.yml → lint ubuntu-latest py3.12 ruff; test matrix os:[ubuntu-latest, macos-latest] × python:[3.10,3.11,3.12]
$ head -3 LICENSE → MIT License / Copyright (c) 2025 HKUDS
$ grep -rn "getuid" clawteam/ → clawteam/spawn/adapters.py:53
$ grep -rn "sys.platform" clawteam/ → registry.py:200, fileutil.py:22,67,77, subprocess_backend.py:124, store/file.py:14,59,69, team/snapshot.py:7,84, transport/file.py:7,25,37
$ which tmux wsh → absent ; claude --version → 2.1.239 ; codex --version → codex-cli 0.148.0 ; openclaw --version → 2026.7.1-2 ; hermes --version → 0.20.4 ; grok --version → 1.0.5
$ claude --help → --append-system-prompt, --session-id <uuid>, -r/--resume [value], -c/--continue, --dangerously-skip-permissions, -p/--print, --output-format, --permission-mode, --agents <json>, --mcp-config, --add-dir, --settings
$ codex --help → exec, resume, --dangerously-bypass-approvals-and-sandbox, -s/--sandbox, -a/--ask-for-approval, -C/--cd, -p/--profile ; codex resume --help → [SESSION_ID] [PROMPT] --last
$ openclaw agent --help → --local, --session-id <id>, -m/--message, --agent <id>, --json, --thinking, --timeout ; openclaw tui --help → --session <key>, --message
$ hermes --help → [-z PROMPT] [--resume SESSION] [--continue] [--yolo] [--skills] [--tui] [--cli] {chat,…} ; hermes chat --help → -q QUERY, -r/--resume (no -p)
$ grok --help → Usage: grok [OPTIONS] [PROMPT] [COMMAND] ; -p, --single <PROMPT> ; --system-prompt-override ; --output-format ; -c/--continue ; --cwd ; --always-approve
```
