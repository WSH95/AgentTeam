---
id: ev:harness-caps-A
topic: HarnessCapability checklist and definition-injection matrix for Claude Code, Codex CLI and Grok CLI (installed versions)
systems: [Claude Code, Codex CLI, Grok CLI, ClawTeam]
sources:
  - {kind: cli, ref: "claude --help; claude {mcp,agents,plugin,project,auth,import} --help; claude mcp add --help", accessed: 2026-08-21, version: 2.1.239}
  - {kind: cli, ref: "claude --version; claude --help; claude auth status --json (sanitized fields only)", accessed: 2026-08-22, version: 2.1.241}
  - {kind: cli, ref: "codex --help; codex {exec,resume,review,mcp,plugin,fork,sandbox,features,login,debug,doctor} --help; codex exec resume --help; codex features list", accessed: 2026-08-21, version: 0.148.0}
  - {kind: cli, ref: "codex --version; codex exec --help; codex login status", accessed: 2026-08-22, version: 0.149.0}
  - {kind: cli, ref: "grok --help; grok {agent,mcp,plugin,sessions,inspect,memory,setup,login} --help; grok agent {stdio,headless,serve} --help; grok inspect", accessed: 2026-08-21, version: "1.0.5 (5115b46bc9)"}
  - {kind: repo, ref: "~/.grok/docs/user-guide/*.md and ~/.grok/README.md (docs bundled with the installed 1.0.5 binary)", accessed: 2026-08-21, version: 1.0.5}
  - {kind: probe, ref: "grep -a -c <string> on installed binaries (claude 2.1.239, codex 0.148.0, grok 1.0.5) for flags/keys absent from --help", accessed: 2026-08-21}
  - {kind: web, ref: https://code.claude.com/docs/en/cli-reference, accessed: 2026-08-21}
  - {kind: web, ref: https://code.claude.com/docs/en/headless, accessed: 2026-08-21}
  - {kind: web, ref: https://code.claude.com/docs/en/memory, accessed: 2026-08-21}
  - {kind: web, ref: https://code.claude.com/docs/en/sub-agents, accessed: 2026-08-21}
  - {kind: web, ref: https://code.claude.com/docs/en/skills, accessed: 2026-08-21}
  - {kind: web, ref: https://code.claude.com/docs/en/hooks, accessed: 2026-08-21}
  - {kind: web, ref: https://code.claude.com/docs/en/mcp, accessed: 2026-08-21}
  - {kind: web, ref: https://code.claude.com/docs/en/plugins, accessed: 2026-08-21}
  - {kind: web, ref: https://code.claude.com/docs/en/setup, accessed: 2026-08-21}
  - {kind: web, ref: https://code.claude.com/docs/en/legal-and-compliance, accessed: 2026-08-21}
  - {kind: web, ref: https://learn.chatgpt.com/docs/config-file/config-reference (redirect target of developers.openai.com/codex/config-reference), accessed: 2026-08-21}
  - {kind: web, ref: https://learn.chatgpt.com/docs/non-interactive-mode, accessed: 2026-08-21}
  - {kind: web, ref: https://learn.chatgpt.com/docs/agent-configuration/agents-md, accessed: 2026-08-21}
  - {kind: web, ref: https://learn.chatgpt.com/docs/build-skills, accessed: 2026-08-21}
  - {kind: web, ref: https://learn.chatgpt.com/docs/agent-configuration/subagents, accessed: 2026-08-21}
  - {kind: web, ref: https://learn.chatgpt.com/docs/hooks, accessed: 2026-08-21}
  - {kind: web, ref: https://learn.chatgpt.com/docs/agent-approvals-security, accessed: 2026-08-21}
  - {kind: web, ref: https://learn.chatgpt.com/docs/windows/windows-sandbox, accessed: 2026-08-21}
  - {kind: web, ref: https://learn.chatgpt.com/docs/extend/mcp?surface=cli, accessed: 2026-08-21}
  - {kind: web, ref: https://learn.chatgpt.com/docs/cli/reference, accessed: 2026-08-21}
  - {kind: web, ref: https://learn.chatgpt.com/docs/auth, accessed: 2026-08-21}
  - {kind: web, ref: https://github.com/openai/codex (README), accessed: 2026-08-21}
  - {kind: web, ref: https://github.com/xai-org/grok-build (README), accessed: 2026-08-21}
  - {kind: repo, ref: "ClawTeam/clawteam/spawn/{adapters,keepalive,subprocess_backend}.py, spawn/session_locators/{claude,codex}.py, cli/commands.py @ 0.3.0 working tree", accessed: 2026-08-21, version: 0.3.0}
method: Local `--help` trees of the three installed CLIs (no prompts sent); bundled Grok docs read from disk; official Claude Code and Codex docs fetched on 2026-08-21; binary string counts used only to confirm presence of flags/config keys that the `--help` text omits; local config inspected for key names only; ClawTeam adapter code cross-checked against installed flag names.
platform: {os: Ubuntu (Linux 5.15), tmux: absent, cli_versions_current: {claude: 2.1.241, codex: 0.149.0, grok: 1.0.5}, original_probe_versions: {claude: 2.1.239, codex: 0.148.0, grok: 1.0.5}}
author_agent: ev:harness-caps-A
date: 2026-08-21
confidence: high
status: current with dated original probe log and 2026-08-22 recheck
---
# Harness CLI capabilities A: Claude Code, Codex CLI, Grok CLI

## 1. Scope & questions

- Which HarnessCapabilities does each installed harness expose, under which exact flag/file/config name? (HB-01, HB-08)
- How can an Assistant definition (persona + principles + Skill dirs + MCP requirements + permissions) reach each harness **without editing the definition**, and what cannot be injected? (HB-02, AD-04, TE-03, AD-02)
- Which per-invocation data (session id, model, usage, cost) does each harness emit for HarnessInvocation records? (HB-07)
- Which flags does ClawTeam's adapter emit per harness, and do they still exist? (HB-08, XC-03)
- Platform support and automation/terms constraints. (TE-08, XC-01, XC-02)

## 2. Findings

### F1. Headless run exists in all three harnesses under different spellings
- Claim: `claude -p/--print "<prompt>"`, `codex exec "<prompt>"` (alias `codex e`; `-` reads stdin), `grok -p/--single "<prompt>"` (also `--prompt-file <PATH>`, `--prompt-json <JSON>`). All three read stdin as additional context. Grok additionally offers `grok agent stdio` (ACP over stdio), `grok agent serve` (WebSocket, `--bind`, `--secret`), `grok agent headless` (relay).
- Evidence: `claude --help` ("-p, --print  Print response and exit"); `codex exec --help` ("If not provided as an argument (or if `-` is used), instructions are read from stdin"); `grok --help` ("-p, --single <PROMPT>  Single-turn prompt. Prints the response to stdout and exits"); `grok agent --help`.
- Level: verified (CLI help)
- Requirements: HB-01, HB-02
- Suggested fit cell: Claude Code → S!, Codex → S!, Grok → S!

### F2. System-prompt injection: Claude and Grok have flags; Codex uses a CLI-overridable config key (recon correction)
- Claim: Claude Code: `--system-prompt <prompt>` (replace), `--append-system-prompt <prompt>` (append); docs also list `--system-prompt-file` and `--append-system-prompt-file` (present in the binary, 14 string hits each, but **not listed in `claude --help`**), and `--append-subagent-system-prompt` (print mode). Grok: `--system-prompt-override <PROMPT>` (alias `--system-prompt`, replaces everything incl. `--rules`) and `--rules <RULES>` (alias `--append-system-prompt`; appended inside a `<human_rules>` block). Codex: **no flag**, but config keys `developer_instructions` ("Additional developer instructions injected into the session") and `model_instructions_file` ("Replacement for built-in instructions instead of AGENTS.md") exist and every Codex subcommand accepts `-c key=value` overrides, so `codex exec -c developer_instructions="..."` is a per-invocation injection path without touching files. The recon appendix statement "codex … no system prompt" is therefore **incomplete**: no dedicated flag, but an equivalent config-override path.
- Evidence: `claude --help`; https://code.claude.com/docs/en/cli-reference (accessed 2026-08-21) "`--append-system-prompt-file` Load additional system prompt text from a file and append"; binary `grep -a -c append-system-prompt-file` = 14; `grok --help`; ~/.grok/docs/user-guide/12-project-rules.md "Session Rules Flags" ("`--rules` (alias `--append-system-prompt`) … `--system-prompt-override` (alias `--system-prompt`) … uses the text verbatim and skips both the default system prompt and `--rules`"); https://learn.chatgpt.com/docs/config-file/config-reference (accessed 2026-08-21) quotes above; `codex exec --help` "-c, --config <key=value> Override a configuration value"; codex binary `developer_instructions` 42 hits, `model_instructions_file` 17 hits.
- Level: verified for Claude/Grok flags; observed (docs + binary strings, not executed) for Codex `developer_instructions`
- Requirements: HB-02, HB-01, AD-01
- Suggested fit cell: Claude Code → S!, Grok → S!, Codex → C~

### F3. Prompt prefix / initial message is a positional argument everywhere
- Claim: All three accept the task text positionally (`claude -p "<text>"`, `codex exec "<text>"`, `grok -p "<text>"`); Grok adds `--verbatim` ("Send the prompt exactly as given") and `--prompt-json` content blocks; Claude supports `--input-format stream-json` for multi-turn piping; Codex appends piped stdin as a `<stdin>` block.
- Evidence: respective `--help` outputs (scratchpad `claude-help.txt`, `codex-sub-help.txt`, `grok-help.txt`).
- Level: verified
- Requirements: HB-02
- Suggested fit cell: all three → S!

### F4. Workspace instruction files: CLAUDE.md / AGENTS.md / Grok reads both; none accepts an arbitrary custom path by flag
- Claim: Claude Code walks cwd upward for `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`, plus `~/.claude/CLAUDE.md`, `.claude/rules/*.md`, `@imports`; it "reads CLAUDE.md, not AGENTS.md" (import via `@AGENTS.md`); `--add-dir` does **not** load CLAUDE.md unless `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`; no custom-path flag. Codex walks git root → cwd for `AGENTS.override.md`, `AGENTS.md`, then `project_doc_fallback_filenames`, plus `~/.codex/AGENTS.md`, capped by `project_doc_max_bytes` (32 KiB); custom filenames only via config (`-c project_doc_fallback_filenames=[...]`), cwd via `-C/--cd`. Grok loads, per directory from repo root to cwd, `Agents.md`, `Claude.md`, `CLAUDE.md`, `CLAUDE.local.md`, `AGENT.md`, `AGENTS.md`, plus `.grok/rules/*.md`, `.claude/rules/*.md`, `~/.grok/rules/`, `~/.grok/AGENTS.md`; `grok inspect` lists what loaded (here: project `CLAUDE.md` ~51 tokens, `AGENTS.md` ~835 tokens); cwd via `--cwd`. Grok binary has **no** `GROK.md` string (0 hits) — the web claim that Grok reads `GROK.md` is unsupported in 1.0.5.
- Evidence: https://code.claude.com/docs/en/memory (accessed 2026-08-21) §"Choose where to put CLAUDE.md files", §"AGENTS.md", §"Load from additional directories"; https://learn.chatgpt.com/docs/agent-configuration/agents-md (accessed 2026-08-21); `codex --help` (`-C, --cd <DIR>`); ~/.grok/docs/user-guide/12-project-rules.md §"Supported File Names"; `grok inspect` output (probe §6); grok binary `GROK.md` = 0, `AGENTS.md` = 49.
- Level: verified (grok inspect, flags) / observed (docs)
- Requirements: HB-02, AD-05
- Suggested fit cell: Claude Code → C~ (temp dir + CLAUDE.md), Codex → C~ (temp dir + AGENTS.md or `-c`), Grok → C~ (reads both names)

### F5. Skill discovery locations and per-invocation injection differ sharply
- Claim: Claude Code: `~/.claude/skills/<name>/SKILL.md`, `.claude/skills/` (cwd up to repo root), plugin `skills/`; **`--add-dir <dir>` loads that dir's `.claude/skills/` and `.claude/agents/`** (documented exception to "file access, not configuration"), also under `--bare`; `--plugin-dir <path|.zip>` loads a plugin bundle (skills+agents+hooks+`.mcp.json`) per session. Codex: `.agents/skills` (cwd, parents, repo root), `$HOME/.agents/skills`, `/etc/codex/skills`, plus `[[skills.config]] path = "…/SKILL.md"`; no skills flag; invoked as `$skill-name`; optional `agents/openai.yaml`. Grok: `./.grok/skills`, `<repo>/.grok/skills`, `~/.grok/skills`, `.agents/skills` at each tier, **plus Claude-compat `~/.claude/skills`, `./.claude/skills`** and Cursor dirs; extra dirs only via `[skills] paths = [...]` in `~/.grok/config.toml`; no skills flag.
- Evidence: https://code.claude.com/docs/en/skills (accessed 2026-08-21) §"Skills from additional directories", §"Where skills live"; `claude --help` (`--plugin-dir`, `--bare` text "Skills still resolve"); https://learn.chatgpt.com/docs/build-skills (accessed 2026-08-21); ~/.grok/docs/user-guide/08-skills.md §"Skill Locations", §"Configuration"; `grok inspect` listed 79 skills incl. `~/.claude/skills` and Claude plugins tagged `[claude]`.
- Level: observed (docs) + verified for Grok discovery (`grok inspect`)
- Requirements: HB-02, AD-02, AR-02
- Suggested fit cell: Claude Code → S! (`--add-dir`/`--plugin-dir`), Codex → C~ (cwd `.agents/skills` or config), Grok → C~ (cwd `.grok/skills` or config)

### F6. MCP configuration: all three support stdio/http/sse; only Claude Code has a per-invocation MCP flag
- Claim: Claude Code: `claude mcp add|add-json|list|get|remove` with `-s/--scope local|user|project` (local/user in `~/.claude.json`, project in `.mcp.json`), **`--mcp-config <files-or-json…>`** and `--strict-mcp-config` per session; `${VAR}` expansion in `.mcp.json`; `-p` sessions load project `.mcp.json` without the approval prompt. Codex: `[mcp_servers.<name>]` in `~/.codex/config.toml` (`command/args/env/cwd`, `url/bearer_token_env_var/http_headers`, `enabled`, `startup_timeout_sec`, `tool_timeout_sec`, `enabled_tools/disabled_tools`), `codex mcp add <name> (--url <URL> | -- <COMMAND>…)` with `--env`, `--bearer-token-env-var`; project `.codex/config.toml` "(trusted projects only)"; `-c mcp_servers.x.command=…` overrides undocumented. Grok: `[mcp_servers.<name>]` in `~/.grok/config.toml` or project `.grok/config.toml` (`command/args/env`, `url/headers`, `enabled`), `grok mcp add <NAME> [COMMAND_OR_URL] -- ARGS` with `-t stdio|http|sse`, `-s user|project`, `-e`, `-H`; plus Claude-compat `~/.claude.json` and `.mcp.json`; **no `--mcp-config` flag** (binary 0 hits); the `GROK_CONFIG` overlay is allowlisted to `models`, `features`, `toolset`, `shell_environment_policy` and "cannot … add a discovery source".
- Evidence: `claude mcp add --help`; https://code.claude.com/docs/en/mcp (accessed 2026-08-21) §"MCP installation scopes", §"Project scope"; https://code.claude.com/docs/en/cli-reference `--mcp-config`; `codex mcp add --help`; https://learn.chatgpt.com/docs/extend/mcp?surface=cli (accessed 2026-08-21); `grok mcp add --help`; ~/.grok/docs/user-guide/07-mcp-servers.md §"Project-Scoped MCP Servers", §"Compatibility"; ~/.grok/docs/user-guide/05-configuration.md §"Injecting config with GROK_CONFIG".
- Level: verified (CLI help) / observed (docs)
- Requirements: HB-02, AR-02, AR-04
- Suggested fit cell: Claude Code → S!, Codex → C~, Grok → C~

### F7. Subagent / agent definitions: Claude and Grok accept JSON on the CLI; Codex uses TOML files only
- Claim: Claude Code: `.claude/agents/*.md`, `~/.claude/agents/*.md`, plugin `agents/`, **`--agents '<json>'`** (fields `description`, `prompt`, `tools`, `disallowedTools`, `model`, `permissionMode`, `mcpServers`, `hooks`, `maxTurns`, `skills`, `initialPrompt`, `memory`, `effort`, `background`, `isolation`) and **`--agent <name>`** runs the whole session as that agent ("The subagent's system prompt replaces the default Claude Code prompt"). Grok: `.grok/agents/*.md`, `~/.grok/agents/*.md`, bundled `~/.grok/bundled/agents/{explore,general-purpose,plan}.md` (frontmatter `name`, `description`, `prompt_mode`, `model`, `permission_mode`, `agents_md`; docs add `tools`, `mcpInheritance`); `--agent <NAME|path>`, `--agent-profile <PATH>` (under `grok agent`), `GROK_AGENT`, `[agent] name|definition`; `--agents <JSON>` (headless-only); Claude-compat `.claude/agents/`; personas (`.grok/personas/*.toml`: `instructions`, `instructions_file`, `model`, `reasoning_effort`, `inputs`/`outputs`) and roles (`.grok/roles/*.toml`). Codex: `~/.codex/agents/*.toml` or `.codex/agents/*.toml` with required `name`, `description`, `developer_instructions`, optional `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, `skills.config`; built-ins `default`, `worker`, `explorer`; `[agents] enabled|max_concurrent_threads_per_session|default_subagent_model`; feature `multi_agent` `stable true` here; **no CLI flag** for inline agent JSON.
- Evidence: `claude --help` (`--agent`, `--agents`); https://code.claude.com/docs/en/sub-agents (accessed 2026-08-21); `grok --help`; `grok agent --help`; ~/.grok/bundled/agents/general-purpose.md lines 1-11; ~/.grok/docs/user-guide/16-subagents.md; ~/.grok/README.md §"Agent Profiles"; https://learn.chatgpt.com/docs/agent-configuration/subagents (accessed 2026-08-21); `codex features list` (`multi_agent  stable  true`).
- Level: verified (flags, bundled files, feature list) / observed (docs)
- Requirements: HB-02, AD-07, TE-04
- Suggested fit cell: Claude Code → S!, Grok → S!, Codex → C~

### F8. Session resume flags exist in all three; ClawTeam's adapter uses them correctly
- Claim: Claude: `-c/--continue`, `-r/--resume [id|name]`, `--session-id <uuid>`, `--fork-session`, `--no-session-persistence` (print only); docs: `--resume` finds the ID in any project since v2.1.223. Codex: `codex resume [SESSION_ID] [PROMPT] --last --all`, `codex exec resume [SESSION_ID] [PROMPT] --last`, `codex fork`, `codex exec fork <id>`, `--ephemeral` (no rollout file); rollouts live in `~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<uuid>.jsonl` whose first line is `{"type":"session_meta","payload":{id, session_id, cwd, cli_version, model_provider, base_instructions, …}}`. Grok: `-c/--continue`, `-r/--resume [id|title]`, `-s/--session-id <uuid>` (new session only), `--fork-session`, `--restore-code`; sessions under `~/.grok/sessions/<url-encoded-cwd>/<session-id>/{summary.json,updates.jsonl,chat_history.jsonl,…}`. ClawTeam builds `claude --continue` / `codex resume --last` (keepalive.py:21-24) and `--resume <id>` / `resume <id>` (session_locators/claude.py:107, codex.py:84); all four spellings exist in the installed versions.
- Evidence: `claude --help`; `codex --help`; `codex exec resume --help`; `grok --help`; ~/.grok/docs/user-guide/17-sessions.md §"Storage Layout"; probe §6 (rollout first-line keys); ClawTeam/clawteam/spawn/keepalive.py:21-24; ClawTeam/clawteam/spawn/session_locators/claude.py:97-107; ClawTeam/clawteam/spawn/session_locators/codex.py:80-84,120-122.
- Level: verified
- Requirements: HB-01, TE-02, HB-07
- Suggested fit cell: all three → S!; ClawTeam → S!

### F9. cwd control: Codex and Grok have a flag; Claude relies on process cwd plus `--add-dir`
- Claim: Codex `-C/--cd <DIR>` and `--add-dir <DIR>` ("Additional directories that should be writable alongside the primary workspace"); Grok `--cwd <CWD>` (no `--add-dir`, binary 0 hits); Claude has no cwd flag (cwd = process cwd) but `--add-dir <directories…>` grants access and loads skills/agents from those dirs; `-w/--worktree` in Claude and Grok creates a fresh git worktree.
- Evidence: the three `--help` outputs; grok binary `add-dir` = 0.
- Level: verified
- Requirements: HB-01, TE-01
- Suggested fit cell: all three → S!

### F10. Structured output and usage/cost: Claude and Grok report USD cost; Codex reports tokens only
- Claim: Claude `-p --output-format text|json|stream-json`, `--json-schema` → `structured_output`; json result carries `result`, `session_id`, `total_cost_usd`, `modelUsage`, `num_turns`; `--max-budget-usd` caps spend; stream `system/init` lists `model`, `tools`, `mcp_servers`, `plugins`, `plugin_errors`, `mcp_server_errors`. Grok `--output-format plain|json|streaming-json|streaming-messages-json`, `--json-schema`; json object has `text`, `stopReason`, `sessionId`, `usage`, `num_turns`, `modelUsage{…costUSD}`, `total_cost_usd`, `total_cost_usd_ticks`, `cost_is_partial`, `usage_is_incomplete`; `streaming-messages-json` mimics Claude's `system/init` … `result` wire format. Codex `exec --json` emits JSONL `thread.started`, `turn.started`, `turn.completed`, `item.*`, `error`; `-o/--output-last-message <FILE>`; `--output-schema <FILE>`; token fields `input_tokens`, `cached_input_tokens`, `output_tokens`, `reasoning_output_tokens` (binary 20 hits each) but **no cost field** (`total_cost_usd` 0 hits).
- Evidence: `claude --help`; https://code.claude.com/docs/en/headless (accessed 2026-08-21) §"Get structured output", §"Read session metadata"; claude binary `total_cost_usd` 13, `modelUsage` 18, `structured_output` 50; `grok --help`; ~/.grok/docs/user-guide/14-headless-mode.md §"Output Formats" (lines 130-330); `codex exec --help`; https://learn.chatgpt.com/docs/non-interactive-mode (accessed 2026-08-21); codex binary string counts above.
- Level: verified (flags, binary strings) / observed (field lists from docs)
- Requirements: HB-07, HB-01
- Suggested fit cell: Claude Code → S!, Grok → S!, Codex → C~ (cost must be computed from tokens externally)

### F11. Permission / sandbox flags: three different models; ClawTeam's bypass flags still valid
- Claim: Claude: `--permission-mode acceptEdits|auto|bypassPermissions|manual|dontAsk|plan`, `--dangerously-skip-permissions` (rejected when root — ClawTeam adapters.py:50-55 omits it under `os.getuid()==0`), `--allowedTools`, `--disallowedTools`, `--tools`, `--permission-prompt-tool` (docs/binary only), `--bare`, `--setting-sources user,project,local`. Codex: `-s/--sandbox read-only|workspace-write|danger-full-access`, `-a/--ask-for-approval untrusted|on-request|never`, `--approve-for-me`, `--dangerously-bypass-approvals-and-sandbox` (ClawTeam adapters.py:57), `--dangerously-bypass-hook-trust`, `--ignore-user-config`, `--ignore-rules`; sandbox = Seatbelt (macOS), `bwrap`+`seccomp` (Linux), Windows sandbox. Grok: `--permission-mode default|acceptEdits|auto|dontAsk|bypassPermissions|plan`, `--always-approve` (docs alias `--yolo`; both in binary), `--allow <RULE>` (alias `--allowedTools`), `--deny <RULE>` (alias `--disallowedTools`), `--tools`, `--disallowed-tools` (incl. `Agent(...)`), `--sandbox off|workspace|devbox|read-only|strict` (Landlock/Seatbelt), `--max-turns`; rules merge `deny > ask > allow` across `~/.grok/config.toml`, project `.grok/config.toml`, `.claude/settings.json` (compat) and flags; project MCP/hooks/LSP gated by folder trust (`trusted_folders.toml`; `GROK_FOLDER_TRUST=0` disables).
- Evidence: `claude --help`; `codex --help`; `grok --help`; https://learn.chatgpt.com/docs/agent-approvals-security (accessed 2026-08-21); ~/.grok/docs/user-guide/22-permissions-and-safety.md §"Permission modes", §"Configuring permissions"; ~/.grok/docs/user-guide/18-sandbox.md; ClawTeam/clawteam/spawn/adapters.py:48-57; grok binary `--yolo` 17, `--always-approve` 30.
- Level: verified
- Requirements: HB-01, AD-03, TE-08
- Suggested fit cell: all three → S!

### F12. Model selection and fallback
- Claim: Claude `--model <alias|full>` (aliases `fable|opus|sonnet|haiku`), `--fallback-model a,b` (print only), `--effort low|medium|high|xhigh|max`; Codex `-m/--model`, `-p/--profile <name>` (layers `$CODEX_HOME/<name>.config.toml`), `--oss --local-provider lmstudio|ollama`, `-c model_provider=…` with `[model_providers.<id>] base_url/env_key`; Grok `-m/--model`, `--reasoning-effort`/`--effort`, `[models] default`, custom providers in `[model.<id>]` (`api_key`/`env_key`), `grok models`.
- Evidence: the three `--help` outputs; https://learn.chatgpt.com/docs/config-file/config-reference; ~/.grok/docs/user-guide/05-configuration.md §"Custom models".
- Level: verified
- Requirements: HB-01, HB-03, HB-04
- Suggested fit cell: all three → S!

### F13. Hooks: all three have lifecycle hooks; Grok also consumes Claude's hook files
- Claim: Claude: 30+ events (`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, `PreCompact`, `SessionEnd`, …) in `~/.claude/settings.json`, `.claude/settings(.local).json`, plugin `hooks/hooks.json`, skill/subagent frontmatter; types `command|http|mcp_tool|prompt|agent`; docs: hooks cannot be passed through `--settings`. Codex: `~/.codex/hooks.json`, `.codex/hooks.json`, inline `[[hooks.<Event>]]`; events `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `Stop`, `PreToolUse`, `PostToolUse`, `PermissionRequest`, `PreCompact`, `PostCompact`, `SubagentStart`, `SubagentStop`; only `type:"command"` runs; each hook needs a trust hash (`[hooks.state]` observed in this host's config.toml) or `--dangerously-bypass-hook-trust`; feature `hooks` `stable true`. Grok: `~/.grok/hooks/*.json`, project `.grok/hooks/*.json` (folder trust), `[[hooks.<Event>]]`, **plus Claude `settings.json` files (compat)**; events as Claude plus `PostToolUseFailure`, `StopFailure`, `StopCancelled`, `Notification`; types `command|http`; fail-open.
- Evidence: https://code.claude.com/docs/en/hooks (accessed 2026-08-21); https://learn.chatgpt.com/docs/hooks (accessed 2026-08-21); `~/.codex/hooks.json` keys (`PostToolUse`, `SessionStart`, `Stop`, `UserPromptSubmit`) and `~/.codex/config.toml` `[hooks.state."…:trusted_hash"]`; `codex features list`; ~/.grok/docs/user-guide/10-hooks.md §"Hook Events", §"Where hooks live".
- Level: observed (docs) + verified (local config structure, feature flag)
- Requirements: HB-01, XC-04, LO-02
- Suggested fit cell: Claude Code → S!, Codex → S!, Grok → S!

### F14. Version and platform support
- Claim: Current installed versions are Claude Code 2.1.241, Codex 0.149.0, and Grok 1.0.5. The original platform findings remain: Claude supports macOS, native Windows/WSL, and Linux; Codex supports macOS, Linux, and native Windows sandboxing; Grok documents macOS/Linux/Windows but calls Windows builds best-effort. No Windows or macOS execution was performed in either evidence pass.
- Evidence: https://code.claude.com/docs/en/setup (accessed 2026-08-21) §"System requirements", §"Set up on Windows"; https://learn.chatgpt.com/docs/windows/windows-sandbox and …/agent-approvals-security (accessed 2026-08-21); https://github.com/openai/codex README; ~/.grok/docs/user-guide/01-getting-started.md lines 11-35; ~/.grok/docs/user-guide/18-sandbox.md §"Platform support"; https://github.com/xai-org/grok-build README (accessed 2026-08-21).
- Level: observed
- Requirements: TE-08, XC-02
- Suggested fit cell: Claude Code → S~, Codex → S~, Grok → S~ (Windows sandbox n/a)

### F15. Provider/authentication configuration and operational boundary
- Claim: Claude supports first-party subscription OAuth plus API-key/gateway modes; Codex supports ChatGPT sign-in plus API-key/custom-provider modes; Grok supports OAuth/device authentication plus API-key/custom-provider modes. The current product boundary is owner-operated native/unattended live runs through each CLI's subscription OAuth. A separate, replaceable API-test profile may use an environment-injected key. Neither mode silently falls back to the other, ATS does not broker third-party login, and hosted CI receives neither subscription nor live API credentials. `--bare` explicitly disables Claude OAuth/keychain access and is therefore only suitable for API-key mode.
- Evidence: original sources above; sanitized `claude auth status --json`; `codex login status`; current help recheck; [ev:m0-product-architecture-review-2026-08-22#F2][ev:m0-product-architecture-review-2026-08-22#F4].
- Level: verified locally for Claude/Codex auth state and help; Grok active auth unverified
- Requirements: XC-01, AR-04, HB-07
- Suggested fit cell: all three → S~ with the owner-operated/no-hosted-CI boundary above

### F16. HarnessCapability checklist (one row per capability)

| # | Capability | Claude Code 2.1.241 | Codex CLI 0.149.0 | Grok CLI 1.0.5 |
|---|---|---|---|---|
| 1 | Headless | `-p/--print` (F1) | `codex exec` (F1) | `-p/--single`, `--prompt-file`, `grok agent stdio` (F1) |
| 2 | System prompt | `--system-prompt`, `--append-system-prompt`, `--*-file` variants, `--append-subagent-system-prompt` (F2) | none as flag; `-c developer_instructions="…"`, `-c model_instructions_file=…` (F2) | `--system-prompt-override` (=`--system-prompt`), `--rules` (=`--append-system-prompt`) (F2) |
| 3 | Prompt prefix | positional / stdin / `--input-format stream-json` | positional / stdin `-` / `<stdin>` block | positional / `--prompt-json` / `--verbatim` |
| 4 | Workspace instruction file | CLAUDE.md hierarchy; no custom path flag; `--add-dir` + `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` (F4) | AGENTS.md chain; `-C`; `-c project_doc_fallback_filenames` (F4) | AGENTS.md + CLAUDE.md + rules dirs; `--cwd` (F4) |
| 5 | Skills | `~/.claude/skills`, `.claude/skills`, `--add-dir` (loads skills), `--plugin-dir`, `--plugin-url` (F5) | `.agents/skills` chain, `$HOME/.agents/skills`, `[[skills.config]]` (F5) | `.grok/skills`, `.agents/skills`, `.claude/skills`, `[skills] paths` (F5) |
| 6 | MCP | `claude mcp add -s …`, `.mcp.json`, `--mcp-config`, `--strict-mcp-config` (F6) | `[mcp_servers.*]`, `codex mcp add`, project `.codex/config.toml` (F6) | `[mcp_servers.*]`, `grok mcp add -s user|project`, `.mcp.json`/`~/.claude.json` compat (F6) |
| 7 | Agent definitions | `.claude/agents/*.md`, `--agents <json>`, `--agent <name>` (F7) | `.codex/agents/*.toml`, `[agents]` (F7) | `.grok/agents/*.md`, `--agent <name|path>`, `--agents <json>`, personas/roles TOML (F7) |
| 8 | Resume | `--continue`, `--resume`, `--session-id`, `--fork-session` (F8) | `resume [id] --last`, `exec resume`, `fork`, `--ephemeral` (F8) | `--continue`, `--resume`, `--session-id`, `--fork-session` (F8) |
| 9 | cwd | process cwd; `--add-dir`; `-w` (F9) | `-C/--cd`, `--add-dir` (F9) | `--cwd`, `-w` (F9) |
| 10 | Structured output / usage | `--output-format json|stream-json`, `--json-schema`, `total_cost_usd`, `modelUsage`, `--max-budget-usd` (F10) | `--json` JSONL, `-o`, `--output-schema`; tokens only (F10) | `--output-format json|streaming-json|streaming-messages-json`, `--json-schema`, `total_cost_usd(_ticks)` (F10) |
| 11 | Permissions/sandbox | `--permission-mode`, `--dangerously-skip-permissions`, `--allowedTools`, `--tools`, `--safe-mode` (F11/F19) | `--sandbox`, `--ask-for-approval`, `--dangerously-bypass-approvals-and-sandbox`, `--ignore-user-config` (F11) | `--permission-mode`, `--always-approve`, `--allow/--deny`, `--tools`, `--sandbox`, `--max-turns` (F11) |
| 12 | Model | `--model`, `--fallback-model`, `--effort` (F12) | `-m`, `-p profile`, `--oss`, `-c model_provider` (F12) | `-m`, `--effort`, `[model.<id>]` (F12) |
| 13 | Hooks | settings.json / plugin / frontmatter; 5 hook types (F13) | hooks.json / config.toml; command only; trust hash (F13) | `.grok/hooks/*.json` + Claude settings compat; command|http (F13) |
| 14 | Platform | macOS/Linux/Windows native (F14) | macOS/Linux/Windows native sandbox (F14) | macOS/Linux/Windows best-effort; sandbox Linux+macOS (F14) |
| 15 | Auth / execution mode | Native subscription OAuth on owner host; API key only in separate test mode (F15) | Native ChatGPT login on owner host; API key only in separate test mode (F15) | OAuth/device native mode; active login unverified; API key only in separate test mode (F15) |

- Level: as per referenced findings
- Requirements: HB-01, HB-08

### F17. Definition-injection matrix (decisive for HB-02 / PoC A)
Parts of an Assistant definition and where each part can land **without editing the definition** (the adapter renders per invocation):

| Definition part | Claude Code | Codex CLI | Grok CLI |
|---|---|---|---|
| Persona + principles (role text) | `--append-system-prompt "<rendered>"` or `--append-system-prompt-file`; alternative `--agents '{"x":{"prompt":…}}' --agent x` — verified flags (docs+help); `--agent` with `--agents`-defined agent **unverified** | `-c developer_instructions="<rendered>"` — observed (docs+binary); fallback: AGENTS.md in a temp workspace or prompt prefix — observed | `--rules "<rendered>"` (appended) or `--system-prompt-override` (replaces) — verified flags; alt. `--agent <tmp.md>` profile — verified flag, format observed |
| Stable working preferences | same channel as above, or `CLAUDE.md` in a temp dir via `--add-dir` + `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` (observed) or `CLAUDE_CONFIG_DIR=<tmp>` user CLAUDE.md (observed) | `$CODEX_HOME/AGENTS.md` with `CODEX_HOME=<tmp>` (observed) or project `AGENTS.md`/`AGENTS.override.md` at repo root (observed) | `~/.grok/AGENTS.md` via `GROK_HOME=<tmp>` or `.grok/rules/*.md`/`AGENTS.md` in cwd chain (observed) |
| Skill dirs (list of SKILL.md dirs) | `--add-dir <dir-containing-.claude/skills>` (observed, docs) or `--plugin-dir <dir|zip>` bundle (verified flag) | symlink/copy into `<cwd>/.agents/skills/` or `$HOME/.agents/skills` or `-c 'skills.config=[{path="…/SKILL.md"}]'` (observed; `-c` array form **unverified**) | `.grok/skills/` or `.agents/skills/` or `.claude/skills/` in cwd/repo chain (verified via `grok inspect`), or `[skills] paths` in `$GROK_HOME/config.toml` (observed) |
| MCP requirements | `--mcp-config <json-or-file> --strict-mcp-config` (verified flags) | `codex mcp add` into `$CODEX_HOME/config.toml` (verified cmd) or `-c mcp_servers.<n>.command=…` (**unverified**) or project `.codex/config.toml` (trust needed, observed) | `grok mcp add -s project` → `.grok/config.toml` (verified cmd; folder trust applies) or `.mcp.json` compat or `GROK_HOME` config (observed); **not** via `GROK_CONFIG` overlay (observed: allowlist excludes `mcp_servers`) |
| Permissions | `--permission-mode`, `--allowedTools`, `--disallowedTools`, `--tools`, `--settings '<json>'` (verified flags) | `--sandbox`, `--ask-for-approval`, `--add-dir`, `--dangerously-bypass-approvals-and-sandbox` (verified flags) | `--permission-mode`, `--allow`, `--deny`, `--tools`, `--disallowed-tools`, `--sandbox` (verified flags) |
| Subagent roster (ephemeral members) | `--agents '<json>'` (verified flag) | `.codex/agents/*.toml` files only (observed) | `--agents '<json>'` (verified flag, JSON shape unverified) or `.grok/agents/*.md` |
| Harness-selection policy | n/a (lives in the Assistant, consumed by the HarnessBroker) | n/a | n/a |
| **Cannot be injected per invocation** | hooks via `--settings` (docs: not honored); CLAUDE.md custom path | system prompt as a flag; agent roster as a flag; MCP as a flag (file/config only); USD cost in output | MCP/skills/agents via env overlay; `--add-dir` (absent); `--mcp-config` (absent) |

- Evidence: F2, F4–F7, F10, F11 above; ~/.grok/docs/user-guide/05-configuration.md §"Injecting config with GROK_CONFIG"; https://code.claude.com/docs/en/hooks §"Command-Line Configuration".
- Level: mixed, marked per cell
- Requirements: HB-02, AD-04, AD-08, TE-03, HB-08
- Suggested fit cell: Claude Code → S! (all parts injectable by flag), Grok → C! (flags for prompt/permissions; files for skills/MCP), Codex → C~ (config override + files)

### F18. ClawTeam's adapter flags cross-checked against installed versions
- Claim: `NativeCliAdapter.prepare_command` behavior is unchanged from the original finding. All emitted flags still exist in Claude Code 2.1.241 and Codex 0.149.0. Grok still has no dedicated adapter branch in the inspected ClawTeam snapshot; the generic `-p <prompt>` branch is syntactically valid but does not render Grok-specific permissions or definition channels.
- Evidence: ClawTeam/clawteam/spawn/adapters.py:32-147; ClawTeam/clawteam/spawn/subprocess_backend.py:80-116; ClawTeam/clawteam/cli/commands.py:98-117,3108,3284-3308; ClawTeam/clawteam/spawn/keepalive.py:11-34; `claude --help`; `codex --help`; `grok --help`.
- Level: verified (code read + installed help)
- Requirements: HB-08, XC-03
- Suggested fit cell: ClawTeam → S! (claude/codex), ClawTeam → Xs! (grok: needs `--always-approve`/`--rules` branch)

### F19. Isolation knobs useful for "fresh by default"
- Claim: For native Claude subscription runs, use `--safe-mode --no-session-persistence` plus an isolated `CLAUDE_CONFIG_DIR` as needed; do not use `--bare`, because 2.1.241 says it disables OAuth/keychain access. Codex exposes `--ignore-user-config`, `--ephemeral`, `--ignore-rules`, and `CODEX_HOME`. Grok exposes `GROK_HOME`, `GROK_MEMORY=0`, `--no-subagents`, and `[compat.claude]` toggles.
- Evidence: current `claude --help`; `codex exec --help`; bundled Grok docs; [ev:m0-product-architecture-review-2026-08-22#F3].
- Level: verified (flags) / observed (docs)
- Requirements: TE-02, AD-05, EV-04
- Suggested fit cell: all three → S!

### F20. Grok reads Claude Code configuration natively (cross-harness reuse fact)
- Claim: Grok discovers `~/.claude/skills`, `.claude/skills`, `.claude/agents`, `~/.claude/plugins/installed_plugins.json`, `~/.claude.json`, `.mcp.json`, `CLAUDE.md`, `.claude/rules`, `.claude/settings.json` permissions and hooks; on this host `grok inspect` listed 5 user skills incl. `statusline-designer … [claude]`, 8 Claude plugins (e.g. `superpowers`, `project-steward`), and `context7 … 1 MCPs`.
- Evidence: ~/.grok/README.md §"Claude Code Compatibility"; `grok inspect` output (probe §6).
- Level: verified
- Requirements: HB-02, AR-05, HB-08
- Suggested fit cell: Grok → S!

### F21. Current recheck fixes the first-pass harness and CI boundaries
- Claim: Claude Code 2.1.241, Codex 0.149.0, and Grok Build 1.0.5 all retain credential-free headless/help surfaces sufficient to include them in the first-pass harness scope. This verifies interface availability, not model behavior. Windows/macOS verification will use GitHub-hosted CI only for deterministic process/path/record plumbing, with no live credentials; live authentication/model claims remain limited to an authenticated persistent host.
- Evidence: 2026-08-22 local version/help recheck; [ev:m0-product-architecture-review-2026-08-22#F1][ev:m0-product-architecture-review-2026-08-22#F3][ev:m0-product-architecture-review-2026-08-22#F5].
- Level: verified locally + owner constraint
- Requirements: HB-01, HB-02, HB-08, TE-08, XC-02
- Suggested fit cell: n/a — current planning constraint, not a matrix reclassification

## 3. Negative findings

- Claude Code: no `--claude-md <path>`/custom instruction-file flag (`claude --help`; memory doc only offers `--add-dir` + env var, `CLAUDE_CONFIG_DIR`). `--append-system-prompt-file`, `--system-prompt-file`, `--max-turns`, `--permission-prompt-tool`, `--append-subagent-system-prompt` are absent from `claude --help` (present in docs and binary strings 9–19 hits each). Hooks not injectable via `--settings` (docs).
- Codex: no `--system-prompt`/`--append-system-prompt`/`--instructions` flag in `codex --help` or `codex exec --help`; no `--agents`/`--mcp-config`/`--plugin-dir`/`--skills` flags; `--full-auto` absent from `codex --help` and binary (0 hits; docs call it deprecated); no USD cost field (`total_cost_usd` 0, `cost_usd` 0 hits); `--strict-config` exists only on session-starting subcommands (`codex features list --strict-config` → "unexpected argument"), so config-key recognition could not be validated without sending a prompt; `experimental_instructions_file` 0 hits (superseded by `model_instructions_file`); `.agents/skills` literal 0 hits in binary (path built dynamically; docs authoritative).
- Grok: no `--add-dir` (0 hits), no `--mcp-config` (0 hits), no `--plugin-dir` on the top-level command (only under `grok agent`; 8 hits), no `GROK.md` support (0 hits), `GROK_CONFIG` overlay cannot carry `mcp_servers`/`skills`/`agent` (docs allowlist); `--yolo` not shown in `grok --help` (binary 17 hits; docs list it as alias of `--always-approve`); `--trust` not in `grok --help` (binary 20 hits; docs mention "launching with `--trust`") — unverified as a real flag.
- ClawTeam: `grep -rn -i grok ClawTeam/clawteam ClawTeam-OpenClaw/clawteam` → 0 hits (no Grok adapter, locator, or resume builder); `grep -rn "append-system-prompt" ClawTeam/clawteam/spawn/*.py` shows insertion only for claude/pi commands.
- Terms: xAI consumer ToS (https://x.ai/legal/terms-of-service) and OpenAI help-center article on ChatGPT-plan Codex use both returned HTTP 403 to WebFetch; automation terms for Grok/Codex subscription logins remain unverified beyond the vendor docs quoted in F15.

## 4. Platform & license notes

| Harness | License | Platforms (source) | Caveats |
|---|---|---|---|
| Claude Code 2.1.241 | Proprietary; Commercial Terms (Team/Enterprise/API) or Consumer Terms (Free/Pro/Max); binary must not be modified when embedded (legal page) | macOS 13+, Windows 10 1809+ native (PowerShell/CMD; Git for Windows optional), WSL, Ubuntu 20.04+/Debian 10+/Alpine 3.19+ (setup page) | Native owner-operated subscription mode; `--bare` disables OAuth, so use `--safe-mode --no-session-persistence`; no live credential in hosted CI |
| Codex CLI 0.149.0 | Apache-2.0 (github.com/openai/codex README) | macOS, Linux, Windows native with Windows sandbox; WSL2; WSL1 dropped in 0.115 (docs) | Native owner-operated ChatGPT login; no live credential in hosted CI |
| Grok CLI 1.0.5 | Apache-2.0 for first-party code of github.com/xai-org/grok-build; "External contributions are not accepted" | macOS, Linux, Windows (PowerShell installer / Git Bash / WSL); upstream README: Windows builds "best-effort and not currently tested" | Sandbox only Linux (Landlock ≥5.13, bubblewrap for deny) and macOS; child-network block Linux-only; xAI ToS unverified (403) |

## 5. Open questions

1. Does `claude --agent <name>` accept an agent defined only via `--agents '<json>'` in the same invocation (docs list built-in/project/user/plugin agents)? Needs a probe.
2. Is `codex exec -c developer_instructions="…"` honored in 0.149.0 (docs + binary say yes; never executed here)? Does it reach subagents spawned by `multi_agent`?
3. Exact JSON shape of Grok `--agents <JSON>` (assumed Claude-compatible; undocumented in bundled docs).
4. Can Codex `[[skills.config]]` be supplied as a `-c` inline-table array, and do skills load in `codex exec`?
5. Whether Grok's `--trust` is a real CLI flag (binary string present, not in `--help`), which matters for auto-trusting a temp workspace's `.grok/config.toml` MCP servers in headless runs.
6. Before any multi-user or hosted product is proposed, re-check vendor policy boundaries. The current design is narrower: owner-operated subscription OAuth on a persistent host, never hosted CI or third-party credential brokerage.

## 6. Probe / CLI log

The excerpts below are the **2026-08-21 historical probe snapshot** (Claude 2.1.239 / Codex 0.148.0). F14–F21 and the frontmatter record the current 2026-08-22 recheck. Original full outputs were written to a temporary path and are not durable project artifacts.

Trimmed excerpts:

```
$ claude --version → 2.1.239 (Claude Code) | codex --version → codex-cli 0.148.0 | grok --version → grok 1.0.5 (5115b46bc9)
$ grok inspect → Project Instructions (2): CLAUDE.md (~51 tokens), AGENTS.md (~835 tokens); Skills (79) incl. [claude]; Plugins (8) incl. context7 1 MCPs
$ codex features list | grep -E "multi_agent|hooks|plugins" → hooks stable true | multi_agent stable true | plugins stable true
$ codex features list --strict-config -c 'x="y"' → error: unexpected argument '--strict-config'
$ grep -a -c -- append-system-prompt-file <claude bin> → 14 ; developer_instructions <codex bin> → 42 ; total_cost_usd <codex bin> → 0
$ grep -a -c -- GROK.md <grok bin> → 0 ; add-dir <grok bin> → 0 ; --yolo <grok bin> → 17
$ head -n1 ~/.codex/sessions/…/rollout-<ts>-<uuid>.jsonl → type=session_meta; payload keys: base_instructions, cli_version, cwd, git, id, model_provider, session_id, …
$ ~/.codex/hooks.json events (keys only): PostToolUse, SessionStart, Stop, UserPromptSubmit
```
