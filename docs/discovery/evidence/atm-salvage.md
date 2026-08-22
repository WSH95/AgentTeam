---
id: ev:atm-salvage
topic: Requirements, verified facts and ADR ideas salvaged from the superseded ATM experiment (agent-team-manager-dev)
systems: [ATM (agent-team-manager-dev), OpenClaw 2026.7.1-2, Telegram Bot API, Agent Skills spec]
sources:
  - {kind: repo, ref: agent-team-manager-dev@12a727e (35 commits, 2026-08-19..21), accessed: 2026-08-22, version: 0.0.0 private}
  - {kind: probe, ref: agent-team-manager-dev/tests/fixtures/openclaw/2026.7.1-2-*.json (recorded by ATM spikes S1–S4 on disposable profiles), accessed: 2026-08-22, version: OpenClaw 2026.7.1-2}
  - {kind: web, ref: https://core.telegram.org/api/bots/bot-to-bot, accessed: 2026-08-22}
  - {kind: web, ref: https://core.telegram.org/bots/api (Getting updates), accessed: 2026-08-22}
  - {kind: web, ref: https://agentskills.io/specification, accessed: 2026-08-22}
  - {kind: cli, ref: "openclaw --version; claude --version; codex --version; hermes --version; grok --version; node --version; tmux -V", accessed: 2026-08-22}
method: Read-only deep read of ATM docs/adr (26 ADRs), docs/design (13 docs), schemas/ (17 JSON Schemas dumped with python3), examples/demo-dev-team, .project-steward/{QUESTIONS,RISKS,HANDOFF,PLAN,PROGRESS,VERIFY,DECISIONS}.md, packages/*/src, tests/fixtures/openclaw (keys and non-secret values only; credential-like keys redacted); git log; greps for absent concepts; web re-verification of ATM's V10/V11/V13 claims.
platform: {os: Ubuntu 20.04.6 (Linux 5.15.0-139), tmux: absent, cli_versions: {openclaw: 2026.7.1-2 (0790d9f), claude-code: 2.1.239, codex: 0.148.0, hermes: 0.20.4, grok: 1.0.5, node: v24.16.0, project-steward: 0.3.2}}
author_agent: ev:atm-salvage
date: 2026-08-22
confidence: high
status: draft
---
# ATM salvage — facts, requirement candidates and failure evidence from the superseded experiment

## 1. Scope & questions

- Which OpenClaw 2026.7.1-2 / Telegram / Agent-Skills facts did ATM verify at probe level that our MS/HB/AR rows can cite? → HB-01, HB-02, MS-02, MS-04, AR-02, AR-03, XC-02.
- Which ATM requirements/ideas survive as *requirements* (never architecture)? → AD-02, AD-04, AD-05, AD-08, TC-02, TC-03, TC-05, AR-01…AR-05, EV-02, EV-03, EV-05, XC-04.
- What failed, why, with what evidence (U2, U10, exit-137)? → TC-03, TE-06, EV-01, XC-04.
- Which ATM concepts are demoted/discarded (feeds `legacy-atm-disposition.md`)? → all layers.
- Corrections to `recon-appendix.md` are in §3 and the structured summary.

## 2. Findings

### (A) Verified facts about OpenClaw / Telegram / Agent Skills from ATM spikes

### F1. Feasibility matrix V1–V15 restated
- Claim: ATM verified 15 questions against installed OpenClaw 2026.7.1-2 and official docs (2026-08-19):

| V | Claim (condensed) | Verdict | ATM source | Ours |
|---|---|---|---|---|
| V1 | Gateway WS protocol v4: `config.get/patch/apply`, `agents.*`, `sessions.*`, `chat.send`, `health`; scopes `operator.read/write/admin`; control-plane writes **3 per 60 s** | ✅ | docs.openclaw.ai/gateway/protocol | HB-01, MS-02 |
| V2 | `openclaw config get|set|patch|unset|file|schema|validate`, `--dry-run`, `--json` | ✅ | /cli/config | HB-01, HB-02 |
| V3 | Per-agent `workspace`, `agentDir` ("Never reuse agentDir"), `model`, `identity`, `tools.allow/deny`, `skills`, `sandbox`, `subagents`; top-level `bindings` | ✅ | /concepts/multi-agent | HB-01, AD-06, MS-03 |
| V4 | Docs ≠ installed schema: `agents.entries` vs `agents.list`; `tools.` vs `session.agentToAgent` | ⚠️ drift | local `config schema` | HB-01, XC-02 |
| V5 | `sessions_spawn` (depth 1 default, max 5; ≤8 concurrent), `sessions_yield`, `sessions_send/list/history/status`; agentToAgent **off by default**, allowlisted; **no native "team" construct** | ✅ thin | /tools/subagents | TE-04, TE-05, TC-05 |
| V6 | `--profile <name>` → `~/.openclaw-<name>`; multi-gateway ≥20 ports apart | ✅ | /gateway/multiple-gateways | TE-07, XC-02 |
| V7 | `${ENV}` substitution; SecretRef `env|file|exec|store`; telegram `tokenFile` | ✅ | /gateway/configuration | AR-04 |
| V8 | Safe config hot-apply; `gateway.*`/plugins need restart | ✅ | — | HB-01 |
| V9 | Agent Skills dirs; precedence `<workspace>/skills` → `<workspace>/.agents/skills` → `~/.agents/skills` → `~/.openclaw/skills` → bundled; extension `metadata.openclaw` (`requires.bins/env/config`) | ✅ | /tools/skills | AR-02, AR-03, HB-02 |
| V10 | Spec: only `name`+`description` required; optional `license`, `compatibility`, `metadata`, `allowed-tools`; **no `version` field**; SKILL.md <500 lines; refs one level deep | ✅ re-verified web 2026-08-22 | agentskills.io/specification | AR-02, AR-03 |
| V11 | Bots **can** see other bots via opt-in *Bot-to-Bot Communication Mode* (BotFather); delivery on `/command@TargetBot` or reply; admin bot with privacy off receives all | 🔁 corrected; re-verified web (page warns of "infinite reply loops") | core.telegram.org/api/bots/bot-to-bot | MS-02, MS-04 |
| V12 | Bot API cannot create groups (MTProto user-only), create bots/tokens, toggle privacy/bot-to-bot (BotFather); after human adds admin bot: `promoteChatMember`, `setChatPermissions`, `createForumTopic` | ✅ | core.telegram.org/bots/api | MS-02 |
| V13 | `getUpdates` vs webhook **mutually exclusive** per token; never poll a gateway-owned token; validate via `getMe`/`getWebhookInfo`; ~1 msg/s per chat, 20/min per group | ✅ re-verified web | /bots/api#getting-updates | MS-02 |
| V14 | No plugin needed; "External apps should not import `openclaw/plugin-sdk/*`" | ✅ | /plugins/architecture | HB-08, XC-03 |
| V15 | "not a hostile multi-tenant security boundary"; hardened baseline (`dmPolicy: pairing`, `requireMention`, `tools.deny`, sandbox `mode: all`, `subagents.allowAgents`); `security audit --deep` | ✅ | /gateway/security | TC-03, XC-04 |

- Evidence: agent-team-manager-dev/docs/design/feasibility-report.md:22-38; web re-checks §6.
- Level: observed (V1–V9, V12, V14, V15); verified-web (V10, V11, V13).
- Requirements: per column.
- Suggested fit cell: OpenClaw→S~ (per-agent isolation, skills, SecretRef, profiles); OpenClaw→M~ (no team construct, V5).

### F2. S1/U1/U11 — installed config path and agent-id constraints
- Claim: `config patch --dry-run` accepted `agents.list`, rejected `agents.entries` (`schema: - agents: Unrecognized key: "entries"`, exit 1). `agents add` materialized a lowercase id matching `^[a-z0-9][a-z0-9_-]{0,63}$` (invalid runs → `-`, leading invalid stripped, `_` kept, truncated at 64); `agents.list[].description` accepts a marker with no declared max; stdout pure JSON; `skills list --json` → 53 bundled skills.
- Evidence: tests/fixtures/openclaw/2026.7.1-2-s1-evidence.json (`u1.dryRun`, `u11.observedConstraints`, `skillsListCount`); .project-steward/QUESTIONS.md:10-13, 66-76.
- Level: verified (recorded probe).
- Requirements: HB-01, MS-03, XC-02.
- Suggested fit cell: OpenClaw→S! (per-Member agent materialization), schema-first caveat.

### F3. S2/U4 — `agents add` hot-apply; no per-agent send attribution
- Claim: new agent + Telegram binding visible immediately via `agents list --json --bindings` and gateway `agents.list`, and after restart; created `agents/<id>/sessions`, a git-initialised workspace, `openclaw.json.bak`, but **not** the explicit `--agent-dir`. `message send --agent` rejected ("does not recognize option `--agent`"); channel `--dry-run` cannot prove which agent handled a message.
- Evidence: 2026.7.1-2-s2-evidence.json (`u4.hotApply`, `u4.messageSend`, `u4.nonConfigProvisioning`); QUESTIONS.md:33-44.
- Level: verified.
- Requirements: HB-01, MS-02, MS-03.
- Suggested fit cell: OpenClaw→S! (agent CRUD); OpenClaw→Xs! (per-Member outbound attribution).

### F4. S3/U9 — deterministic, messaging-free session addressing
- Claim: `openclaw agent --agent <agent-id> --session-key <tuple-key> --message … --thinking off --json` drives a specific context, rediscovered as `agent:<agent-id>:<tuple-key>`; same key twice preserved state, distinct keys stayed distinct; survived restart and state-map deletion; no messaging surface used.
- Evidence: 2026.7.1-2-s3-evidence.json (`addressingRule`, `u9`); QUESTIONS.md:49-55; collaboration-choreography.md:91-96.
- Level: verified.
- Requirements: HB-02, TE-02 (fresh vs resume controllable by key), MS-01.
- Suggested fit cell: OpenClaw→S! (headless invocation, opt-in resume).

### F5. S3/U10 — `unsupported` (verbatim) and the two candidate facts
- Claim (verbatim): "U10 — Resolved 2026-08-20 — `unsupported` on OpenClaw 2026.7.1-2: … Native project sessions on a persistent role agent fail workspace and A2A confinement. Role-by-project agents isolate workspaces, but OpenClaw's global `tools.agentToAgent.allow` membership permits cross-project delivery, so they fail A2A confinement. Neither satisfies ADR 0017". Fixture: candidate A `projectScopedWorkspaceVisibility:false, a2aConfinement:false`; candidate B workspace `true`, A2A `false`; both `independentSessionState/restartSurvival/rediscovered…:true`.
- Evidence: QUESTIONS.md:56-65; 2026.7.1-2-s3-evidence.json (`candidateA/B`, `projectContextIsolation:"unsupported"`); RISKS.md:10.
- Level: verified.
- Requirements: AD-05, TE-02, MS-04, TC-03.
- Suggested fit cell: OpenClaw→S! (per-agent workspace/session isolation); OpenClaw→M! (mechanical per-pair A2A confinement in one gateway).

### F6. S3b/U16 — public surfaces insufficient; test-only router works mechanically only
- Claim: per-agent tool policy "removes bypasses but does not route"; session-send policy matchers only `channel, chatType, keyPrefix, rawKeyPrefix`; an MCP probe received no trusted source tuple. A test-only plugin tool `atm_project_send({targetRole,message})` deriving source from runtime `agentId`/`sessionKey` passed forgery/cross-project/forbidden-edge/raw-bypass/restart/rediscovery gates (`result:"supported-by-test-only-router"`), but `modelToolDeliveryObserved:false`.
- Evidence: 2026.7.1-2-s3b-evidence.json (`publicSurfaces`, `router`, `u16`); QUESTIONS.md:81-102; docs/adr/0023:44-60.
- Level: verified (mechanical); observed (model part).
- Requirements: TC-03, XC-04, HB-01.
- Suggested fit cell: OpenClaw→XL! (hard reviewer independence needs a plugin); OpenClaw→C! (trusted routing via route catalogs).

### F7. Fixture shapes usable as HarnessProfile evidence
- Claim: `agents list --json` rows `{id, name?, workspace, agentDir, bindings, isDefault}`; gateway `agents.list` `{defaultId:"main", scope:"per-sender", agents[]}`; `skills list --json` `{workspaceDir, managedSkillsDir, skills[{name, description, emoji, eligible, disabled, blockedByAllowlist, blockedByAgentFilter, modelVisible, userInvocable, commandVisible, source, bundled, homepage, missing}]}` (per-agent skill visibility flags); `config schema` draft-07, 2.4 MB, top-level `agents, tools, security, bindings, session, skills, plugins, mcp, acp, approvals, hooks, channels, gateway, memory…`; `sessions list` `{path, stores[], sessions[], count, hasMore}`.
- Evidence: -s1-agents-list.raw.json; -s2-immediate-gateway-agents-list.raw.json; -s1-skills-list.raw.json; -s1-config-schema.raw.json; -s3-sessions-*.raw.json.
- Level: verified.
- Requirements: HB-01, AR-05, MS-02.
- Suggested fit cell: OpenClaw→S! (introspection for a HarnessProfile).

### F8. Agent Skills spec constraints (re-verified)
- Claim: `name` (≤64, lowercase/digits/hyphens, equals directory name) and `description` (≤1024) required; `license`, `compatibility` (≤500), `metadata` (string→string; `version` by convention only), `allowed-tools` (experimental) optional; "Keep your main `SKILL.md` under 500 lines"; "Keep file references one level deep". ATM's vendored fixture complies (`examples/demo-dev-team/artifacts/local/code-review-checklist/SKILL.md:1-4`).
- Evidence: https://agentskills.io/specification (2026-08-22); feasibility-report.md:33.
- Level: verified-web.
- Requirements: AR-02, AR-03, AD-09 (a Skill has no persona/policy fields).
- Suggested fit cell: n/a.

### (B) Requirement candidates with our IDs

### F9. ADR 0016: definition ≠ runtime agent; materialization recorded per invocation
- Claim: "`RoleDefinition` is a portable description … carries no runtime identity and no persistence assumption"; materialization declared via `role_persistence` (`persistent | project-lifetime | either`), recorded as `(namespace, team, role[, project]) → runtime-opaque reference` + resolved model binding, "never written back into core models". Pressure test: four lifecycle shapes (OpenClaw persistent agent; Claude Agent Teams fresh per project; DeepSeek Harness either; Hermes profile+session), zero runtime-specific core fields.
- Evidence: docs/adr/0016:11-13; runtime-portability-pressure-test.md:13-24, 75-82.
- Level: observed.
- Requirements: AD-05, AD-08, HB-02, HB-07, HB-08, TE-02.
- Suggested fit cell: ATM→n/a (idea only).

### F10. ADR 0022: semantic capability vs explicit artifact; lock; readiness
- Claim: `requires.capabilities[] {capability, level: required|preferred, params?}` vs `requires.artifacts[] {ref, version?, level}` — "adapters must never silently substitute"; `skills:` shorthand normalises to kind `agent-skill`. `ArtifactSpec = {id, kind (open: agent-skill, runtime-plugin, mcp-server, cli-binary, script-package, role-support-package, model-provider-extension), source (registry{registry,name,versionConstraint} | git{repo,subdir?,ref} | local{path ^artifacts/local/}), integrity sha256, compatibility{runtimes[], platforms{os[linux|darwin|win32], arch[x64|arm64]}}, requires{bins, runtimes[{name,range}], env}, install{policy: auto|approval-required|manual}, secrets[{ref, contract}], provides{capabilities}}`. Outcomes: capability → `native | artifacts[1..n] | emulated{strategy, degraded[]} | unsupported`; artifact → `exact | unsupported|incompatible-runtime|incompatible-platform|missing-prerequisite|missing-secret|unspecified|version-conflict`. `ArtifactLock` entries `{id, kind, resolved (registry name@version | git commit | local path), digest, resolvedAt, selections[{capability, runtime}], provenance}`; readiness `materialized-and-dependency-ready | -missing-required | -degraded-preferred | artifact-failed-verification`; fingerprints `clean | locally-modified | unknown/unmanaged` ("blocks destructive replacement"); migration preference "portable agent-skill → portable MCP/service → runtime-specific plugin".
- Evidence: docs/adr/0022:11-27; capability-artifact-model.md:9-12, 36-55, 58-63, 94-98, 131-136; schemas/{artifact-spec,requirement-resolution,artifact-lock}.schema.json.
- Level: observed (schemas executable, never exercised at runtime).
- Requirements: AR-01 (near-verbatim), AR-02, AR-03, AR-04, AR-05, AD-02. **Register gap candidates:** portable lock/reproducibility layer; local-modification safety; host-platform vs harness compatibility as independent dimensions; per-host migration report.
- Suggested fit cell: ATM→n/a.

### F11. Top-level fields of the other ATM schemas (metadata ideas)
- Claim (python dump; all `additionalProperties:false`, `x-*` allowed):

| Schema | Fields |
|---|---|
| `role-template` frontmatter | `name*`, `summary`, `metadata{string→string}`; body = instructions; `allowed-tools` explicitly invalid ("host-agent concern") |
| `team-definition` | `spec.roles[]{name*, purpose*, template* (^role-templates/…\.md), modelPolicy, requires{capabilities,artifacts}, skills[], steward{grants[]}}`; `collaboration{bus: runtime-a2a|none, topology.allow[[a,b]], spawn{intraRole, maxDepth 0..5}}`; `defaults.projectPolicy{isolation{level: strict, communication: trusted-runtime|hard}, access{role: rw|ro}}`; `capabilityRequirements[]` |
| `project-definition` | `spec{teamRef*, source*{type: local-git|remote-git|dir, location, initIfMissing}, access, isolation, overrides.roles, surfaces[], lifecycle: active|archived}` |
| `defs` | `name ^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$`, `secretRef`, `modelPolicy{reasoningTier: low|medium|high, codingCapability: unneeded|preferred|required, costTier: economy|standard|premium, preferredModels[]}`, `sha256Digest`, `ulid`, `relpath` |
| `artifact-catalog` | `spec.artifacts[ArtifactSpec]` |
| `surface-spec` | `type*, mode*: dm|group|topic, identity{secretRef*}, features[]` |
| `export-manifest` | `formatVersion:1, exportedAt, contents[{path,sha256}], requiredSecretRefs[] (names only), sourceNamespace` |
| `deployment-record` | `namespace, namespaceEncoding, team, runtime{adapter,version,targetFingerprint}, materializations[{tuple,runtimeRef,modelBinding,generation}], artifacts[{id,tupleScope,installRef,generation,fingerprint,classification,verifiedAt}], appliedPlans[], verifications[]` |
| `plan` / `approval-record` | `planHash, basisSnapshotHash, manifestHashes, basisArtifactLockHash, proposedArtifactLock, resolutions[], actions[{id,kind,servesTuples,summary,params,risk,humanSteps}], validity{approvable,blockers,warnings}`; approval adds `approvedBy, approvedAt, auth{alg: hmac-sha256, keyRef, mac}` |
| `management-proposal` | `id (ulid), author{team,role}, intent ∈ {add_role, remove_role, update_role_policy, change_collaboration_policy, create_project, archive_project, request_surface_change}, payload (typed), justification, createdAt` |

- Evidence: schemas/*.schema.json (17 files, 1,681 lines); docs/design/schemas.md:54-124, 264-276, 373-376.
- Level: observed.
- Requirements: AD-01/AD-02 (role-template), AD-03 (access, topology), TC-02 (directed edges), TC-05 (`spawn{intraRole,maxDepth}` precedent), AD-04/HB-03 (modelPolicy intent), MS-03 (`identity.secretRef`), EV-03/EV-05 (typed proposal + MAC'd decision), XC-04, AR-03/AR-04 (export with secret *names*).
- Suggested fit cell: ATM→n/a.

### F12. Example shapes (role template, team, dependencies, vendored Skill)
- Claim: `role-templates/reviewer.md` = frontmatter `{name, summary, metadata.version}` + *Responsibilities* / *Working rules*; every template says "Work strictly within the current project's context … (This rule reinforces — but does not implement — the platform-enforced project isolation.)". `teams/demo-development.yaml`: three roles by `template:` reference, `topology.allow: [[lead,implementer],[lead,reviewer]]` (reviewer↔implementer edge deliberately absent), `spawn {intraRole:true, maxDepth:1}`, `access {lead: rw, implementer: rw, reviewer: ro}`; only the reviewer requires `{ref: code-review-checklist, level: required}`. `artifacts/dependencies.yaml`: one vendored `agent-skill`, `compatibility.platforms.os: [linux, darwin]`, `install.policy: auto`, `provides.capabilities: [structured-code-review]`.
- Evidence: examples/demo-dev-team/role-templates/*.md; teams/demo-development.yaml:15-60; artifacts/dependencies.yaml:8-17; artifacts/local/code-review-checklist/SKILL.md.
- Level: observed.
- Requirements: AD-01, AD-03, AD-08, TC-01, TC-02, TC-03 (edge absence = independence), AR-03.
- Suggested fit cell: ATM→n/a.

### F13. ADR 0024: messaging identity ≠ runtime participant ≠ route
- Claim: "Messaging Role Identity = (Team, Role); Runtime Participant = (Team, Project, Role); Project Route = routing discriminator"; Telegram default one group, one bot per role, Projects as Topics; per-Project bot identity "explicitly reported degraded fallback, never the default"; "Missing, stale, or ambiguous project routing fails closed".
- Evidence: docs/adr/0024:17-49.
- Level: observed.
- Requirements: MS-03, MS-04, AD-06.
- Suggested fit cell: ATM→n/a (topology itself demoted).

### F14. ADR 0026: isolation level vs communication posture; honest emulation
- Claim: `isolation.level: strict` (independent session + project-scoped workspace per tuple, surviving restart/rediscovery) separated from `isolation.communication: trusted-runtime | hard`; `hard` "must not silently fall back"; every `via: emulated` resolution "includes an explicit `degraded` array; `[]` states that no residual degradation is known".
- Evidence: docs/adr/0026:28-69; schemas/rule-ids.md:48-49.
- Level: observed.
- Requirements: TC-03 (declare enforcement level), AR-05, XC-04. **Register gap candidate:** isolation posture (advisory vs mechanical reviewer independence) with fail-closed semantics.
- Suggested fit cell: ATM→n/a.

### F15. ADR 0010/0011/0021: trust zones, hostile proposals, approval integrity
- Claim: zones Z0 operator (sole approval authority) → Z1 controller (only mutating zone) → Z2 runtime → Z3 team agents (Z3s steward = Z3 + "exactly one grant: writing proposal files") → Z4 messaging (untrusted). Proposals: typed intents only ("patch/diff/path-based intents are structurally unrepresentable"), authorization from the manifest never the proposal, decisions MAC'd with an operator-held key — "self-approval is structurally impossible — by authentication, not by hashing"; bounded blast radius (dir cap, ULID dedupe). Plans pinned by `planHash/basisSnapshotHash/manifestHashes/basisArtifactLockHash`; staged apply re-validation, "any mismatch aborts with zero mutations"; interrupted apply ⇒ new plan + new approval; lease lock `{ownerToken, pid, host, acquiredAt, leaseExpiresAt}` TTL 60 s.
- Evidence: docs/adr/0010:11-13; security-trust-boundaries.md:9-29; docs/adr/0011:11-16; docs/adr/0021:13-35.
- Level: observed.
- Requirements: EV-03, EV-05, XC-04. **Register gap candidates:** "what is applied == what was approved" for evolution proposals; automatic actors propose / only humans approve; bounded proposal spam.
- Suggested fit cell: ATM→n/a.

### F16. ADR 0013 + portability-dr: portable workspace, export/import, DR
- Claim: portable set = definitions, role templates, catalog + vendored trees, lock, proposals/decisions (✅); deployment records (✅ rebuildable); secrets (❌ by logical name); runtime sessions (❌). `atm export` = tarball + `atm-export.json` (hashes, `requiredSecretRefs` names only); import verifies digests, "re-point secretRefs", rejects "state but no manifests". Four DR scenarios. "Not migrated by design: conversation state".
- Evidence: portability-dr.md:9-20, 26-28, 32-39; docs/adr/0013:11-13.
- Level: observed.
- Requirements: AR-03, AR-04, TE-07, EV-04. **Register gap candidate:** credential-free definition export/import archive.
- Suggested fit cell: ATM→n/a.

### F17. ADR 0007 + adapter-contract: capability classes and query names
- Claim: behaviours classify `native | emulated(strategy) | unsupported(reason)`; provisioning `native | partially-automated | manual | unsupported` (manual ⇒ `BootstrapInstruction[] {id,title,steps,verify}`); modelPolicy `satisfied | degraded(gaps) | unsupported`; "the plan must display the strategy chosen". Queries: `role_persistence, project_context_isolation, a2a_messaging, subagent_spawn, tool_scoping, sandboxing, skill_injection, artifact_install:<kind>, restart_persistence, surface_binding`; messaging features `human_interaction, role_identities, bot_to_bot_visibility, public_peer_discussion, topics_or_threads, approvals, notifications`.
- Evidence: docs/adr/0007:11-16; adapter-contract.md:11-18, 60-71.
- Level: observed.
- Requirements: HB-01 (HarnessCapability candidates), HB-03/HB-04, AR-05, MS-02.
- Suggested fit cell: ATM→n/a.

### F18. ADR 0002/0003/0004/0005/0008: core-neutrality disciplines
- Claim: unknown core fields rejected except `^x-[a-z0-9-]+$` blocks "never required for correct operation"; "Long role instructions live in reusable role-template files, never inline manifest blobs"; four planes (desired / deployment / runtime / secrets) with late-binding `SecretProvider.materialize(ref)` → env name or 0600 file; skill-first surface "defines the interaction model, not process lifetime" — no required daemon, optional watch mode later; Node ≥20 "must not be justified by 'OpenClaw guarantees Node'".
- Evidence: docs/adr/0004:11; 0005:11; 0008:11-20; 0002:11-13; 0003:11.
- Level: observed.
- Requirements: AD-02, AD-09, HB-08, AR-04, MS-01, LO-01, XC-02.
- Suggested fit cell: ATM→n/a.

### F19. ADR 0017 + AT-11/AT-13: isolation verified, definitions byte-identical
- Claim: "Prompt instructions are never an isolation boundary"; AT-11 plants contradictory `PROJECT-FACTS.md` (alpha "port 1111, HERON"; beta "port 2222, OTTER") and asserts zero leakage across roles × projects × {normal, post-A2A, post-restart, post-rediscovery}; "Two distinct session IDs existing is explicitly insufficient evidence". AT-13: project add/archive leaves `teams/demo-development.yaml` **byte-identical**.
- Evidence: docs/adr/0017:12-14; milestones.md:28-30; examples/demo-dev-team/projects/alpha.yaml:5-8.
- Level: observed (designed, never executed).
- Requirements: TC-03, TE-07, EV-04, AD-08/TC-01 (precedent for our "definition byte-identical" PoC criterion).
- Suggested fit cell: ATM→n/a.

### F20. ADR 0014 + guard.ts: fail-closed disposable-profile testing
- Claim: `atm-test-<ulid>` profiles, foreground gateways, teardown pinned to `^$HOME/\.openclaw-atm-test-`; guard rules `guard/production-target, test-profile-required, profile-path-mismatch, env-override, argv-override, version-mismatch, namespace-mismatch, target-fingerprint-mismatch, revalidation-required, secret-value-leak`; `SUPPORTED_OPENCLAW_VERSION = "2026.7.1-2"`; one hash-only canary read of production config. This guard/seam (608 + 41 lines) is the only product code ATM shipped.
- Evidence: docs/adr/0014:11-14; packages/adapter-openclaw/src/guard.ts:4-17; seam.ts:20-33; VERIFY.md:412, 418-428.
- Level: observed.
- Requirements: XC-04, TE-07, XC-02; PoC constraint "no production OpenClaw/Telegram".
- Suggested fit cell: ATM→n/a (pattern reusable for our PoC harness).

### F21. ADR 0019: messaging provisioning tiers and Telegram invariants
- Claim: `MessagingAdapter` ops `discover_surfaces, provision_role_identity, provision_team_surface, provision_project_surface, reconcile_surface, destroy/archive_surface`, each `native | partially-automated | manual | unsupported`; "Manifests are provisioning-tier-independent"; validate via `getMe`/`getWebhookInfo` only, never consume a gateway-owned update queue.
- Evidence: docs/adr/0019:11-14.
- Level: observed.
- Requirements: MS-02, MS-01.
- Suggested fit cell: ATM→n/a.

### F22. Developing-insights disposition (adopt/reject facts, 2026-08-20)
- Claim: adopted — multi-file candidate diff per proposal; MAC-covered basis hashes; evidence coverage `full|partial|none` + `unverified` ("prohibit ready status when required evidence is incomplete"); versioned `AuditEvent` (attempted/applied/failed); deterministic approval render with `renderHash`; closed JSON "refusal envelope" telling an autonomous host to stop/re-plan/seek approval/retry. Rejected as default — "controller mailbox/router … would make ATM an agent-messaging runtime". "No … controller daemon, GUI/protocol layer, supervisor, mailbox runtime, new task manager … is introduced".
- Evidence: review-2026-08-20-developing-insights-disposition.md:16-44.
- Level: observed.
- Requirements: XC-04, EV-03/EV-05, TE-06 (inherit messaging from substrate).
- Suggested fit cell: ATM→n/a.

### F23. RISKS register (21 rows) → our RISKS candidates
- Claim: *realized* rows: (1) strict project context/workspace isolation with persistent-role sessions (U10); (2) trusted-runtime A2A can address a participant outside the intended project; (3) model-facing router use not repeatable. Rows worth carrying: docs↔installed-schema drift (high); clobbering operator config (critical); tests hitting production `~/.openclaw` (critical); LLM e2e tests flaky/costly (high); proposals as injection vector; "Core abstraction leaks runtime specifics, making a second adapter a rewrite"; Telegram assumptions hardening into core; release-train drift; supply-chain tampering; local artifact edits destroyed.
- Evidence: .project-steward/RISKS.md:7-27.
- Level: observed.
- Requirements: XC-02, XC-04, HB-01, TC-03, AR-03, MS-04.
- Suggested fit cell: n/a.

### (C) Lessons / failure evidence

### F24. U2 `unsupported` — model-facing autonomy/compliance failure (verbatim + fixture)
- Claim (verbatim): "U2 — Resolved 2026-08-20 — `unsupported` for model-facing autonomy on OpenClaw 2026.7.1-2 with DeepSeek `deepseek-v4-flash`: … Profile 1 invoked, accepted, and delivered all eight controlled allowed edges and denied all four forbidden directions, but Alpha Implementer emitted the same `IMPLEMENTED` chain hop five times under five distinct tool-call IDs … Profile 2 completed both exact three-hop chains, but emitted only three of eight controlled allowed router calls … its successful model commands sometimes returned receipt-like prose instead of the required tool call. Runs passed: 0/2. This is repeatability/compliance failure, not a mechanical-isolation failure". V4-Pro non-thinking repeat: 0/2 (2/8 then 4/8 accepted deliveries lacked target receipts); V4-Pro thinking/max: hit the 2,400,000 ms Vitest timeout — "not certified", not 0/2.
- Evidence: QUESTIONS.md:14-31, 115-126; 2026.7.1-2-s4-evidence.json (`certification.runsPassed:0`, `u2.result:"unsupported"`); -s4-deepseek-v4-pro-nonthinking-evidence.json (`failurePatterns`); VERIFY.md:332-350, 363, 386.
- Level: verified.
- Requirements: EV-01 (concrete role-level failure modes: tool-call omission, duplicate hops, prose instead of tool call), TC-02, HB-01 (model reliability as a capability dimension), HB-05 (ensembles as mitigation), XC-04.
- Suggested fit cell: OpenClaw→?! (model-dependent; DeepSeek here).

### F25. Exit-137 interruption: no evidence, no postmortem
- Claim: "The attended terminal exited 137 before native-U2 evidence construction. No fixture was written … The operator's major-problem report is required before further work." VERIFY: "**not certified** and … neither a completed pass nor an `unsupported` model result"; production config hash unchanged; no profile residue. No description of the problem and no postmortem exists (§3). Last commit 12a727e "chore(steward): record interrupted native U2 run"; worktree clean.
- Evidence: HANDOFF.md:26-33, 49-55, 81-86; VERIFY.md:418-428; PLAN.md:73-78; git log.
- Level: verified (repo state).
- Requirements: XC-04 (record aborted automated actions), EV-05.
- Suggested fit cell: n/a.

### F26. "Tried and rejected" (verbatim) and warnings
- Claim (HANDOFF.md verbatim): "Persistent role Agent + Project sessions: fails strict workspace isolation." · "U16 ATM router as the default bus: superseded because it replaces native runtime collaboration and over-owns messaging." · "Route catalogs/global allowlists as hard confinement: rejected; they are trusted-runtime correctness inputs only." · "One Gateway per Project as the default: rejected; an explicit hard-boundary deployment option only." Warnings: "Do not classify exit 137 as a model/path failure or partial certification." · "Keep Core free of OpenClaw Gateway, Agent/session, plugin, raw-tool, route layout, and participant-materialization mechanics." · "No Gateway outside disposable `atm-test-*` profiles … Never push."
- Evidence: HANDOFF.md:71-91.
- Level: observed.
- Requirements: AD-05, MS-04, TE-06, XC-03 (native substrate collaboration before own bus).
- Suggested fit cell: OpenClaw→M! (persistent-role + project-session model).

### F27. Where ATM's effort went
- Claim: 35 commits in 3 days; ADRs 0023→0025→0026 superseded each other on 2026-08-20 over A2A confinement; 13/13 adversarial-review findings confirmed against the first M1 plan (7 blockers); spike harness code (15,948 lines) dwarfs product code (666); the pipeline was never built. Absent from every ATM document: nested run, ephemeral/hidden member, overlay, evolution/learning, ensemble, harness selection, Windows/tmux (§3).
- Evidence: git log; review-2026-08-19-m1-plan-disposition.md:7-23; docs/adr/0025:3, 0026:3; `wc -l` (§6).
- Level: verified (counts); inferred (interpretation in product-intent §1.1).
- Requirements: XC-03, TE-06, AD-07/TE-05 (genuinely new requirements).
- Suggested fit cell: n/a.

### (D) Concept disposition table (feeds `legacy-atm-disposition.md`)

### F28. ATM concept → keep-as-requirement | demote | discard

| ATM concept | Disposition | Reason | File refs |
|---|---|---|---|
| `RoleDefinition` ≠ runtime Agent (ADR 0016) | keep-as-requirement | = AD-05/AD-08 | docs/adr/0016:11-13 |
| `requires.capabilities` vs `requires.artifacts`; ArtifactSpec/Catalog/Lock; RequirementResolution (ADR 0022) | keep-as-requirement (metadata ideas) | = AR-01…AR-05; lock/fingerprint = register gaps | docs/adr/0022; schemas/artifact-*.json |
| Role template = Markdown + frontmatter, referenced never inlined | keep-as-requirement | AD-01/AD-02/AD-08 | schemas/role-template.schema.json; docs/adr/0005:11 |
| `modelPolicy` as portable intent; binding recorded at materialization | keep-as-requirement | AD-04/HB-03/HB-07 | schemas/defs.schema.json; 2026-08-19-architecture.md:107-121 |
| `topology.allow` directed edges + `spawn{intraRole,maxDepth}` | keep-as-requirement | TC-02/TC-03/TC-05 precedent | schemas/team-definition.schema.json; teams/demo-development.yaml:45-53 |
| Capability classes native/emulated/unsupported; provisioning tiers; BootstrapInstruction | keep-as-requirement | HB-01/HB-04/AR-05/MS-02 vocabulary | docs/adr/0007; adapter-contract.md:11-18 |
| `x-*` extensions; strict YAML; no runtime-specific core fields | keep-as-requirement | AD-02/HB-08 | docs/adr/0004, 0005; pressure-test.md:75-82 |
| Trust zones; proposals hostile; MAC'd decisions; plan-hash approval | keep-as-requirement | EV-03/EV-05/XC-04 + gaps | docs/adr/0010, 0011, 0021 |
| Four planes + secret late binding; export/import archive; DR | keep-as-requirement | AR-04/AR-03/TE-07 | docs/adr/0008, 0013; portability-dr.md |
| Isolation level vs communication posture; `degraded[]` | keep-as-requirement | TC-03 enforcement level; AR-05 | docs/adr/0026 |
| Messaging identity (team,role) ≠ participant ≠ route; surfaces non-authoritative | keep-as-requirement | MS-01/MS-03/MS-04 | docs/adr/0012, 0019, 0024 |
| Disposable-profile fail-closed testing; hash-only canary | keep (PoC practice) | XC-04 | docs/adr/0014; packages/adapter-openclaw/src/guard.ts |
| `TeamDefinition` / `ProjectDefinition` / `TeamBundle` | demote | project = execution-time input (TC-06/TE-01); keep only lifecycle-separation lesson | docs/adr/0020; schemas/project-definition.schema.json |
| `ProjectRoleContext` (persistent per-tuple context) | demote | contradicts TE-02 fresh-by-default; keep "isolation verified not assumed" | docs/adr/0017 |
| `Workspace` as core resource; namespace/collision model | demote | workspace = execution-time input; deployment machinery | docs/adr/0013, 0018; schemas/workspace.schema.json |
| Reconciliation loop validate→discover→plan→approve→reconcile→verify | demote | never built; runs are fresh instantiations, not converged deployments | docs/adr/0006; packages/core/src/index.ts |
| OpenClaw adoption / agent-ID / marker / agentDir-generation machinery | demote (adapter detail) | HarnessProfile/adapter concern at most | docs/adr/0009; DECISIONS.md 0013 |
| A2A router `atm_project_send`, ADR 0023/0025 | discard | superseded by ADR 0026; uncertified; "over-owns messaging" | docs/adr/0025:3; HANDOFF.md:74-76 |
| Telegram topic-per-Project topology as team semantics | discard | MS-04; keep only V11–V13 facts | docs/adr/0024:29-44 |
| Team Steward role | discard as role; keep idea | → EV-03 proposals from run experience | docs/adr/0011 |
| Deployment record / namespace encoding / lease lock / controller daemon | discard | reconciliation-specific; no TeamRun counterpart | schemas/deployment-record.schema.json; docs/adr/0021 §3 |

- Level: inferred (analyst disposition on the facts above).
- Requirements: all layers.
- Suggested fit cell: n/a.

## 3. Negative findings

- **Product pipeline never ran.** `packages/core/src/index.ts` and `packages/core/src/interfaces/index.ts` each contain only `export {};`. No `validate|discover|plan|apply|verify` implementation exists; PLAN.md:105-108 shows Phases G/C/E/F unchecked; no `skills/team-manager` directory exists.
- **Real product source lines:** `wc -l packages/*/src/*.ts packages/core/src/interfaces/index.ts` = **666** (guard.ts 608, seam.ts 41, index.ts 15, core 1+1). Test/harness code 15,948 lines (harness 9,281; unit+acceptance 5,577; ~1.1k test-only plugin/probe fixtures). Docs: 40 md files / 2,821 lines; steward md 1,403; schemas 1,681; 99 fixture files.
- **No postmortem:** `grep -rniE 'post-?mortem|retrospective|lessons[- ]learned' --include='*.md' .` → 0. The "major problem" that stopped the last run is never described (HANDOFF.md:38-40, 49-51).
- **No license file:** `ls LICENSE*` → none; `package.json` has no `license` (`"private": true`); QUESTIONS.md:146 unresolved.
- **Concepts absent** (grep over docs/, schemas/, examples/, .project-steward/*.md, AGENTS.md): `nested` 0, `ephemeral` 0, `overlay` 0, `evolution` 1 (schema evolution), `learning` 0, `ensemble` 0, `TeamRun` 0, `Assistant` 0, `tmux` 0, `Windows` 0, `Grok` 0, `macOS` 1, `hidden` 4 (hidden TTY key prompt only); `harness` 82 hits all "test harness"/"DeepSeek Harness", never harness selection; `Claude Code` 5 (host agent only).
- **Other harnesses never exercised:** Claude Agent Teams, DeepSeek Harness, Hermes are "stipulated" pressure-test shapes only (runtime-portability-pressure-test.md:9).
- **U-items never run:** U3, U5, U6, U7, U8, U12–U15 unchecked (QUESTIONS.md:32, 45-48, 77-80) — ATM has no evidence on `sessions_spawn` child semantics, session survival across restart, per-role skill materialization precedence, or stub-provider feasibility.
- **Corrections to recon-appendix.md:** (1) RISKS has **21 rows, 3 marked `realized`** (not 20/4); (2) "~5% code" ignores ~16k lines of spike/test/harness code — but the product claim (666 lines, pipeline never implemented) is correct; (3) the interruption was already committed (12a727e), worktree clean; (4) guard.ts/seam.ts as the only product code, ADR 0010 trust zones and ADR 0026 as terminal isolation decision — confirmed.

## 4. Platform & license notes

- ATM targets **Ubuntu 20.04 + Node ≥20** (ADR 0003; test-harness.md:58); `ArtifactSpec.compatibility.platforms.os` enumerates `linux|darwin|win32`, `arch x64|arm64`, but no Windows/macOS path was designed or tested; spikes used `/tmp/atm-openclaw-test-home-1000/.openclaw-atm-test-*` profiles and `strace` (Linux-only, scripts/run-s4-native-live.sh:59-74).
- **License:** none declared. Owner's own repository, so reuse is the owner's choice, but XC-01 requires an explicit statement before any schema text is copied.
- Telegram terms (V12/V13, web-reconfirmed): bot creation, privacy/bot-to-bot toggles, group creation are human actions; one update queue per token.
- OpenClaw: not a hostile multi-tenant boundary (V15); control-plane writes 3/60 s (V1).

## 5. Open questions

1. What was the "major problem" that stopped the native-U2 run (HANDOFF.md:38)? Only the owner knows; it may bear on OpenClaw native `sessions_send` as a TE-06 substrate.
2. Is DeepSeek-specific tool-call non-compliance (F24) reproduced on Claude Code / Codex? Relevant to HB-05 and the EV-01 failure-mode catalog.
3. Reuse ATM schemas textually (needs XC-01 licence statement) or as ideas only?
4. Should the register gap candidates (lock layer, local-modification safety, approval-hash integrity, isolation posture, export/import archive, trust zones) become new rows or notes under AR/EV/XC?
5. Are U3/U5/U7/U12–U15 still needed by MS/HB evidence agents, or do they die with the persistent-runtime model?

## 6. Probe / CLI log

- `git log --oneline | wc -l` → 35; HEAD `12a727e`; `git status --short` → clean.
- `wc -l packages/*/src/*.ts packages/core/src/interfaces/index.ts` → 666; `find tests -name '*.ts' -o -name '*.mjs' | xargs wc -l` → 15948 (harness 9281; unit+acceptance 5577); docs md 40 files / 2821 lines; steward md 1403; schemas 1681; fixtures 99 files.
- python3 schema dump (`properties`/`required`/`$defs`/`oneOf`, no values) → F10/F11; python3 fixture dump (top-level keys; `token|secret|password|authorization|credential|apikey|mainKey|sessionKey` redacted) → F2–F7. No secret values read or printed.
- postmortem grep → 0; concept greps → §3.
- CLI: `openclaw --version` → "OpenClaw 2026.7.1-2 (0790d9f)"; `claude --version` → "2.1.239 (Claude Code)"; `codex --version` → "codex-cli 0.148.0"; `hermes --version` → "Hermes Agent v0.20.4 (2026.8.18)"; `grok --version` → "grok 1.0.5"; `node --version` → v24.16.0; `tmux -V` → not found; `lsb_release -ds` → "Ubuntu 20.04.6 LTS". (`pnpm --version` triggered a Corepack download prompt for pnpm 11.22.0 — incidental, not evidence.)
- Web (2026-08-22): core.telegram.org/api/bots/bot-to-bot (mode enabled per bot in @BotFather; delivery on `/command@TargetBot` or reply; admin bot with Group Privacy Mode disabled receives all; warns of infinite reply loops); agentskills.io/specification (fields as F8); core.telegram.org/bots/api ("two mutually exclusive ways of receiving updates … getUpdates … and webhooks"; page too long for the fetcher to confirm `createForumTopic`/`promoteChatMember`, so V12 stays *observed*).
