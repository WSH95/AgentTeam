---
title: Proposal A — ClawTeam maximalist ("build almost nothing")
label: arch:clawteam-maximalist
date: 2026-08-22
status: panel proposal (analysis only; no code, no PoC code)
inputs: product-intent.md (register v3.1), existing-systems-fit-gap.md, reuse-vs-build-analysis.md, assistant-domain-model.md, team-execution-model.md, harness-broker-model.md, legacy-atm-disposition.md, evidence/*.md, recon-appendix.md
---

# Proposal A — ClawTeam maximalist

## 1 Bias statement & what would change my mind

**Bias.** ClawTeam already does the expensive part of team execution on this host: dynamic spawn of any executable through the subprocess backend with no tmux [ev:clawteam-probe-log#F12], per-member harness command purely by TOML configuration [ev:clawteam-probe-log#F16], profiles with credential-by-env-name [ev:clawteam-probe-log#F5], a task DAG with auto-unblock and advisory locks [ev:clawteam-probe-log#F7][ev:clawteam-probe-log#F8], file inboxes plus a non-consumed events log [ev:clawteam-probe-log#F9], per-Member git worktrees supplied at run time [ev:clawteam-probe-log#F22], snapshots that survive cleanup [ev:clawteam-model#F22], an MCP server with 26 coordination tools [ev:clawteam-probe-log#F2], an event bus with hooks [ev:clawteam-model#F23][ev:clawteam-model#F24], and a 269-line leader Skill plus 608 lines of workflow/CLI references (`ClawTeam/skills/clawteam/SKILL.md`, `references/*.md`) that already tell a Claude Code or Codex Lead how to create teams, spawn, wait and shut down [ev:clawteam-model#F16]. An Assistant can be a directory of files; a TeamTemplate can compile to a ClawTeam TOML template; the Lead — a Claude Code or Codex process holding the ClawTeam Skill — can do the brokering and the nesting by following instructions; OpenClaw and Telegram stay optional Surfaces. Everything else is convention plus a few scripts.

**What would change my mind.** (1) A PoC-A probe showing that a Codex Member spawned by ClawTeam does not actually start or does not receive the definition: ClawTeam appends the prompt *positionally* for Codex (TUI-with-initial-prompt, never `codex exec`) and never executed it without a TTY [ev:clawteam-spawn-platform#F1 open q.1]. (2) A Windows probe showing the subprocess backend unusable even with file-delivered prompts (cmd.exe truncation, no exit code, `os.getuid()` under the default config) [ev:clawteam-spawn-platform#F20]. (3) A requirement for *mechanical* cross-run isolation (per-run `CLAWTEAM_DATA_DIR`) breaking `task wait`/inbox discovery for the Lead [model:team-execution-model#13]. (4) HKUDS reviving (merging PRs #159/#165/#167) — O5 would then rise [ev:clawteam-spawn-platform#F24]. Honesty up front: the evidence already shows that *pure* convention (O1) leaves several M-priority rows unsatisfied; my ranking therefore puts the thin composition layer (O2) first and O1 as the zero-code on-ramp.

## 2 Option-by-option evaluation

Scores 1–5 (higher is better). Size = newly written code only.

### O1 — ClawTeam as-is + reusable Assistant packages (conventions + scripts)

**Shape.** An Assistant is a directory (`assistant.yaml`, `persona.md`, `principles.md`, `harness-policy.yaml`, `skills/`), a TeamTemplate is a hand-written or script-rendered ClawTeam TOML under `~/.clawteam/templates/` whose `AgentDef.task` strings are the rendered persona+principles+task and whose `AgentDef.command` names the harness per Member [ev:clawteam-probe-log#F16][ev:clawteam-model#F13]. The Lead (Claude Code/Codex with the ClawTeam Skill) creates the run with `clawteam launch <tmpl> --backend subprocess` or `spawn subprocess … --task`, reads `harness-policy.yaml` and picks `command`, nests by the documented CLI composition (`team spawn-team B -n <self>` → `spawn --team B` → `task wait B --agent <self>` → `inbox receive B` → `team snapshot B` → `team cleanup B`) [ev:clawteam-model#F22]. Three scripts are allowed: a template renderer, a `tee` wrapper so worker output is not lost, and a Hermes shim that turns ClawTeam's generic `-p <prompt>` into `hermes chat --source tool -q` [ev:clawteam-spawn-platform#F2]. **Not built:** any new object, record, broker, gate, overlay engine or proposal tool. **Size: S** (≈300–800 LOC of scripts).

| R | Score | One-line justification |
|---|---|---|
| R1 | 5 | Scripts only; no layer [reuse:G-TE-01 rung 1][reuse:G-TE-03 rung 1]. |
| R2 | 3 | Depends only on the ClawTeam CLI surface; upstream dormant but pinned; `mcp<2` pin if MCP used [ev:clawteam-probe-log#F1][ev:clawteam-spawn-platform#F24]. |
| R3 | 2 | Windows: `os.getuid()` under default `skip_permissions`, no keepalive/exit code, cmd.exe truncation of multi-line `-p` persona prompts; POSIX `tee`/shim scripts [ev:clawteam-spawn-platform#F20][ev:clawteam-probe-log#F25]. |
| R4 | 2 | PoC A/B/C pass only with hacks (attribution by member name, hidden-by-naming, cleanup leaves processes); ensemble synthesis = prose; proposals = convention (details §5, §8). |
| R5 | 4 | Definitions are plain files; TOML is a derived artifact; swapping ClawTeam = rewrite the renderer [ev:clawteam-model#F13]. |
| R6 | 5 | MIT; `--dangerously-*` flags are harness-ToS matters [ev:clawteam-spawn-platform#F25][ev:harness-cli-capabilities-a#F15]. |
| R7 | 5 | Runnable today on this host (subprocess backend probe-verified) [ev:clawteam-probe-log#F12][ev:clawteam-probe-log#F16]. |
| R8 | 3 | Harness flag drift lands in TOML `command` strings and shims; ClawTeam bugs stay unfixed (dormant) [ev:clawteam-spawn-platform#F22][ev:clawteam-spawn-platform#F24]. |
| R9 | 3 | Rung 1 — but below the rung that *satisfies* the M rows (fit-gap AD/TC/HB roll-ups: no `S/C` on AD-01/TC-01/HB-01/HB-03) [fitgap:AD-01][fitgap:TC-01][fitgap:HB-01]. |
| R10 | 2 | Unmet mechanically: AD-02, AD-05 (enforcement), AD-07 (hidden+auditable), TC-05 (gate), TE-07 (output/exit code), HB-01, HB-03, HB-05 (attribution), HB-07, EV-02/03, AR-01/02/03 [fitgap:TE-07][fitgap:HB-05][fitgap:EV-03]. |

### O2 — ClawTeam + thin Assistant composition layer (my answer)

**Shape.** A small package (`ats`) that owns the data objects nothing else has — Assistant, TeamTemplate, overlays, HarnessProfile files, selection policy, run/invocation records, Proposals — and *compiles* a TeamRun into ClawTeam CLI calls: `team spawn-team`, `task create --blocked-by`, per-Member `spawn subprocess … -- <wrapper> <fully rendered harness argv>`, `task wait`, `snapshot`, stop, `cleanup`. Passing an explicit positional command bypasses ClawTeam's adapter chain and profile inference [ev:clawteam-spawn-platform#F5][ev:clawteam-probe-log#F11], so the renderer — not ClawTeam — decides how the definition reaches each harness [ev:harness-cli-capabilities-a#F17][ev:harness-cli-capabilities-b#F24]. The wrapper tees output, reads the harness JSON/usage file and writes the HarnessInvocation record, closing ClawTeam's DEVNULL/`exit_code: null` holes [ev:clawteam-spawn-platform#F21][ev:clawteam-probe-log#F14]. The Lead still coordinates through ClawTeam tasks/inbox (or `clawteam-mcp`), but calls `ats member add` / `ats nest` / `ats ensemble` for anything that must be gated or recorded. **Not built:** message bus, task store, liveness, tmux, surfaces, a ClawTeam fork, other execution backends. **Size: M** (≈3–4k LOC; §4).

| R | Score | One-line justification |
|---|---|---|
| R1 | 3 | ≈3–4k LOC, almost all data handling + one compiler; runtime stays ClawTeam [reuse §6 "new by evidence"]. |
| R2 | 4 | Couples to the ClawTeam *CLI* (pinned 0.3.0), not Alpha library seams; `mcp<2` pin; no fork [ev:clawteam-spawn-platform#F15][ev:clawteam-probe-log#F1]. |
| R3 | 4 | Wrapper delivers prompts by file, captures output/exit code itself; `skip_permissions=false` + explicit flags avoids `os.getuid()`; Windows still unprobed [ev:clawteam-spawn-platform#F20][ev:clawteam-openclaw-fork-delta#F19]. |
| R4 | 5 | All eight pressure tests walk through cleanly (§5). |
| R5 | 4 | ClawTeam sits behind a ≈600-LOC compile step; definitions/records are ClawTeam-free [model:team-execution-model#11]. |
| R6 | 5 | MIT substrate; harness flags only; ATM text not copied [reuse §7]. |
| R7 | 4 | Days: schema + renderer for claude/codex + wrapper unlock PoC A; compiler unlocks B/C. |
| R8 | 3 | Five renderers track five fast-moving CLIs; ClawTeam dormant (stable target, unfixed bugs) [ev:clawteam-spawn-platform#F24]. |
| R9 | 5 | Rung 2 over ClawTeam; rung 6 only for objects no system offers [reuse §2 "rung 6: 23 data objects"][fitgap:XC-03]. |
| R10 | 5 | All M rows addressed; TE-08 and Codex HB-02 channel unverified (§9). |

### O3 — ClawTeam + HarnessBroker extension (ClawTeam backend/plugin)

**Shape.** Same broker as O2 but packaged as a custom `SpawnBackend` registered via `register_backend` (receives `prompt`/`system_prompt`) plus a plugin [ev:clawteam-spawn-platform#F8][ev:clawteam-spawn-platform#F17]. Because `clawteam spawn` never loads plugins and `register_backend` is process-local, the entry point must be *our* Python process importing ClawTeam — so the definition/overlay/record objects are still needed and the broker inherits ClawTeam's Alpha internals. **Not built:** definitions, templates, nesting, evolution (unless O2 is added). **Size: M.**

| R | Score | One-line justification |
|---|---|---|
| R1 | 3 | Broker ≈ O2's renderer+policy, plus ClawTeam glue [ev:clawteam-spawn-platform#F8]. |
| R2 | 2 | No `__all__`, "Alpha", plugins loaded only by `harness conduct`; `BeforeWorkerSpawn` never fires on the CLI path [ev:clawteam-spawn-platform#F15][ev:clawteam-spawn-platform#F16][ev:clawteam-spawn-platform#F17]. |
| R3 | 3 | Inherits ClawTeam backend code on Windows; our backend could file-deliver prompts [ev:clawteam-spawn-platform#F20]. |
| R4 | 3 | Ensemble/fallback/record yes; nesting, hidden, overlays, proposals untouched. |
| R5 | 2 | Broker written against ClawTeam internals; reversibility poor [ev:clawteam-spawn-platform#F15]. |
| R6 | 5 | MIT. |
| R7 | 3 | Needs our own CLI entry anyway; PoC A possible, B/C need O2 pieces. |
| R8 | 2 | Internal API drift + harness drift. |
| R9 | 3 | Rung 2/3 where plain subprocess (rung 1) already launches [ev:clawteam-probe-log#F12]. |
| R10 | 3 | HB rows yes; AD/TC/TE-05/EV/AR rows no. |

### O4 — ClawTeam core + optional OpenClaw/Telegram Surface

**Shape.** O1/O2 unchanged; a Surface adapter presents a TeamRun's *visible* Members over OpenClaw channels (`agent --deliver`, bindings, `identity`) or Hermes `send --to`, never defining team semantics [ev:openclaw-native-and-telegram-verification#F15][ev:openclaw-native-and-telegram-verification#F20][ev:claude-agent-teams-hermes-openbot#F26]. **Not built:** core. **Size: S** adapter (+ daemon dependency).

| R | Score | One-line justification |
|---|---|---|
| R1 | 4 | Adapter only; but it is additive to O1/O2, not a substitute. |
| R2 | 2 | OpenClaw flag/key drift (fork `--model` on `tui` invalid; kit keys stale; `OPENCLAW_WORKSPACE` unread) [ev:clawteam-openclaw-fork-delta#F5][ev:openclaw-native-and-telegram-verification#F17][ev:harness-cli-capabilities-b#F4]. |
| R3 | 3 | Gateway daemon per OS; Windows via WSL2 recommended [ev:harness-cli-capabilities-b#F16]. |
| R4 | 2 | Adds nothing to PoC A/B/C (which forbid OpenClaw/Telegram) [product-intent §4]. |
| R5 | 3 | Optional; but identity binds to a persistent OpenClaw agent (MS-03 gap) [fitgap:MS-03]. |
| R6 | 5 | MIT; BotFather steps human-only [ev:openclaw-native-and-telegram-verification#F33]. |
| R7 | 2 | Needs gateway, bot token, `agents.list` entries first [ev:openclaw-native-and-telegram-verification#F24]. |
| R8 | 2 | Two daemons' release trains [ev:openclaw-native-and-telegram-verification#F12]. |
| R9 | 3 | Rung 2 for a C-priority row (MS-02). |
| R10 | 2 | Same unmet rows as O1; MS rows already satisfied by CT [fitgap:MS-01][fitgap:MS-04]. |

### O5 — Upstream ClawTeam extensions (PRs)

**Shape.** Bounded PRs: `os.getuid` guard + `mcp<2` pin, logs dir + read `CLAWTEAM_EXIT_CODE`, `TeamConfig.created_by` + `--parent-team`, `BeforeWorkerSpawn` on the CLI path with mutable prompt/command + plugin load, Hermes/Grok adapter branches + Codex `-c developer_instructions`, `launch` error surfacing + `AgentDef.profile` + `TaskDef.blocked_by`, `TeamMember.hidden`, cleanup stops processes, inbox ACL — ≈400–700 LOC total [reuse §5]. **Not built:** our objects. **Size: S.**

| R | Score | One-line justification |
|---|---|---|
| R1 | 4 | Small deltas, each with tests [reuse §5]. |
| R2 | 1 | No upstream commit since 2026-05-09, 22 open PRs (#159/#165/#167 unanswered) — until merged this is a local patch set [ev:clawteam-spawn-platform#F24]. |
| R3 | 4 | The guard/logs/`platform_compat` PRs are exactly the Windows fixes [ev:clawteam-spawn-platform#F20][ev:clawteam-openclaw-fork-delta#F19]. |
| R4 | 3 | Removes hacks (hidden flag, parent link, output, launch errors); still no definition/broker/overlay/proposal objects. |
| R5 | 3 | Deeper reliance on ClawTeam semantics. |
| R6 | 5 | MIT, attribution [ev:clawteam-spawn-platform#F25]. |
| R7 | 2 | Merge latency unknown; patched local install = rung 5 in practice. |
| R8 | 2 | Carrying patches against a dormant tree [ev:clawteam-openclaw-fork-delta#F27]. |
| R9 | 3 | Rung 3 where every item has a rung-2 equivalent [reuse §2 "rung 3 is never the only path"]. |
| R10 | 2 | Same objects missing as O1. |

### O6 — Selective reuse of modules into a new small layer

**Shape.** Vendor CTF `platform_compat.py`, `model_resolution.py`, `spawn_with_retry`, the `subprocess_wrapper` shape, and ClawTeam's `FileTaskStore`/`MailboxManager`/registry into a layer that *replaces* ClawTeam as the runtime [ev:clawteam-openclaw-fork-delta#F28][reuse §4]. **Not built:** tmux, surfaces. **Size: M–L** (own DAG/inbox/spawn/liveness plus everything in O2).

| R | Score | One-line justification |
|---|---|---|
| R1 | 2 | Re-owns coordination machinery O2 inherits for free. |
| R2 | 3 | No upstream dependency, but `respawn.py`/registry are coupled; the vendored task store drags `fileutil`, `paths`, models [ev:clawteam-openclaw-fork-delta#F28]. |
| R3 | 4 | `platform_compat` vendored; own launcher can file-deliver prompts [ev:clawteam-openclaw-fork-delta#F19]. |
| R4 | 4 | Can satisfy all tests, at a cost. |
| R5 | 5 | No lock-in. |
| R6 | 4 | MIT; fork-only files lack SPDX headers (attribute HKUDS); ATM schemas unlicensed [ev:clawteam-openclaw-fork-delta#F30][reuse §7]. |
| R7 | 2 | Weeks before PoC B/C. |
| R8 | 3 | We maintain forked copies. |
| R9 | 2 | Rung 4 where rung 1–2 on ClawTeam satisfies TE [fitgap TE roll-up]. |
| R10 | 4 | All rows reachable; nothing special. |

### O7 — Independent Assistant/Harness layer above multiple execution backends

**Shape.** O2's objects plus a backend abstraction: ClawTeam, direct CLI invocation, Claude Code native subagents/teams, OpenClaw sessions, Hermes kanban. Evidence on the extra backends: Claude Code teams are experimental, Claude-only, interactive-only, non-nested, config deleted at session end [ev:claude-agent-teams-hermes-openbot#F2][ev:claude-agent-teams-hermes-openbot#F6][ev:claude-agent-teams-hermes-openbot#F7][ev:claude-agent-teams-hermes-openbot#F8][ev:claude-agent-teams-hermes-openbot#F4]; OpenClaw `sessions_spawn(runtime:"acp")` needs the Gateway and the absent acpx plugin and gives ACP children prompt+cwd only [ev:openclaw-native-and-telegram-verification#F16][ev:harness-cli-capabilities-b#F12]; Hermes kanban dispatches `hermes -p <profile>` workers with per-task models and durable runs but is Hermes-only and un-nestable [ev:claude-agent-teams-hermes-openbot#F25][ev:harness-cli-capabilities-b#F19]. Hermes is therefore a first-class *Harness* (profile distributions as a secret-free package, `-z --usage-file`) in every option, but a weak *team backend*. **Size: M–L.**

| R | Score | One-line justification |
|---|---|---|
| R1 | 2 | O2 + N backend adapters. |
| R2 | 4 | No single substrate dependency; weak backends cost little if unused. |
| R3 | 4 | Direct-CLI backend with file prompts is the cleanest Windows path [ev:harness-cli-capabilities-a#F14]. |
| R4 | 5 | All tests, by construction. |
| R5 | 5 | Best reversibility. |
| R6 | 5 | MIT/Apache/proprietary-invocation only. |
| R7 | 2 | Abstraction before need. |
| R8 | 2 | N backends × fast-moving CLIs. |
| R9 | 3 | Builds a second backend before evidence demands one (XC-03). |
| R10 | 5 | All rows. |

### O8 — New implementation

**Shape.** Team execution from scratch. Nothing in the evidence demands it: ClawTeam's TE layer is reachable at rung 1–3 with probe-verified DAG/inbox/spawn [fitgap TE roll-up]. **Size: L.**

| R | Score | One-line justification |
|---|---|---|
| R1 | 1 | Largest. |
| R2 | 5 | None. |
| R3 | 4 | Designed in. |
| R4 | 5 | By construction. |
| R5 | 5 | — |
| R6 | 5 | — |
| R7 | 1 | Months. |
| R8 | 1 | Everything is ours. |
| R9 | 1 | Rung 6 with rung 1–2 available — violates XC-03. |
| R10 | 5 | — |

## 3 Ranking with reasons

Totals: O2 42 · O7 37 · O1 35 · O6 33 · O8 33 · O3 29 · O5 29 · O4 28. Ranking (judgment, weighting R1/R7/R9 because the question is about the *smallest* layer): **O2 > O1 > O7 > O5 > O4 > O3 > O6 > O8**.

- **O2 first** because it is the smallest thing that satisfies every M row and all eight pressure tests without a hack, and everything it adds is a data object the fit-gap shows no system has (AD-01/02/04, TC-01/05, HB-01/03/05/07, EV-02/03, AR-01/02/03) [reuse §6].
- **O1 second** as the on-ramp: it runs today and proves the spawn/DAG/inbox path, but the probe evidence shows where convention stops (§8) — it cannot be the answer to "what must be built".
- **O7 third**: the same layer as O2 with more backends; justified only if ClawTeam fails a PoC. Claude Code teams and OpenClaw sessions are poor backends on the evidence; Hermes is a good Harness but a single-harness backend.
- **O5 before O4** (against my stated bias order): the PRs remove exactly the hacks PoC B/C need, whereas a Surface adds nothing to the PoCs and imports OpenClaw drift; but O5 is gated on a dormant upstream, so it is filed, not depended on.
- **O3** is O2's broker in the wrong place; **O6** re-owns what ClawTeam gives; **O8** violates XC-03.

## 4 My "smallest new layer" (O2: `ats`)

| Component | Responsibility | Size | Substrate primitive it wraps / new | Evidence |
|---|---|---|---|---|
| Assistant package loader + closed schema + exclusion validator | `assistant.yaml` + referenced files; reject unknown keys; heuristics for paths/sessions/topics/secrets | S ~400 | **new** (schema idea: DG `.strict()`) | [reuse:G-AD-01][reuse:G-AD-05][ev:dsh-agent-teams-and-gui#F20] |
| Overlay resolver | Base → Reviewed Evolution → User → effective definition + hash; per-field rules | S ~200 | **new** (two-layer precedent: Hermes ownership split) | [reuse:G-EV-02][ev:claude-agent-teams-hermes-openbot#F24] |
| HarnessProfile files + injection renderers | YAML per installed harness seeded from the checklists; render bundle → argv/prepared dir per harness | S ~600 + data | wraps harness CLIs; **new** as data; bypasses ClawTeam adapter by explicit command | [ev:harness-cli-capabilities-a#F16][ev:harness-cli-capabilities-b#F23][ev:clawteam-spawn-platform#F5] |
| Selection policy resolver | user > Assistant > team > default; fallback = new invocation | S ~150 | **new**; pattern CTF `model_resolution.py` | [reuse:G-HB-03][ev:clawteam-openclaw-fork-delta#F15] |
| TeamTemplate format + ClawTeam compiler | template + project + task → `team spawn-team`, `task create --blocked-by`, `spawn subprocess … -- wrapper argv`, `task wait`, `snapshot`, stop, `cleanup` | S–M ~600 | wraps ClawTeam CLI (not library) | [ev:clawteam-probe-log#F16][ev:clawteam-probe-log#F23][ev:clawteam-model#F22] |
| Invocation wrapper + HarnessInvocation record | tee stdout/stderr, exit code, parse `-p` JSON / `--usage-file` / rollout meta; file-delivered prompt | S ~300 | **new** (shape: CTF `subprocess_wrapper.py`) | [ev:clawteam-spawn-platform#F21][ev:clawteam-probe-log#F14][ev:harness-cli-capabilities-a#F10] |
| TeamRun record + roster projections | `run.json`; Members {visibility, origin, definition_ref, policy_decision}; user view vs archive view | S ~250 | **new** sidecar over `~/.clawteam/teams/<run>` | [model:team-execution-model#3][model:team-execution-model#9] |
| Dynamic-member gate + Ephemeral Assistant writer | `ats member add` checks `dynamic_members`, writes definition into run dir, spawns | S ~200 | gate **new**; spawn = ClawTeam | [model:team-execution-model#5][ev:clawteam-model#F5] |
| Nesting contract | `ats nest`: inner run with parent link, delegated task, RunResult → outer task metadata + `inbox send`, snapshot, stop, cleanup | S ~300 | composition over ClawTeam + **new** record | [ev:clawteam-model#F22][ev:clawteam-probe-log#F18][ev:clawteam-probe-log#F19][ev:clawteam-probe-log#F20] |
| Ensemble fan-out + synthesis record | N invocations, one `bundle_id`; synthesis = one more invocation with structured inputs | S ~200 | **new** record; fan-out = ClawTeam/subprocess | [model:harness-broker-model#8][ev:clawteam-probe-log#F16] |
| Artifact manifest + lock writer + resolution report | requirements vocabulary; lock {ref, resolved, digest, fingerprint}; per-host native/installed/degraded/unsupported | S ~250 | **new** data (ideas: ADR 0022, OC eligibility) | [reuse:G-AR-01][reuse:G-AR-06][ev:harness-cli-capabilities-b#F11] |
| Proposal generator + review CLI | bounded typed Proposals from the archive; accept/reject with applied hash | S ~300 | **new**; transport = files (ClawTeam `plan_submit` optional) | [reuse:G-EV-03][ev:clawteam-model#F17] |
| Operational mode (S-priority) | watcher registry, OS-scheduler wiring, RunStateSummary, decision log | S ~300 | **new**; schedulers borrowed | [model:team-execution-model#7][ev:openclaw-native-and-telegram-verification#F9] |
| `ats` CLI + Lead Skill (`SKILL.md`) | commands above; Skill telling the Lead when to call `ats` instead of raw `clawteam spawn` | S ~300 + docs | wraps ClawTeam Skill | [ev:clawteam-model#F16] |

**Explicit exclusions.** No message bus, task store, liveness, worktree manager (ClawTeam) [ev:clawteam-probe-log#F7][ev:clawteam-probe-log#F9][ev:clawteam-probe-log#F13][ev:clawteam-probe-log#F22]; no tmux; no ClawTeam fork or library-seam coupling; no second execution backend; no Surface adapter (O4 later); no OpenClaw Gateway dependency; no artifact *installer* (metadata, lock and report only); no UI; no ATM schema text [reuse §7].

**Interfaces.** Lead (Claude Code/Codex, ClawTeam Skill + `ats` Skill) → `ats run|member add|nest|ensemble|proposals` → ClawTeam CLI (`team spawn-team`, `task create/update/wait`, `inbox send/receive`, `spawn subprocess -- <wrapper> …`, `team snapshot/cleanup`) and harness CLIs (inside the wrapper). Members coordinate directly with `clawteam task/inbox` (or `clawteam-mcp`, `mcp<2`). `ats` reads `~/.clawteam/teams/<run>/{config,spawn_registry,events,inboxes}` and `tasks/<run>` for the archive [ev:clawteam-model#F2]. Process stop uses `registry.stop_agent` semantics through `spawn --replace` or a SIGTERM on the registry pid [ev:clawteam-probe-log#F21][ev:clawteam-probe-log#F13].

**Data owned.** `~/.ats/{assistants/<id>/, templates/, overlays/, harnesses/<name>.yaml, policies/user.yaml, runs/<run>/{run.json, members/, ephemeral/, invocations/, output/, nested/, proposals/, snapshot.json}, proposals/, locks/}`. ClawTeam's own dirs are the substrate half of the archive.

## 5 Pressure-test walkthroughs

**PoC A — same Assistant on Codex / Claude Code.** *Scenario:* `code-reviewer` reviews one diff on Codex (run 1) then Claude Code (run 2); definition byte-identical afterwards. *Mechanics:* `ats run --assistant code-reviewer --harness codex --repo … --task …` resolves overlays → bundle hash → renders Codex: `codex exec -c developer_instructions="<persona+principles>" --json --output-schema review.json -C <worktree>` (fallback: `CODEX_HOME=<tmp>` with `AGENTS.md`) [ev:harness-cli-capabilities-a#F2][ev:harness-cli-capabilities-a#F4]; run 2 renders `claude -p --bare --append-system-prompt-file <bundle> --output-format json --json-schema …` [ev:harness-cli-capabilities-a#F17][ev:harness-cli-capabilities-a#F19]. Both launch through ClawTeam `spawn subprocess --no-keepalive -- ats-wrap <argv>` into a one-Member team (or directly for a solo run); the wrapper records session id, cost (`total_cost_usd` for Claude; tokens only for Codex, `cost_source: unavailable`) and exit code [ev:harness-cli-capabilities-a#F10]. *New:* renderer, policy, wrapper/record. *Reused:* harness flags, ClawTeam spawn/registry. *Where convention alone broke:* ClawTeam drops the system prompt for Codex and appends the prompt positionally [ev:clawteam-spawn-platform#F6][ev:clawteam-spawn-platform#F1]; ClawTeam records argv+pid, cost self-reported, `exit_code: null` [ev:clawteam-probe-log#F13][ev:clawteam-probe-log#F14].

**PoC B — fresh TeamRun, hidden temporary Member, mixed harnesses.** *Scenario:* template {Lead, Implementer, Reviewer}; Lead adds a hidden migration-safety specialist; ≥2 harnesses. *Mechanics:* `ats run development --repo …` compiles: `clawteam team spawn-team run-7f3a -n lead`, `task create … --blocked-by`, per-Member `spawn subprocess … -- ats-wrap <rendered argv>` (Lead=claude, Implementer=codex, Reviewer=hermes `chat --source tool -q … -p <tmp profile>`) [ev:clawteam-probe-log#F16][ev:harness-cli-capabilities-b#F6]; `run.json` lists the roster. Lead runs `ats member add --hidden --assistant-inline …`; `ats` checks `dynamic_members` (requester, count, harness), writes `runs/<run>/ephemeral/migsafe.yaml`, spawns via ClawTeam with `visibility: hidden` in the sidecar; `ats status` filters hidden; `ats archive` shows it. Task flows through ClawTeam's DAG; `task wait` confirms completion [ev:clawteam-probe-log#F7][ev:clawteam-model#F8]. *New:* gate, roster projections, ephemeral writer. *Where convention broke:* `TeamMember` has no visibility field and `team status` lists everyone [ev:clawteam-model#F1][ev:clawteam-probe-log#F10]; no gate on `spawn`; `BeforeWorkerSpawn` never fires on the CLI path [ev:clawteam-spawn-platform#F16]; output DEVNULL [ev:clawteam-probe-log#F12].

**PoC C — nested TeamRun with result return + archive.** *Scenario:* CodeMod Member of `ops` creates an inner `development` run for task t4, collects the result, inner run archived, outer continues. *Mechanics:* `ats nest --template development --task t4` → inner run id `dev-c21d`, `parent: {run: ops, member: codemod, task: t4}`, depth check; ClawTeam: `team spawn-team dev-c21d -n codemod` first (so the creating Member is ClawTeam "leader", avoiding the child-becomes-leader trap) [ev:clawteam-probe-log#F18][ev:clawteam-model#F22 step 7]; inner Members spawned with inner identity and worktrees based on t4's branch; `task wait dev-c21d --agent codemod` (explicit `--agent`, avoiding the default-inbox trap) [ev:clawteam-model#F8]; inner Lead writes `RunResult` via `ats result`; `ats` copies it into outer task t4 `metadata.result` and sends `clawteam inbox send ops codemod` (cross-team send probe-verified) [ev:clawteam-probe-log#F19]; `team snapshot dev-c21d`, SIGTERM registry pids, `team cleanup dev-c21d --force` [ev:clawteam-probe-log#F20]; `ops/run.json.nested_runs[]` records the archive ref. *New:* parent link, delegated-task marker, RunResult, stop-before-cleanup. *Where convention broke:* no parent field, no isolation (any identity sends/waits on any team), cleanup leaves processes and `harness/B`, orphan recreates dirs [ev:clawteam-probe-log#F6][ev:clawteam-probe-log#F19][ev:clawteam-probe-log#F20].

**Nested TeamRun result + archive (contract detail).** The outer task completes only when the inner run reaches terminal status; failure (inner Lead dead with pending tasks, detected via `is_agent_alive`/`check-zombies`) marks t4 `failed` + message [ev:clawteam-probe-log#F13]; nothing is written to any Assistant or TeamTemplate (ClawTeam writes only under its data dir) [ev:clawteam-model#F22 step 8]; inner invocations use `--bare`/`--ephemeral`/fresh profile so harness memory cannot leak (EV-04) [ev:harness-cli-capabilities-a#F19]. Open: `inbox send` vs `task update --metadata` with real agents [ev:clawteam-probe-log §5 q.3].

**Ensemble + synthesis (PoC A run 3).** `ats ensemble --legs codex,claude-code` renders one bundle twice, spawns two Members with separate worktrees and fresh-session flags, requires `--json-schema`/`--output-schema` outputs, then one synthesis invocation whose prompt carries both outputs labelled by invocation id and whose schema is `{agreements[], disagreements[{claim, sources[]}]}` [ev:harness-cli-capabilities-a#F10][model:harness-broker-model#8]. *Reused:* ClawTeam per-member command fan-out [ev:clawteam-probe-log#F16]. *Where convention broke:* shared cwd/mailbox, attribution by member name only, synthesis as the leader's prose turn, no version/model/cost [fitgap:HB-05][fitgap:HB-07].

**Evolution overlays + proposals.** After each run `ats proposals generate` reads the archive, emits ≤N typed Proposals with `independence_check`; `ats proposals accept <id>` appends to the Reviewed Evolution Overlay with `applied_hash` and provenance; User Overlay is hand-edited; the resolver merges per the field table [model:assistant-domain-model#9]. *New:* all three objects (no substrate has them) [fitgap:EV-02][fitgap:EV-03]. *Where convention broke:* a Lead "instructed not to edit the definition" is not EV-03's guarantee; ClawTeam's only layering is whole-file template override [ev:clawteam-probe-log#F4].

**Long-running operational run with deterministic backends.** `ats run training-ops --mode operational` registers watchers (metric poller, checkpoint detector) as OS-scheduled commands (cron/systemd timer/schtasks; OpenClaw cron optional) that call `ats trigger <member>`; each trigger = fresh HarnessInvocation with the definition + RunStateSummary; decisions logged [model:team-execution-model#7]. ClawTeam is *not* the resident loop — its keepalive/worker-loop model is inverted [ev:clawteam-model#F15][ev:clawteam-model#F18]; the run's ClawTeam team holds tasks/messages only. *New:* watcher registry, summary, decision log (all S-priority). *Where convention broke:* `inbox watch --exec` → `spawn --no-keepalive` composition is file:line-only, unprobed [ev:clawteam-model#F19]; no keepalive for openclaw/generic CLIs or Windows [ev:clawteam-spawn-platform#F14][ev:clawteam-spawn-platform#F20].

**Ephemeral hidden Member audit.** The archive contains the generated definition file, the gate decision, the full argv (ClawTeam registry keeps it) [ev:clawteam-probe-log#F13], tee'd output, exit code, harness session id and transcript hint; `ats status` omits hidden Members; promotion to a persistent Assistant is `ats promote` (human, validator-stripped). *Where convention broke:* ClawTeam's registry has the prompt but not output/exit code; board shows all members [ev:clawteam-probe-log#F12][ev:clawteam-probe-log#F10].

## 6 Cross-platform story

Ubuntu (this host): ClawTeam 0.3.0 installs under uv 3.11; subprocess backend, tasks, inbox, lifecycle, templates, worktrees probe-verified; tmux absent and never required; `clawteam-mcp` needs `mcp<2` [ev:clawteam-probe-log#F1][ev:clawteam-probe-log#F12][ev:clawteam-probe-log#F15]. macOS: same POSIX paths, ClawTeam CI covers it [ev:clawteam-spawn-platform#F20]. Windows: set `skip_permissions=false` in config (configuration) so `adapters.py:53 os.getuid()` is never reached, and let the renderer emit bypass flags explicitly per harness [ev:clawteam-spawn-platform#F20]; the wrapper delivers prompts by file (`--append-system-prompt-file`, `--message-file`, `-q` with short text) to dodge cmd.exe newline truncation, captures exit codes itself (ClawTeam's Windows branch has no keepalive and no `CLAWTEAM_EXIT_CODE`), and never relies on keepalive (fresh-by-default) [ev:clawteam-spawn-platform#F10]; `platform_compat.py` (130 lines, stdlib, MIT) may be vendored for `pid_alive`/locks [ev:clawteam-openclaw-fork-delta#F19]. The harnesses themselves run natively on all three OSes per vendor docs, `S?~` until probed [ev:harness-cli-capabilities-a#F14][ev:harness-cli-capabilities-b#F16][ev:harness-cli-capabilities-b#F22]. Residual: no Windows CI anywhere; PR #159 open; a Windows/macOS probe is the TE-08 evidence gap [fitgap:TE-08].

## 7 Risks & unknowns

1. Codex under ClawTeam's subprocess backend (positional prompt, no TTY) unexecuted; `-c developer_instructions` unverified — PoC A day-one probe [ev:clawteam-spawn-platform#F1][ev:harness-cli-capabilities-a#F2].
2. Upstream dormant: bugs (`launch` swallows errors, `template show harness-default` crash, `--blocked-by` unvalidated, cleanup leaves processes) stay; the compiler works around each [ev:clawteam-probe-log#F26].
3. No inter-team isolation in ClawTeam: mechanical reviewer independence (TC-03 S) and concurrent runs rely on our addressing discipline; per-run data dirs may break Lead discovery [ev:clawteam-probe-log#F19][model:team-execution-model#13].
4. ClawTeam "leader" semantics (first spawn into a new team becomes leader; `task wait` default inbox) are traps the compiler must never expose to the Lead [ev:clawteam-probe-log#F18][ev:clawteam-model#F8].
5. Hermes `--source tool` hiding and `--ignore-rules` memory-write suppression unprobed on 0.20.4 [ev:harness-cli-capabilities-b §5]; per-run profiles mitigate.
6. Harness ToS for subscription logins in unattended runs (Codex/Grok pages 403) [ev:harness-cli-capabilities-a#F15].
7. Model tool-call compliance (ATM U2 0/2 on DeepSeek) may hit LLM-emitted protocol steps; keep protocol state in the DAG, not in prose [ev:atm-salvage#F24].

## 8 Where my bias breaks

- **"Assistants are files + conventions."** True for content; false for AD-02/AD-05/AD-07 enforcement, overlays and proposals — no substrate validates, merges or gates, and a Lead instructed "do not edit the definition" is not EV-03 [fitgap:EV-03][ev:clawteam-probe-log#F4]. Minimum new code: schema + validator + resolver + Proposal record (~1k LOC).
- **"TeamTemplates compile to TOML."** Only the static roster does; `launch` has no DAG edges, hides spawn failures, one profile for all, and `AgentDef.task` is one prose slot — so the compiler drives `spawn` per Member, not `launch` [ev:clawteam-probe-log#F15][ev:clawteam-probe-log#F23][ev:clawteam-spawn-platform#F12].
- **"The Lead does the brokering."** It can *choose* a command, but HB-01 (profile as data), HB-03 (precedence — ClawTeam's is inverted), HB-05/HB-07 (attribution, record) need data and a wrapper ClawTeam lacks [ev:clawteam-probe-log#F17][ev:clawteam-probe-log#F14]; ClawTeam silently drops the system prompt for 8 of 10 CLIs and its generic `-p` is invalid for Hermes [ev:clawteam-spawn-platform#F6][ev:clawteam-spawn-platform#F2].
- **"The Lead nests by instruction."** Feasible (probe-verified composition) but unsafe: traps, no parent link, no isolation, cleanup leaves processes [ev:clawteam-probe-log#F18][ev:clawteam-probe-log#F19][ev:clawteam-probe-log#F20] — ~300 LOC of contract.
- **Hidden-member audit, logging, Windows** — no flag, DEVNULL, `exit_code: null`, `os.getuid()` [ev:clawteam-model#F1][ev:clawteam-spawn-platform#F21][ev:clawteam-spawn-platform#F20] — the wrapper + sidecar are unavoidable.
- **O4 over O5** in my assigned order is wrong on the evidence; **Hermes** as a substrate (distributions, kanban, MoA) is a strong *Harness* and an honest AR-03 precedent but cannot host mixed-harness or nested runs [ev:claude-agent-teams-hermes-openbot#F22][ev:claude-agent-teams-hermes-openbot#F25].
- Absolute minimum new code, all options considered: ≈3k LOC of data objects + one compiler + one wrapper. Less than that is the O1 hack set.

## 9 M-priority requirements my proposal cannot (yet) satisfy

None are flatly unsatisfiable; three are at risk: **TE-08** — Windows path is documented (config + file prompts + wrapper), not probe-verified; no candidate has Windows CI [fitgap:TE-08]. **HB-02 (Codex channel)** — `-c developer_instructions` is observed only; the AGENTS.md-in-`CODEX_HOME` fallback is also observed, so PoC A run 1 may start degraded [ev:harness-cli-capabilities-a#F2]. **AR-03** — satisfied as *metadata* (manifest, sources, lock); re-establishing artifacts on another host is a manual step in the smallest layer, not an installer [reuse:G-AR-03].
