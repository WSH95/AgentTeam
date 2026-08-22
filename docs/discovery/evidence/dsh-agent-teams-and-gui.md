---
id: ev:dsh-teams-gui
topic: dsh-agent-teams (in-session team runtime) and dsh-agent-team-gui (persistent definitions + bounded DAG runs) — layer solved, borrowable mechanisms, host coupling
systems: [dsh-agent-teams, dsh-agent-team-gui, DeepSeek Harness (DSH)]
sources:
  - {kind: repo, ref: dsh-agent-teams@801954dd7be67213cf4adc1aeb6f97bd3daa12cc, accessed: 2026-08-22, version: 0.1.8}
  - {kind: repo, ref: dsh-agent-team-gui@3b56aa4dbe20cc128d710928d20c80404ec7fff6, accessed: 2026-08-22, version: 1.0.0}
  - {kind: web, ref: https://github.com/deepseek-ai/deepseek-harness, accessed: 2026-08-22, version: developer preview (no version on README)}
  - {kind: cli, ref: "git log / grep / find / test -d (see §6)", accessed: 2026-08-22}
method: Full read of both `src/` trees (all teams modules; gui types/spec/index/orchestration/dispatch/recipes/run-history/storage-transaction/usage-meter plus key slices of definition/execution services), PLAN.md, docs/v0.5-*.md, READMEs, CHANGELOG, example recipe, verification scripts, CI workflows, LICENSE; negative greps; one WebFetch of the DSH repo page. No code executed; DSH not installed here.
platform: {os: Ubuntu (Linux 5.15), tmux: absent, cli_versions: {dsh: "not installed", node: "24 (present)", pnpm: "present"}}
author_agent: ev:dsh-teams-gui
date: 2026-08-22
confidence: high
status: draft
---
# dsh-agent-teams and dsh-agent-team-gui — layers solved, borrowable mechanisms, host coupling

## 1. Scope & questions

- (a) dsh-agent-teams: team model, on-disk format, member spawning (`memberProvider`, `memberMaxDepth`, `maxMembers`), per-member provider/model, the 10 tools, scheduler (atomic claim, `attempt_id` takeover, cold recovery), continuable members, activity panel → TC-05, TE-03, TE-04, TE-06, TE-07, LO-04; negatives: external harness, nested teams, persistent member definitions.
- (b) dsh-agent-team-gui: persistent reusable definitions (schema), Team/Solo/Inherited, Always/Smart/Manual, planner → validated acyclic plan → DAG waves → bounded handoffs → quality gate, stored plans/retry, recursion guards, usage meter coverage, versions/recipes, credential-free export/import → AD-01, AD-04, AD-08, TC-01, TC-02, TC-05, TE-01, TE-02, TE-06, TE-07, HB-03, HB-04, HB-07, AR-04; negatives: EV-*, MS-*.
- (c) Relationship between the two and host coupling (could either run outside DSH?) → XC-03, HB-08.
- (d) Licenses and activity → XC-01, XC-02.

## 2. Findings

### A. dsh-agent-teams (NanmiCoder, `@nanmicoder/dsh-agent-teams` 0.1.8)

### F1. It is a DSH (DeepSeek Harness) host-plane plugin composed via cordis; no other host
- Claim: The plugin is a function-form cordis plugin (`export const name = 'agent-teams'`, `inject = ['tools','llm','subagents','systemPrompt','agents']`) mounted by a bundle patch; every runtime capability (subagents, tools, system prompt, web routes) is a DSH service.
- Evidence: dsh-agent-teams/src/index.ts:55-56, 107-157; dsh-agent-teams/cordis.patch.yml:10-21; dsh-agent-teams/package.json `peerDependencies` `@deepseek-ai/cordis ^4.0.1-rc.1`, `@deepseek-ai/dsh-subagent ^0.1.0-rc.6` etc. Install: `dsh plugin --profile web add @nanmicoder/dsh-agent-teams` (README.md:44).
- Level: observed
- Requirements: HB-08, XC-03
- Suggested fit cell: dsh-agent-teams → n/a (no harness adapter concept)

### F2. On-disk team format: `<workspace>/.agent-teams/<teamId>/{team.json, inbox/*.jsonl}` plus `retired-members.json` and `archive/`
- Claim: `TeamState` = `{name, id, description?, captainSessionId, createdAt, members: TeamMember[], tasks: TeamTask[], taskSeq}`; `TeamMember` = `{id (child session id), name, role?, provider?, model?, reasoningEffort?, joinedAt, status: idle|working|removed}`; `TeamTask` = `{id 't1'…, subject, description?, status, assignee?, dependencies[], output?, attempt?, attemptId?, handoffId?, reassigning?, createdAt, updatedAt}`. Mailboxes are one JSONL file per agent key (`captain` or sanitized member name); writes are same-directory temp + rename with Windows EPERM retry/direct-write fallback; deleting a team **moves** the directory to `<stateRoot>/archive/<teamId>/`.
- Evidence: dsh-agent-teams/src/types.ts:24-104; src/state.ts:1-14 (layout), :170-175 (`createTeamDir`), :346-365 (`appendMailbox`), :509-615 (`replaceFileAtomicOrDirect`, `atomicWriteText`), :761-802 (`archiveTeamDir`), :26-27 (`retired-members.json`); docs/usage.md:32-42.
- Level: observed
- Requirements: TE-06, TE-07
- Suggested fit cell: dsh-agent-teams → S~ (run archive exists; format is per-workspace, not per-definition)

### F3. Captain = the calling session; exactly one active team per captain; captain implicit
- Claim: `agent_teams_create` makes `exec.agent` the captain; a session that already leads or belongs to a team cannot create another; `findTeamByCaptain`/`findTeamByParticipant` throw if a session appears in >1 active team.
- Evidence: dsh-agent-teams/src/tools.ts:251-289; src/state.ts:270-296, 305-332; README.md:124 "One captain leads one active team at a time".
- Level: observed
- Requirements: TE-05 (negative), TC-02
- Suggested fit cell: dsh-agent-teams → M! for nesting (see F14)

### F4. Members are durable continuable subagents spawned with persona, tool deny-list, depth cap and size cap
- Claim: `spawnMember` requires a `ctx.subagents` provider named by config `memberProvider` (default `spawn`; `fork` allowed) that supports `prepareContinuable`, `capabilities.persona` and `capabilities.toolFilter`, then calls `ctx.subagents.startContinuable({provider, label:'agent-teams:<teamId>:<name>', request:{prompt, parent: captain, persona, toolFilter:{deny: MEMBER_DENIED_TOOLS}, agentOptions:{provider, model}, maxDepth}})`. `MEMBER_DENIED_TOOLS` = create/add_member/remove_member/reassign_task/create_task/delete. Config: `memberMaxDepth` default 1 (0 forbids delegation), `maxMembers` default 8, `memberModel` optional.
- Evidence: dsh-agent-teams/src/members.ts:25-33, 304-354; src/index.ts:58-91; src/tools.ts:336-338 (cap enforced).
- Level: observed
- Requirements: TC-05, TE-04, AD-07
- Suggested fit cell: dsh-agent-teams → C! (count/depth via config; "who may add" = captain only via tool deny); no hidden/visible flag → Xs~ for AD-07 visibility

### F5. Heterogeneous LLM provider/model per member, snapshotted into team.json and restored on cold resume
- Claim: `agent_teams_add_member` accepts optional `provider`, `model`, `reasoning_effort`; resolution order is explicit member `provider+model` → config `memberModel` → captain's current route; reasoning effort is inherited only on the same route, else the target model default; the resolved triple is persisted in `TeamMember` and re-applied by `registerContinuableSetup` when a child is cold-resumed (label prefix `agent-teams:` + `readTeamSync`). It is a *model route*, not a harness: all members are DSH in-process subagents.
- Evidence: dsh-agent-teams/src/members.ts:124-185 (`resolveMemberLlmSelection`), :194-233 (`installMemberSelectionRuntime`), :53-61; src/tools.ts:293-301; docs/usage.md:75; README.md:118 "`memberProvider` is the sub-agent runtime backend (`spawn` / `fork`), not an LLM provider".
- Level: observed
- Requirements: TE-03, HB-07
- Suggested fit cell: dsh-agent-teams → S! for model heterogeneity, M~ for harness heterogeneity

### F6. The ten tools and their parameters
| Tool | Parameters (required*) | Who |
|---|---|---|
| `agent_teams_create` | `name*`, `description` | any session → becomes captain |
| `agent_teams_add_member` | `name*`, `role`, `provider`, `model`, `reasoning_effort` | captain |
| `agent_teams_remove_member` | `name*` | captain |
| `agent_teams_create_task` | `subject*`, `description`, `dependencies[]`, `assignee` | captain |
| `agent_teams_reassign_task` | `task_id*`, `assignee*` (member or `"captain"`), `reason` | captain |
| `agent_teams_claim_task` | `task_id*`, `assignee` (captain only) | captain or member |
| `agent_teams_update_task` | `task_id*`, `status` ∈ {in_progress, completed, failed, cancelled}, `output`, `attempt_id` | captain or member |
| `agent_teams_send_message` | `to*` (`captain` or member), `content*`, `from` (must equal caller) | captain or member |
| `agent_teams_status` | — | captain sees all mailboxes; member sees own |
| `agent_teams_delete` | — | captain; archives, not deletes |
- Evidence: dsh-agent-teams/src/tools.ts:229-1099 (each `defineTool`); src/index.ts:122-133.
- Level: observed
- Requirements: TE-06, TE-04
- Suggested fit cell: dsh-agent-teams → S!

### F7. Task state machine and attempt capabilities
- Claim: `TASK_TRANSITIONS`: pending→{claimed,cancelled}; claimed→{in_progress,failed,cancelled}; in_progress→{completed,failed,cancelled}; terminal states immutable. `beginTaskAttempt` increments `attempt` and mints a random `attemptId`; `invalidateTaskAttempt` clears `attemptId`, sets `handoffId`, returns the task to `pending` (optionally `reassigning=true`). Members must present the current `attempt_id` on update; a stale id is rejected ("stop work and request fresh assignment"). A member may not own two open tasks; claims are refused while dependencies are unfinished.
- Evidence: dsh-agent-teams/src/state.ts:105-163; src/tools.ts:702-716, 777-783; src/types.ts:38-45.
- Level: observed
- Requirements: TE-06
- Suggested fit cell: dsh-agent-teams → S!

### F8. Scheduler: event-driven atomic claim with mailbox-first flush and rollback; "cold recovery" = re-dispatch of an owned open task
- Claim: `installTeamScheduler` listens on `agent/status`; when a member turns idle it (1) flushes unread durable mailbox messages first (delivery lease `deliveryClaimedAt`, 60 s), (2) inside the per-team lock picks `ownedOpenTask ?? nextReadyTask` (assigned-to-me first, then unassigned pool), begins a fresh attempt, marks member `working`, writes team.json, (3) delivers an assignment prompt via `ctx.subagents.followup`; if delivery fails it rolls back only when `task.attemptId === ticket.attemptId`. An idle/ready member that still owns a `claimed/in_progress` task after an interrupted turn or process restart is retried with a fresh capability. Limit: no captain live → no kicks (README "队长离线时无法冷恢复成员").
- Evidence: dsh-agent-teams/src/scheduler.ts:66-82, 137-236 (`kickMember`), :239-262 (`syncMemberStatus` + `ctx.on('agent/status')`), :179-183 comment; docs/usage.md:79, 83; README.md:75.
- Level: observed (scripts/lifecycle-verify.mjs and stress-verify.mjs exercise it — "8 成员、31 节点多层 DAG … 4 个开放任务冷重启", docs/usage.md:93; not run here)
- Requirements: TE-06, LO-04
- Suggested fit cell: dsh-agent-teams → S!

### F9. Reassignment/takeover protocol is three-phase and race-checked
- Claim: `agent_teams_reassign_task`: phase 1 (locked) invalidate old attempt with `reassigning=true`; phase 2 (unlocked) `interruptMember` + `waitForMemberIdle`; phase 3 (locked) verify `handoffId`/`assignee`/`reassigning` unchanged else "changed during reassignment; refusing to overwrite", then for `captain` begin a captain attempt. Captain cannot update member-owned work without takeover (`update_task` guard).
- Evidence: dsh-agent-teams/src/tools.ts:536-636, 772-776.
- Level: observed
- Requirements: TE-06, LO-04
- Suggested fit cell: dsh-agent-teams → S!

### F10. Messaging: durable JSONL mailbox first, then best-effort live delivery; no relay; no impersonation
- Claim: `send_message` appends to the recipient mailbox, then if the captain agent is live: member→captain uses `captain.steer(...)` ("delivered: live"), anyone→member uses `followup` ("wake"); otherwise "mailbox" and the scheduler retries later. `from` must equal the caller identity. Messages carry `deliveryClaimedAt/deliveredAt/readAt`.
- Evidence: dsh-agent-teams/src/tools.ts:827-937, 206-217 (`steerCaptainReport`); src/state.ts:411-501; src/types.ts:71-86.
- Level: observed
- Requirements: TE-06
- Suggested fit cell: dsh-agent-teams → S!

### F11. Audit trail: seven `agent-teams/*` session events (conditionally emitted), archive directory, retired-member deny-list
- Claim: Event types `team-created, member-added, member-removed, task-created, task-updated, message-sent, team-deleted` are appended to the captain's Session **only if** the harness's `KNOWN_SESSION_EVENT_TYPES` contains them; otherwise silently omitted ("Disk state remains the authoritative source"). `agent_teams_delete` retires every member id into `retired-members.json` (guards `listChildren/listDescendants/followup`, error `NOT_RESUMABLE`) and archives the directory.
- Evidence: dsh-agent-teams/src/event-types.ts:113-121; src/events.ts:39-54; src/members.ts:426-467; src/tools.ts:1057-1098.
- Level: observed
- Requirements: TE-07, XC-04
- Suggested fit cell: dsh-agent-teams → S~ (archive yes; event audit depends on host)

### F12. Activity panel: server snapshot route + 1 s polling; disk truth enriched with live activity; archived view
- Claim: Host registers `GET /plugins/dsh-agent-teams/state` (`?archived=1` for archived teams) and an allow-listed artwork route; the browser floater polls; snapshot = team.json + `listChildren` + `ctx.agents` status (`running|idle|ready`), task `depth` lanes and visual states `blocked|open|running|completed`. Panel shows only teams whose `captainSessionId` is the current session.
- Evidence: dsh-agent-teams/src/index.ts:164-248; src/snapshot.ts:21-117; src/state.ts:835-882; docs/usage.md:20, 26-30.
- Level: observed
- Requirements: TE-06, MS-01
- Suggested fit cell: dsh-agent-teams → S! (local UI only; DSH Web profile)

### F13. Activation is deterministic: system-prompt section (order 117) + `/agent-teams` command + gesture boundary
- Claim: The captain protocol (7 numbered steps) is injected as system-prompt section `agent-teams:usage`; `/agent-teams <goal>` is a host command whose handler queues a follow-up user message (never reaches the model as slash text); an `agent/pre-step` listener recognizes a leading `/agent-teams` token only in `source.kind === 'user'` messages.
- Evidence: dsh-agent-teams/src/index.ts:93-105, 134-138, 152-157; src/command.ts:54, 99-148.
- Level: observed
- Requirements: TE-01
- Suggested fit cell: dsh-agent-teams → S! (within DSH)

### F14. Negative: no nested teams, no team-of-teams API
- Claim: Members are denied `agent_teams_create` (F4); a captain already in a team cannot create another (F3); `memberMaxDepth` only caps ordinary subagent delegation below a member. No parent-team field in `TeamState`.
- Evidence: grep `nested|sub-team|subteam` src → 0; `parent` only as `parentSession` (src/members.ts:205-217); src/types.ts:88-104 has no parent/child-team field.
- Level: observed
- Requirements: TE-05
- Suggested fit cell: dsh-agent-teams → M!

### F15. Negative: no persistent reusable member/team definitions
- Claim: `role` is a free-form string captured at `add_member`; persona text is generated (`memberPersona`) from name/role/team; nothing is stored outside the run directory; no template/definition types.
- Evidence: dsh-agent-teams/src/members.ts:264-281; grep `definition|template|reusable` src → comments only (§6).
- Level: observed
- Requirements: AD-01, AD-08, TC-01
- Suggested fit cell: dsh-agent-teams → M!

### F16. Negative: no external harness, no process spawning, no messaging surface
- Claim: No `child_process`, no Claude Code/Codex/tmux/Telegram code; "Claude Code" appears only in comments describing the mirrored mailbox layout.
- Evidence: grep results §6; src/members.ts:373-390 uses `ctx.subagents.followup` only.
- Level: observed
- Requirements: TE-03, HB-01, MS-02
- Suggested fit cell: dsh-agent-teams → M! (harness brokerage), n/a (surfaces)

### B. dsh-agent-team-gui (toolclub, `dsh-agent-team-gui` 1.0.0)

### F17. Web-profile DSH Service plugin with storage-domain persistence and a loopback RPC channel
- Claim: `AgentTeamService extends ExecutionApplicationService` (class form), `static inject = ['storageDomain','tools','subagents','llm','agents','sessions','systemPrompt']`; opens storage domain `agent_team_gui` v0; registers `dispatch_to_squad`, system-prompt section `agent-team:squad-mode` (order 118), an `agent/pre-step` hook and RPC channel `/agent-team-gui`. Declared compatibility DSH `>=0.1.0-rc.5 <0.2.0`, "Web profile only; there is no headless Settings UI".
- Evidence: dsh-agent-team-gui/src/index.ts:33-79; src/rpc.ts:13; README.md:33-36, 334-335; package.json `peerDependencies`.
- Level: observed
- Requirements: HB-08, XC-03
- Suggested fit cell: dsh-agent-team-gui → n/a (harness adapter), P~ (could host a UI layer only inside DSH)

### F18. Persistent, reusable definitions: `AgentRecord` and `SquadRecord` (exact schema)
- Claim: `AgentRecord {name, systemPrompt, provider, model, maxTokens?, toolScope?{allow?,deny?}, fallbackProvider?, fallbackModel?}` ("Model routes contain no credential material"). `SquadRecord {name, members: AgentId[], collabNote?, executionOrder?, executionMode? serial|parallel, contextMode? spawn|fork|chain, leaderAgentId?, triggerMode? guaranteed|model-tool, failurePolicy? continue|stop|retry-once, maxConcurrency?, memberTimeoutMs?, tokenBudget?, activationMode? always|smart|manual, memberSelectionMode? all|adaptive, responseMode? foreground|background, planningContext? current|recent|full, plannerMaxTokens?, qualityGate?{reviewerAgentId, repairAgentId, maxRounds 0|1|2, criteria?}}`. Write bounds: name ≤120, systemPrompt ≤50 000, members 1..32, maxConcurrency ≤32, memberTimeoutMs 1 000..3 600 000, plannerMaxTokens 256..8 192. "One agent may appear in several squads."
- Evidence: dsh-agent-team-gui/src/types.ts:35-91; src/spec.ts:29-103; Settings views "Teams / Member library / Recipes & data" (src/client/i18n.ts:68).
- Level: observed
- Requirements: AD-01, AD-02, AD-04, AD-08, TC-01, TC-02, TC-06
- Suggested fit cell: dsh-agent-team-gui → S! (AD-08, TC-01), C~ (AD-01: persona/principles/preferences are one `systemPrompt` string), Xs~ (AD-04: model route + fallback, no harness)

### F19. Eight storage tables; versions snapshot member definitions; recipes are credential-free
- Claim: Domain tables `agents, squads, session_modes, next_modes, message_claims, runs, squad_versions, project_defaults`. `SquadVersionRecord {squadId, version, createdAt, record, memberSnapshots?: {id, record}[]}`; restore is preview-first. Recipe document `{format:'agent-team-gui/recipe', version:1, exportedAt, squad: SquadExportItem, agents: AgentExportItem[]}`; `prepareRecipe` rejects duplicates/missing/extra agents, `findMissingRecipeRoutes` validates primary and fallback routes via `ctx.llm`, `copyRecipeIds` mints a closed identity graph; URL fetch deliberately not implemented (`snapshot.capabilities.remoteRecipeFetch` always false). Example recipe uses placeholders `your-provider/your-model`.
- Evidence: dsh-agent-team-gui/src/spec.ts:348-363; src/types.ts:309-323, 405-452; src/tools/recipes.ts:10-122; docs/v0.5-product-spec.md:143-157, 182-183; examples/full-stack-delivery.recipe.json.
- Level: observed
- Requirements: AR-03, AR-04, AD-08, EV-05 (versioning, not review)
- Suggested fit cell: dsh-agent-team-gui → S! (AR-04), C~ (AR-03: routes only, no artifact/skill sources)

### F20. Export/import: versioned document, merge|replace, impact preview, strict schemas reject credential-like fields, compensating rollback
- Claim: `AgentTeamExportDocument {format:'agent-team-gui/definitions', version: 1|2, agents[], squads[]}`; `AgentTeamImportPreview {definitionRevision, mode, incoming, conflicts, affectedSquads[{squadId, squadName, agentIds}], deletions{agents, squads, sessionModes, nextModes, projectDefaults, squadVersions}}`. All record schemas are zod `.strict()`, so an `apiKey` field fails validation (test "rejects credential-like extra fields"). Multi-table writes use `StorageUnitOfWork` (snapshot participating tables, restore in reverse on failure) because storage-domain "exposes atomic single-key updates but no multi-table transaction".
- Evidence: dsh-agent-team-gui/src/types.ts:368-403; src/spec.ts:133-152; tests/v05-host.spec.ts:455-471; src/tools/storage-transaction.ts:1-42; src/tools/application/definition-service.ts:735-749.
- Level: observed
- Requirements: AR-04, AD-08, XC-04
- Suggested fit cell: dsh-agent-team-gui → S!

### F21. Conversation modes: Team / Solo / Inherited (durable), one-shot next-message, project default; idempotent message claims
- Claim: `SessionSquadModeRecord {squadId?, disabled?}` (explicit Team or explicit Solo), absence = Inherited → `ProjectSquadDefaultRecord {projectKey = session.header.cwd, squadId, enabled}`; `SessionNextSquadModeRecord {state: solo|team, squadId?, claimedMessageId?, claimedAt?}` consumed exactly once; `SquadMessageClaimRecord` binds one dispatch to one top-level user message (`claimGuaranteedMessage`), so repeated tool calls cannot start duplicate teams. The `agent/pre-step` hook runs the squad before the lead model in `guaranteed` mode.
- Evidence: dsh-agent-team-gui/src/types.ts:93-122, 325-330; src/index.ts:81-165; src/tools/application/definition-service.ts:609-665; docs/v0.5-product-spec.md:159-169.
- Level: observed
- Requirements: TE-01, TE-02
- Suggested fit cell: dsh-agent-team-gui → S! (fresh run per message; workspace = session cwd)

### F22. Planning: `always|smart|manual` × `all|adaptive`; planner is a tool-free, depth-1, schema-constrained child; validated acyclic plan; deterministic fallback
- Claim: `SquadExecutionPlan {decision run|skip, reason, summary, memberOrder[], assignments[{agentId, task, dependsOn[]}], planner: main-agent|squad-leader|deterministic-fallback, plannerProvider?, plannerModel?, usage?, warning?}`. `validateExecutionPlan` enforces: members ⊆ squad, unique, non-empty tasks, ≤32 nodes, `dependsOn` ⊆ selected, no self-dependency, `memberOrder` is a complete permutation consistent with dependencies, then Kahn topological order else "plan dependencies contain a cycle". Planner children get `maxDepth: 1`, no delegation tools, structured output. Fixed `executionOrder` bypasses planning. `deterministicExecutionPlan` assigns role-scoped tasks (serial chain or parallel).
- Evidence: dsh-agent-team-gui/src/types.ts:188-202; src/tools/orchestration.ts:17-139; src/tools/application/execution-service.ts:737-790; docs/v0.5-product-spec.md:52-95.
- Level: observed
- Requirements: TC-02, TE-06
- Suggested fit cell: dsh-agent-team-gui → S!

### F23. Execution: dependency waves up to `maxConcurrency`, soft token budget, failure policy, retry-once with fallback route, per-attempt timeout
- Claim: `executionWaves` groups ready nodes; `concurrency = parallel ? min(maxConcurrency ?? n, n) : 1`; before each batch the run halts on abort or `used.totalTokens >= tokenBudget`; `failurePolicy 'stop'` skips dependants of failed nodes and halts; `retry-once` reruns a failed member once, on `fallbackProvider/fallbackModel` if set, recording `attempts: 2` and both attempts' route/usage (`attemptUsage`, max 2). `memberTimeoutMs` aborts via `AbortSignal.any`. Provider `fork` only when `contextMode === 'fork'`.
- Evidence: dsh-agent-team-gui/src/tools/orchestration.ts:142-156; src/tools/application/execution-service.ts:1228-1275, 645-660, 448-451, 503; src/types.ts:283-291.
- Level: observed
- Requirements: TE-06, HB-04 (model-route fallback), HB-07
- Suggested fit cell: dsh-agent-team-gui → S! (HB-04 at model level; M~ at harness level)

### F24. Bounded handoffs between members and to the lead; full output stays durable
- Claim: `SquadMemberHandoff {summary ≤4 000, deliverables ≤12×1 000, risks ≤12×1 000, changedFiles ≤50×1 000}` via `normalizeHandoff`; a dependant receives `JSON.stringify(dependencyHandoffs).slice(0, 12_000)` as `chainText`; the lead model's tool result is a bounded render (task ≤1 000, error ≤2 000, handoff lists ≤8/≤20) with the note "Full member outputs are persisted in Run Center and intentionally omitted here".
- Evidence: dsh-agent-team-gui/src/tools/orchestration.ts:159-173; src/tools/application/execution-service.ts:1253-1255; src/tools/dispatch-to-squad.ts:94-177; docs/v0.5-product-spec.md:14-16.
- Level: observed
- Requirements: TC-02 (handoff conventions), TE-07
- Suggested fit cell: dsh-agent-team-gui → S!

### F25. Quality gate: named reviewer + repair owner, ≤2 rounds, structured verdict, reviewer has zero tools
- Claim: Reviewer child runs with `toolFilter: { allow: [] }`, `maxDepth: 1`, output schema `{approved: boolean, feedback: string}`; on rejection only `repairAgentId` reruns with the feedback, then reviewer again; `maxRounds ∈ {0,1,2}`; `qualityProgress {round, maxRepairRounds, totalReviews ≤3, state reviewing|repairing}` is persisted live; budget/abort breaks the loop.
- Evidence: dsh-agent-team-gui/src/types.ts:85-91, 250-258, 295-307; src/tools/application/execution-service.ts:847-1001; README.md:170-173.
- Level: observed
- Requirements: TC-02, TC-03 (reviewer gets fresh child; independence by construction in `spawn` mode)
- Suggested fit cell: dsh-agent-team-gui → C! (TC-03: reviewer independence only if `contextMode=spawn`; `fork` seeds parent history)

### F26. Recursion guards: delegated-lineage check, subagent-tool denial (incl. shape detection), fail-closed provider capability check
- Claim: `isDelegatedSession = header.origin === 'subagent' || header.parentSession !== undefined || (header.delegationDepth ?? 0) > 0`; `dispatch()` and `startBackgroundDispatch` throw `INVALID_DISPATCH "nested squad dispatch is blocked for delegated child sessions"`; pre-step hook and project-default inheritance skip delegated agents. `childToolScope` denies `dispatch_to_squad`, `subagent`, `workflow` when visible and additionally any tool whose compiled schema matches the official subagent shape (`description`+`prompt`[+`run_in_background`]) or workflow shape (`script`+`meta`[+`args`]); throws if a member allow-list exposes such a tool or if the provider lacks `toolFilter`/`depthLimit`; members get `maxDepth: 1`.
- Evidence: dsh-agent-team-gui/src/tools/application/definition-service.ts:636-653; src/tools/application/execution-service.ts:569-640, 1057-1059, 1400-1402, 478-481; tests/service.spec.ts:307-341; CHANGELOG.md:47-50.
- Level: observed
- Requirements: TE-05 (negative), TC-05 (negative), XC-04
- Suggested fit cell: dsh-agent-team-gui → M! (nested TeamRun is explicitly prohibited); M! (TC-05: no dynamic members — planner "may not create agents")

### F27. Durable run record with crash reconciliation, official Jobs integration, linked immutable retry replaying the stored plan
- Claim: `SquadRunRecord` status `planning|queued|running|completed|partial|failed|cancelled|interrupted|skipped`, `phase`, per-member rows with `childId`, `runId`, `stopReason`, `output`, `usage`, `attemptUsage`, `handoff`; at Service init `recoverRunHistory()` marks orphaned active runs `interrupted` and applies opt-in retention (`historyMaxRuns`, `historyMaxAgeDays`, `versionMaxPerSquad`, default 0 = keep). Background runs register a `jobs.start({kind:'agent-team', owner: parent, run})` when `ctx.jobs` exists, else process-local with a warning. `retryRun` refuses active runs and runs without a stored plan ("cannot be retried faithfully"), otherwise starts a new run with `retryOf` and `replayPlan` (usage stripped, warning appended); member-only retry replays that member's persisted assignment.
- Evidence: dsh-agent-team-gui/src/types.ts:221-293; src/tools/application/execution-service.ts:85-92, 1521-1535, 1632-1675; src/index.ts:63-67; docs/v0.5-product-spec.md:119-132.
- Level: observed
- Requirements: TE-07, HB-07, LO-04
- Suggested fit cell: dsh-agent-team-gui → S!

### F28. Usage meter: official `tokenUsage` projection, four buckets, coverage `full|partial|none`, never currency
- Claim: `OfficialUsageMeter` reads `sessionProjections.snapshot(child.session).values.tokenUsage`, subtracts a fork-seed baseline, returns `undefined` (not zero) until a provider reports; `AgentTokenUsage {uncachedInputTokens, outputTokens, cacheReadTokens, cacheWriteTokens, totalTokens, providerReported}`; `runMeteringCoverage` compares expected samples (planner, each member attempt, review, repair) with metered ones; Insights aggregates by squad/agent/model/project. "Tokens are not money."
- Evidence: dsh-agent-team-gui/src/tools/infrastructure/official-usage-meter.ts:24-115; src/tools/run-history.ts:29-66; src/types.ts:177-186, 454-485; README.md:154-165.
- Level: observed
- Requirements: HB-07
- Suggested fit cell: dsh-agent-team-gui → S! (usage only; no cost/price; DSH-only source)

### F29. `dispatch_to_squad` tool contract and squad-mode system prompt
- Claim: Parameters `squadId*` (id or case-insensitive name), `task*`, `assignments[]{agentId, task}`, `memberOrder[]`, `executionMode`, `contextMode`; `isConcurrencySafe: () => false`. The squad-mode section lists members as `id (name, provider/model)`, the fixed order or planning note, and instructs the lead to produce a six-section "structured retrospective" (what each member did, went well/not, knowledge-gap analysis, improvement recommendations, verdict). The retrospective is **conversation text only**; nothing is written back to definitions.
- Evidence: dsh-agent-team-gui/src/tools/dispatch-to-squad.ts:7-49, 181; src/tools/application/definition-service.ts:700-733; CHANGELOG.md:5-11.
- Level: observed
- Requirements: EV-03 (negative), TE-01
- Suggested fit cell: dsh-agent-team-gui → M! for EV (no proposals, no overlays; see §3)

### C. Relationship and host coupling

### F30. The two plugins are independent, parallel designs with no dependency and different authors
- Claim: gui never references `dsh-agent-teams`, `@nanmicoder`, or `agent_teams_*` (0 grep hits) and teams never references gui; authors differ (NanmiCoder/"Relakkes" vs toolclub/leizihao). Both are single-row cordis inserts over the DSH Web profile peering on `@deepseek-ai/dsh-*` 0.1.0-rc.6. Split: teams = **runtime** (one session's ephemeral team, durable continuable members, task DAG, mailboxes; nothing reusable persists); gui = **definitions + run ledger** (reusable agents/squads, bounded one-shot runs with fresh children, run history; no member-to-member messaging, no durable members).
- Evidence: §6 grep; dsh-agent-teams/package.json `author`; dsh-agent-team-gui/package.json `author`; PLAN.md:31-45 (gui design decisions); recon-appendix confirmed.
- Level: observed
- Requirements: XC-03
- Suggested fit cell: both → n/a

### F31. Neither runs outside DSH; the portable parts are pure-logic modules
- Claim: Both import `@deepseek-ai/cordis`, `dsh-subagent`, `dsh-tools`, `dsh-llm`; gui adds `dsh-storage-domain`, Connection RPC and the Web UI; teams' activity panel needs `webServer`+`workspaceRegistry` but "In a webless profile the plugin stays tool-only". Files with no DSH runtime import: teams `src/state.ts` (rules, JSONL mailbox, atomic write, archive; imports only `node:*` and `./types`), `src/types.ts`, `src/event-types.ts`; gui `src/tools/orchestration.ts`, `src/tools/recipes.ts`, `src/tools/run-history.ts` (only the `KvTable` type), `src/tools/storage-transaction.ts`, `src/types.ts`. Everything else is bound to DSH services and Session header fields (`cwd`, `parentSession`, `origin`, `delegationDepth`, `seedLength`).
- Evidence: dsh-agent-teams/src/index.ts:159-163; src/state.ts:16-20; dsh-agent-team-gui/src/tools/orchestration.ts:1; src/tools/recipes.ts:1-2; src/tools/run-history.ts:1-4; src/tools/application/definition-service.ts:650-653.
- Level: observed
- Requirements: XC-03, HB-08
- Suggested fit cell: both → M~ as substrates for a harness-neutral Core; selective module reuse (rung 4) is MIT-compatible

### F32. DeepSeek Harness itself: MIT, "developer preview", not installed here
- Claim: The DSH repo page states "Everything is a Plugin", MIT license, "THERE WILL BE COMPATIBILITY-BREAKING CHANGES", Web UI at `http://127.0.0.1:3080`, install `npx @deepseek-ai/dsh web`; no OS matrix or version on the README. `dsh` is not on this host's PATH and no harness checkout exists under `/home/wsh/Documents/00000/`.
- Evidence: https://github.com/deepseek-ai/deepseek-harness (accessed 2026-08-22); CLI `which dsh` → not found (§6).
- Level: observed (web) / verified (CLI absence)
- Requirements: XC-02, XC-01
- Suggested fit cell: DSH → ?w as a harness candidate (no HarnessProfile data gathered)

### D. Comparison table

| Aspect | dsh-agent-teams | dsh-agent-team-gui |
|---|---|---|
| Layer solved | In-session team **runtime**: captain + durable continuable members + task DAG + mailboxes + scheduler + activity panel | Persistent **definitions** (agents, squads) + bounded one-shot **DAG runs** + durable run ledger/insights + versions/recipes/backup + Web Settings/Run Center |
| Key mechanism | `startContinuable` members, `team.json` + JSONL inboxes, `attempt_id` capabilities, event-driven atomic claim, archive-on-delete | storage-domain tables, planner→`validateExecutionPlan`→`executionWaves`, bounded handoffs, quality gate, `retryOf` replay, lineage + tool-denial guards, official `tokenUsage` meter |
| File refs | src/{types,state,members,scheduler,tools,index}.ts | src/{types,spec,index}.ts, src/tools/{orchestration,recipes,run-history,dispatch-to-squad}.ts, src/tools/application/{definition,execution}-service.ts |
| Requirement IDs informed | TC-05, TE-03 (model level), TE-04, TE-06, TE-07, LO-04; negatives TE-05, AD-*, EV-*, HB-* | AD-01, AD-04, AD-08, TC-01, TC-02, TC-03, TE-01, TE-02, TE-06, TE-07, HB-04, HB-07, AR-04; negatives TE-05, TC-05, EV-*, MS-* |
| Portability outside DSH | Not runnable; `state.ts`/`types.ts` pure (file format + rules) reusable | Not runnable (Web profile only); `orchestration.ts`, `recipes.ts`, `run-history.ts`, `storage-transaction.ts`, schemas reusable |
| License / activity | MIT; 77 commits 2026-08-12→08-20; v0.1.0→v0.1.8; npm published | MIT; 21 commits 2026-08-15→08-19; v0.1.0→v1.0.0; GitHub install only |

## 3. Negative findings

- No external harness or process spawning in either repo: `grep -rn -i 'claude\|codex\|telegram\|tmux\|child_process\|execFile\|spawn(' dsh-agent-teams/src/*.ts` → comment-only hits (state.ts:7, tools.ts:6, scheduler.ts:4, snapshot.ts:4, members.ts:364, index.ts:173); same grep on `dsh-agent-team-gui/src` → 0. `grep -rli 'hermes\|openclaw\|grok'` both → none.
- No nested teams in dsh-agent-teams: `grep -rn -i 'nested\|sub-team\|subteam' src/*.ts` → 0; `TeamState` has no parent field (types.ts:88-104); members are denied `agent_teams_create` (members.ts:25-33). In gui nesting is affirmatively blocked (execution-service.ts:1057-1059) and tested (tests/service.spec.ts:333-341).
- No persistent reusable member definitions in dsh-agent-teams: `grep -rn -i 'definition\|template\|persist\|reusable' src/*.ts` → persistence comments only; no definition type, no template loader, no `~/.…` config dir.
- No evolution/learning in either: dsh-agent-teams `grep -rn -i 'learn\|evolve\|feedback\|improve' src/*.ts` → 0; gui `grep -rn -i 'learn\|evolv\|improve' src PLAN.md docs README.md` → only retrospective prompt strings (dispatch-to-squad.ts:174; definition-service.ts:724,729; execution-service.ts:278,287); `grep -rn -i 'memory\|overlay' src` → 0. The retrospective is rendered text, never written to `agents`/`squads` tables.
- No messaging surfaces (Telegram/Discord/…) in either; gui has no member-to-member messaging at all (dependants receive handoff JSON only, execution-service.ts:1253-1255).
- No cost/price model in gui ("Tokens are not money", README.md:163-165); no usage accounting at all in dsh-agent-teams (`grep -n 'usage\|cost' src/*.ts` → 0 in runtime code).
- No dependency between the two repos: `grep -rn 'dsh-agent-teams\|nanmicoder\|agent_teams_' dsh-agent-team-gui/{package.json,src,PLAN.md,docs,README.md,CHANGELOG.md}` → 0.
- No harness-selection policy or precedence (HB-03) in gui: route is per-agent `provider/model` + one `fallback*`; no user-level/role-level/default layering (types.ts:36-46; grep `precedence|policy` → only `failurePolicy`).
- No visibility flag (visible/hidden) for members in either (types.ts both; `grep -rn -i 'hidden\|visib' src` → teams: UI-only `ActivityPanel` strings; gui: none in records).

## 4. Platform & license notes

- Licenses: dsh-agent-teams/LICENSE = MIT (Copyright (c) 2026 程序员阿江(Relakkes)); dsh-agent-team-gui/LICENSE = MIT (Copyright (c) 2026 dsh-agent-team-gui contributors); DSH itself MIT per its README (web, 2026-08-22). No additional terms; no automation-flag constraints (no "dangerous"/bypass flags exist — everything is in-process).
- Node engines: teams `^22.19.0 || >=24`; gui `^22.19.0 || >=24.0.0`, README adds "Node.js 23 is not supported".
- OS: both are pure Node/TS with no `process.platform` branches in `src` (teams has one in `scripts/verify.mjs:851`). teams contains explicit Windows handling for `rename` over an open file (EPERM/EACCES/EBUSY retry then direct write; `archiveTeamDir` retry) — state.ts:509-615, 737-750 — and a merged PR "fix(state): harden Windows team.json atomic replace" (git 9cce543, 2026-08-17), i.e. Windows use was reported in the wild. gui has no platform-specific code; its durability is delegated to DSH storage backends (json/sqlite).
- CI: both `runs-on: ubuntu-latest` only (teams publish.yml Node 24; gui ci.yml matrix Node 22.19.0/24). No macOS/Windows CI.
- Runtime prerequisites: a running DSH Web profile (both; teams also works tool-only in headless profiles per index.ts:159-163); configured DSH provider/model routes; no tmux, no external CLIs. Multi-process safety: teams "concurrent processes editing the same team are not coordinated" (README.md:126).
- Both checkouts are unbuilt (`lib/` absent); gui installs via `dsh plugin --profile web add -w github:toolclub/dsh-agent-team-gui#v1.0.0` and requires pnpm `allowBuilds` for its `prepare` build (README.md:38-49).

## 5. Open questions

1. Coexistence of both plugins in one profile (prompt sections 117/118; gui's deny-list does not name `agent_teams_*`, so a gui member could call `agent_teams_create`) — unverified, no DSH installed.
2. Whether DSH `SubagentRuntime` has any external-process provider; PLAN.md:91-92 cites only `subagent-spawn-in-process` / `subagent-fork-in-process` — unverified against DSH source.
3. Stability of `header.delegationDepth`/`origin`/`parentSession` (lineage guard, definition-service.ts:650-653) in a "developer preview" harness.
4. DSH Windows/macOS support — README lacks a matrix.
5. Out-of-tree session-event registration in DSH (teams events.ts:39-54; gui PLAN.md:41-43 both state it is currently unsupported).

## 6. Probe / CLI log

Full log: `/tmp/claude-1000/-home-wsh-Documents-assistant-team-system-dev/17fd77ac-75ce-402b-a1a9-5d1eebba9843/scratchpad/ev:dsh-teams-gui/cli-log.md`. Key lines:

```
$ git log --format='%h %ad %s' --date=short | head -1   → teams: 801954d 2026-08-20 chore: bump version to 0.1.8 (77 commits, tags v0.1.0..v0.1.8, first 2026-08-12)
                                                          → gui:   3b56aa4 2026-08-19 chore: release v1.0.0 (21 commits, tags v0.1.0/v0.4.0/v0.4.1/v0.5.0/v1.0.0, first 2026-08-15)
$ find src -name '*.ts*' | xargs wc -l | tail -1   → teams 5186 ; gui 8531
$ test -d lib || echo no-lib   → no-lib (both) ; which dsh → not on PATH
$ grep -rn 'dsh-agent-teams\|nanmicoder\|agent_teams_' dsh-agent-team-gui/{package.json,src,PLAN.md,docs,README.md,CHANGELOG.md}   → 0 hits
$ grep -rn -i 'learn\|evolve\|feedback\|improve' dsh-agent-teams/src/*.ts   → 0 ; grep -rn -i 'nested\|sub-team\|subteam' → 0
$ grep -rn 'process.platform\|win32\|darwin' dsh-agent-teams/src dsh-agent-team-gui/src   → 0 ; CI runs-on → ubuntu-latest (all workflows)
$ WebFetch https://github.com/deepseek-ai/deepseek-harness (2026-08-22)   → "Everything is a Plugin"; MIT; "developer preview"; no OS/version matrix
```
