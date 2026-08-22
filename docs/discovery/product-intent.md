---
title: Product intent — Assistant Team System
status: draft v3 — register FROZEN 2026-08-22 after evidence phase W1 (AR-06 added; notes folded into TC-03, EV-05, AR-03, XC-02 from ATM salvage)
date: 2026-08-21
owns: requirement register (the only place requirements are authored), lifecycle principles, non-goals, PoC acceptance criteria
---

# Product intent

> Reading guide: this document restates the product brief faithfully and turns it into a numbered **requirement register**. Every other discovery document cites requirements by ID (e.g. `TE-05`) and never re-authors them. Terminology: [`evidence/glossary.md`](evidence/glossary.md).

## 1. What this product is

The primary reusable product object is a **portable Assistant definition** — a reusable specialized colleague (code reviewer, implementation planner, software architect, paper reviewer, scientific writer/editor, research analyst, run-and-monitor assistant, evaluator, coordinator, product critic) — **not** a runtime agent, process, session, or workspace.

Assistants are composed into **TeamTemplates** (stable collaboration structure) and executed as **TeamRuns** (fresh instances, fresh context, current project/workspace supplied at execution time, selected harnesses, temporary state). Assistants and TeamTemplates may **evolve** over time through *reviewed, project-independent* learning. Messaging surfaces (Telegram, OpenClaw channels, Hermes, Discord, local UI) are **optional**; the product must be fully useful locally.

This project **supersedes** the ATM experiment but does not inherit its architecture (see `legacy-atm-disposition.md`).

### 1.1 The problem

Today the owner runs specialized AI colleagues across several coding harnesses (Claude Code, Codex, Grok CLI, OpenClaw, Hermes) and several kinds of work (software, papers, training operations). The reusable knowledge — *how a good code reviewer reviews, what a methods reviewer checks, how a run-and-monitor colleague escalates* — lives in scattered prompts, per-harness config files, chat topics and one-off team scripts. Each new project re-creates it; each harness binds it to its own session model; each messaging setup turns bot topology into team semantics. The earlier ATM experiment tried to fix this by managing **runtime agents** (deployment reconciliation, persistent agent identity, per-project sessions/workspaces, A2A routing) and stalled: the persistent-runtime model fought every harness and every surface, and the reusable *colleague* was never the first-class object.

### 1.2 The product object

The reusable object is the **Assistant definition** — a specialized colleague you prepare once and instantiate fresh whenever a project needs it. Examples: code reviewer; implementation planner; software architect; paper reviewer; scientific writer/editor; research analyst; run-and-monitor assistant; evaluator; coordinator; product critic.

A durable Assistant definition may contain or reference: role/persona · purpose and responsibilities · judgment principles · stable user-independent or user-specific working preferences · Skills · plugins/tools/capability requirements · permissions · collaboration behavior · harness-selection policy · reviewed role evolution · optional user-visible identity. It contains none of the items in the exclusion list of §2.

Illustration (an Assistant is a composition, not a prompt):

```
Code Reviewer Assistant
├── review persona
├── review principles
├── code-review Skill
├── security-review Skill
├── test-analysis Skill
├── tool permissions
├── collaboration behavior
└── harness-selection policy
```

Illustration (an Assistant is not a harness — same definition, different executions):

```
Run A: code-reviewer → Codex
Run B: code-reviewer → Claude Code
Run C: code-reviewer → Codex + Claude Code independently → compare disagreement → synthesize review
```

### 1.3 Teams

A **TeamTemplate** composes Assistants into a stable collaboration structure. Examples from the brief:

```
Paper Team                          Training Operations Team
├── Paper Lead                      ├── Run & Monitor
├── Writer                          ├── Evaluator
├── Methods Reviewer                └── Code Modification Assistant
├── Adversarial Reviewer
└── Editor
```

A TeamTemplate may define normal members, a lead/coordinator, collaboration relationships, reviewer independence, visibility, handoff conventions, a dynamic-member policy and stable team-level user preferences. It owns no project, session or workspace state. Using it creates a **TeamRun**: fresh AssistantInstances, fresh context, the current task/project/workspace, selected harnesses, temporary state.

Two run-time behaviors are first-class: a Lead may create **ephemeral Assistants** (hidden from the UI if desired, still auditable, never forced to become permanent packages), and a Member may decide a delegated task deserves its own temporary **nested TeamRun**:

```
Training Operations Team
    └── Code Modification Assistant
            └── temporary Development Team (Planner, Implementer, Reviewer, Tester)
                    → completes, returns result, archives; the outer run continues
```

### 1.4 Long-running operational colleagues

A Run & Monitor Assistant supervising a multi-day training job does **not** mean a continuously live LLM loop. Deterministic components (process monitoring, metric collection, checkpoint detection, schedulers, health checks, log parsing, trigger conditions) do the watching; the Assistant is invoked for interpretation, decisions, escalation, planning, coordination and reporting. Execution backends therefore include both agent harnesses and deterministic tools/services.

### 1.5 Evolution, portability, surfaces

Assistants and TeamTemplates improve over time through **reviewed, project-independent** learning (stable preferences, review standards, collaboration habits, role-level failure modes, harness preferences, workflow improvements) layered as overlays; automatic evolution produces *proposals*, never silent mutation. Definitions are **portable**: Skill/plugin/MCP/script/binary dependencies are declared with enough metadata to re-establish them on another host, distinguishing semantic capability requirements from explicit artifact requirements, supporting vendored and Git/registry sources, and never embedding secrets. **Messaging is optional**: a visible Bot on Telegram/Discord/OpenClaw/Hermes is presentation state; the Core is never built around groups/topics.

### 1.6 "Fully useful locally" means

With nothing but this machine, a local coding-agent conversation (or local UI) and the installed harnesses, the owner can: pick an Assistant or TeamTemplate; point it at a repo/paper/job; get a fresh TeamRun with the right harnesses (possibly several in ensemble); see a run archive; and accept or reject evolution proposals afterwards. No Telegram bot, no OpenClaw gateway, no tmux are prerequisites.

### 1.7 Success for the owner

Fewer re-created prompts; the same reviewer colleague giving consistent judgment across harnesses and projects; teams that can be re-instantiated on a new project in minutes; hidden and nested delegation that is auditable; and learning that survives projects without dragging project facts along.

## 2. Lifecycle principles (normative)

| Persistent | Fresh by default |
|---|---|
| Assistant definition | AssistantInstance |
| TeamTemplate | TeamRun |
| Reviewed, project-independent evolution (overlays) | session / context |
| — | project / workspace (supplied at execution time) |

An Assistant definition **must not intrinsically contain**: a concrete project; a project workspace; a project session; a runtime-specific agent identity; a Telegram topic; a Claude Code/Codex session; temporary project facts; branches/checkpoints/current task state; a permanently bound coding harness.

An Assistant **is not a Skill** (a Skill is a reusable capability/procedure; an Assistant is a role composition that may use several Skills, tools, plugins and harnesses) and **is not a harness** (the same Assistant may run on Codex, on Claude Code, or on both independently with synthesis, without its definition changing).

## 3. Requirement register

Priority: **M** must · **S** should · **C** could. "Brief §" = section of the originating product brief. Fit-gap cells are recorded per requirement in `existing-systems-fit-gap.md`.

### AD — Assistant definition

| ID | P | Requirement | Brief § |
|---|---|---|---|
| AD-01 | M | A portable Assistant definition carries role/persona, purpose & responsibilities, judgment principles, and stable (user-independent or user-specific) working preferences. | 1 |
| AD-02 | M | The definition expresses Skill, plugin/tool and capability requirements in a runtime-neutral way (not bound to one harness's config format). | 1, 2, 10 |
| AD-03 | S | The definition declares permissions and collaboration behavior (how it hands off, reviews, escalates). | 1 |
| AD-04 | M | Harness preferences / harness-selection policy are data inside the definition; no permanent binding to one harness. | 1, 3 |
| AD-05 | M | Exclusion list is enforceable: no project, workspace, session, runtime agent identity, Telegram topic, harness session, temporary facts, branches/checkpoints/task state, bound harness. | 1 |
| AD-06 | C | Optional user-visible identity (name/avatar) is separable presentation state, not Assistant identity. | 1, 11 |
| AD-07 | M | Ephemeral Assistants can be generated at run time by a Lead, stay hidden from the user UI if desired, remain auditable, and need not become permanent packages. | 6 |
| AD-08 | M | One Assistant definition is reusable across TeamTemplates and runs without copy-editing. | 1, 4 |
| AD-09 | M | Assistant ≠ Skill is modeled explicitly (an Assistant composes multiple Skills/tools/plugins/harnesses; it is never collapsed into one prompt or one Skill). | 2 |

### TC — Team composition

| ID | P | Requirement | Brief § |
|---|---|---|---|
| TC-01 | M | A TeamTemplate composes reusable Assistants by reference. | 4 |
| TC-02 | M | A TeamTemplate defines a lead/coordinator, collaboration relationships and handoff conventions. | 4 |
| TC-03 | S | Reviewer independence (e.g. adversarial reviewer must not share context with the writer) is expressible and enforceable at run time; the template declares the enforcement level (advisory vs mechanical isolation). | 4 |
| TC-04 | S | Per-member visibility (visible/hidden to the user) is expressible. | 4, 6 |
| TC-05 | M | A dynamic-member policy states who may add temporary members, how many, and with which harnesses. | 4, 6 |
| TC-06 | M | Team-level stable user preferences exist; the template owns no project/session/workspace state. | 4 |

### TE — Team execution

| ID | P | Requirement | Brief § |
|---|---|---|---|
| TE-01 | M | Instantiating a TeamTemplate creates a fresh TeamRun with the project/workspace and task supplied at execution time. | 5 |
| TE-02 | M | AssistantInstances and sessions are fresh by default; resuming is opt-in. | 1, 5 |
| TE-03 | M | Members of one TeamRun may run on different harnesses. | 3, 17 |
| TE-04 | M | The Lead can create a temporary (possibly hidden) member during a run. | 6, 17 |
| TE-05 | M | Nested TeamRun: a Member can create a temporary inner TeamRun for a delegated task; it completes, returns its result, archives, and the outer run continues. | 7, 17 |
| TE-06 | S | Task DAG, messaging, monitoring and recovery exist for a run (may be inherited from the substrate). | 12 |
| TE-07 | M | Every run (including hidden and nested members) leaves an auditable archive; project-specific facts stay in the run. | 5, 6 |
| TE-08 | M | Runs work on Ubuntu, Windows and macOS; a tmux/Linux-only path is not the only viable path. | 18 |

### HB — Harness brokerage

| ID | P | Requirement | Brief § |
|---|---|---|---|
| HB-01 | M | Each harness is described by a HarnessProfile / HarnessCapability set (headless, system-prompt injection, resume, MCP, output format, permissions, platform). | 3 |
| HB-02 | M | The Assistant definition can be injected into each supported harness (system prompt, prompt prefix, workspace instruction files, skill dirs) without changing the definition. | 3, 17 |
| HB-03 | M | Harness selection follows a policy with precedence user-level > role-level > default, applied per invocation. | 3 |
| HB-04 | S | Fallback to another harness on failure/unavailability. | 3 |
| HB-05 | M | Ensemble: several harnesses run the same task independently; a synthesis step compares disagreement and merges. | 3, 17 |
| HB-06 | S | Deterministic tools/services are invokable Backends alongside harnesses. | 8 |
| HB-07 | S | Every HarnessInvocation is recorded (harness, version, model, cost, outcome). | 5, 9 |
| HB-08 | S | A new harness can be added without changing the Assistant core (adapter-level change only). | 3, 14 |

### AR — Artifact / dependency

| ID | P | Requirement | Brief § |
|---|---|---|---|
| AR-01 | M | Semantic capability requirements and explicit concrete artifact requirements are distinct concepts. | 10 |
| AR-02 | M | Artifact kinds covered: Agent Skills, plugins, MCP servers, local scripts, binaries, capability packages. | 10 |
| AR-03 | M | Sources: local/vendored artifacts and Git/registry sources; enough metadata to re-establish capabilities on another host (credential-free export/import of definitions + dependency metadata). | 10 |
| AR-04 | M | No secrets in portable configuration (references only). | 10 |
| AR-05 | S | Resolution report per host: native / artifact-installed / degraded / unsupported. | 10 |
| AR-06 | S | Artifact lock/fingerprint (source + version + hash) so a definition's dependencies can be re-established reproducibly on another host; local modifications to vendored artifacts are detectable. *(Added 2026-08-22 from ATM ADR 0022 salvage; owner decision.)* | 10 |

### EV — Evolution

| ID | P | Requirement | Brief § |
|---|---|---|---|
| EV-01 | M | Only project-independent learning is persisted: stable user preferences, review standards, collaboration habits, known role-level failure modes, harness preferences, high-level workflow improvements. | 9 |
| EV-02 | M | Overlay model: Base Definition + User Overlay + Reviewed Evolution Overlay, with defined merge order and conflict rules. | 9 |
| EV-03 | M | Automatic evolution produces Proposals; it never silently mutates the reusable Assistant/TeamTemplate. | 9 |
| EV-04 | M | Never persisted: current branch, checkpoint path, paper-specific claims, temporary project arguments, raw session transcripts, one project's implementation details. | 9 |
| EV-05 | S | Review workflow with provenance (which runs produced which proposal; who approved); what is applied is exactly what was approved; automatic actors only propose, humans approve; proposal volume is bounded. | 9 |

### MS — Messaging / surface

| ID | P | Requirement | Brief § |
|---|---|---|---|
| MS-01 | M | Surfaces are optional; the product is fully useful with only a local coding-agent conversation or local UI. | 11 |
| MS-02 | C | Surface adapters: Telegram, OpenClaw channels, Hermes, Discord, future providers. | 11 |
| MS-03 | S | A visible Bot identity is presentation state bound to a Member on a Surface, not Assistant identity. | 11 |
| MS-04 | M | Team semantics are never derived from Telegram groups/topics or any surface topology. | 11, 15 |

### LO — Long-running operations

| ID | P | Requirement | Brief § |
|---|---|---|---|
| LO-01 | S | An operational Assistant (e.g. Run & Monitor) can supervise jobs for days/weeks without a continuously live LLM loop. | 8 |
| LO-02 | S | Deterministic components handle process monitoring, metric collection, checkpoint detection, schedulers, health checks, log parsing, trigger conditions. | 8 |
| LO-03 | S | The Assistant is invoked for interpretation, decisions, escalation, planning, coordination and reporting when triggers fire. | 8 |
| LO-04 | S | Health/restart semantics for long runs (what resumes, what is fresh). | 8 |

### XC — Cross-cutting

| ID | P | Requirement | Brief § |
|---|---|---|---|
| XC-01 | M | Licenses verified before any source reuse is proposed. | 14 |
| XC-02 | M | Platform limitations of every candidate substrate documented (Ubuntu/Windows/macOS); host-platform support and harness availability are tracked as independent dimensions. | 18 |
| XC-03 | M | Reuse ladder honored with evidence: configuration/composition → thin adapter → upstream-friendly extension → selective licensed reuse → fork only if necessary → new implementation only if nothing else satisfies. | 14 |
| XC-04 | S | All automated actions (spawns, invocations, proposals) are auditable. | 6, 9 |

## 4. Minimal PoC acceptance criteria (definitions only — no PoC code in this phase)

**PoC A — reusable Assistant, interchangeable harness.** One `code-reviewer` Assistant definition. Run 1 executes it on Codex; Run 2 on Claude Code; Run 3 on both independently followed by a synthesis step. Pass if: the definition file is byte-identical before and after all three runs; each run produces a review of the same target; Run 3's synthesis lists agreements and disagreements with per-harness attribution; each HarnessInvocation is recorded. Covers AD-04, AD-08, HB-02, HB-03, HB-05, HB-07.

**PoC B — reusable Team + dynamic member.** TeamTemplate {Lead, Implementer, Reviewer}. A fresh TeamRun is created for a supplied repo/task. The Lead dynamically creates one temporary hidden specialist. At least two members use different harnesses. Pass if: the TeamTemplate is unchanged; the run archive shows the hidden member (auditable) while the user-facing member list does not; the task completes through the DAG. Covers TC-01, TC-05, TE-01, TE-03, TE-04, TE-07, AD-07.

**PoC C — nested TeamRun.** One visible Assistant receives a complex task, creates a temporary inner TeamRun, collects the result, reports back, and the inner run is ended/archived while the outer run continues. Pass if: the inner run's tasks/messages are isolated from the outer run; the result is returned to the creating Member; the inner run is archived; nothing of the inner run leaks into any persistent definition. Covers TE-05, TE-07, EV-04.

Constraints for all PoCs: no Telegram or OpenClaw required unless the analysis proves necessity; must be runnable on this host (Ubuntu, no tmux) and have a documented path for Windows/macOS (TE-08).

## 5. Non-goals of this phase

- No production code; no PoC implementation (PoCs are *defined* in `minimal-poc-plan.md`).
- No ATM architecture inheritance by default (demotions enumerated in `legacy-atm-disposition.md`).
- No commitment yet to project name, implementation language, or upstream engagement (tracked in `.project-steward/QUESTIONS.md`).

## 6. Success criteria for the discovery phase

The nine documents exist, are internally consistent, cite evidence, and `architecture-options.md` answers **"What is the smallest new software layer that genuinely needs to be built?"** with a recommendation a reviewer can accept or reject — then the project STOPs for product/architecture review.
