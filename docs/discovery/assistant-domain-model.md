---
title: Assistant domain model
status: draft v2 (W3 critic findings applied 2026-08-22)
date: 2026-08-22
owns: [Assistant content model and exclusion list, Assistant vs AssistantInstance vs Member, Capability/Skill/Artifact requirements, harness preferences and selection policy as data (shape only), Ephemeral Assistant at definition level, OVERLAY pressure test (Base + User Overlay + Reviewed Evolution Overlay), mapping of these concepts to substrates]
depends_on: [product-intent.md, evidence/glossary.md, existing-systems-fit-gap.md, evidence/*.md]
---

# Assistant domain model

## 1. Purpose and scope

This document models the **Assistant** — the product's primary reusable object (product-intent §1.2) — precisely enough that later documents can map it onto substrates. It owns: the content model and exclusion list (AD-01..AD-06, AD-08, AD-09), the Assistant / AssistantInstance / Member boundary (the instance *boundary* of TE-02; the run lifecycle is `team-execution-model.md` §3), Capability vs Skill vs Artifact requirements (AD-02, AR-01..AR-06), harness preferences as *data* (AD-04, HB-03 — shape only), the Ephemeral Assistant at definition level (AD-07), and the Evolution-overlay pressure test (EV-01..EV-05). Substrate versions are those pinned in the `evidence/*` frontmatters: Claude Code 2.1.239, Codex 0.148.0, Grok 1.0.5, OpenClaw 2026.7.1-2, Hermes 0.20.4, ClawTeam 0.3.0@0119833.

It does **not** own: TeamTemplate content, Member slots, hidden members, nested runs, run archives (→ `team-execution-model.md`); HarnessProfile, the definition-injection matrix, broker/selection execution, ensembles, invocation records (→ `harness-broker-model.md`); reuse rungs (→ `reuse-vs-build-analysis.md`); the "smallest new layer" answer (→ `architecture-options.md`). Fit cells are quoted from `existing-systems-fit-gap.md` and never re-classified here. Terms follow `evidence/glossary.md`; where a substrate's own word is meant it is quoted ("ClawTeam agent", "OpenClaw agent", "Claude subagent").

## 2. Assistant ≠ Skill ≠ harness ≠ runtime agent

The register makes three separations explicit (AD-09, AD-04, AD-05). Each is stated once with a concrete example and the substrate that conflates it today.

**(a) An Assistant is not a Skill (AD-09).** The `code-reviewer` Assistant *uses* a `code-review` Skill, a `security-review` Skill and a `test-analysis` Skill, but it also carries judgment principles, permissions, collaboration behavior and a harness policy that no Skill can hold: the Agent Skills specification requires only `name` + `description` and has no persona or policy fields [ev:atm-salvage#F8]. ClawTeam collapses the two: `spawn --skill <name>` reads `~/.claude/skills/<name>/SKILL.md` and inlines it into `--append-system-prompt`, so the Skill *becomes* the only persona text, and only for claude/pi [ev:clawteam-spawn-platform#F6]; the worker prompt has no persona slot (`## Identity / ## Task / protocol`) and `agent_type` is the only role signal [ev:clawteam-model#F15]. OpenBot states the separation in one sentence — "A tool is something a Bot calls; a skill is something a Bot is told" [ev:claude-agent-teams-hermes-openbot#F32].

**(b) An Assistant is not a harness (AD-04).** Run A executes `code-reviewer` on Codex, Run B on Claude Code, Run C on both with synthesis, and the definition file is byte-identical afterwards (PoC A). Every substrate's definition unit is harness-bound: ClawTeam's `AgentDef.command` is a fixed CLI per template member and wins over `launch --command`/`--profile` [ev:clawteam-model#F13][ev:clawteam-probe-log#F17]; Claude subagent files run only as Claude sessions ("In every approach the workers are Claude sessions") [ev:claude-agent-teams-hermes-openbot#F6]; a Hermes profile distribution is a Hermes-only package (`hermes_requires`, installed by `hermes profile install`) [ev:claude-agent-teams-hermes-openbot#F24] and Hermes `delegate_task` children "cannot target other profiles or harnesses" [ev:claude-agent-teams-hermes-openbot#F22]; a dsh-gui `AgentRecord` is a DSH model route [ev:dsh-agent-teams-and-gui#F18].

**(c) An Assistant is not a runtime agent (AD-05).** An "OpenClaw agent" is a persistent identity (`agentDir`; the docs' rule "Never reuse agentDir" [ev:atm-salvage#F1]) plus a workspace holding `SOUL.md` *next to* `.git`, `openclaw-workspace-state.json` and, when present, the `MEMORY.md` bootstrap slot [ev:openclaw-native-and-telegram-verification#F14][ev:harness-cli-capabilities-b#F8], plus a session store [ev:openclaw-native-and-telegram-verification#F13]; `agents add` provisions 41 paths and no schema key expresses an ephemeral agent [ev:harness-cli-capabilities-b#F10]. A "ClawTeam agent" is seven env-derived identity fields for one process [ev:clawteam-model#F3][ev:clawteam-probe-log#F24]; a dsh-agent-teams member is a persona string generated per run from name/role/team [ev:dsh-agent-teams-and-gui#F15]. The Assistant carries none of this; dsh-gui's separate `agents`/`squads` tables versus `runs`/`session_modes` tables is the closest structural precedent [ev:dsh-agent-teams-and-gui#F18][ev:dsh-agent-teams-and-gui#F21].

## 3. Assistant definition content model (AD-01..AD-06, AD-08)

The definition is a small directory (or one document) whose sections are stable across harnesses and projects. Long persona/principle prose lives in referenced files, never inline blobs — the one ATM discipline salvaged here [ev:atm-salvage#F18]. Illustrative, not a schema:

```yaml
# assistant.yaml — illustrative, not a schema
id: code-reviewer            # stable name, lowercase (cf. Agent Skills name rule)
version: 3                   # Base Definition version; overlays are versioned separately
summary: Reviews code changes for correctness, security and test adequacy.
persona: persona.md          # voice, stance, what kind of colleague this is
purpose:                     # responsibilities; what "done" means for this Assistant
  - produce a review with findings ranked by severity
  - never approve without running available tests
principles: principles.md    # judgment rules ("prefer reversible migrations", ...)
preferences:                 # user-INDEPENDENT stable working preferences only
  output: findings table grouped by severity, then narrative
  # user-specific preferences: modelled as User-Overlay-only (§9) — provisional, see §13 Q1
skills: [code-review, security-review, test-analysis]   # shorthand -> agent-skill artifacts (§6)
capabilities:                # semantic; satisfiable natively or by different Artifacts (§6)
  - {capability: run-unit-tests, level: required}
  - {capability: read-pdf, level: preferred}
artifacts:                   # explicit, never substituted (§6)
  - {ref: migration-lint, kind: local-script, source: {vendored: artifacts/migration-lint}, level: required}
permissions:                 # harness-neutral intent; rendered per harness by the broker
  filesystem: read-write-workspace
  network: deny
  shell: allow
collaboration:               # hand-off / review / escalation behavior (AD-03)
  handoff: {format: structured-findings, to: lead}
  review: independent-of-author        # enforcement level is the TeamTemplate's (TC-03)
  escalate_when: [tests cannot run, security finding of severity high]
harness_policy: harness-policy.yaml   # Assistant-level selection preferences as data (§7)
presentation_defaults:       # optional hints only; never an account/topic/token (§10)
  display_name: Code Reviewer
  emoji: "🔍"
evolution:
  accepts_proposals_for: [principles, preferences, collaboration, harness_policy, failure_modes]
  failure_modes: failure-modes.md   # known role-level failure modes (EV-01)
```

| Section | Required | Portable |
|---|---|---|
| `id`, `version`, `summary` | yes | yes |
| `persona`, `purpose` | yes | yes |
| `principles` | yes | yes |
| `preferences` (user-independent) | no | yes |
| `skills`, `capabilities`, `artifacts` | no | yes (by reference + metadata, §6) |
| `permissions` | no (harness default applies) | yes (intent, not flags) |
| `collaboration` | no | yes |
| `harness_policy` | no | yes |
| `presentation_defaults` | no | yes (hints) |
| `evolution` | no | yes |

The author owns every section of the Base Definition; which layer may append, override or narrow which section is defined **once**, in the §9 per-field table (EV-02) — this table deliberately carries no edit-rights column.

AD-08 follows from the shape: a TeamTemplate references `code-reviewer@3` (resolved to a content hash at instantiation, §5) and supplies nothing that lives inside it; reuse across templates needs no copy-editing because nothing project- or team-shaped is in the file.

## 4. Exclusion list enforcement (AD-05, EV-04)

What must never appear in a Base Definition or any overlay (product-intent §2): a concrete project or workspace, a project session, a runtime-specific agent identity, a Telegram topic, a Claude Code/Codex session, temporary project facts, branches/checkpoints/task state, a permanently bound harness, and secrets (AR-04).

Two enforcement mechanisms are modeled — one borrowed (the closed schema), one new (the content validator; only its heuristics are borrowed from the substrates' identifier shapes, §12):

1. **Closed schema.** Every section is a closed object; unknown keys are rejected (dsh-gui's zod `.strict()` records reject credential-like extra fields by test [ev:dsh-agent-teams-and-gui#F20]; ATM's `additionalProperties:false` with an `x-*` escape [ev:atm-salvage#F18]). This alone removes `session_id`, `workspace`, `branch`, `topic`, `command` as *fields*.
2. **Content validator** over string values, reporting violations by section and line:

| Violation class | Detection heuristic (illustrative) | Why the shape is known |
|---|---|---|
| Filesystem/workspace paths | absolute paths, `~/.clawteam/workspaces/…`, `workspace-<id>` | ClawTeam worktree paths [ev:clawteam-probe-log#F22]; OpenClaw `<stateDir>/workspace-<agentId>` [ev:harness-cli-capabilities-b#F9] |
| Branch/checkpoint names | `refs/heads/`, `clawteam/<team>/<agent>`, `openclaw/<name>`, `checkpoint-*/step_*` | ClawTeam branch scheme [ev:clawteam-probe-log#F22]; OpenClaw worktree branches [ev:openclaw-native-and-telegram-verification#F23] |
| Harness/project session identifiers | UUIDv4 next to `session`, `agent:<id>:…` keys, `rollout-<ts>-<uuid>`, `clawteam-<team>-<agent>` | Claude `--session-id`, Codex rollouts [ev:harness-cli-capabilities-a#F8]; OpenClaw keys [ev:atm-salvage#F4]; fork session keys [ev:clawteam-openclaw-fork-delta#F4] |
| Surface topology | `-100…` chat ids, `topic:<n>`, `Channel:` lines, bot usernames | kit `IDENTITY.md` carries `Channel:`/`Model:` [ev:openclaw-native-and-telegram-verification#F2] |
| Bound harness | `command: [claude]`, `--dangerously-skip-permissions`, model ids outside `harness_policy` | ClawTeam `AgentDef.command` [ev:clawteam-model#F13]; fork default `["openclaw"]` [ev:clawteam-openclaw-fork-delta#F33] |
| Secrets | token-shaped strings; env *values* instead of env *names* | AR-04; ClawTeam `api_key_env` names [ev:clawteam-model#F25]; Hermes `env_requires` names [ev:claude-agent-teams-hermes-openbot#F24] |
| Run-time memory | `MEMORY.md`, `memories/`, transcripts referenced as content | OpenClaw `MEMORY.md` bootstrap slot + ungated `session-memory` hook [ev:harness-cli-capabilities-b#F8][ev:harness-cli-capabilities-b#F14]; Hermes profile `memories/` [ev:claude-agent-teams-hermes-openbot#F23][ev:harness-cli-capabilities-b#F19] |

**Provenance exemption.** TeamRun ids issued by the run layer (`run-…`) are permitted *only* in designated provenance fields — `provenance.runs` of a Proposal, `runs`/`from_proposal` of an overlay entry, and decision records (§9; EV-05 "which runs produced which proposal") — and the validator skips exactly those fields. A Base Definition carries no run id at all (promotion provenance lives in the promotion decision record, §8). Harness-session, project-session, topic and branch identifiers remain banned everywhere, overlays included.

The acceptance test is PoC A's "byte-identical before and after all three runs" (product-intent §4), the same invariant ATM's AT-13 planned for its team file [ev:atm-salvage#F19]. The validator is advisory for prose (heuristics) and mechanical for structure.

## 5. Assistant vs AssistantInstance vs Member (TE-02)

| | Assistant | AssistantInstance | Member |
|---|---|---|---|
| Lifetime | persistent, versioned | one TeamRun (or solo run) | one TeamRun |
| Identity | `id@version`, resolved to a content hash at instantiation (the hash `team-execution-model.md` §3 records per Member) | run-scoped instance id | name within the run |
| Adds | — | harness invocation binding, resolved effective definition (Base + overlays, §9), workspace, task, session handle (none by default), artifact resolution report (§6) | relationships (lead/reviewer/…), visibility, origin (persistent/ephemeral) — owned by `team-execution-model.md` |
| Fresh by default | n/a | yes; resume is opt-in and recorded on the invocation | n/a |
| Where run facts go | never | instance state, then the run archive (TE-07) | run archive |

The instantiation boundary is the moment an effective definition is rendered for one harness. Substrate precedents: ClawTeam generates a `--session-id` per spawn and resumes only on explicit `--resume` [ev:clawteam-spawn-platform#F19]; Claude Code offers `--bare`/`--no-session-persistence` and Codex `--ephemeral` [ev:harness-cli-capabilities-a#F19]; OpenClaw and Hermes invert the default — a fresh context is a new session key on a persistent OpenClaw agent [ev:atm-salvage#F4] or a fresh profile because "Never point two agent processes at the same profile" [ev:harness-cli-capabilities-b#F19] — so for them the instance boundary is materialized by the adapter, not native.

## 6. Capability vs Skill vs Artifact requirements (AD-02, AR-01..AR-06)

Three requirement kinds, one harness-neutral vocabulary (AD-02):

- **Capability** — semantic ("can run unit tests"); satisfied natively by a harness, or by any Artifact that `provides` it; `level: required|preferred`.
- **ArtifactRequirement** — explicit (`ref`, `kind`, `source`, `version`, `integrity`); never substituted (AR-01). Kinds per AR-02: `agent-skill`, `plugin`, `mcp-server`, `local-script`, `binary`, `capability-package`.
- **Skill shorthand** — normalized exactly once: `skills: [x]` ≡ `{ref: x, kind: agent-skill, source: {shared-root}, level: required}`; the lock (below) records the resolved digest, which is what "never substituted" binds to for a ref without an explicit source pin; an explicit `artifacts:` entry with the same `ref` overrides the shorthand. The shorthand exists because `SKILL.md` dirs are the only de-facto neutral name today, read by OpenClaw, Hermes, Codex, Grok and Claude Code [ev:harness-cli-capabilities-b#F11][ev:harness-cli-capabilities-a#F5].

```yaml
# requirements — illustrative, not a schema
capabilities:
  - {capability: structured-code-review, level: required}
artifacts:
  - ref: dependency-audit          # explicit, git-pinned (a shorthand `skills:` entry would use the shared root)
    kind: agent-skill
    source: {git: {repo: https://github.com/example/skills, subdir: dependency-audit, ref: v1.4.0}}
    integrity: sha256:…          # filled by the lock
    level: required
  - ref: migration-lint
    kind: local-script
    source: {vendored: artifacts/migration-lint}   # ships inside the definition package
    level: required
secrets_required: [GITHUB_TOKEN]  # names only (AR-04); resolved by the host at run time
```

**Lock and fingerprint (AR-06).** A resolved set is recorded per definition version: `{ref, kind, resolved: <name@version | git commit | vendored path>, digest, resolved_at, fingerprint: clean|locally-modified|unmanaged}`. ClawTeam's `skills-lock.json` (`{"source": "anthropics/skills", "sourceType": "github", "computedHash": "<sha256>"}`, ClawTeam/skills-lock.json:1-10) is the only substrate precedent — source + hash, no per-skill version/ref (only a top-level format `"version": 1`, ClawTeam/skills-lock.json:2), no reader; ATM's `ArtifactLock` adds version/ref, digest and the `locally-modified` fingerprint that "blocks destructive replacement" [ev:atm-salvage#F10]. Hermes distributions carry `version` but no hash and no ref pinning yet [ev:claude-agent-teams-hermes-openbot#F24].

**Resolution report (AR-05).** Per host and per definition: each capability/artifact → `native | artifact-installed | degraded | unsupported`, with the reason. Existing partial reports feed it: OpenClaw `skills list --json` (`eligible, missing, blockedByAllowlist, blockedByAgentFilter`, `metadata.openclaw.requires` gating) [ev:atm-salvage#F7][ev:harness-cli-capabilities-b#F11]; Hermes `skills list --source builtin|hub|local` and `env_requires[{required, default}]` [ev:harness-cli-capabilities-b#F20]; Claude `stream-json system/init` `plugin_errors`/`mcp_server_errors` (docs) [ev:harness-cli-capabilities-a#F10]; `grok inspect` [ev:harness-cli-capabilities-a#F20]. ATM's `RequirementResolution` (`native | artifacts[] | emulated{degraded[]} | unsupported`) is the vocabulary precedent [ev:atm-salvage#F10].

**No secrets (AR-04).** Only names/references appear (`secrets_required`, `${ENV}`), matching every substrate's portable config: ClawTeam `api_key_env` [ev:clawteam-model#F25], OpenClaw SecretRef [ev:atm-salvage#F1], Hermes `env_requires` with `.env` hard-excluded from export [ev:claude-agent-teams-hermes-openbot#F24], Claude `.mcp.json` `${VAR}` [ev:harness-cli-capabilities-a#F6].

## 7. Harness preferences as data (AD-04, HB-03)

The definition carries the **Assistant-level** layer of the HarnessSelectionPolicy (the register's "role-level", HB-03); the User Overlay carries the **user-level** layer; the HarnessBroker supplies defaults and executes (`harness-broker-model.md`). Shape only:

```yaml
# harness-policy.yaml — illustrative, not a schema
preferred: [codex, claude-code]        # ordered
allowed:   [codex, claude-code, hermes, grok]
forbidden: [openclaw]                  # e.g. must not assume a Gateway
requires_capabilities: [headless, system_prompt, structured_output]   # HarnessCapability names per harness-broker-model §3
fallback: next-allowed                 # HB-04 semantics live in harness-broker-model
per_task_type:
  security-review: {preferred: [claude-code]}
  bulk-lint:       {preferred: [hermes], model_hint: cheap}
ensemble:
  review: {members: [codex, claude-code], synthesis: compare-disagreements}   # a wish, not a run
model_hints: {reasoning: high, cost: standard}   # portable intent, not model ids
```

Precedence (HB-03): user overlay `harness_policy` > this block > broker default, applied per invocation; a TeamTemplate layer (TC-06 team preferences, TC-05 "with which harnesses" for dynamic members) slots between the Assistant level and the default — `harness-broker-model.md` §5. Substrate precedents are partial: OpenClaw's per-agent `model{primary,fallbacks}` and `runtime{type: embedded|acp}` is policy-as-config but bound to one persistent OpenClaw agent and to an absent acpx plugin [ev:harness-cli-capabilities-b#F9][ev:openclaw-native-and-telegram-verification#F16]; ClawTeam's `AgentDef.command` is the *inverse* precedence (template member beats launch override) [ev:clawteam-probe-log#F17]; the fork's 7-level `resolve_model` chain selects models, not harnesses [ev:clawteam-openclaw-fork-delta#F15]; ATM's `modelPolicy{reasoningTier, costTier, preferredModels[]}` is the "intent, bound at materialization" idea reused for `model_hints` [ev:atm-salvage#F11]; the kit's "never pin a model" rule is the same stance [ev:openclaw-native-and-telegram-verification#F8].

## 8. Ephemeral Assistant (AD-07, TE-04, TE-07)

An Ephemeral Assistant is a *definition* with the same content model, created at run time by a Lead (who may create, how many, with which harnesses is the TeamTemplate's dynamic-member policy, TC-05, owned by `team-execution-model.md`). Definition-level rules:

- **Minimal content**: `summary`, `purpose`, inline `persona`/`principles` text, optionally `capabilities`/`skills`. It carries **no** origin or run facts: `origin: ephemeral`, `created_by` and `definition_ref` live on the Member/roster entry (`team-execution-model.md` §5; the archive roster in `architecture-options.md`), so the unchanged §4 validator applies to the Ephemeral Assistant exactly as to a persistent one.
- **Inheritance is enumerated**, not wholesale: `preferences`, `collaboration`, `presentation_defaults` and `evolution` default from the Lead's *effective* definition; `harness_policy` comes from the TeamTemplate's dynamic-member policy (TC-05 "with which harnesses"), not from the Lead; `permissions` default to the *narrower* of the Lead's and the dynamic-member policy's (§9: narrow only, never widen); `persona`, `purpose`, `principles` are never inherited — an Ephemeral Assistant is a different colleague. Anything still unset takes the broker default.
- **Hidden** is a Member property, not a definition property (TC-04); the definition is identical whether or not the user sees the Member.
- **Audit**: the full rendered text is written to the run archive with the spawning invocation (TE-07, XC-04), so a hidden Member is always reconstructable.
- **Promotion**: a human review may copy an Ephemeral Assistant into a persistent Base Definition (new `id@1`) after the §4 validator confirms it is run-fact-free; the provenance `{run, member}` is recorded in the promotion decision record (§9 step 6), not in the new Base Definition; nothing promotes automatically (AD-07: "need not become permanent packages").

Today's substrates create ephemeral workers, but as **task text without a definition object** (fit-gap G-AD-07): Claude `--agents '<json>'` is a session-only roster and background subagents leave transcripts under `~/.claude/projects/…/subagents/` [ev:harness-cli-capabilities-a#F7][ev:claude-agent-teams-hermes-openbot#F11]; Hermes `delegate_task` spawns fresh-context children from goal text and `--source tool` hides sessions [ev:claude-agent-teams-hermes-openbot#F22][ev:harness-cli-capabilities-b#F6]; OpenClaw sub-agents receive only `AGENTS.md` + `TOOLS.md` — no persona file [ev:openclaw-native-and-telegram-verification#F14] — and `sessions_spawn` announce delivery needs a running Gateway (harness-cli-capabilities-b §4; spawning under `--local` is UNVERIFIED); ClawTeam `spawn` registers a member whose full prompt is kept in `spawn_registry.json` but lists every member on the board [ev:clawteam-probe-log#F18][ev:clawteam-probe-log#F13]; dsh-gui forbids it ("planner may not create agents") [ev:dsh-agent-teams-and-gui#F26].

## 9. Pressure test — Evolution overlays (EV-01..EV-05)

### Scenario

`code-reviewer@3` is used in three projects: a Python service (A), a paper's analysis code (B), a training-script repo (C). Three things happen: (i) the owner wants findings "as a table grouped by severity, then narrative" — a stable, user-specific preference; (ii) across A and C the reviewer twice missed irreversible migrations and a run critique proposes "always check migration reversibility" — a project-independent review standard; (iii) in A the reviewer learned "migration 0042 drops `users.email` and cannot be reversed" — a project fact that must never persist (EV-04).

### Walkthrough — Hermes today

Hermes is the substrate with the most layering today (the only partial EV-02 cell in the fit-gap), so the scenario is run on it first. The reusable unit is a profile — `~/.hermes/profiles/<name>/` holding `config.yaml`, `.env`, `SOUL.md`, `memories/`, `sessions/`, `skills/`, `state.db` — optionally installed as a distribution whose `distribution_owned[]` paths (`SOUL.md`, `mcp.json`, `skills/`, `cron/`) are replaced on `profile update` while user-owned paths (`memories/`, `sessions/`, `.env`, …) are never touched [ev:harness-cli-capabilities-b#F19][ev:claude-agent-teams-hermes-openbot#F24]. **(i)** The user preference has two homes: `USER.md`, assembled into the volatile part of the system prompt, or a hand edit of `SOUL.md` [ev:harness-cli-capabilities-b#F17]; neither is field-scoped or shared across profiles (it is repeated per profile), and the `SOUL.md` edit is lost on the next `profile update` because that path is distribution-owned [ev:claude-agent-teams-hermes-openbot#F24]. **(ii)** The review standard has no place: the only moves are a hand edit of the distribution-owned `SOUL.md` (overwritten on update) or of the user-owned `agent.system_prompt` string in `config.yaml` (preserved on update, but a flat overlay string with no provenance, no Proposal, no review, no field merge) [ev:harness-cli-capabilities-b#F17][ev:claude-agent-teams-hermes-openbot#F24]; no Hermes component turns run experience into a proposed definition change — `curator` reviews agent-created *skills* with a ledger and rollback but no approval step [ev:claude-agent-teams-hermes-openbot#F28]. **(iii)** The project fact lands in `memories/` with no filter: excluded from export/distribution (packaging-time enforcement), but it stays on the profile and re-enters every later run on that profile; and because "Never point two agent processes at the same profile", per-run cloned profiles (`profile create --clone`) discard the memory together with the fact — learning and leak are coupled [ev:harness-cli-capabilities-b#F19][ev:claude-agent-teams-hermes-openbot#F24]. Net: (i) is expressible but not as an overlay, (ii) is not expressible as a reviewed change, (iii) is prevented only by isolating everything.

**Claude Code today (one line).** (i) and (ii) are hand edits of the subagent body; a user-level `~/.claude/agents/code-reviewer.md` does not overlay the project-level one — scope precedence (managed > `--agents` > project > user > plugin) selects *whole* definitions [ev:claude-agent-teams-hermes-openbot#F11]; (iii) with `memory:` lands in an agent-written `MEMORY.md` that is loaded into later contexts, with no filter and no review gate [ev:claude-agent-teams-hermes-openbot#F12].

**ClawTeam today (one line).** (i) and (ii) are edits to the `task` string of a TOML template, and a user template overrides a builtin *whole-file* by name [ev:clawteam-probe-log#F4]; (iii) has no slot — a fresh worker per spawn keeps nothing but its prompt in `spawn_registry.json` [ev:clawteam-probe-log#F13] — so nothing leaks and nothing is learned.

### Breakpoints in today's substrates

- **No overlay object anywhere** (fit-gap EV-02: no `S`/`C` cell). ClawTeam's only layering is a whole-file user template replacing a builtin by name [ev:clawteam-probe-log#F4]; Hermes offers two layers by path ownership (distribution-owned replaced on update, user-owned never touched) but no field merge inside `SOUL.md` and no reviewed third layer [ev:claude-agent-teams-hermes-openbot#F24]; Claude Code scopes select *whole* definitions (managed > `--agents` > project > user > plugin) [ev:claude-agent-teams-hermes-openbot#F11]; OpenClaw layers config (`agents.defaults` → `agents.list[]`) but persona files are single-layer, with `agent:bootstrap` as the one composition hook [ev:harness-cli-capabilities-b#F8][ev:harness-cli-capabilities-b#F9]; dsh-gui has versions with preview-first restore, not overlays [ev:dsh-agent-teams-and-gui#F19].
- **No Proposal, no human gate on automatic learning** (fit-gap EV-03). Claude subagent `memory:` is an agent-written file [ev:claude-agent-teams-hermes-openbot#F12]; OpenClaw `session-memory`/`MEMORY.md` writes are ungated [ev:harness-cli-capabilities-b#F14]; Hermes `curator` mutates agent-created skills with a ledger and rollback but no approval step [ev:claude-agent-teams-hermes-openbot#F28]; dsh-gui's retrospective is deliberately never applied [ev:dsh-agent-teams-and-gui#F29]; ClawTeam's plan round-trip is a human-gate primitive for *plans*, not definitions [ev:clawteam-model#F17].
- **No project-independence filter** (fit-gap EV-01): every memory slot holds whatever the model writes; Hermes' export-time exclusion of `memories/` is enforcement at packaging time, not a filter [ev:claude-agent-teams-hermes-openbot#F24].
- **Provenance and "applied == approved"** exist only as ATM ideas (typed proposals, MAC'd decisions, plan hashes), never executed [ev:atm-salvage#F15][ev:atm-salvage#F22].

### Minimal addition — Base + User Overlay + Reviewed Evolution Overlay

1. **Layers.** Base Definition (author-owned, §3). User Overlay: per-user, project-independent modifications. Reviewed Evolution Overlay: accepted Proposals, project-independent. All three are closed documents validated by §4.
2. **Merge order** to produce the *effective definition* for an instance: Base → Reviewed Evolution Overlay → User Overlay; later layers win where the field's policy allows override. Resolution is deterministic and hashed (the hash is recorded on the HarnessInvocation).
3. **Per-field conflict rules** (conflicts are flagged at review time, never merged silently):

| Field | Base | Reviewed Evolution Overlay | User Overlay | Conflict rule |
|---|---|---|---|---|
| `persona`, `purpose` | owns | read-only | read-only | overlay touching it is rejected |
| `principles`, `failure_modes` | owns | append | append | contradiction with base → rejected at review |
| `preferences` | user-independent defaults | append/override keys | override keys (user-specific modelled here only; §13 Q1) | user > evolution > base |
| `skills`/`capabilities`/`artifacts` | owns | add `preferred` only | add `preferred` only | may never remove or downgrade `required` |
| `permissions` | owns | none | narrow only | widening rejected |
| `collaboration` | owns | append habits | append | — |
| `harness_policy` | Assistant level | append preferences | user level | user > Assistant > default (HB-03; a TeamTemplate layer sits between Assistant and default, §7) |
| `presentation_defaults` | hints | none | override | — |

4. **Applying the scenario.** (i) lands in the User Overlay as `preferences.output`; it travels to A, B and C unchanged and is never a Proposal. (ii) is generated by an automatic actor as a Proposal (step 5), reviewed, accepted, and appended to `principles` in the Reviewed Evolution Overlay with provenance. (iii) is rejected by the project-independence check (names a migration id, a table and a column of one repo) and, had it slipped through, by the human reviewer; it stays in run A's archive only.
5. **Proposal generation from run experience.** After a run, a generator reads the run archive (reviewer findings, corrections the Lead or user made, harness outcomes) and emits bounded, typed Proposals:

```yaml
# proposal — illustrative, not a schema
id: 01J…                                 # dedupe key = (target, field, normalized change)
target: {assistant: code-reviewer, version: 3, layer: reviewed-evolution}
field: principles
change: {append: "Always check migration reversibility; flag irreversible schema changes as high severity."}
justification: "Missed irreversible migrations in 2 of 5 runs; both caught late by humans."
provenance: {runs: [run-2026-08-14-A, run-2026-08-19-C], generated_by: proposal-generator@1}
independence_check: {status: pass, hits: []}
status: pending                           # pending | accepted | rejected | superseded
```

   Volume is bounded per run (cap + dedupe) so reviewers are not flooded (EV-05).
6. **Review and acceptance.** A human accepts or rejects; the decision record stores `approved_by`, `at`, and the hash of the exact change applied ("applied == approved"); automatic actors only propose (EV-03, EV-05). Accepted entries carry `from_proposal` and `runs` (TeamRun ids — the §4 provenance exemption) in the overlay; a promotion (§8) is the same kind of decision record, with `{run, member}` as its provenance.
7. **What would be rejected** (illustrative): `{field: preferences, change: {set: {default_branch: "feature/0042-fix"}}, provenance: {runs: [run-A]}}` fails `independence_check` (branch name); `{field: permissions, change: {set: {network: allow}}}` is structurally rejected (widening); a Proposal to change `purpose` is rejected by the per-field table.

Illustrative overlay after acceptance:

```yaml
# overlays/code-reviewer.evolution.yaml — illustrative, not a schema
for: code-reviewer@3
layer: reviewed-evolution
entries:
  - field: principles
    append: "Always check migration reversibility; flag irreversible schema changes as high severity."
    from_proposal: 01J…
    runs: [run-2026-08-14-A, run-2026-08-19-C]
    approved: {by: owner, at: 2026-08-21, applied_hash: sha256:…}
```

**Summary of the addition.** Three conceptual objects and one function, all data-level: (1) an **Overlay document** = list of field-path operations (`append`, `override`, `narrow`) on the closed schema; (2) a **Proposal + decision record** with provenance, independence check, dedupe and a volume bound; (3) the **per-field merge policy** (table above) owned by the definition schema; (4) a deterministic **resolver** Base → Evolution → User → effective definition + hash. Borrowed pieces: Hermes' ownership split as the user-vs-package precedent, dsh-gui's never-applied retrospective as the "propose, don't mutate" precedent, ClawTeam's plan-approval round-trip as the scriptable human-gate primitive, ATM's proposal/approval integrity ideas.

## 10. Portability and identity (AD-06, MS-03)

Visible identity is a **presentation binding** created when a Member is shown on a Surface: `{member, surface, display_name, avatar, account_ref}` where `account_ref` is a secret *name*. The definition may carry `presentation_defaults` hints (§3), nothing else. Evidence: OpenClaw keeps `agents.list[].identity{name,emoji,theme,avatar}` as a separate config object (`agents set-identity --from-identity`) while `agentId` routes the brain and the channel account is the visible sender ("no per-agent sender identity" when accounts are shared) [ev:openclaw-native-and-telegram-verification#F3][ev:openclaw-native-and-telegram-verification#F20]; OpenBot separates `agent_profiles` from `agents` endpoints [ev:claude-agent-teams-hermes-openbot#F31]; the kit's `IDENTITY.md` conflates card fields with `Channel:`/`Model:` and is the anti-pattern [ev:openclaw-native-and-telegram-verification#F2]; ATM's "messaging identity ≠ runtime participant" is kept as the rule, its topology discarded [ev:atm-salvage#F13]. Portability of the definition itself is credential-free export/import of `assistant.yaml` + referenced files + lock (§6); the Hermes distribution exclusion list is the precedent [ev:claude-agent-teams-hermes-openbot#F24].

## 11. Mapping to substrates

Grounded in the definition-injection matrices [ev:harness-cli-capabilities-a#F17][ev:harness-cli-capabilities-b#F24] and the fit-gap AD/EV/AR rows. "no primitive — new" means the adapter renders it or the Core owns it.

| Concept | ClawTeam | Claude Code | Codex | OpenClaw | Hermes | dsh (teams / gui) |
|---|---|---|---|---|---|---|
| Assistant definition (whole) | no primitive; renders into `AgentDef.task` + `--skill`/`--append-system-prompt` (claude/pi only) [ev:clawteam-model#F13][ev:clawteam-spawn-platform#F6] | `.claude/agents/*.md` or `--agents '<json>'` (Claude-only; `skills`/`mcpServers` ignored as teammate) [ev:harness-cli-capabilities-a#F7][ev:claude-agent-teams-hermes-openbot#F10] | `.codex/agents/*.toml` (docs-only) or `-c developer_instructions` (unverified) [ev:harness-cli-capabilities-a#F7][ev:harness-cli-capabilities-a#F2] | per-agent workspace `SOUL.md`/`AGENTS.md`/`USER.md`/`IDENTITY.md` + `agents.list[]` entry [ev:harness-cli-capabilities-b#F8][ev:harness-cli-capabilities-b#F9] | profile `SOUL.md` + `config.yaml`; distribution package [ev:claude-agent-teams-hermes-openbot#F24] | teams: none (persona generated per run) [ev:dsh-agent-teams-and-gui#F15]; gui: `AgentRecord.systemPrompt` [ev:dsh-agent-teams-and-gui#F18] |
| Persona / principles / preferences | `## Task` string; the split is lost | subagent body, `--append-system-prompt(-file)`, `CLAUDE.md` via `--add-dir` | `AGENTS.md` at repo root or `$CODEX_HOME` [ev:harness-cli-capabilities-a#F4] | `SOUL.md` (+`USER.md` for prefs), 20k/60k char caps | `SOUL.md`; `HERMES_EPHEMERAL_SYSTEM_PROMPT` for a run overlay [ev:harness-cli-capabilities-b#F17] | gui: one `systemPrompt` (≤50 000) |
| Skills / artifacts | `--skill` inlines one SKILL.md (claude/pi); no field | `--add-dir` skills, `--plugin-dir`, `--mcp-config` [ev:harness-cli-capabilities-a#F5][ev:harness-cli-capabilities-a#F6] | `.agents/skills`, `[[skills.config]]`, `codex mcp add` [ev:harness-cli-capabilities-a#F5][ev:harness-cli-capabilities-a#F6] | `<workspace>/skills`, `agents.list[].skills`, `mcp.servers` [ev:harness-cli-capabilities-b#F11] | `<HERMES_HOME>/skills`, `mcp.json`, `env_requires` | none (gui `toolScope` names DSH tools) |
| Permissions | global `skip_permissions` → bypass flags [ev:clawteam-model#F25] | `--permission-mode/--allowedTools/--tools` [ev:harness-cli-capabilities-a#F11] | `--sandbox/--ask-for-approval` [ev:harness-cli-capabilities-a#F11] | `agents.list[].tools{allow,deny,profile}` [ev:harness-cli-capabilities-b#F14] | `--yolo`, `command_allowlist` [ev:harness-cli-capabilities-b#F21] | gui `toolScope{allow,deny}` [ev:dsh-agent-teams-and-gui#F18] |
| Collaboration behavior | protocol boilerplate + ClawTeam Skill, not per member [ev:clawteam-model#F16] | prose | prose | prose; `subagents{allowAgents}` | prose; kanban `--assignee` [ev:claude-agent-teams-hermes-openbot#F25] | gui `qualityGate`, handoff schema [ev:dsh-agent-teams-and-gui#F24] |
| Harness policy (Assistant level) | no primitive (`AgentDef.command` = binding) | no primitive (Claude only) | no primitive | partial: `model{primary,fallbacks}`, `runtime.acp` (acpx absent) | no primitive (`-m/--provider`, fallback chain = models) | no primitive (model route + one fallback) |
| Exclusion enforcement | 7-key TOML parser drops unknown keys [ev:clawteam-model#F13] | none; `memory:` persists an agent-written memory file *next to* the definition (location per docs, not captured) [ev:claude-agent-teams-hermes-openbot#F12] | none in evidence | contradicts (workspace = definition + memory + sessions) [ev:harness-cli-capabilities-b#F10] | partial: distribution excludes `.env/memories/sessions` [ev:claude-agent-teams-hermes-openbot#F24] | gui: strict zod schemas [ev:dsh-agent-teams-and-gui#F20] |
| AssistantInstance (fresh) | spawn with new `--session-id`; `--resume` opt-in [ev:clawteam-spawn-platform#F19] | `-p --bare`/`--no-session-persistence` | `exec --ephemeral` | new `--session-key` on a persistent OpenClaw agent, or disposable `--profile` [ev:atm-salvage#F4][ev:harness-cli-capabilities-b#F10] | `profile create --clone` or `HERMES_HOME=<tmp>` [ev:harness-cli-capabilities-b#F19] | teams: continuable child [ev:dsh-agent-teams-and-gui#F4]; gui: fresh child per dispatch [ev:dsh-agent-teams-and-gui#F21] |
| Ephemeral Assistant | `clawteam spawn` (prompt kept in registry; never hidden) | `--agents '<json>'`; hidden background subagent | `.codex/agents/*.toml` files only | `sessions_spawn` (no `SOUL.md` for the child; announce delivery needs a Gateway) | `delegate_task`, `--source tool` | teams: `add_member` [ev:dsh-agent-teams-and-gui#F15]; gui: blocked [ev:dsh-agent-teams-and-gui#F26] |
| Overlays (3 layers) | no primitive (whole-file override) | no primitive (scope precedence) | no primitive (`-c`/profiles = config) | no primitive (`agents.defaults`→`list`; `agent:bootstrap` hook) | partial: distribution-owned vs user-owned paths | no primitive (versions) |
| Proposal / review | no primitive (plan approval gate reusable) | no primitive | no primitive | no primitive (`skill-workshop/proposals/` unexplored) | no primitive (curator ledger, no gate) | no primitive (retrospective never applied) |
| Visible identity | member names only | `color`/`name` frontmatter | none | `agents.list[].identity` (separable; per persistent OpenClaw agent) | gateway token in `.env` (unnamed) [ev:harness-cli-capabilities-b#F24] | none |

**What is lost per substrate, one line each.** ClawTeam: persona, preferences, permissions, collaboration and harness policy fold into one `task` string plus a global bypass flag, and the system prompt is dropped for eight of ten CLIs [ev:clawteam-spawn-platform#F1]. Claude Code: the full structure survives by flag for Claude only; teammates ignore `skills`/`mcpServers`; `memory:` threatens AD-05 by adjacency — an agent-written memory file beside the definition, not inside it. Codex: only `AGENTS.md` and (unverified) `-c developer_instructions` carry text; skills/MCP need files or config. OpenClaw: persona/skills/identity/permissions materialize cleanly as workspace files, but the reusable unit *is* a persistent OpenClaw agent that accumulates memory and sessions (the persistent-agent tension, fit-gap AD-05 `M!`), and native sub-agents get no persona file. Hermes: the distribution is the closest package format, but it is Hermes-shaped, memory/sessions live in the same profile directory, and concurrent instances need cloned profiles.

## 12. What is new vs borrowed

| Concept | Borrowed from (system + mechanism) | New? |
|---|---|---|
| Assistant ≠ Skill | OpenBot "a skill is something a Bot is told" [ev:claude-agent-teams-hermes-openbot#F32]; Agent Skills spec has no persona fields [ev:atm-salvage#F8] | distinction borrowed; harness-neutral definition object new |
| Content model sections | OpenClaw `SOUL`/`AGENTS`/`USER`/`IDENTITY` split [ev:harness-cli-capabilities-b#F8]; ATM role-template by reference [ev:atm-salvage#F11]; Claude subagent frontmatter [ev:claude-agent-teams-hermes-openbot#F11] | section vocabulary borrowed; neutral container + per-field edit policy new |
| Exclusion enforcement | dsh-gui strict schemas [ev:dsh-agent-teams-and-gui#F20]; Hermes distribution exclusions [ev:claude-agent-teams-hermes-openbot#F24]; ATM AT-13 byte-identical [ev:atm-salvage#F19] | closed schema borrowed; content validator new |
| Assistant / Instance / Member split | dsh-gui definition tables vs run ledger [ev:dsh-agent-teams-and-gui#F21]; ATM ADR 0016 [ev:atm-salvage#F9] | borrowed as idea |
| Fresh-by-default instance | ClawTeam `--session-id`/`--resume` [ev:clawteam-spawn-platform#F19]; Claude `--bare`; Codex `--ephemeral` [ev:harness-cli-capabilities-a#F19] | borrowed (adapter-materialized on OpenClaw/Hermes) |
| Capability vs Artifact | ATM ADR 0022 `requires.capabilities[]`/`requires.artifacts[]` [ev:atm-salvage#F10] | idea borrowed; no substrate primitive — new |
| Artifact kinds / sources | OpenClaw/Hermes/Claude/Codex skill, plugin, MCP installers [ev:harness-cli-capabilities-b#F11][ev:harness-cli-capabilities-a#F5] | sources borrowed; cross-harness manifest new |
| Lock / fingerprint | ClawTeam `skills-lock.json` shape (ClawTeam/skills-lock.json:1-10); ATM `ArtifactLock` [ev:atm-salvage#F10] | shape borrowed; consumed lock new |
| Resolution report | OpenClaw `skills list --json` eligibility [ev:harness-cli-capabilities-b#F11]; Hermes `env_requires` [ev:harness-cli-capabilities-b#F20]; ATM `RequirementResolution` [ev:atm-salvage#F10] | inputs borrowed; per-definition report new |
| No secrets | every substrate's env-name references (fit-gap AR-04 row) | borrowed |
| Harness policy as data | OpenClaw `model{primary,fallbacks}`/`runtime.acp` [ev:harness-cli-capabilities-b#F9]; ATM `modelPolicy` intent [ev:atm-salvage#F11]; fork `resolve_model` chain [ev:clawteam-openclaw-fork-delta#F15] | partial shapes borrowed; Assistant/user/default harness policy new |
| Ephemeral Assistant | Hermes `delegate_task`, Claude `--agents`, OpenClaw `sessions_spawn` [ev:claude-agent-teams-hermes-openbot#F22][ev:harness-cli-capabilities-a#F7][ev:openclaw-native-and-telegram-verification#F15] | spawn mechanisms borrowed; definition object + promotion path new |
| Overlays + merge policy | Hermes ownership split [ev:claude-agent-teams-hermes-openbot#F24]; OpenClaw `agent:bootstrap` [ev:harness-cli-capabilities-b#F8] | two-layer precedent borrowed; three-layer field merge new |
| Proposal + review | dsh-gui never-applied retrospective [ev:dsh-agent-teams-and-gui#F29]; ClawTeam plan approval [ev:clawteam-model#F17]; Hermes curator ledger [ev:claude-agent-teams-hermes-openbot#F28]; ATM proposal integrity [ev:atm-salvage#F15] | primitives borrowed; Proposal object + independence filter new |
| Visible identity binding | OpenClaw `agents.list[].identity` [ev:openclaw-native-and-telegram-verification#F3]; OpenBot `agent_profiles` [ev:claude-agent-teams-hermes-openbot#F31]; ATM ADR 0024 [ev:atm-salvage#F13] | separability borrowed; per-Member binding new |

## 13. Open questions

1. Should user-specific preferences ever be allowed in a *Base* Definition (AD-01 says "user-independent or user-specific"), or always forced into the User Overlay as modeled here? Affects whether a single-user owner needs overlays at all.
2. Permissions as harness-neutral intent (`filesystem/network/shell`) vs per-harness flag bundles: is three-valued intent expressive enough for Codex sandbox modes and OpenClaw `tools.exec.mode`? (→ `harness-broker-model.md`.)
3. Project-independence check: heuristics only, or also a model-based classifier? A false negative (project fact reaches a Proposal) is caught by human review; a false positive loses learning.
4. Does a Reviewed Evolution Overlay belong to the Assistant globally or per user (shared review standard vs personal learning)? The merge order above assumes global evolution and a personal User Overlay.
5. Whether `claude --agent <name>` accepts an agent defined only via `--agents '<json>'` (harness-cli-capabilities-a open question 1) and whether Codex honors `-c developer_instructions` decide how cheaply the content model reaches those two harnesses.
6. Hermes: does `--ignore-rules` suppress memory *writes* on a shared profile (harness-cli-capabilities-b open question 4)? Decides whether cloned profiles are mandatory for AD-05 on Hermes.
7. ATM schema text (role-template, ADR 0022) may be reused verbatim only after a licence statement (XC-01); this document reuses ideas, not text.

## 14. Inconsistencies noted

- `claude-agent-teams-hermes-openbot.md` F23 suggests Hermes `M~` on AD-05 (the profile conflates `SOUL.md` with `memories/`/`sessions/`), while the fit-gap cell is `C!` on the strength of the distribution's exclusion list. This document follows the fit-gap cell and treats the *profile* (runtime unit) as conflating and the *distribution* (package) as separating — both statements hold for different objects, as the fit-gap rationale says.
- The fit-gap rates OpenClaw `C!` on AD-04 (policy as data) and `M!` on AD-02 (neutral requirement vocabulary) for config that lives in the same `agents.list[]` object. That is a difference of reading (presence of a policy object vs neutrality of its container), not a contradiction; this document uses OpenClaw only as the shape precedent for §7 and does not treat it as satisfying "no permanent binding".
- (resolved in the W3 owner pass) `existing-systems-fit-gap.md` AR-06 now cites `ClawTeam/skills-lock.json:1-10` directly; the content matches the file read for this document.
- No conflict with the AD/EV/AR matrix cells was found. The "best" systems named in the roll-ups are HM for AD-01/07, OC for AD-04/06/09 and DG for AD-05/08; §12 borrows from them where the mechanism is reusable, but borrows AD-09's separation from OpenBot (plus the Agent Skills spec) and AD-01's section vocabulary from OpenClaw/ATM/Claude — the fit-gap "best" column and the borrow column are different questions.
