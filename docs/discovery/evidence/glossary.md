---
id: glossary
topic: Shared terminology for all discovery documents
status: normative
date: 2026-08-21
amended: 2026-08-23 — G1 documentation hygiene (review H10/R10/R16; M1a plan §4 item 6) added HarnessAdapter, CoordinationSubstrate, Run / direct run, `atm`, legacy ATM, and independence {declared, achieved}; existing rows unchanged except the HarnessInvocation "Do NOT call it" cell and the TeamRun row, which now point at the run-vs-TeamRun wording
---

# Glossary (normative for `docs/discovery/`; the 2026-08-23 additions are also the vocabulary of `docs/plans/`)

Every discovery document and evidence file MUST use these terms with these meanings. Banned loose synonyms are listed so reviewers can grep for drift. Rows marked *(added 2026-08-23)* come from the approved M1a plan and the 2026-08-23 independent review; they define terms that the M0 documents already used without a glossary entry.

| Term | Definition | Do NOT call it |
|---|---|---|
| **Assistant** | A portable, reusable *definition* of a role composition: persona, purpose/responsibilities, judgment principles, stable working preferences, Skill/capability/tool/plugin requirements, permissions, collaboration behavior, harness-selection policy, reviewed evolution overlays, optional visible identity. Carries **no runtime state** and no project facts. | "agent", "role", "bot", "persona" (persona is one *part* of an Assistant) |
| **AssistantInstance** | One live materialization of an Assistant inside a TeamRun (or a solo run): fresh context by default, bound to a harness invocation, a workspace and a task at execution time. | "session", "agent process" |
| **Member** | An AssistantInstance's slot in a TeamRun: name within the run, relationships (lead/reviewer/…), visibility (visible/hidden), persistent-or-ephemeral origin. | "bot", "worker" (worker is ClawTeam's term for its spawned process) |
| **Ephemeral Assistant** | An Assistant created at run time by a Lead for a specific need; auditable; may be hidden from the user UI; not persisted as a reusable package unless a human review promotes it. | "temp agent", "sub-agent" |
| **Lead** | The Member designated to coordinate a TeamRun (task decomposition, delegation, dynamic-member creation, reporting). | "leader" (ClawTeam term), "orchestrator", "captain" (dsh term) |
| **Skill** | A reusable capability/procedure package (e.g. Agent Skills `SKILL.md` format or equivalent). An Assistant *uses* Skills; an Assistant is never *just* a Skill. | — |
| **Capability** | A *semantic* ability requirement ("can run security review", "can read PDFs") satisfiable natively or by different Artifacts. | "tool" |
| **Artifact** | A *concrete* installable thing with source + version: Skill package, plugin, MCP server, local script, binary, capability package. | — |
| **ArtifactRequirement** | An *explicit* demand for one specific Artifact (never substituted). Contrast with Capability. | — |
| **Harness** | A coding-agent runtime CLI/API that can execute an AssistantInstance: Claude Code, Codex, Grok CLI, OpenClaw, Hermes, DeepSeek Harness, future engines. | "runtime", "engine", "backend" (Backend is wider) |
| **HarnessProfile** | The description of one installed harness: version, capabilities, flags, definition-injection methods, limits, platform support. | — |
| **HarnessCapability** | A named feature a harness does or does not have: headless mode, system-prompt injection, workspace instruction file, resume, MCP config, JSON/usage output, permission bypass, cwd control, … | — |
| **HarnessSelectionPolicy** | Rules + preferences (role-level, user-level, task-level) that resolve an Assistant + task to one or more harnesses, with fallback and ensemble rules. | — |
| **HarnessBroker** | The component that applies a HarnessSelectionPolicy: resolves, invokes, falls back, fans out for ensembles, records invocations. | "router", "dispatcher" |
| **HarnessAdapter** *(added 2026-08-23)* | One of the two declared seams of the AgentTeam core: the per-harness component that **probes** a harness's capabilities, **renders** a portable definition into that harness's injection channels (files, flags, stdin — never mutating the portable package), **invokes** it through the shared shell-free direct runner, and **parses** its output into the normalized record. One adapter per harness (`claude-code`, `codex`, `grok`, …); a new harness is an adapter-only change (HB-08). M1a plan §9. | "plugin", "driver", "backend" (Backend is wider) |
| **CoordinationSubstrate** *(added 2026-08-23)* | The second declared seam: the protocol through which a TeamRun obtains team/member/task/wait/message/snapshot/stop/cleanup operations from an optional coordination provider (a local deterministic provider first; ClawTeam as the first external provider). Never launches harnesses — that is the direct runner's job. Documented in M1a, implemented from M1b. | "substrate" alone (Substrate is the wider noun), "backend" |
| **HarnessInvocation** | One execution of one Backend for one Member/task: command, cwd, injected definition, session/resume info, cost, outcome. Recorded. | "run" — a run is the Member-level record (see Run / direct run); an invocation is one execution inside it |
| **Ensemble** | N independent HarnessInvocations of the same task (possibly different harnesses) followed by a synthesis step (compare, reconcile, merge). | "competition" |
| **Backend** | Anything the HarnessBroker can invoke: a Harness or a deterministic tool/service (monitor, scheduler, log parser, health check). | — |
| **Deterministic backend** | A non-LLM Backend used for monitoring, metric collection, checkpoint detection, scheduling, health checks, log parsing, trigger evaluation. | "agent" |
| **TeamTemplate** | A persistent composition of Assistants (by reference) + stable collaboration structure: members, Lead, relationships, reviewer independence, visibility, handoff conventions, dynamic-member policy, team-level preferences. Owns **no** project/session/workspace state. | "team" (ambiguous), "team definition" (ATM term) |
| **TeamRun** | One instantiation of a TeamTemplate: fresh AssistantInstances, fresh context, the current task/project/workspace, selected harnesses, temporary state, an archive/audit record. A direct run (below) is its one-Member case, recorded with the same record family. | "session", "project", "deployment" |
| **Run / direct run** *(added 2026-08-23)* | What `atm run` produces: one `RunRecordV1` (`run.json`) whose single Member is bound to exactly one *execution* — a HarnessInvocation (solo mode) or an Ensemble (legs plus synthesis). A direct run is the one-Member case of a TeamRun; M1b extends the same record with coordination fields instead of adding a second record kind. "Run" therefore never means a single HarnessInvocation, and the historical "Run 1/2/3" labels in M0 PoC sketches are dated wording. | "session", "job"; "run" for one invocation |
| **Nested TeamRun** | A TeamRun created by a Member for a delegated task; isolated task/message space; returns a result to the creating Member; archives; the outer TeamRun continues. | "sub-team" (ClawTeam has no such concept) |
| **Project / Workspace** | Execution-time inputs (repo, paths, branch, data, credentials by reference). Never part of an Assistant or TeamTemplate. | — |
| **Surface** | An optional interaction/messaging channel presenting a run: local coding-agent conversation, local UI, Telegram, OpenClaw channels, Hermes, Discord, future. | "channel" (OpenClaw term) |
| **Visible identity** | Presentation state of a Member on a Surface (display name, avatar, bot account). Not Assistant identity. | — |
| **Base Definition** | The authored content of an Assistant or TeamTemplate. | — |
| **User Overlay** | A user's stable, project-independent modifications layered on a Base Definition. | — |
| **Reviewed Evolution Overlay** | Project-independent learning (review standards, collaboration habits, role-level failure modes, harness preferences, workflow improvements) accepted through human review. | "memory" |
| **Proposal** | A candidate change to an overlay, generated automatically from run experience, pending human review; never applied silently. | — |
| **Substrate** | An existing system a layer is built on or composed with (e.g. ClawTeam for team execution). | — |
| **independence {declared, achieved}** *(added 2026-08-23)* | The two-part record of reviewer/member independence (TC-03/TE-05). `declared` is what the TeamTemplate asks for: `advisory` (convention, bypass visible and audited) or `mechanical` (enforced by the runtime). `achieved` is the fact recorded per run/nested run: `namespace` (separate names/spaces inside one data root), `data-dir` (separate data roots), or `mechanical` (enforced separation). `achieved` may be weaker than `declared`; the record never upgrades it. | "isolation level" used as a single value; "full" isolation without the pair |
| **`atm`** *(added 2026-08-23)* | The AgentTeam product CLI (and the name of its future MCP edge). Working-name CLI `ats` appears only in dated M0 records. | "ATM" (see legacy ATM) |
| **legacy ATM** *(added 2026-08-23)* | The superseded agent-team-manager experiment (ADR 0002): a source of requirements, experiments, failure evidence and research, owner-authorized for internal copy/adaptation with provenance, never the architecture baseline. Always write "legacy ATM" (or "ATM experiment") for the project and `atm` for the CLI. | "ATM" unqualified in new text; "atm" for the old project |
| **Reuse rung** | Position on the 6-step reuse ladder: 1 configuration/composition · 2 thin adapter · 3 upstream-friendly extension · 4 selective licensed module reuse · 5 fork only when necessary · 6 new implementation only when nothing else satisfies. | — |
| **Fit cell** | A classification of one requirement against one system: `S` already supported · `C` supported through configuration · `P` supported through composition · `Xs` small extension required · `XL` major extension required · `M` architectural mismatch · `n/a` · `?` unverified; confidence suffix `!` (probe/file:line) `~` (read/inferred) `w` (web-only). | — |

## Layers (used to group requirements and fit-gap rows)

AD Assistant definition · TC Team composition · TE Team execution · HB Harness brokerage · AR Artifact/dependency · EV Evolution · MS Messaging/surface · LO Long-running operations · XC cross-cutting.

## ATM terms that are demoted (may appear only in `legacy-atm-disposition.md` and evidence)

TeamDefinition, ProjectDefinition, RoleDefinition, ProjectRoleContext, Workspace-as-core, A2A router, OpenClaw adoption/agent-ID machinery, desired-state reconciliation, Telegram topic topology as team semantics.
