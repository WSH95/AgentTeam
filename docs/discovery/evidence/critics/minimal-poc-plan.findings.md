---
critic: critic:minimal-poc-plan
document: docs/discovery/minimal-poc-plan.md
date: 2026-08-22
verdict: PASS-WITH-MAJORS
---

# Findings — `minimal-poc-plan.md`

## 1. Verdict

**PASS-WITH-MAJORS.** The plan does what its frontmatter claims: three PoCs, substrate named, harness versions pinned (Claude Code 2.1.239, Codex 0.148.0, Hermes 0.20.4, ClawTeam 0.3.0@0119833 `mcp<2`), exact run shapes, product-intent §4 criteria quoted verbatim and made measurable, `defhash` "definition unchanged" assertion, no Telegram/OpenClaw, a platform matrix, no PoC code, and a STOP. The §1 paragraph and component table are byte-identical to `architecture-options.md` §5 (and the paragraph to `README.md`). Glossary compliance is clean (no stray "agent/role/bot/session"; "leader/worker" only as ClawTeam's words). Of ~45 evidence citations checked, none contradicts its evidence file. Two defects are MAJOR because each makes a PoC C PASS criterion or mechanism wrong *by construction* on the substrate as the plan itself describes it: (1) criterion 1's "outer events contain only the RunResult notification(s) / inner inboxes name no outer Member" is violated by the very `lifecycle on-exit` noise the plan accepts in §4(4) once codemod is made ClawTeam's leader of the inner team; (2) the RunResult carrier `clawteam task update … --metadata` does not exist as a CLI verb — `metadata` is reachable only through the library seam or the MCP tool, both of which the plan and the answer exclude. Neither kills the plan (criterion 2 is "and/or", the inbox carrier is probe-verified), but both must be fixed before owner review. The rest are MINOR/NIT: an unflagged seam-constraint violation in a fallback row, a misattributed open question, Q-number labels that do not resolve in `QUESTIONS.md`, two model-doc open questions answered implicitly, and several two-reading ambiguities in PoC B mechanics.

## 2. Findings table

| id | severity | check | location | problem | evidence | suggested fix |
|---|---|---|---|---|---|---|
| F1 | MAJOR | C12, C2 | §5 "Success criteria" item 1 ("inner inboxes/events name no outer Member except the explicit codemod↔inner-lead edge; outer events contain only the RunResult notification(s)") | Unachievable under the plan's own mechanics. §5(1) makes `codemod` ClawTeam's leader of `run-C1`; §4(4) accepts that *every* `spawn subprocess` exit runs `lifecycle on-exit`, which messages the team leader and is mirrored to `events/`. So every inner Member's exit writes a message addressed to `codemod` (an outer Member, not the inner Lead) into `teams/run-C1/inboxes/…codemod` and `run-C1/events`; and codemod's own exit writes "Agent 'codemod' exited unexpectedly" into `teams/ops-lite/events`. Criterion 1 as worded fires FAIL-HARD by design. | [ev:clawteam-probe-log#F14] (on-exit → leader inbox even on exit 0); [ev:clawteam-probe-log#F9] ("every send is mirrored to `teams/T/events`"); [ev:clawteam-model#F5] (leader = spawn-team caller); ClawTeam/clawteam/cli/commands.py:2971-2980 (`# Notify leader … mailbox.send(… "exited unexpectedly")`), clawteam/team/mailbox.py:118 (`self._log_event(msg)`) | Restate criterion 1 to exclude ClawTeam lifecycle notices by type/content (`on-exit`, `idle`, join/shutdown) or evaluate it on a filtered projection that the archive records alongside the raw events; keep "no task/message of the inner DAG appears in the outer team". |
| F2 | MAJOR | C2, C11 | §5 "Mechanics" (5) "`clawteam task update ops-lite t4 --metadata` (record; unverified with real Members …)"; §5 criterion 2 "RunResult JSON present in outer t4 `metadata.result`"; §1 table row "Run layer … RunResult via task metadata + inbox"; §7 row "Neither result carrier works" | The CLI verb does not exist. `clawteam task update` accepts only `--status/--owner/--subject/--description/--priority/--add-blocks/--add-blocked-by/--force`; `task create` has no metadata option either. Task `metadata` is settable only via the library (`FileTaskStore.update(..., metadata=)`) or the MCP `task_update` tool — the two paths §2 ("`clawteam` CLI only, never `clawteam-mcp`") and the §1 answer ("no library-seam coupling") exclude. The carrier is therefore *absent on the permitted path*, not "unverified with real Members"; the cited probe-log open question 3 only hypothesised it. | ClawTeam/clawteam/cli/commands.py:2180-2191 (task_update options), :2104-2112 (task_create options), `grep -n metadata clawteam/cli/commands.py` → 0; clawteam/store/file.py:146,199-200; clawteam/mcp/tools/task.py:49,75; [ev:clawteam-probe-log] §5 q3 ("or via `task update --metadata`? Untested") | Drop the metadata carrier or replace it with a CLI-reachable record (e.g. RunResult JSON in `task update --description` / subject, or layer-side only in outer `run.json`), fix criterion 2, the §7 row and the §1/architecture-options table wording; flag to `team-execution-model.md` §6 item 3 and `architecture-options.md` §3 which repeat the same verb. |
| F3 | MINOR | C7, C11 | §7 stop table row "Codex `exec` Member cannot run under `spawn subprocess -- ats-wrap` → Members launched by `direct` and registered as `backend: subprocess` + pid [panel:judge-1.md#5]" | This fallback requires the layer to *write* `teams/<run>/spawn_registry.json`, while the answer restated in §1 (CoordinationSubstrate row, assumption (g); judge-2 §5 amendment 7) binds the layer to "state read via `--json`/snapshot; only `spawn_registry.json` read directly". The row silently widens the seam contract without the "back to architecture-options" tag it gives the O6 alternative in the same cell. | §1 table row "CoordinationSubstrate seam + ClawTeam-CLI adapter"; architecture-options §3 (g); evidence/panel/judge-2.md §5 item 7; [ev:clawteam-probe-log#F13] (registry format) | Either mark this fallback as a seam exception that itself routes "back to architecture-options", or drop it and keep only the O6 route. |
| F4 | MINOR | C2 | §4 "Proves / falsifies": "FALSIFIED if a Codex `exec` Member cannot run under ClawTeam `spawn subprocess -- ats-wrap` (open question 1 of [ev:clawteam-spawn-platform])" | Open question 1 of that file asks whether ClawTeam's *own* `codex <positional prompt>` argv (TUI-with-initial-prompt, `adapters.py:137-138`) starts without a TTY — a path the plan never takes (no `--task`, explicit `ats-wrap` command). The relevant precondition is probe (a) (`codex exec` + positional prompt without a TTY under the wrapper). | evidence/clawteam-spawn-platform.md §5 q1; [ev:clawteam-spawn-platform#F1] codex row; §2 probe (a) | Cite probe (a) / [ev:harness-cli-capabilities-a#F1] and remove the open-question-1 reference. |
| F5 | MINOR | C11 | §2 ("per Q5"), §3 ("Q9"), §4 ("Q6", "Q10"), §7 ("Q2", "Q3"), §8 ("Q2…Q10 … `.project-steward/QUESTIONS.md`") | `QUESTIONS.md` carries no Q-numbers (unnumbered check-boxes); the labels resolve only via `architecture-options.md` §7 items 1–10. A reader following the stated pointer cannot find "Q6". | .project-steward/QUESTIONS.md:15-27 (unnumbered bullets); architecture-options.md §7 items 1–10 | Write "Q<n> = `architecture-options.md` §7 item n (mirrored unnumbered in QUESTIONS.md)" once in §2, or number the QUESTIONS.md bullets. |
| F6 | MINOR | C11 | §3 "Injection per harness" / criterion 4 ("the same `bundle_hash` … the proof that different channels carried one definition"); §4 "launches the harness headless as in §3" | Two open questions delegated to this document are answered only implicitly: `harness-broker-model.md` §13 Q4 ("is persona-as-system-prompt the same bundle as persona-as-AGENTS.md for ensemble purposes, or one channel class per leg? For `minimal-poc-plan.md`") — the plan's implicit rule is "same pre-render `bundle_hash` + recorded `render{part→channel}` + `degraded[]` = equivalent; no per-leg channel-class rule", but never says so; `team-execution-model.md` §13 Q4 (does PoC B need `--bare`/fresh profile; broker's or run layer's job) — implicitly yes via "as in §3". | harness-broker-model.md §13 Q4; team-execution-model.md §13 Q4; minimal-poc-plan.md §3, §4 | Add one sentence per question stating the rule the plan adopts and that it closes the question (or returns it to the owner). |
| F7 | MINOR | C12 | §4 "Substrate mechanics" (2) "With the Lead's identity in env, `clawteam team spawn-team run-B --agent-name lead`" | Two readings: (a) the *layer* fabricates `CLAWTEAM_AGENT_ID/AGENT_NAME=lead` before any process exists and later `spawn -n lead` re-uses or duplicates the member record (your own open question 1); (b) the Lead's own process runs `spawn-team` — impossible, the Lead is spawned *into* `run-B` by the layer. Leader-ness is decided by name (`is_leader = _name == leader_name`), so a second agentId is tolerable but must be stated. | [ev:clawteam-model#F5] (`team spawn-team` takes leader id from caller env; `is_leader = _name == leader_name`); [ev:clawteam-probe-log#F18] | State reading (a) explicitly and what the layer records if `spawn -n lead` mints a new agentId. |
| F8 | MINOR | C12, C8 | §4 (4) "Per Member: `clawteam spawn subprocess … -- ats-wrap <inv-id>` … launches the harness headless as in §3" | (i) Spawn timing unstated: all Members at run start (implementer/reviewer idle-poll until t2/t3 unblock; a one-shot `codex exec` may return before its task unblocks → on-exit reset noise + cost) vs lazily when the observer sees a task unblocked. (ii) "as in §3" would apply the *reviewer's* read-only rendering (`--allowedTools Read,Grep,Glob,Bash(git diff*)`, `-s read-only -a never`) to the Lead (must run `ats`/`clawteam`) and the implementer (must write code). | §3 injection table; §4 (4)-(5); [ev:clawteam-probe-log#F14] | State spawn-on-unblock vs spawn-all (and its cost/noise consequence), and per-Member permission rendering (Lead: Bash allowed for `ats`/`clawteam`; implementer: `-s workspace-write`). |
| F9 | MINOR | C12, C1 | §1 "PoC A exercises the PoC-A slice (schemas, overlay resolver, …)" vs §3 "No User Overlay; user-level overrides arrive only as run flags" | The overlay resolver is never exercised beyond the identity merge; no criterion observes `effective_hash ≠ base hash` while `defhash` stays equal. The §1 sentence over-claims. | §1; §3 "Definition under test"; harness-broker-model §7 `assistant_ref{… effective_hash}` | Either say "resolver built, not exercised by any PoC", or add an informational check (one-line User Overlay on `preferences.output` changes `effective_hash`, `defhash` unchanged). |
| F10 | MINOR | C9, C12 | §5 "Isolation variants (ii) per-run `CLAWTEAM_DATA_DIR` for the inner run" + criterion 2 | With the inner data dir in the inner Members' env, `clawteam inbox send ops-lite codemod` writes a stray `teams/ops-lite/inboxes/codemod` under the *inner* data dir (non-member inbox dirs are created on demand) unless `--data-dir <outer>` is passed; criterion 2 could then fail for a reason unrelated to the `task wait`/inbox-discovery question variant (ii) is meant to settle. | [ev:clawteam-model#F2] (`CLAWTEAM_DATA_DIR` root); [ev:clawteam-probe-log#F9] (stray inbox dirs); [ev:clawteam-probe-log#F2] via architecture-options §3 (global `--data-dir` flag) | State that `ats result` delivers with the parent run's data dir (`--data-dir`), and that the wait in (ii) is `task wait run-C1 --data-dir <inner> --agent codemod`. |
| F11 | NIT | C3, C12 | §6 "TE-08 is M and unverified everywhere [fitgap:TE-08]"; §8 "(TE-08 is M …)" | "M" reads as priority (must) or as fit cell `M` (architectural mismatch); the fit-gap row has CT `Xs!` (verified on Ubuntu), so "unverified everywhere" is also an overstatement for this host. | existing-systems-fit-gap.md row TE-08 (`| TE-08 | M | Xs! | C! | C! | S?~ …`) | "TE-08 (priority M) is unverified off this host". |
| F12 | NIT | C2 | §4 (4) "no `-p` append because no `--task` is given [ev:clawteam-spawn-platform#F5][ev:clawteam-probe-log#F12]" | Neither finding states the conditional; F12 shows the generic branch *does* append `-p prompt`. The conditional lives in `commands.py:3251-3252` (`prompt = None; if task:`) and `adapters.py:131` (`elif prompt:`), quoted in judge-2 §5 item 2 / architecture-options §3 (b). | ClawTeam/clawteam/cli/commands.py:3251-3255; clawteam/spawn/adapters.py:131-140 (verified read-only) | Cite those lines (or [panel:judge-2.md#5] item 2) instead of F5/F12. |
| F13 | NIT | C12 | §3 injection table, "permissions" row | Definition intent `permissions {filesystem: read-only, network: deny, shell: allow}` is rendered for Claude as `--allowedTools Read,Grep,Glob,Bash(git diff*)` (shell narrowed to one command) and for Codex as `-s read-only -a never` (shell allowed, FS read-only). Two renderings of one intent differ in shell scope; "(illustrative)" covers only the Claude cell. | §3 "Definition under test" vs table | Say which shell scope is the intent and render both cells to it. |
| F14 | NIT | C2 | §4 (5) "a run-scoped `CLAWTEAM_BIN` shim refuses raw `clawteam spawn` from Members" | `CLAWTEAM_BIN` is honoured only by ClawTeam's own rendered prompt text; a Member whose coordination section is rendered by the layer (Q10 = yes) may call `clawteam` from PATH. Judge-2 wrote "`CLAWTEAM_BIN`/PATH shim". | [ev:clawteam-probe-log#F12] (env `BIN` injected; prompt references it); evidence/panel/judge-2.md §5 item 3 | "PATH-shadowing `clawteam` shim + `CLAWTEAM_BIN`". |

No BLOCKER: no claim contradicts the evidence file it cites; the ATM-demotion list is honoured (no TeamDefinition/ProjectDefinition/RoleDefinition/ProjectRoleContext/A2A/desired-state/topic semantics; ATM appears only as practices K12/R4/R6/R11 "kept as practice not code"); no requirement ID outside the register is used; the answer paragraph/table are identical to `architecture-options.md` §5; the document ends with STOP and contains no code, schedule or implementation tasks.

## 3. Citation spot-check log

| Citation (as used) | Claim in the plan | Result |
|---|---|---|
| [ev:clawteam-probe-log#F1] | ClawTeam 0.3.0 on uv CPython 3.11, `mcp<2`, `clawteam-mcp` broken | OK |
| [ev:clawteam-probe-log#F3] | `CLAWTEAM_DATA_DIR`, `default_backend subprocess env` | OK |
| [ev:clawteam-probe-log#F7] | `--blocked-by` not validated; dependents auto-unblock | OK |
| [ev:clawteam-probe-log#F9] | no membership check; stray inbox dirs; events mirror | OK (used against F1 above) |
| [ev:clawteam-probe-log#F10] | `team status`/`board show` list all members, no liveness | OK |
| [ev:clawteam-probe-log#F12] | subprocess runs any executable; DEVNULL; `-p prompt` generic branch | OK; conditional `-p` not stated there (F12 NIT) |
| [ev:clawteam-probe-log#F13] | registry pid liveness; dead entries persist | OK |
| [ev:clawteam-probe-log#F14] | on-exit after clean exit: reset + "exited unexpectedly" + `exit_code: null` | OK |
| [ev:clawteam-probe-log#F15] | subprocess viable without tmux; `launch` lies | OK |
| [ev:clawteam-probe-log#F16] | per-Member command by TOML; registry `cmd0` per agent | OK |
| [ev:clawteam-probe-log#F18] | spawned child becomes leader; no parent link | OK |
| [ev:clawteam-probe-log#F19] | cross-team send/wait works from anywhere; no boundary | OK |
| [ev:clawteam-probe-log#F20] | cleanup deletes data, not processes; orphan recreates dirs | OK |
| [ev:clawteam-probe-log#F22] | `--repo` worktree per Member; branch scheme | OK |
| [ev:clawteam-probe-log#F25] | win32 branches: msvcrt, ctypes, `cmd &`, `os.getuid`, CI matrix | OK |
| [ev:clawteam-probe-log] open q3 | `task update --metadata` carrier | Evidence only *hypothesised* it; source shows no CLI flag (F2 MAJOR) |
| [ev:clawteam-model#F2] | `config.json` always `~/.clawteam/config.json` | OK |
| [ev:clawteam-model#F5] | spawn-team leader from caller env; first spawn = leader | OK |
| [ev:clawteam-model#F8] | `task wait` default inbox = leader's; `--agent` overrides | OK |
| [ev:clawteam-model#F16] | Lead behaviour = Skill + template text | OK |
| [ev:clawteam-model#F17] | plan round-trip | OK |
| [ev:clawteam-model#F22] | nested walk-through steps 7, 9, 12 | OK |
| [ev:clawteam-spawn-platform#F1] | codex positional prompt (ClawTeam's path) | OK as a fact; misapplied in §4 falsification (F4 MINOR) |
| [ev:clawteam-spawn-platform#F5] | explicit command suppresses implicit profile | OK |
| [ev:clawteam-spawn-platform#F16] | no hook/gate on CLI spawn path | OK |
| [ev:clawteam-spawn-platform#F20] | OS matrix; `os.getuid` under `skip_permissions`; no Windows CI; macOS CI | OK (macOS "unit tests only" is at file line 255) |
| [ev:clawteam-spawn-platform#F21] | worker output not logged | OK |
| [ev:harness-cli-capabilities-a#F2] | `--append-system-prompt-file` in docs/binary not `--help`; Codex `-c developer_instructions` observed only | OK |
| [ev:harness-cli-capabilities-a#F10] | `--output-format json`, `--json-schema`, `total_cost_usd`, `--max-budget-usd`; Codex tokens only | OK |
| [ev:harness-cli-capabilities-a#F14] | Claude macOS 13+/Windows 10 1809+; Codex native Windows sandbox | OK |
| [ev:harness-cli-capabilities-a#F15] | `--bare` never reads OAuth; API key for automation | OK |
| [ev:harness-cli-capabilities-a#F17] | injection matrix; `--add-dir` skills; AGENTS.md fallback | OK (F5 adds "`--add-dir` loads skills also under `--bare`") |
| [ev:harness-cli-capabilities-a#F19] | `--bare`, `--no-session-persistence`, `CLAUDE_CONFIG_DIR`, `--ephemeral`, `--ignore-user-config`, `CODEX_HOME` | OK |
| [ev:harness-cli-capabilities-b#F6] | Hermes `chat --source tool -q`; `-p` profile | OK |
| [ev:harness-cli-capabilities-b#F7] | `-z --usage-file` | OK |
| [ev:harness-cli-capabilities-b#F19] | profile clone = isolation unit | OK |
| [ev:harness-cli-capabilities-b#F22] | Hermes macOS/Windows | OK |
| [ev:claude-agent-teams-hermes-openbot#F30] | Hermes native Windows | OK |
| [ev:atm-salvage#F19], #F20, #F24 | AT-13 byte-identical precedent; fail-closed guard; U2 0/2 | OK |
| [ev:clawteam-openclaw-fork-delta#F19], #F28, #F30 | `platform_compat.py`, standalone modules, MIT HKUDS | OK |
| [panel:judge-1.md#5], [panel:judge-2.md#5], [panel:judge-2.md#7] | registry `backend: subprocess`+pid; shim/two rosters; no-op tier | OK (sections exist, content matches) |
| [fitgap:HB-02], [fitgap:TE-08], [fitgap:MS-01], [fitgap:TC-04], [fitgap:XC-02] | cells exist | OK (HB-02 CX = `C?~`, TE-08 CT = `Xs!`) |
| ClawTeam/clawteam/cli/commands.py:3251-3255, spawn/adapters.py:131-140 | `prompt=None` unless `task`; `-p` only `elif prompt` | Verified read-only (supports the plan) |
| ClawTeam/clawteam/cli/commands.py:3107 | `--keepalive/--no-keepalive` exists | Verified |

Counted: 45 citations checked; 2 failed/weak (task-metadata carrier; spawn-platform open q1 misattribution).

## 4. Coverage map (brief items relevant to this document)

| Brief item | Status | Note |
|---|---|---|
| 1 portable Assistant definition; lifecycle; definition unchanged | covered | `defhash` + `git status` assertion; bundles are copies |
| 2 Assistant ≠ Skill | covered (implicit) | `code-reviewer` = persona + principles + vendored SKILL.md + permissions + policy |
| 3 Assistant ≠ harness (select/fallback/ensemble/synthesize) | covered | Runs 1–3, `decided_by`, Ensemble record, synthesis; fallback only as `degraded[]`/stop rows |
| 4 TeamTemplate | covered | `development` template; dynamic-member policy; independence declared `advisory` |
| 5 TeamRun fresh instances/context | covered | `run.json`, fresh `--bare`/`--ephemeral`/cloned profile |
| 6 persistent + hidden temporary members | covered | `testgap`, two rosters, reconstruction test |
| 7 nested dynamic teams | covered (with F1/F2 defects) | PoC C |
| 8 long-running operational Assistants | deferred, stated | out of PoC scope per answer |
| 9 reviewed evolution | partial | only EV-04 leak check; resolver in slice but unexercised (F9) |
| 10 artifact portability | partial | one vendored SKILL.md; manifest/lock/report not checked (not required by §4) |
| 11 messaging optional | covered | no Telegram/OpenClaw; `[fitgap:MS-01]` |
| 12–16 (study ClawTeam/fork/kit; behavioural refs; ladder+licence; ATM demotion; fit-gap) | n/a here (owned elsewhere) | plan cites rungs/licence for vendored modules; ATM only as practices |
| 17 minimal PoCs A/B/C, no Telegram/OpenClaw | covered | |
| 18 cross-platform, tmux not the only path | covered | §6 matrix + precondition (d); honesty "not probed" |
| 19 STOP / no production code | covered | final STOP line; no code |

## 5. What must change before the owner's review

1. Rewrite PoC C criterion 1 so that ClawTeam's own `on-exit`/`idle` lifecycle notices (inner Members → `codemod` as inner ClawTeam leader; `codemod` → `ops-lite` events) do not fail the isolation check; the plan accepts this noise in §4 and must not penalise it in §5.
2. Remove or replace the `clawteam task update … --metadata` RunResult carrier: the CLI has no such option (commands.py:2180-2191); metadata is library/MCP-only, both excluded; update criterion 2, the §7 row and the §1 table, and notify the owners of `team-execution-model.md` §6 and `architecture-options.md` §3.
3. Tag the "register `backend: subprocess` + pid" fallback as a seam-contract exception (it writes `spawn_registry.json`) or drop it.
4. Fix the misattributed open question in §4's falsification rule; make the Q-number scheme resolvable; state explicitly the rule adopted for harness-broker-model §13 Q4 and team-execution-model §13 Q4.
5. Disambiguate PoC B mechanics: who sets the Lead's identity before `spawn-team`; spawn-all vs spawn-on-unblock; per-Member permission rendering (the reviewer's read-only flags cannot be "as in §3" for Lead/implementer); and in PoC C variant (ii) which data dir the carriers and the wait use.
6. Correct the §1 over-claim that PoC A exercises the overlay resolver, or add an informational overlay check; tidy the NITs (TE-08 "M" wording, F12 citation, permission rendering consistency, PATH-shadowing shim).
