---
id: ev:fork-delta
topic: ClawTeam-OpenClaw fork (win4r) vs upstream HKUDS/ClawTeam — definitive feature delta, classification, merge cost, and what the installed OpenClaw/Hermes CLIs actually accept
systems: [ClawTeam, ClawTeam-OpenClaw]
sources:
  - {kind: repo, ref: /home/wsh/Documents/00000/ClawTeam-OpenClaw@8dac3fc, accessed: 2026-08-21, version: 0.3.0+openclaw2 (tag v0.3.0+openclaw2, 2026-07-04)}
  - {kind: repo, ref: /home/wsh/Documents/00000/ClawTeam@0119833, accessed: 2026-08-21, version: 0.3.0 (2026-05-09)}
  - {kind: web, ref: https://api.github.com/repos/win4r/ClawTeam-OpenClaw/commits?per_page=3, accessed: 2026-08-21}
  - {kind: web, ref: https://api.github.com/repos/HKUDS/ClawTeam/commits?per_page=3, accessed: 2026-08-21}
  - {kind: cli, ref: "openclaw --version; openclaw --help; openclaw tui --help; openclaw agent --help; openclaw approvals --help", accessed: 2026-08-21, version: OpenClaw 2026.7.1-2 (0790d9f)}
  - {kind: cli, ref: "hermes --version; hermes chat --help", accessed: 2026-08-21, version: Hermes Agent v0.20.4 (2026.8.18)}
method: Upstream HEAD 0119833 is a direct ancestor of fork HEAD (merge-base = 0119833), so `git -C <fork> diff 0119833 HEAD` is the exact delta. Read every changed file under clawteam/, tests/, skills/, scripts/ (diffs in scratchpad/ev-fork-delta/); grepped both trees per feature keyword; counted commits/tests; diffed LICENSE/ci.yml; read CHANGELOG.md/CLAUDE.md; checked GitHub HEADs; ran read-only `--help` on installed OpenClaw/Hermes. No repo scripts executed; ~/.openclaw inspected for key NAMES only.
platform: {os: Ubuntu (Linux 5.15), tmux: absent, cli_versions: {openclaw: 2026.7.1-2 (0790d9f), hermes: 0.20.4 (2026.8.18), python_system: 3.8 (uv 3.11/3.13 available)}}
author_agent: ev:fork-delta
date: 2026-08-21
confidence: high
status: draft
---
# ClawTeam-OpenClaw fork delta — verified classification

## 1. Scope & questions
- Which fork features are already upstream, fork-only, worth upstreaming, worth selective reuse, or irrelevant to the revised product? → HB-01..HB-08, TE-06, TE-08, LO-04, XC-01..XC-03.
- How expensive is it to merge fork work back into upstream (adapter bypass, xfail markers, dead code)? → XC-03 (reuse ladder rung 3 vs 4 vs 5).
- How exactly does each side spawn an OpenClaw worker, and do those flags exist on the OpenClaw CLI installed here (2026.7.1-2)? → HB-01, HB-02, MS-02.
- Licensing and platform constraints of both trees. → XC-01, XC-02, TE-08.
- Which recon-appendix statements were wrong or imprecise? (listed inline and in the summary).

Terminology note: ClawTeam's own words "agent/worker/leader/team" are quoted as ClawTeam code vocabulary; product terms (Harness, HarnessInvocation, TeamRun, Member) follow the glossary.

## 2. Findings

### F1. The fork is upstream HEAD + 112 commits; both local clones are current
- Claim: Fork HEAD `8dac3fc` (2026-07-04, "chore(release): v0.3.0+openclaw2") contains upstream HEAD `0119833` (2026-05-09) as a direct ancestor; `git log --oneline HEAD ^0119833 | wc -l` = 112; totals 329 (fork) vs 217 (upstream). Fork-only commits span 2026-03-18 → 2026-07-04; upstream merge happened in `cc2b09a` (2026-05-28, "merge upstream/main 2026-05-28 (197 commits)"). GitHub API shows the same HEADs on both repos today.
- Evidence: `git -C ClawTeam-OpenClaw merge-base HEAD 0119833` → `0119833…`; GitHub API responses (accessed 2026-08-21).
- Level: verified
- Requirements: XC-03
- Suggested fit cell: n/a

### F2. Exact delta size: 88 files, +13 158/−2 006, 5 new modules, 2 deleted
- Claim: `git diff --shortstat 0119833 HEAD` → 88 files changed; name-status 37 A / 48 M / 3 D. New Python modules: `clawteam/model_resolution.py` (70 lines), `clawteam/platform_compat.py` (130), `clawteam/spawn/respawn.py` (86), `clawteam/spawn/subprocess_wrapper.py` (66), `clawteam/team/gateway.py` (140). Deleted: `clawteam/spawn/wsh_backend.py` (454), `clawteam/spawn/wsh_rpc.py` (106), `tests/test_wsh_backend.py`. LOC clawteam/: 18 966 → 20 060. Tests: 564 functions/39 files → 705/50 files.
- Evidence: scratchpad `ev-fork-delta/name-status.txt`, `diffstat.txt`.
- Level: verified
- Requirements: XC-03
- Suggested fit cell: n/a

### F3. Bare-`openclaw` default differs (`agent --local` vs `tui`), but the adapter's `tui --session` branch is ALREADY upstream
- Claim: Upstream `normalize_spawn_command` expands bare `openclaw` to `["openclaw","agent","--local"]` (ClawTeam/clawteam/spawn/command_validation.py:302-303); fork returns `[command[0],"tui"]` (ClawTeam-OpenClaw/clawteam/spawn/command_validation.py:302-307, comment: "OpenClaw >= 2026.6 made `openclaw agent` a single-turn command"). However `NativeCliAdapter.prepare_command` in BOTH trees already contains an `agent` branch (`--local`, `--session-id <agent_name>`, `--message`) and an else-branch for `tui` (`--session <agent_name>`, `--message`) — ClawTeam/clawteam/spawn/adapters.py:104-116 and identical text at ClawTeam-OpenClaw/clawteam/spawn/adapters.py:121-133 (fork did not touch this block). So "tui --session form" is fork-only only as the *default* plus the session-key scheme; recon listed it as wholly fork-only — **correction**.
- Level: observed
- Requirements: HB-01, HB-02, MS-02
- Suggested fit cell: ClawTeam → C~ (explicit `openclaw tui` works via adapter; bare default stale) · ClawTeam-OpenClaw → S~

### F4. Fork tmux argv for an OpenClaw worker (exact composition)
- Claim: `TmuxBackend.spawn` builds `full_cmd = "unset CLAUDECODE CLAUDE_CODE_ENTRYPOINT CLAUDE_CODE_SESSION OPENCLAW_NESTED 2>/dev/null; . <env.sh>; [cd <cwd> &&] trap \"<clawteam> lifecycle on-exit --team T --agent A\" EXIT; openclaw tui --session clawteam-T-A [--model M] [--agent ID] --message <prompt>"` and launches it with `tmux new-session|new-window … -P -F '#{window_id}'`, recording the window id as the agent's target. Session key = `f"clawteam-{team_name}-{agent_name}"`; every flag append is guarded (`"--session" not in final_command`) so respawn is idempotent.
- Evidence: ClawTeam-OpenClaw/clawteam/spawn/tmux_backend.py:228-249 (flags), :296-308 (trap + unset), :323-337 (`-P -F #{window_id}`, `_kill_stale_same_name_windows`), :198-206 (env temp file). Upstream instead calls `self._adapter.prepare_command` (ClawTeam/clawteam/spawn/tmux_backend.py:97,116), wraps with `build_keepalive_shell_command` (:156) and sets tmux hooks `pane-exited`/`pane-died` (:217-226); upstream session key for openclaw is bare `agent_name` (adapters.py:109,114).
- Level: observed
- Requirements: HB-02, HB-07, TE-02
- Suggested fit cell: ClawTeam-OpenClaw → S~ (OpenClaw worker spawn) · ClawTeam → Xs~

### F5. What OpenClaw 2026.7.1-2 actually accepts — `tui` has `--session/--message` but NOT `--model`/`--agent`/`--session-id`
- Claim: `openclaw tui --help` options: `--deliver, --history-limit, --local, --message <text>, --password, --session <key>, --thinking, --timeout-ms, --token, --url`. `openclaw agent --help` options: `--agent <id>, --local, -m/--message, --message-file, --model <id>, --session-id <id>, --session-key <key>, --to, --thinking, --timeout, --json, --deliver, --channel…`; description "Run an agent turn via the Gateway (use --local for embedded)". `chat`/`terminal` = "alias for tui --local". Consequences: (a) fork tmux form `tui --session … --message …` is valid; (b) fork's `--agent` append is gated by `_openclaw_supports_agent_flag()` which greps `openclaw tui --help` for `--agent` (tmux_backend.py:52-64) → False on 2026.7.1-2, flag dropped with a stderr warning (:113-118) — i.e. `--openclaw-agent` is a no-op here; (c) fork appends `--model M` to the `tui` form whenever a model resolves (tmux_backend.py:237-238, subprocess_backend.py:132-133) — not a `tui` option in 2026.7.1-2, so `--model`/`model_tier` on the OpenClaw path would be rejected by the parser (inferred, not executed); (d) upstream's bare `agent --local --session-id A --message P` uses existing flags, but `agent` is single-turn (CHANGELOG.md:31 "spawned workers exited immediately").
- Evidence: scratchpad `ev-fork-delta/openclaw-tui-help.txt`, `openclaw-agent-help.txt`; fork lines above.
- Level: verified (CLI help) / inferred (rejection of `--model`)
- Requirements: HB-01, HB-02, HB-03
- Suggested fit cell: ClawTeam-OpenClaw → Xs! (OpenClaw HarnessProfile: resident TUI session OK; per-invocation model selection not expressible on `tui`)

### F6. Fork subprocess path for bare `openclaw` emits `openclaw tui --session-id …` (flag mismatch, untested)
- Claim: `SubprocessBackend.spawn` normalizes bare `openclaw` → `["openclaw","tui"]`, then (since "tui" is present it does not insert "agent") appends `["--session-id", "clawteam-T-A", "--message", prompt]` (ClawTeam-OpenClaw/clawteam/spawn/subprocess_backend.py:160-168). `--session-id` is an `agent` option, not a `tui` option (F5). No test asserts the subprocess+openclaw argv: `grep -n openclaw tests/test_spawn_backends.py` → 0 hits; `tests/test_openclaw_agent.py` covers tmux only plus `NotImplementedError` for `openclaw_agent` on subprocess (:318-325). Also the worker-workspace isolation is not applied on subprocess (`grep -c OPENCLAW_WORKSPACE subprocess_backend.py` → 0). Relevant here because this host has **no tmux** (TE-08).
- Level: inferred (from source + CLI help; not executed)
- Requirements: TE-08, HB-02, XC-02
- Suggested fit cell: ClawTeam-OpenClaw → Xs~ (no-tmux OpenClaw path)

### F7. Worker-workspace isolation (tmux only) — fork-only
- Claim: `_ensure_worker_workspace()` creates `~/.clawteam/worker-workspace/AGENTS.md` (content `_WORKER_AGENTS_MD`, tmux_backend.py:44-48, :67-79) and exports `OPENCLAW_WORKSPACE` to the worker (:165-169) "to prevent NO_REPLY behavior or workspace-rule pollution" from the user's SOUL.md/AGENTS.md/USER.md. Upstream: `grep -rn OPENCLAW_WORKSPACE ClawTeam/clawteam` → 0.
- Level: observed
- Requirements: TE-02, AD-05, HB-02
- Suggested fit cell: ClawTeam-OpenClaw → S~ · ClawTeam → Xs~

### F8. Gateway-token propagation — fork-only; copies a secret into env and a temp file
- Claim: `propagate_openclaw_gateway_token(env_vars)` reads `~/.openclaw/openclaw.json` → `gateway.auth.token` and sets `OPENCLAW_GATEWAY_TOKEN` unless already set (ClawTeam-OpenClaw/clawteam/spawn/cli_env.py:190-212; called tmux_backend.py:169, subprocess_backend.py:98). On this host `openclaw.json` has key path `gateway.auth.{mode,token}` (names only inspected). In the tmux path env vars are written to a `NamedTemporaryFile` `.env.sh` sourced by the shell (tmux_backend.py:198-206), so the token transits disk. Upstream: 0 hits for `GATEWAY_TOKEN`.
- Level: observed
- Requirements: AR-04, HB-02
- Suggested fit cell: ClawTeam-OpenClaw → S~ (works) but AR-04 → M~ (secret materialization)

### F9. `--agent` capability probe — fork-only, currently a no-op on 2026.7.1-2
- Claim: see F5(b). Spawn option `--openclaw-agent` (commands.py:3280) → `openclaw_agent` kwarg added to `SpawnBackend.spawn` signature (spawn/base.py:23-24). Subprocess raises `NotImplementedError` (subprocess_backend.py:62).
- Level: verified (probe logic read + CLI help shows no `--agent` on tui)
- Requirements: HB-01
- Suggested fit cell: ClawTeam-OpenClaw → n/a (dead on current CLI)

### F10. Exec-approvals allowlist hint — fork-only; `openclaw approvals allowlist` exists today
- Claim: tmux backend prints `Hint: OpenClaw 4.2+ requires absolute paths in exec allowlist. Run: openclaw approvals allowlist add --agent "*" "<clawteam_bin>"` (tmux_backend.py:158-161); the worker prompt says "spawned OpenClaw workers run under exec allowlist mode. Use only the allowlisted executable path from $CLAWTEAM_BIN" (prompt.py:138); `scripts/install-openclaw.sh:178-205` rewrites `~/.openclaw/exec-approvals.json` `defaults.security` from `full` to `allowlist` and runs `openclaw approvals allowlist add`; CLAUDE.md:166 gotcha "exec-approval mode must be `allowlist`, not `full`, otherwise spawned workers hang". `openclaw approvals --help` (2026.7.1-2) lists `allowlist | get | set`. On this host `~/.openclaw/exec-approvals.json` is ABSENT.
- Level: verified (CLI) / observed (source)
- Requirements: HB-01, AR-05
- Suggested fit cell: ClawTeam-OpenClaw → C~

### F11. Auto-respawn: `trap EXIT` + `lifecycle on-exit` + `respawn.py` + `subprocess_wrapper` — fork-only mechanism; upstream has different recovery
- Claim: Fork: shell `trap "<clawteam> lifecycle on-exit …" EXIT` (tmux_backend.py:296-308) or `python -m clawteam.spawn.subprocess_wrapper --team T --agent A -- <cmd>` which runs the command then always invokes `lifecycle on-exit` (subprocess_wrapper.py:21-62; subprocess_backend.py:183-196). `lifecycle_on_exit` (commands.py:3005-3152) releases stale locks, resets in_progress tasks, unregisters dead agents, captures the last 80 pane lines, then calls `respawn_agent()` if pending tasks remain (:3129-3133). `respawn_agent` (respawn.py:12-86): `record_outcome(success=False)`, stops beyond `MAX_RESPAWN_ATTEMPTS = 2`, re-spawns the *recorded* argv via `spawn_with_retry(max_retries=1)`; fallback in `TaskWaiter._check_dead_agents` (waiter.py:186-191). Upstream: `build_keepalive_shell_command` `while true … lifecycle should-keepalive` loop (ClawTeam/clawteam/spawn/keepalive.py:53-95), tmux `set-hook pane-exited/pane-died` → `lifecycle on-exit/on-crash` (tmux_backend.py:217-226), plugin `ralph_loop_plugin.py:74 spawner.respawn(` → `harness/spawner.py:101`. The fork's `keepalive.py` is dead code (0 importers).
- Level: observed
- Requirements: LO-04, TE-06
- Suggested fit cell: ClawTeam-OpenClaw → S~ (crash respawn, max 2) · ClawTeam → S~ (keepalive resume + plugin respawn) — both "what resumes vs fresh" semantics differ (fork re-runs recorded argv; upstream builds a resume command)

### F12. Circuit-breaker health — model exists, only the failure path is wired; never consulted for admission
- Claim: `HealthState {healthy, degraded, open}`, `AgentHealth` (quality_score, consecutive_failures, cooldown 60 s), `record_outcome()` persisted in `teams/<T>/agent_health.json` (ClawTeam-OpenClaw/clawteam/spawn/registry.py:25-55, 99-152). Production callers: `record_outcome` only from respawn.py:38 with `success=False`; `get_agent_health`, `get_all_health`, `AgentHealth.is_accepting_tasks` have 0 callers outside tests. Upstream: 0 hits for `AgentHealth|circuit`.
- Level: verified (grep)
- Requirements: LO-04, TE-06
- Suggested fit cell: ClawTeam-OpenClaw → Xs~ (data model present, enforcement absent)

### F13. Retry/backoff and idempotency keys — fork-only, small and self-contained
- Claim: `spawn_with_retry(backend, max_retries=3, backoff_base=1.0, backoff_max=30.0, **kw)` (spawn/__init__.py:46-70) + `RetryConfig` on `AgentDef` (templates/__init__.py:37-41; used in `launch` commands.py:4419-4428). Idempotency: `TeamMessage.idempotency_key` / `TaskItem.idempotency_key` (team/models.py:126,148), `MailboxManager.send(idempotency_key=…)` scanning `events/evt-*.json` (mailbox.py:92-98, 256-266), `FileTaskStore.create(idempotency_key=…)` checked inside the write lock (store/file.py:86-106, 130-140). Upstream: 0 hits for `idempotency|spawn_with_retry`.
- Level: observed
- Requirements: TE-06, XC-04
- Suggested fit cell: ClawTeam-OpenClaw → S~ · ClawTeam → Xs~

### F14. Hermes as spawn target — fork-only; flags exist on installed Hermes 0.20.4
- Claim: `is_hermes_command` (command_validation.py:368; adapters.py:242); adapter inserts `chat` for bare `hermes`, adds `--source tool`, `-q <prompt>`, `--yolo` when skip_permissions (adapters.py:64-82); backends re-inline the same plus `-m <model>` (tmux_backend.py:265-282; subprocess_backend.py:177-185); `skills/hermes/SKILL.md` (262 lines, front matter `license: MIT`, documents the `--source tool` no-op on Hermes ≤ 0.8.0 with an upstream patch pointer at :141-163). `hermes chat --help` (0.20.4) lists `-q/--query, -m/--model, --yolo, --source SOURCE, --continue/-c, --resume, --worktree/-w, --skills, --toolsets`. Upstream: `grep -rn hermes ClawTeam/clawteam` → 0.
- Level: verified (CLI) / observed (source)
- Requirements: HB-08, HB-01
- Suggested fit cell: ClawTeam-OpenClaw → S! (Hermes Harness adapter) · ClawTeam → Xs~ (fallback `-p` path only)

### F15. Per-agent model resolution — 7-level chain, pure function, fork-only
- Claim: `resolve_model(cli_model, agent_model, agent_model_tier, template_model_strategy, template_model, config_default_model, agent_type, tier_overrides)` (model_resolution.py:29-70) with `DEFAULT_TIERS = {strong: "opus", balanced: "sonnet-4.6", cheap: "haiku-4.5"}` and `AUTO_ROLE_MAP` keywords leader/reviewer/architect/manager → strong. Plumbing: `AgentDef.model/model_tier`, `TemplateDef.model/model_strategy` (templates/__init__.py:54-61, 76-87), `ClawTeamConfig.default_model/model_tiers` + env `CLAWTEAM_DEFAULT_MODEL` (config.py:63-64,121), `spawn --model/-m` and `launch --model/--model-strategy` (commands.py:3282, 4235-4236, 4395-4404), env `CLAWTEAM_MODEL` to the worker + `AgentIdentity.model` (identity.py:61,88,107-108), `TeamMember.model_name` (team/models.py:75). The module has **zero** internal imports (stdlib only). Upstream: 0 hits for `default_model|model_tier`. Precedence is CLI > agent > tier > template strategy > template > config — there is no "user-level" layer distinct from CLI.
- Level: observed
- Requirements: HB-03, HB-01
- Suggested fit cell: ClawTeam-OpenClaw → Xs~ (per-Member model policy exists; user>role>default precedence not modeled) · ClawTeam → XL~

### F16. Cost dashboard — `cost show --by agent|model|task` + `cost_rate`; README's `clawteam board cost` does not exist
- Claim: `CostEvent.task_id`, `CostSummary.by_model/by_task`, `CostStore.cost_rate(window_minutes=5)`, `ingest_external_event(source="a2a-gateway")` (team/costs.py:34,47-48,307-367); CLI `cost report --task-id`, `cost show --by/-b` printing `cost_rate_per_min` (commands.py:2401, 2444-2460). README.md:430 and CHANGELOG.md:60 advertise `clawteam board cost`; `grep -n 'board.*cost' commands.py` → no such command (board sub-app has show/update/overview/live/serve/attach/gource). Cost events remain self-reported by the worker (`clawteam cost report …` in the prompt, prompt.py:149) — no automatic capture from the Harness.
- Level: verified (grep)
- Requirements: HB-07
- Suggested fit cell: ClawTeam-OpenClaw → Xs~ · ClawTeam → Xs~ (both: self-reported cost only)

### F17. "Gateway APIs" = an A2A-protocol gateway export, not the OpenClaw gateway; mostly uncalled
- Claim: `team/gateway.py` exports `peers[]` with `agentCardUrl …/.well-known/agent.json`, an `agentCard.skills` list and regex routing rules `(?i)@<name>\b → agentId` (gateway.py:21-100) and POSTs `{agentName, agentId, status, teamName}` to `<url>/a2a/webhooks/agent-status` (:103-140) when `CLAWTEAM_GATEWAY_URL` is set (lifecycle.py:137-156). Commit f885fea (2026-04-04): "No CLI commands added — all APIs are designed for programmatic invocation by Gateway… Gateway-side integration … deferred". README.md:672 roadmap "v0.4 … A2A Gateway integration — In Progress". Callers outside tests: `export_gateway_config` 0, `ingest_external_event` 0, `handle_agent_exit` 0, `approve_shutdown_and_notify` 0. Recon's label "gateway APIs" is imprecise — **correction**: this is not OpenClaw-gateway integration.
- Level: verified (grep + commit message)
- Requirements: MS-02, HB-06
- Suggested fit cell: ClawTeam-OpenClaw → n/a (ATM-style A2A router direction is demoted)

### F18. Prompt-layer research blocks — fork-only prose in `build_agent_prompt`
- Claim: `BOIDS_RULES` (Separation/Alignment/Cohesion/Boundary, injected when `team_size > 1`), `METACOGNITION_BLOCK` (`[confidence: 0.X]` tagging, escalate < 0.6), `## Mission` (Auftragstaktik `intent/end_state/constraints` from `AgentDef`), `## Shared Memory` telling the worker to use OpenClaw `memory_store`/`memory_recall` with scope `custom:team-<T>` (prompt.py:14-33, 54-118; env `CLAWTEAM_MEMORY_SCOPE` tmux_backend.py:136 / subprocess_backend.py:78; `TeamMessage.confidence` team/models.py:124). `DEFAULT_MAX_AGENTS = 4` warning citing arXiv:2512.08296 (templates/__init__.py:26, 96-105; commands.py:3343-3348). Upstream: 0 hits for `Boids|etacognition|Auftragstaktik|memory_scope|MAX_AGENTS`.
- Level: observed
- Requirements: AD-01, AD-03, TC-02 (as *examples* of role prose; not a definition format)
- Suggested fit cell: ClawTeam-OpenClaw → P~ (prompt composition only; no Assistant definition object)

### F19. `platform_compat.py` — centralized Windows/macOS shims, stdlib-only, fork-only
- Claim: `is_windows()`, `default_spawn_backend()` ("subprocess" on Windows else "tmux"), `exclusive_file_lock()` (msvcrt/fcntl), `install_signal_handlers()/restore_signal_handlers()`, `shell_join()`, `shell_quote()`, `pid_alive()` (ctypes on Windows) — platform_compat.py:15-130; imports only os/shlex/signal/subprocess/time/contextlib/pathlib/typing. Consumers: config.py:12,59, spawn/__init__.py:22-28 (`normalize_backend_name` forces tmux→subprocess on Windows), registry.py:18, waiter.py/watcher.py/board/renderer.py, `_tmux_unavailable_message` (tmux_backend.py:551-563). pyproject adds `Operating System :: Microsoft :: Windows / MacOS / POSIX :: Linux` classifiers (fork pyproject.toml:16-18; absent upstream). Upstream keeps `msvcrt` inline in 4 files (fileutil.py, store/file.py, team/snapshot.py, transport/file.py) and hard-codes `backend or "tmux"` (ClawTeam/clawteam/cli/commands.py:3125, 4633). Both trees ship `adapters.py:53 os.getuid()` (raises on Windows); the fork's backends bypass the adapter, so its spawn path avoids it — and also loses upstream's root guard (fork appends `--dangerously-skip-permissions` unconditionally, tmux_backend.py:214-216; `grep getuid` in fork backends → 0). CI is ubuntu+macos only in both (F25).
- Level: verified
- Requirements: TE-08, XC-02
- Suggested fit cell: ClawTeam-OpenClaw → C~ (Windows via subprocess, documented) · ClawTeam → Xs~

### F20. Extra CLIs: kimi/qwen/opencode/pi already upstream; only Hermes is fork-only
- Claim: Upstream `adapters.py` defines `is_kimi_command:200, is_qwen_command:205, is_opencode_command:210, is_openclaw_command:215, is_pi_command:220`; grep counts upstream clawteam/: kimi 30, qwen 12, opencode 18. Fork adds only `is_hermes_command` to `is_interactive_cli` (adapters.py diff; command_validation.py:368-385). Fork also changed qwen to `--yolo` and Gemini tmux to `-i` (CHANGELOG.md:26-27) — but upstream adapters already use `-i` for Gemini interactive; the fork's backends hard-code the same.
- Level: verified
- Requirements: HB-08
- Suggested fit cell: ClawTeam → S~ · ClawTeam-OpenClaw → S~

### F21. Skill injection (`--skill` → `--append-system-prompt`) — already upstream
- Claim: Upstream `spawn --skill` (ClawTeam/clawteam/cli/commands.py:3108, "repeatable, claude only") and `launch --skill/-s` (:4557); `append-system-prompt` 7 hits in upstream clawteam/. Fork keeps the same option and injects in backends (tmux_backend.py:303-306).
- Level: verified
- Requirements: HB-02
- Suggested fit cell: both → S~ (Claude Code/pi only; other Harnesses get prompt-prefix only)

### F22. Runtime injection (`runtime inject/watch/state`) — already upstream; fork retargets to tmux window id
- Claim: Upstream defines `runtime_inject:1968, runtime_watch:2012, runtime_state:2068`. Fork: inject uses the `tmux_target` window id recorded at spawn (tmux_backend.py:466-475; CHANGELOG.md:33). Recon correct.
- Level: verified
- Requirements: TE-06
- Suggested fit cell: both → S~ (tmux only)

### F23. Session capture/resume — already upstream (PR #154); fork keeps calls but its own known issue says OpenClaw sessions are not captured
- Claim: Upstream `clawteam/spawn/session_capture.py` + `session_locators/{claude,codex,gemini,nanobot,openclaw,opencode}.py`; fork calls `prepare_session_capture`/`persist_spawned_session` in both backends (tmux_backend.py:170-176; subprocess_backend.py:100-106, 214-218). CHANGELOG.md:52 "`clawteam session show` stays empty for openclaw agents — the session locator inspects the command before flag expansion, so the exact `--session` key is never captured … cosmetic only."
- Level: observed
- Requirements: TE-02, HB-01 (resume capability)
- Suggested fit cell: ClawTeam → S~ (claude/codex/gemini) · ClawTeam-OpenClaw → Xs~ (openclaw)

### F24. Subprocess mode — already upstream; fork rewrote it (wrapper module, no `shell=True`, no keepalive loop)
- Claim: Upstream `subprocess_backend.py` uses `prepare_command` (:80,101), a POSIX keepalive shell string or a Windows `cmd & exit_hook` string, `Popen(shell_cmd, shell=True, stdout=DEVNULL, stderr=DEVNULL)` (:122-146). Fork runs `[sys.executable, "-m", "clawteam.spawn.subprocess_wrapper", …, "--", *final_command]` without a shell (subprocess_backend.py:183-199), still `DEVNULL` for stdout/stderr (logging still absent on both sides).
- Level: observed
- Requirements: TE-08, HB-07
- Suggested fit cell: both → C~ (no-tmux path exists; output discarded)

### F25. Docs/CI hygiene — CHANGELOG/CONTRIBUTING/CLAUDE.md/issue+PR templates/10 READMEs are fork-only; `ci.yml` is identical
- Claim: Added: `CHANGELOG.md`, `CONTRIBUTING.md`, `CLAUDE.md`, `.github/ISSUE_TEMPLATE/{bug_report,feature_request}.yml`, `.github/PULL_REQUEST_TEMPLATE.md`, `README_{DE,ES,FR,IT,JA,KO,PT-BR,RU,TW}.md`, `docs/superpowers/{plans,specs}/2026-03-21-per-agent-model-assignment*.md`. `diff ci.yml` → empty (both: ruff on 3.12; pytest matrix os [ubuntu-latest, macos-latest] × py [3.10, 3.11, 3.12]); fork history "097bce8 chore: remove CI workflow" then "4b55e2d ci: add GitHub Actions workflow from upstream". Recon listed CI as fork-only — **correction**.
- Level: verified
- Requirements: XC-02, XC-03
- Suggested fit cell: n/a

### F26. Dropped wsh (TideTerm/WaveTerm) backend — files absent, residual references remain
- Claim: `wsh_backend.py`/`wsh_rpc.py` (upstream added 7dec341, 2026-03-30) are absent from the fork tree; `--full-history` shows the drop at merge `cc2b09a`. `get_backend` error reads "Available: subprocess, tmux" (spawn/__init__.py:43). Residue: `grep -c wsh registry.py` → 13 (`is_agent_alive` still has an `elif backend == "wsh"` branch at :215-216, 290). Upstream README does not mention wsh either (`grep -iE 'wsh|tideterm|wave' ClawTeam/README.md` → 0).
- Level: verified
- Requirements: TE-08, HB-06
- Suggested fit cell: n/a (wsh is irrelevant to the product; noted for merge cost)

### F27. Merge cost: backends bypass `adapter.prepare_command`; 5 `xfail(strict=False)`; dead `keepalive.py`
- Claim: `prepare_command(` callers — upstream 7 (subprocess_backend.py:80,101; tmux_backend.py:97,116; wsh_backend.py:269,294; cli/commands.py:747) vs fork 1 (cli/commands.py:748 inside `profile_test`, :730). Per-CLI flag logic is therefore duplicated three times in the fork (adapters.py, tmux_backend.py:209-306, subprocess_backend.py:118-181). `tests/test_spawn_backends.py` marks 5 tests `@pytest.mark.xfail(reason="fork PR #60 (subprocess_wrapper / trap EXIT / manual flag) vs upstream PR #154 (adapter.prepare_command / tmux set-hook / build_keepalive_shell_command) — backlog §10.3 chose fork path; …", strict=False)` at lines **79, 139, 436, 773, 1212**; upstream has 0 xfail. `spawn/keepalive.py` exists in the fork but has 0 importers. CHANGELOG.md:45-47 "Known follow-ups (xfail)".
- Level: verified
- Requirements: XC-03
- Suggested fit cell: ClawTeam-OpenClaw → M~ for "upstream-friendly extension" (rung 3); Xs~ for "selective module reuse" (rung 4)

### F28. Isolation of candidate reuse modules (can it be vendored standalone?)
| Module | Lines | Internal imports | Standalone? |
|---|---|---|---|
| `model_resolution.py` | 70 | none | yes (pure function) |
| `platform_compat.py` | 130 | none (stdlib) | yes |
| `spawn/subprocess_wrapper.py` | 66 | `cli_env.resolve_clawteam_executable` | yes with 1 helper; but it shells out to `clawteam lifecycle on-exit` |
| `spawn/respawn.py` | 86 | `spawn.get_backend/spawn_with_retry`, `spawn.registry`, `team.manager` | no (coupled to registry + TeamManager) |
| `spawn/registry.py` health block (:25-152) | ~130 | `fileutil`, `paths`, `team.models.get_data_dir` | partially (needs atomic_write/lock helpers) |
| `team/gateway.py` | 140 | `team.manager`, `team.models` | no; and irrelevant (F17) |
| `spawn/__init__.py::spawn_with_retry` | 25 | `SpawnBackend` protocol | yes (protocol only) |
- Level: verified (import lines read)
- Requirements: XC-03, XC-01
- Suggested fit cell: n/a

### F29. Fork known issues and gotchas (verbatim)
- CHANGELOG.md:49-53 "Known issues (from 2026-07-04 bot smoke test)": (1) "**Hard-killed agents lose conversation context on resume** — OpenClaw may not have flushed the session transcript when the process dies, so reconnecting with the same session key rotates to a fresh sessionId. Task-store recovery + identity re-injection still restore the working state. Mitigation direction: graceful termination before respawn." (2) "**`clawteam session show` stays empty for openclaw agents** — … cosmetic only." (3) "**Idle `openclaw tui` workers may time out and exit** — long-lived teams should tune `agents.defaults.timeoutSeconds` (or accept worker churn + auto-respawn as the recovery path)." (`openclaw tui --timeout-ms` "defaults to agents.defaults.timeoutSeconds" confirms the knob exists.)
- CLAUDE.md:163-170 "Fork-specific gotchas": OpenClaw is the default (do not change to claude); exec-approval must be `allowlist` not `full`; Hermes workers use `hermes chat --yolo --source tool -q "<task>"`, never add `--continue`; Hermes `--source tool` is a no-op on Hermes ≤ 0.8.0 (`run_agent.py:1057`/`:6600`); built-in templates default to openclaw (`clawteam launch <template> --command hermes --force`); CHANGELOG conventions.
- Level: observed
- Requirements: LO-04, TE-02, HB-01
- Suggested fit cell: ClawTeam-OpenClaw → Xs~ (long-lived OpenClaw workers)

### F30. Licenses: both MIT, identical file, copyright HKUDS; no SPDX headers in fork-only files
- Claim: `diff ClawTeam/LICENSE ClawTeam-OpenClaw/LICENSE` → identical (21 lines, "MIT License / Copyright (c) 2025 HKUDS"); both `pyproject.toml:7 license = {text = "MIT"}` and classifier "OSI Approved :: MIT License". Fork-only modules carry no license/copyright/SPDX notice (0 hits); `skills/hermes/SKILL.md:6` front matter `license: MIT`. Fork versions are PEP 440 local identifiers (`0.3.0+openclaw2`). Many fork commits carry `Co-Authored-By: Claude Opus 4.6` trailers (e.g. f885fea, c595f0e, 037d0e8) — provenance note only.
- Level: verified
- Requirements: XC-01
- Suggested fit cell: n/a

### F31. Subproject workspace overlay — fork-only
- Claim: `WorkspaceManager` records `repo_subpath` when invoked from a sub-directory and copies untracked files of that subpath into the worktree, skipping `_IGNORED_DIR_NAMES`, `_SENSITIVE_FILE_NAMES` (.env, .npmrc, credentials.json) and key suffixes (.pem/.key/.p12/.pfx) (workspace/manager.py:18-41, 85-94, 128-129, 358-389; `WorkspaceInfo.repo_subpath` workspace/models.py:17; `_workspace_cwd_from_info` commands.py:1561-1578). Upstream: 0 hits.
- Level: observed
- Requirements: TE-01, AR-04
- Suggested fit cell: ClawTeam-OpenClaw → S~ · ClawTeam → Xs~

### F32. Liveness surfaced in `team status` and board — fork-only, small
- Claim: `team status` adds `"alive": is_agent_alive(team, m.name)` and an "Alive" column (commands.py:1598-1629); `BoardCollector` adds `alive` (board/collector.py:7, 82-91). Upstream status lists members only.
- Level: observed
- Requirements: TE-06, TE-07
- Suggested fit cell: ClawTeam-OpenClaw → S~ · ClawTeam → Xs~

### F33. Defaults flipped to OpenClaw throughout
- Claim: `spawn` default `command = ["openclaw"]` (commands.py:3404; upstream :3217 `["claude"]`), `TemplateDef.command = ["openclaw"]` (templates/__init__.py:74), all four built-in TOML templates `command = ["openclaw"]`, `skills/clawteam/SKILL.md` text updated, `skills/openclaw/SKILL.md` (273 lines) installed to `~/.openclaw/workspace/skills/clawteam/SKILL.md` by `scripts/install-openclaw.sh:167-168` (script hard-requires tmux at :50-54).
- Level: verified
- Requirements: HB-03, HB-08
- Suggested fit cell: ClawTeam-OpenClaw → C~

### F34. Definitive classification table
| Feature | Fork anchor | Upstream equivalent | Class | Reason (req IDs) |
|---|---|---|---|---|
| Bare-`openclaw` → `tui` default + `clawteam-T-A` session key + flag appends | command_validation.py:302-307; tmux_backend.py:228-249 | adapters.py:104-116 (`tui --session` branch); bare default `agent --local` (:302-303) | partly already-upstream; default + key scheme fork-only | HB-01/HB-02 resident-session form |
| Worker-workspace isolation | tmux_backend.py:44-48, 67-79, 165-169 | absent | worth-selective-reuse (idea) | TE-02/AD-05; tmux-only |
| Gateway token propagation | cli_env.py:190-212 | absent | irrelevant-to-revised-product | AR-04 conflict; MS-01 |
| `--agent` capability probe | tmux_backend.py:52-64, 113-118 | absent | irrelevant (no-op on 2026.7.1-2) | HB-01 wants declared HarnessProfile |
| Approvals allowlist hint | tmux_backend.py:158-161; prompt.py:138; install-openclaw.sh:178-205 | absent | fork-only (HarnessProfile evidence) | HB-01/AR-05 |
| Auto-respawn + `subprocess_wrapper` | respawn.py; subprocess_wrapper.py; commands.py:3129-3152; waiter.py:186-191 | keepalive.py:53-95; tmux set-hook :217-226; ralph_loop_plugin.py:74 | fork-only (divergent) | LO-04/TE-06; re-runs argv, no resume |
| Circuit-breaker health | registry.py:25-152 | absent | worth-selective-reuse (model only) | LO-04; unenforced (F12) |
| Retry/backoff + idempotency keys | spawn/__init__.py:46-70; models.py:126,148; mailbox.py:92-98; store/file.py:86-106 | absent | worth-upstreaming | TE-06/XC-04 |
| Hermes spawn target | adapters.py:64-82, 242; skills/hermes/SKILL.md | absent | worth-upstreaming / selective-reuse | HB-08; flags exist on Hermes 0.20.4 |
| Per-agent model resolution | model_resolution.py:29-70 + plumbing | absent | worth-selective-reuse (pure function) | HB-03; `--model` not a `tui` flag (F5) |
| Cost dashboard | costs.py:307-367; commands.py:2441-2460 | by-agent only | fork-only, partial | HB-07 self-reported; `board cost` missing |
| Gateway (A2A) APIs | gateway.py; lifecycle.py:137-156 | absent | irrelevant-to-revised-product | A2A demoted; uncalled |
| Prompt research blocks | prompt.py:14-33, 84-118; templates/__init__.py:50-52 | absent | fork-only, reference prose | AD-01/AD-03 |
| `platform_compat.py` + Windows defaults | platform_compat.py; spawn/__init__.py:22-28; config.py:59 | inline msvcrt ×4; `backend or "tmux"` | worth-upstreaming / selective-reuse | TE-08/XC-02 |
| Extra CLIs kimi/qwen/opencode/pi | — | adapters.py:200-220 | already-upstream | HB-08 |
| Skill injection `--skill` | same | commands.py:3108, 4557 | already-upstream | HB-02 |
| Runtime injection | commands.py:2020+ | commands.py:1968-2068 | already-upstream (window-id retarget) | TE-06 |
| Session capture/resume | backend call sites | session_capture.py + locators | already-upstream | TE-02 |
| Subprocess mode | subprocess_backend.py (rewritten) | subprocess_backend.py | already-upstream (divergent impl) | TE-08 |
| Docs/CI hygiene | CHANGELOG/CONTRIBUTING/CLAUDE.md/templates/READMEs | ci.yml identical | docs fork-only; CI already-upstream | XC-02 |
| Dropped wsh backend | absent | wsh_backend.py/wsh_rpc.py | fork-only deletion; irrelevant | — |
| Subproject overlay; `alive` column; max-4 warning; `approve-join` cleanup | F31/F32/F18; commands.py:1436-1449 | absent | fork-only, small | TE-01/TE-06 |

## 3. Negative findings
- No Windows CI on either side: `grep -n 'os:' .github/workflows/ci.yml` → `[ubuntu-latest, macos-latest]` in both.
- No production consumer of circuit-breaker admission: `grep -rn is_accepting_tasks clawteam/` → only the definition; `grep -rn 'record_outcome(' clawteam/` → respawn.py:38 only (failure path).
- No `clawteam board cost` command despite README.md:430/CHANGELOG.md:60: `grep -n -E 'board.*cost|def board_' clawteam/cli/commands.py` → board_show/update/overview/live/serve/attach/gource only.
- No test for subprocess+openclaw argv: `grep -n openclaw tests/test_spawn_backends.py` → 0; `grep -rn 'session-id' tests/` → only test_session_capture.py (claude).
- No callers of `handle_agent_exit`, `approve_shutdown_and_notify`, `export_gateway_config`, `ingest_external_event` in fork clawteam/ (0); no importer of fork `spawn/keepalive.py` (0); no `OPENCLAW_WORKSPACE` on the subprocess path (`grep -c` → 0).
- No license/SPDX header in any fork-only module: `grep -ciE 'copyright|licen[cs]e|SPDX'` → 0 for model_resolution.py, platform_compat.py, respawn.py, subprocess_wrapper.py, gateway.py, skills/openclaw/SKILL.md, scripts/install-openclaw.sh.
- Upstream has none of: `hermes`, `memory_scope`, `model_name`, `MAX_AGENTS`, `idempotency`, `circuit`, `AgentHealth`, `platform_compat`, `gateway`, `cost_rate`, `by_model`, `Boids`, `repo_subpath`, `OPENCLAW_WORKSPACE`, `GATEWAY_TOKEN`, `is_windows`, `default_model`, `model_tier`, `spawn_with_retry`, `unregister_agent`, `get_agent_info`, `OPENCLAW_NESTED`, `window_id` (all `grep -rn … ClawTeam/clawteam/` → 0).
- `~/.openclaw/exec-approvals.json` is ABSENT on this host (names-only `ls ~/.openclaw`), so the fork's allowlist workflow has not been run here.
- Upstream commits newer than 0119833: none on GitHub (API, 2026-08-21). Fork commits newer than 8dac3fc: none.

## 4. Platform & license notes
- **OS support.** Upstream: tmux default on all OSes; `commands.py:3125 backend or "tmux"`; Windows shims inline (msvcrt in fileutil/store/transport/snapshot); `adapters.py:53 os.getuid()` reachable on Windows when `skip_permissions` → crash (recon correct). Fork: `default_spawn_backend()` = subprocess on Windows, tmux elsewhere; `normalize_backend_name` coerces tmux→subprocess on Windows; README.md:43-46 documents Windows 10/11 via subprocess, `board attach` needs tmux, `board serve` as alternative, WSL for tmux; pyproject OS classifiers added. Neither CI runs Windows. On this Ubuntu host without tmux, both trees fall to the subprocess backend, whose OpenClaw argv in the fork appears flag-mismatched (F6) and whose output is discarded (DEVNULL) in both.
- **Harness CLI reality** (read-only `--help`, 2026-08-21): see F5, F14 and §6.
- **Licenses.** Both MIT, identical `LICENSE` (Copyright (c) 2025 HKUDS); `pyproject.toml:7 license = {text = "MIT"}` both. Fork-only modules have no separate notice; `skills/hermes/SKILL.md` declares `license: MIT`. No terms-of-use constraints on automation flags found in either repo; the `--dangerously-skip-permissions` / `--dangerously-bypass-approvals-and-sandbox` / `--yolo` flags are vendor CLI flags (their vendors' terms are out of scope here).

## 5. Open questions
- Does `openclaw tui` reject unknown `--model`/`--session-id` (commander strict mode) or ignore them? Not executed (would start a TUI). If rejected, the fork's `--model` path for OpenClaw and its subprocess+openclaw path are broken on 2026.7.1-2.
- Is the Hermes `--source tool` no-op (≤ 0.8.0 per CLAUDE.md:168) fixed in the installed 0.20.4? `hermes chat --help` shows `--source SOURCE` but storage behaviour was not probed.
- Which external "A2A Gateway" project `team/gateway.py` targets (win4r side project?) — not identified locally; irrelevant unless MS-02 revisits A2A.
- Does upstream intend to adopt the `tui` default (OpenClaw ≥ 2026.6 single-turn `agent`)? No upstream commit after 2026-05-09 addresses it.
- Whether the fork's `clawteam-<team>-<agent>` session keys survive OpenClaw's "rotates to a fresh sessionId" behaviour after hard kill (CHANGELOG.md:51) — needs a live probe (probe agent's scope).

## 6. Probe / CLI log
All commands read-only; outputs saved under `/tmp/claude-1000/-home-wsh-Documents-assistant-team-system-dev/17fd77ac-75ce-402b-a1a9-5d1eebba9843/scratchpad/ev-fork-delta/` (`name-status.txt`, `diffstat.txt`, `diff-*.patch`, `openclaw-help.txt`, `openclaw-tui-help.txt`, `openclaw-agent-help.txt`).
```
git -C ClawTeam-OpenClaw log --oneline | wc -l                 → 329
git -C ClawTeam log --oneline | wc -l                          → 217
git -C ClawTeam-OpenClaw log --oneline HEAD ^0119833 | wc -l   → 112
git -C ClawTeam-OpenClaw merge-base HEAD 0119833               → 01198332ef92…
git -C ClawTeam-OpenClaw log -1 --date=iso  → 8dac3fc 2026-07-04 02:15:35 +0800 chore(release): v0.3.0+openclaw2
git -C ClawTeam log -1 --date=iso           → 0119833 2026-05-09 15:25:55 +0800 Merge pull request #156 …
git -C ClawTeam-OpenClaw diff --shortstat 0119833 HEAD         → 88 files changed, 13158 insertions(+), 2006 deletions(-)
diff LICENSE (both) / diff .github/workflows/ci.yml (both)     → identical / identical
grep -n xfail ClawTeam-OpenClaw/tests/test_spawn_backends.py   → 79,139,436,773,1212 (strict=False); upstream: 0
grep -rn 'prepare_command(' */clawteam | grep -v 'def '        → upstream 7 call sites; fork 1 (cli/commands.py:748)
openclaw --version                                             → OpenClaw 2026.7.1-2 (0790d9f)
openclaw tui --help                                            → --deliver --history-limit --local --message --password --session --thinking --timeout-ms --token --url
openclaw agent --help                                          → --agent --channel --deliver --json --local --message --message-file --model --reply-* --session-id --session-key --to --thinking --timeout --verbose
openclaw approvals --help                                      → allowlist | get | set
hermes --version; hermes chat --help                           → v0.20.4; -q/--query -m/--model --yolo --source --continue/-c --resume --worktree …
WebFetch api.github.com/repos/{win4r/ClawTeam-OpenClaw,HKUDS/ClawTeam}/commits → HEADs 8dac3fc / 0119833 (match local)
~/.openclaw/openclaw.json key names → top: agents auth gateway hooks meta plugins session skills tools wizard; gateway.auth: mode token; exec-approvals.json: ABSENT
```
