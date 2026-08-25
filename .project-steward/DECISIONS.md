# Decisions (ADR-lite, append-only)

## 0001 — 2026-08-22T01:42:57Z — Adopt Project Steward

**Context**: The project needs durable, cross-agent continuity.
**Decision**: Manage state in `.project-steward/` with AGENTS.md as the
canonical instruction file and CLAUDE.md as a thin Claude Code adapter.
**Consequences**: Sessions are resumable across tools and devices via git.

## 0002 — 2026-08-21 — ATM is superseded, not the baseline

**Context**: The prior experiment (agent-team-manager-dev) centered on runtime deployment reconciliation, persistent runtime agents, sessions/workspaces, OpenClaw materialization and project-level A2A isolation; its pipeline never ran end-to-end.
**Decision**: ATM is a source of requirements, experiments, failure evidence and research only. Its demoted concepts (OpenClaw-centered reconciliation, persistent runtime Agent identity as Core, ProjectRoleContext/workspace/session as central model, custom A2A router, hard same-user cross-project isolation, OpenClaw agent-ID/adoption machinery, Telegram topology as Team semantics) may not re-enter the architecture without fresh evidence.
**Consequences**: `docs/discovery/legacy-atm-disposition.md` records keep/demote/discard per concept.

## 0003 — 2026-08-21 — The portable Assistant definition is the product object

**Context**: Product brief §1–§3.
**Decision**: Assistant (definition) ≠ Skill ≠ harness ≠ runtime agent. Persistent: Assistant definitions, TeamTemplates, reviewed evolution. Fresh by default: AssistantInstances, TeamRuns, sessions; project/workspace supplied at execution time.
**Consequences**: Normative glossary in `docs/discovery/evidence/glossary.md`; requirement register in `docs/discovery/product-intent.md`.

## 0004 — 2026-08-21 — ClawTeam is the leading candidate substrate for team execution, to be fit-gapped, not presumed

**Context**: Brief §12; reconnaissance shows ClawTeam provides dynamic spawning, task DAG, inbox, worktrees, multi-CLI adapters, MCP server; it lacks persona/role packages, nested teams, and per-team harness policy.
**Decision**: Evaluate ClawTeam as-is / configured / extended upstream / wrapped, against every requirement, alongside the other systems. No architecture is chosen before `existing-systems-fit-gap.md` and `architecture-options.md` exist.
**Consequences**: W1 includes an isolated ClawTeam probe on this tmux-less host.

## 0005 — 2026-08-21 — Discovery deliverables live in `docs/discovery/`; messaging surfaces are optional

**Decision**: The nine discovery documents and their evidence files live under `docs/discovery/` with the exact filenames from the brief. Telegram/OpenClaw are treated as optional Surfaces; no Core concept depends on them.
**Consequences**: PoCs A–C are defined without Telegram/OpenClaw unless analysis proves necessity.

## 0006 — 2026-08-21 — Discovery method: multi-agent workflows with owner-held anchors

**Context**: ~19k LOC ClawTeam, a 112-commit fork, six other repos and web verification exceed one context; the brief demands source-level analysis and adversarial pressure tests.
**Decision**: Evidence (W1) → fit-gap/reuse/models (W2a) → architecture judge panel (W2b) → adversarial critics (W3) as workflows; the owner (this session) writes the glossary, requirement register, product-intent prose, merges fit-gap, tiebreaks the panel, and performs the final read-through. Web verification and isolated probes approved by the user.
**Consequences**: Evidence files follow one schema and never recommend; each pressure test has exactly one owning document.

## 0007 — 2026-08-22 — Architecture answer: thin format-independent layer over ClawTeam CLI with two declared seams

**Context**: Architecture panel (three biased architects — ClawTeam-maximalist, independent layer, upstream-extension-first — scored by two judges on a shared R1–R10 rubric; records in `docs/discovery/evidence/panel/`). Both judges independently endorsed the same composition; the session owner confirmed it as tiebreak.
**Decision**: The smallest new software layer = A's O2 scope with B's two seams: substrate-neutral data (Assistant definitions + exclusion validator, TeamTemplates by reference, overlays + Proposal/review record, HarnessProfiles + selection policy, invocation ledger + ensemble record, artifact manifest/lock/resolution report, TeamRun record/rosters/nesting contract/archive) behind exactly two seams — HarnessAdapter and CoordinationSubstrate — with one implementation each today (five harness adapters; ClawTeam 0.3.0@0119833 over its CLI, subprocess backend, no tmux) plus a trivial `direct` launcher for solo/ensemble legs. No second team substrate, no ClawTeam fork, no library-seam coupling (in-process backend = documented Windows fallback only), no surface adapters (OpenClaw/Telegram remain optional O4), no artifact installer, no UI. Build by slice: PoC-A slice first (≈2–3k LOC), run layer gated on PoC A.
**Consequences**: `docs/discovery/architecture-options.md` states the answer (one paragraph + one table); `minimal-poc-plan.md` tests it; ClawTeam PRs are filed as intent and planned as if none merges; TC-05/TE-05 enforcement levels are labeled honestly (gate+convention; recorded isolation). Owner-level open questions recorded in `QUESTIONS.md`.

## 0008 — 2026-08-23 — AGENTS.md left untouched at the end of M0 (owner decision)

**Context**: The session proposed a one-time addition to `AGENTS.md` (pointers to `docs/discovery/`, normative glossary/register rules, read-only reference repos, phase-gate note) outside the managed blocks.
**Decision**: The owner chose to keep `AGENTS.md` unchanged for now. The same guidance lives in `.project-steward/HANDOFF.md` and `docs/discovery/README.md`.
**Consequences**: Successor sessions must read `HANDOFF.md` first (per the session protocol) to find the discovery deliverables and conventions; any future AGENTS.md change still requires a diff + explicit approval.

## 0009 — 2026-08-23 — W3 fix-pass owner decisions (D1–D15) amend tiebreak assumption (e)

**Context**: Adversarial critics (9 per-document + completeness) found two blockers and ~25 majors, several needing a single cross-document decision. The owner wrote binding decisions D1–D15 (`docs/discovery/evidence/critics/owner-decisions-fix-pass.md`).
**Decision**: Notably — D1: the nested-run result carrier is the layer-owned outer `run.json` + inner archive, signalled by `clawteam inbox send`, delegated task closed by `task update --status completed` (`task update --metadata` does not exist in ClawTeam 0.3.0@0119833), amending tiebreak assumption (e); D3: `independence {declared: advisory|mechanical, achieved: namespace|data-dir|mechanical}`; D7: fit-gap cells where "our layer carries it" are `Xs`, not `P` (TE-05/TE-07/HB-04 CT re-scored); fit-gap rung columns are non-binding; D8: reuse bolding rule restated, new rung tally 17/7/0/1/0/28/1; D9: Ephemeral origin lives on the Member, never in the definition; D10: TC-05 = gate + convention + `CLAWTEAM_BIN` shim + post-hoc reconciliation until enforced.
**Consequences**: All nine documents say one thing on these points; `architecture-options.md` §5.0 enumerates the owner assumptions with attribution; the answer paragraph is byte-identical across architecture-options §5, minimal-poc-plan §1 and README.

## 0010 — 2026-08-22 — M0 review retains the architecture direction but reopens detailed PoC design

**Context**: The delivered M0 package contained useful architecture evidence but also a future-dated verification claim, stale CLI guidance, an AD-07 scoring-method omission, and a detailed PoC slice presented more firmly than the owner intended.
**Decision**: Retain the thin Assistant/Team layer, HarnessAdapter and CoordinationSubstrate direction. Treat the existing PoC A/B/C run shapes, synthesis, schemas, language, sequence, gates and slice LOC as a historical proposal requiring re-baselining. Correct only AD-07 and its derived text semantically; trust and rerun the original 54×11 structural lint as regression rather than re-judging every cell.
**Consequences**: `minimal-poc-plan.md` is not implementation authorization. M1 begins only after a detailed plan is reviewed and approved. Historical panel/critic records remain unchanged.

## 0011 — 2026-08-22 — Fix execution modes, CI boundary, first-pass harnesses and reuse permission

**Context**: Owner confirmations and current CLI/platform verification after M0.
**Decision**: (1) Claude Code + Codex + Grok Build are required first-pass harnesses; Hermes/OpenClaw are deferred. (2) Native and unattended live runs use each CLI's subscription OAuth on the owner's persistent host; ATS does not broker third-party login, copy credential stores, or put live credentials in hosted CI. (3) API-test mode is separate/replaceable, stores credential environment-variable names only, and never substitutes for native auth; provider, endpoint, and model selection remains deferred and unverified. (4) GitHub-hosted Windows/macOS CI proves deterministic direct/ClawTeam plumbing only. (5) Advisory PoC controls are acceptable only when bypass-visible/audited; production requires mechanical enforcement; hidden is UI projection. (6) ATM internal copy/adaptation is authorized with provenance and third-party obligations retained.
**Consequences**: Current architecture/model/evidence documents use Claude `--safe-mode --no-session-persistence` for subscription mode, not `--bare`; open questions Q2/Q3/Q5/Q7 and the first-pass-harness question are closed; no API key is requested until a canary is explicitly approved.

## 0012 — 2026-08-23 — Adopt the AgentTeam product identity and TypeScript baseline

**Context**: The working name, implementation language, documentation language,
repository target, CLI name, and publication license had to be fixed before a
reviewable implementation plan could be exact.
**Decision**: The product name is AgentTeam; the future repository is
`WSH95/AgentTeam`; the new product CLI is `atm`; the eventual local directory
is `/home/wsh/Documents/AgentTeam`. Implement in TypeScript on Node.js, keep
English as the canonical product-documentation language, and use MIT with
`Copyright (c) 2026 ShuhanWang`. Keep the package private and do not publish to
npm during M1a.
**Consequences**: The rename is G1 of the proposed M1a plan rather than part of
this planning change. Historical ATM/M0 evidence remains dated history instead
of receiving a blanket rename. Public repository creation and every push still
require separate owner approval.

## 0013 — 2026-08-23 — Make M1a a direct, three-harness ensemble PoC

**Context**: The historical PoC A/B/C sequence was intentionally reopened, and
the owner supplied the choices needed to define the first implementation
slice.
**Decision**: M1a uses direct CLI subprocess adapters for Claude Code, Codex,
and Grok Build before ClawTeam or ACP. Run three fresh independent review legs
in parallel, require all three, then use a separate fresh Claude invocation to
synthesize with per-leg attribution. Allow one retry only for a classified
transient failure. Use harness defaults when model/effort is unspecified;
concrete overrides live in a local HarnessProfile or ephemeral RunRequest,
while portable Assistants contain abstract hints only. Retain full local
gitignored evidence with redacted argv/environment metadata and raw streams;
commit only explicitly reviewed sanitized summaries. Hosted Windows/macOS CI
is deterministic and credential-free; live subscription acceptance is on the
owner's Ubuntu host.
**Consequences**: The exact proposed scope, contracts, gates, fixture, call
bound, and acceptance criteria live in
`docs/plans/m1a-direct-harness-poc.md`. That plan must be reviewed and
explicitly approved before implementation. ClawTeam, API-test mode, Hermes,
OpenClaw, Telegram, TeamTemplates, dynamic Members, and nesting are outside
M1a.

## 0014 — 2026-08-23 — Use a Python core with language-neutral edges

**Context**: ClawTeam 0.3.0 is Python-first and exposes useful in-process
coordination seams. Keeping a TypeScript core would force AgentTeam through a
less capable CLI boundary or duplicate those mechanisms, while every target
harness can already integrate through CLI, JSON, or MCP.
**Decision**: Implement the AgentTeam core in Python `>=3.11`, manage it with
`uv`, and package it with Hatchling. Define external records with checked-in
JSON Schema; expose the `atm` CLI first and an `atm` MCP server in M2. Keep
harness and coordination boundaries as typed async Python protocols internally
and language-neutral contracts externally. DG/DT TypeScript is evidence and
schema/mechanism inspiration, not code vendored into the core; a small native
TypeScript edge adapter may be considered later if DSH becomes primary.
**Consequences**: This supersedes only the TypeScript/Node portion of ADR 0012
and the "no library-seam coupling"/CLI-only portions of ADR 0007. AgentTeam's
name, `atm` CLI, MIT intent, direct-first M1a ensemble, license/provenance
constraints, and publication gates remain unchanged. The owner explicitly
approved the corresponding one-time `AGENTS.md` identity/stack wording change;
the managed command block remains `n/a` until the scaffold exists.

## 0015 — 2026-08-23 — Keep ClawTeam optional and qualify its in-process seam early

**Context**: In-process ClawTeam can make later dynamic-member and nested-run
enforcement mechanical at the product-owned boundary, but its public package is
alpha, its event bus and data directory are process-global, and its built-in
subprocess backend uses `shell=True`.
**Decision**: The direct runner is built into the core and remains fully usable
without ClawTeam. Offer ClawTeam only through the optional extra
`agentteam[clawteam]`, pinned to full Git commit
`01198332ef9270c32c5460b8a178f964fc0df451` plus `mcp>=1,<2`. Confine every
ClawTeam import to one AgentTeam-owned compatibility/provider module, translate
events into AgentTeam-owned records, reset/contain global hooks during use, and
never call its subprocess/tmux/wsh launch backends. Qualify this seam in M1a;
use one process-scoped data root with opaque AgentTeam team namespaces and claim
namespace separation, not mechanical filesystem isolation.
**Consequences**: A compatibility failure blocks ClawTeam provider
qualification and M1b provider work, but never the direct core. ClawTeam does
not become a required install, execution engine, public schema, or harness
adapter. No fork or upstream PR is required for M1a.

## 0016 — 2026-08-23 — Commit the team-execution proof sequence to the roadmap

**Context**: Selecting a direct-first M1a must not silently drop the original
dynamic-member, nested-team, evolution, artifact, or operational requirements.
**Decision**: Follow M1a with M1b TeamRun foundations, M1c dynamic-member PoC B,
M2 nested TeamRun PoC C plus MCP, M3 reviewed evolution/artifacts, and M4
long-running operations. Hermes, OpenClaw, DSH, messaging surfaces, and API-test
providers remain optional later integrations.
**Consequences**: M1a may stop before TeamRun implementation without treating
the broader requirements as optional. Each later milestone still needs its own
reviewed implementation plan and explicit owner approval.

## 0017 — 2026-08-23 — Keep prospective API-test routes provider-neutral

**Context**: Candidate-specific route details appeared in current and historical
documentation before any future CI or live API-test provider, endpoint, or model
had been selected. That wording could be mistaken for an approved choice.
**Decision**: Until the owner makes a separate selection, tracked documentation
uses provider-neutral terms for prospective API testing and does not name a
tentative provider, endpoint, model, credential-variable name, or provider URL.
Generic profile fields, protocol distinctions, environment-only credential
handling, redaction, and the prohibition on native-auth fallback remain.
Unrelated factual third-party inventories remain intact.
**Consequences**: Candidate-context passages are narrowly neutralized while Git
history retains their earlier wording. M1a CI remains deterministic and
credential-free, no API-test route is approved, and any later selection needs
its own evidence, owner approval, and decision update.

## 0018 — 2026-08-23 — Independent review of the `3407ec9` baseline recorded; decisions taken on its findings

**Context**: At the owner's request a Claude session reviewed the M0/M0.1 package
strictly at commit `3407ec9` — without reading the M1a plan or ADRs 0012–0017 —
and wrote an independent next-step proposal; the owner answered eight questions
the review raised. Records: `docs/reviews/2026-08-23-m0-review-at-3407ec9.md`
(22 substantive + 14 hygiene findings, three read-only audits reconciled) and
`docs/plans/m1-agentteam-direct-slice.md`.
**Decision**: (1) The tiebreak assumptions (a)–(l) quoted in
`architecture-options.md` §5.0 are historical, session-authored panel inputs,
not owner decisions; later plans restate only what they need. (2) ClawTeam's
place in team execution is decided by measurement in PoC B under a written exit
criterion drafted before PoC B starts; a local deterministic coordination
provider is built first (deterministic tier / CI). This complements ADR 0015
(optional, exact-pinned, in-process seam) and does not reopen it. (3) The first
real use is code/dev teams: PoC A → B → C in the brief's order; no early
operational-mode slice. (4) Approval of any plan is recorded as a DECISIONS
entry naming the plan file and commit SHA (review R20). Reaffirmed, not
re-decided: all three first-pass harnesses required for PoC A (ADR 0011/0013;
review R4 kept as a recorded dissent), Python `>=3.11` + `uv` (ADR 0014), the
deterministic tier as precondition with live evidence as the only passing tier
(QUESTIONS Q8), English-only documentation, and AgentTeam / `atm` naming.
**Consequences**: Two candidate M1 plans exist (`docs/plans/m1a-direct-harness-poc.md`,
owner; `docs/plans/m1-agentteam-direct-slice.md`, independent); the owner merges
or selects. Review hygiene items H1–H14 and findings R7/R19/R21/R22 are tracked
as cleanup work in the next plan (T0), not fixed retroactively inside the dated
review. The review is valid for `3407ec9` only; ADRs 0012–0017 post-date it and
may already address some findings.

## 0019 — 2026-08-23 — Merge the independent M1 proposal into M1a revision r2

**Context**: Two candidate M1 plans existed after ADR 0018: the owner's
`docs/plans/m1a-direct-harness-poc.md` (r1, `9aff78f`) and the independent
`docs/plans/m1-agentteam-direct-slice.md`. The owner asked for one merged plan;
the comparison was cross-checked by an independent plan agent, which also found
internal gaps in r1 (vendor structured-output dialects, Codex instruction-channel
semantics, Windows `.cmd` shims and environment baseline, CRLF/hash identity,
oracle placement, CI-vs-live gate order, local state layout, budget wording).
**Decision**: M1a is revised in place to **r2** and is the single candidate plan;
the independent proposal is superseded and kept as a dated record with a banner.
Owner decisions for the merge: (1) render the example Assistant's three Skills
into every harness in M1a; (2) keep the hard semantic acceptance bar, with
mechanical/semantic traceability labelling; (3) commit a reviewed sanitized
evidence bundle per live cycle (the complete form of ADR 0013's reviewed
summary); (4) defer `OverlayV1` to M3, keeping `overlay_refs` and
`effective_definition_hash` reserved, and answer review item R15 before M3;
(5) G1 renames the directory to `/home/wsh/Documents/AgentTeam` first, then G2
creates the **public** `WSH95/AgentTeam` repository with the MIT licence and
pushes the scaffold after an explicit approval at that moment, so the core CI
matrix runs from the scaffold; G7 becomes "CI matrices green + pre-publication
checks". Adopted from the independent proposal: harness-selection precedence
with `decided_by` (HB-03/AD-04), cross-OS hash identity with `.gitattributes`
(AR-03), `RunRecordV1` as the one-Member subset of the later TeamRun record,
probe verification levels and day-one probes at G5, falsification routing, the
ClawTeam exit-criterion inputs and M1b provider order (ADR 0018), the
documentation-hygiene list in G1, and the approval artefact convention. Not
adopted: the early operational-mode slice, a `noop` harness kind,
`--max-budget-usd` control, extra CLI verbs, live solo runs, any TeamRun
behaviour in M1a. `gh` authentication is in place (account `WSH95`, `repo`
scope, SSH; verified read-only 2026-08-23), so the earlier G7 blocker is gone.
**Consequences**: r2 remains *proposed*: multi-agent review against its
section 21 and an explicit owner approval entry (naming the file and the
commit SHA of the approved text) still precede G1. Review R4 (Grok as the
HB-08 test rather than a gate) stays a recorded dissent. The documentation
hygiene items (review H3, H6, H8–H12, R7, R19) are executed in G1 under the
approved plan, not before.

## 0020 — 2026-08-23 — M1a revision r3 resolves the multi-agent review findings on r2

**Context**: The multi-agent review of M1a r2 returned "do not approve yet" with
five blocking findings and required corrections while confirming the
architecture choices. Claims were verified read-only before resolving:
`claude --help` (2.1.241) shows `--safe-mode` disables Skills, plugins, hooks,
and MCP servers and `--bare` never reads OAuth; `codex exec --help` (0.149.0)
shows `--ignore-rules` covers execpolicy `.rules` only; `grok inspect` (1.0.5)
lists both `.grok/skills/` and `.agents/skills/` as project skill roots; Python's
`subprocess` documentation warns that batch files may be shell-parsed despite
`shell=False`.
**Decision**: `docs/plans/m1a-direct-harness-poc.md` is revised to **r3** (still
*proposed*): (1) the Claude recipe drops `--safe-mode`; isolation rests on a
fresh `CLAUDE_CONFIG_DIR`, `--setting-sources user`, `--strict-mcp-config` with
an empty MCP config, explicit tool restriction, and `--no-session-persistence`;
Skill channels are probe-selected at G5 (isolated-home `skills/`, `--plugin-dir`,
workspace `.claude/skills/`); (2) Grok uses workspace `.grok/skills/` first with
`.agents/skills/` as a verified fallback; Codex keeps `.agents/skills/` and the
`AGENTS.md` fallback is valid under `--ignore-rules`; (3) a pre-first-push
checklist (history secret scan, licence/notices, provenance, name checks) runs
at G2 before the public repository exists; CI grows gate by gate (G2 scaffold
smoke → G3 adapters and the Windows `.cmd` fake → G4 acceptance, hash identity,
optional ClawTeam → G7 final matrices plus a credential-free vendor-smoke job);
(4) a Member is bound to one execution at a time — one HarnessInvocation or one
Ensemble holding its legs and synthesis — `RunRecordV1.members[].execution`
carries that binding and `team-execution-model.md` §4 is amended accordingly;
(5) an explicit Windows launcher policy (resolve npm `.cmd` shims to `node` plus
script; fail-closed safe-character allowlist otherwise; `PATH`/`SystemDrive` in
the environment baseline) with a Windows-only `.cmd` fake test. Further
corrections: `effective_definition_hash` is computed state, never
client-supplied; required Skills that cannot be delivered fail before launch
(`degraded[]` covers optional parts only); G5 probe captures stay in gitignored
probe storage and tracked fixtures change only by reviewed promotion; an owner
waiver may close M1a as failed/abandoned, never as semantic PASS; the complete
harness-selection algorithm (hard failure for a forbidden/ineligible user
request; no implicit force); the V1 portable-archive contract (regular UTF-8
text files only, NFC paths sorted by code point, case collisions rejected, modes
excluded, CR/CRLF→LF, SHA-256 over `(path, NUL, size, NUL, bytes)`); Q5 wording
preserved for M4. **Budget ceiling approved by the owner**: one initial
acceptance cycle after G5, at most two reruns each separately confirmed, probes
≤ 2 per harness, hard ceiling 30 calls.
**Consequences**: r3 goes back to the reviewers; approval still requires a
DECISIONS entry naming the file and commit SHA (ADR 0018/0019). The only
discovery-document change is the one-sentence execution-binding amendment in
`team-execution-model.md` §4 (v2.3). Review R4 (Grok as HB-08 test) remains a
recorded dissent.

## 0021 — 2026-08-23 — M1a revision r3 approved for product implementation (G0)

**Context**: The multi-agent review findings on r2 were resolved in r3
(ADR 0020). On 2026-08-23 the owner stated "I approve the r3" and asked for
implementation to begin.
**Decision**: `docs/plans/m1a-direct-harness-poc.md` revision **r3**, as
committed in `0f3e478` (`docs(plan): M1a r3 — resolve review findings …`), is
the approved M1a implementation plan. This entry is the G0 approval artefact
required by that plan (section 2/3: a DECISIONS entry naming the plan file and
the commit SHA holding the approved text); the plan's status line flips to
`approved` in the following commit. The approval covers gates G1–G8 as written
in r3 and nothing beyond M1a; it does not pre-approve the first push (G2, its
own explicit approval moment), the AGENTS.md managed-block edit (own shown
diff), live acceptance reruns (each separately confirmed, ceiling 30 calls), or
any later milestone plan.
**Consequences**: G1 (directory move to `/home/wsh/Documents/AgentTeam`, root
files, identity updates, documentation-hygiene commit) starts in a fresh, sole
session; this session only records the approval and hands off. `PLAN.md`,
`QUESTIONS.md`, and `HANDOFF.md` are updated in the following commit.

## 0022 — 2026-08-23 — Amendment markers for ADRs 0007, 0009, and 0012 (append-only; G1 documentation hygiene)

**Context**: The independent review of `3407ec9` (R19; ADR 0018) found that
this append-only log carried silent reversals: ADR 0007's build plan was
reopened by 0010 and its harness count superseded by 0011 without a marker;
ADR 0009's D7 was reversed by the M0.1 AD-07 correction (review addendum F9,
ADR 0010/0011) without a marker; and ADR 0012 pairs the still-valid AgentTeam
identity with a TypeScript baseline that 0014 replaced. The approved M1a plan
(§4 item 6) requires one append-only entry that adds the markers. Earlier
entries are not edited; this entry is the marker. The log's append order also
differs from its decision dates (0008/0009 are dated 2026-08-23 but were
appended before 0010/0011, dated 2026-08-22): entries are appended when they
are written and dated by the decision event; both orders stand as recorded.
**Decision**:
- **ADR 0007 — superseded in part.** Stands: the thin, format-independent
  Assistant/Team layer; the substrate-neutral data it owns; the two declared
  seams HarnessAdapter and CoordinationSubstrate. Superseded: "over the ClawTeam
  CLI, subprocess backend" and ClawTeam as the one team substrate → ClawTeam is
  an optional, exact-pinned in-process provider that never launches harnesses
  (0014, 0015) with a local deterministic provider first (0018); "five harness
  adapters" → three first-pass harnesses (0011, 0013); "PoC-A slice ≈2–3k LOC,
  run layer gated on PoC A" and the rest of the slice/sequence → reopened by 0010
  and replaced by the approved M1a plan (0021) and the committed roadmap (0016).
- **ADR 0009 — amended and reclassified.** D7 ("hidden is the TC-04 row's
  concern only — AD-07/TE-04 score the ability to create a temporary member")
  was reversed on 2026-08-22 by the M0.1 AD-07 correction (hidden-if-desired
  restored into AD-07 and its derived fit-gap text; `evidence/m0-product-architecture-review-2026-08-22.md`
  F9; ADR 0010). D1/D10/D11 describe ClawTeam-CLI mechanics (`inbox send` result
  carrier, `CLAWTEAM_BIN` shim, wrapper spawn) that belong to the superseded
  CLI-over-ClawTeam architecture and are historical. D3 (`independence
  {declared, achieved}`) stands and is now a glossary term. Per ADR 0018, D1–D15
  were session-authored in the owner's voice and are historical fix-pass inputs,
  not human owner decisions; the same applies to 0009's own "owner decisions"
  wording.
- **ADR 0012 — superseded in part.** Stands and executed at G1 (commits
  `chore(project): rename project to AgentTeam` and this one): product name
  AgentTeam, repository `WSH95/AgentTeam`, CLI `atm`, directory
  `/home/wsh/Documents/AgentTeam`, English documentation, MIT with
  `Copyright (c) 2026 ShuhanWang`. Superseded: "Implement in TypeScript on
  Node.js" → Python `>=3.11` with `uv` and Hatchling (0014); "keep the package
  private and do not publish to npm" → the repository is created public at G2
  after the pre-first-push checklist and an explicit approval, and no package is
  published during M1a (0019, M1a plan §2/§16).
- **Convention going forward.** When a later entry supersedes or amends an
  earlier one, the later entry names the earlier ID and the clause it changes
  (as 0014 and 0019 already do); earlier entries are never rewritten.
**Consequences**: Readers of 0007/0009/0012 must read this entry with them.
`docs/discovery/evidence/critics/owner-decisions-fix-pass.md` carries a matching
provenance note; the critic findings files carry closure notes (review H8); the
glossary defines the seam and identity terms (review H10/R10/R16).

## 0023 — 2026-08-23 — AGENTS.md managed command table updated for the G2 scaffold

**Context**: The approved M1a plan (§4) prescribes updating the managed
command table once the Python scaffold exists, and requires that managed-block
edit to have its own shown diff and explicit approval (ADR 0008/0014;
DECISIONS 0021 excluded it from the plan approval).
**Decision**: The `PROJECT-STEWARD:BEGIN commands` block now reads Build
`uv build`, Test `uv run pytest`, Lint `uv run ruff check .`, Typecheck
`uv run mypy src tests`, Schemas `uv run python -m agentteam.schema check`.
The exact diff was shown to the owner inside the G2 execution plan (step B4)
together with the question "How do you want that edit approved?"; the owner
selected **"Approve with this plan (Recommended)"** on 2026-08-23. Deviations
from the plan §4 table, recorded there and in VERIFY: the `Live PoC` row is
deferred to G4 (its command and request file do not exist yet) and a `Schemas`
row is added; `ruff check .` is safe because `pyproject.toml` excludes `*.md`
from ruff. Nothing outside the managed block changed; the stale
"(implementation planned)" stack line stays until its own shown edit.
**Consequences**: Agents use the real commands from G2 on. The table gains the
`Live PoC` row at G4 via the same guarded procedure.

## 0024 — 2026-08-23 — Public repository WSH95/AgentTeam created; first push executed on explicit approval (G2)

**Context**: The approved M1a plan makes the first push its own approval
moment inside G2 (§2/§16/§17); ADR 0019 fixed the repository as public with
the MIT licence, created after the G1 rename and the pre-first-push checklist.
**Decision**: After the checklist passed (VERIFY "G2 local verification":
history secret scan 0 hits at `8660e6a`; GitHub/PyPI/`atm` name checks free
2026-08-23; LICENSE + `docs/provenance.md`), the owner was asked "Create the
public GitHub repository WSH95/AgentTeam (MIT) and push main (HEAD 8660e6a)
now?" and answered **"Yes — create and push"** (2026-08-23). The repository
https://github.com/WSH95/AgentTeam was created public with
`gh repo create … --public --source . --remote origin --disable-wiki` and
`main @ 8660e6a` pushed. A follow-up CI fix (`671c2d9`, setup-uv pinned to the
v10.0.1 commit — no floating v10 tag exists) was pushed after its own separate
approval the same day.
**Consequences**: The scaffold smoke matrix must be green on
Ubuntu/Windows/macOS to close G2 (evidence in VERIFY). Every further push
remains its own visible gate; nothing is published to any package registry in
M1a.

## 0025 — 2026-08-23 — G4 AGENTS.md edits: Live PoC command row and stack-line cleanup (owner-approved diffs)

**Context**: AGENTS.md is a high-risk guarded file (managed-block edits only,
shown diff + explicit approval). The M1a plan defers the `Live PoC` command
row to G4, when `examples/run-requests/live-review.yaml` exists; the stack
line still carried "(implementation planned)" from before G2.
**Decision**: During G4 planning (2026-08-23, AskUserQuestion with both diffs
shown) the owner approved **both** edits: (1) the managed commands block gains
`| Live PoC | `uv run atm run examples/run-requests/live-review.yaml` |`;
(2) the stack line drops "(implementation planned)". The edits land verbatim
in the G4 closure commit.
**Consequences**: The commands table now names the G6 live entry point; the
live run itself stays behind G5 logins and the G6 gate with its call budget.
No other AGENTS.md content changes; the guardrail process stays in force.

## 0026 — 2026-08-24 — G5 probes are attended, version-bound, and evidence-first

**Context**: G5 must prove native subscription authentication and real
instruction/Skill delivery without allowing a probe retry, fallback, stale CLI
row, or raw capture to silently become live-readiness evidence. Claude also
needs a persistent config-home Skill channel without racing another AgentTeam
process or deleting an owner's unmanaged directory.
**Decision**: `profile init` is credential-blind and owner-only; the no-call
doctor checks install/version/home/flag/auth readiness without mutating the
profile. `doctor --probe` requires a TTY, preflights all three native profiles,
prompts on stderr immediately before every call, runs in profile order with a
hard two-call/harness ceiling and `min(profile timeout, 180s)`, and persists a
pending/terminal owner-only capture before atomically updating only assessed
capability rows. Random markers live only in instruction and Skill channels;
adapters consume the first current `verified` channel in fixed ladders. Grok
auth is verified only by a successful structured probe. Live runs use the
persistent resolved vendor homes and reject stale/incomplete rows before a
model call; render-only keeps synthetic homes. Claude config-home Skills use an
exclusive marked-directory lease held through invocation and cleaned in
`finally`. A second call assesses only unresolved rows, so a fallback failure
cannot erase evidence proven by call 1. The shell-free runtime process runner
uses `subprocess.Popen` with nonblocking pipe/process polling because this
sandbox intermittently lost short-lived asyncio child-watcher notifications;
tree-kill, timeout, and cancellation semantics remain covered by tests.
**Consequences**: `HarnessProfileSetV1` remains schema version 1 and owner
profile settings/custom rows survive probe updates. Cancellation exits 130 and
keeps completed evidence; two failed calls leave G5 open. Raw captures are
never promoted automatically. Deterministic implementation does not close G5:
the owner still must log into all three dedicated homes, approve each of the
3–6 live calls, review/sanitize representative output, and record the actual
versions and selected channels before G6.

## 0027 — 2026-08-24 — Standard native profiles inherit the owner's terminal proxy

**Context**: The G5 plan assumed the owner's normal terminal had no proxy
variables and generated profiles with `proxy_policy: deny`. During attended
setup the owner clarified that Sing-box is intentional system network
infrastructure and rejected an attempted login wrapper that removed
`HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY` variants. The login was cancelled
before completion and no model call occurred. Runtime already had a partial
inherit path, but no-call doctor ignored it and the pass-through depended on
proxy names also appearing in the custom conflict list.
**Decision**: Profiles produced by `atm profile init` explicitly use
`proxy_policy: inherit`. Login, diagnostics, probes, and live runs preserve all
present standard proxy variables unchanged (`HTTP_PROXY`, `HTTPS_PROXY`,
`ALL_PROXY`, and `NO_PROXY`, including lowercase variants) while continuing to
reject API-key, base-URL, and alternate-provider conflicts. Doctor reports the
effective policy and inherited names only. Explicit `deny` rejects every
standard proxy name even if a custom conflict list omits it. The schema stays
V1 and its omitted-field default stays `deny` so legacy/custom profiles do not
silently acquire a new network path; the already-created owner profiles receive
a narrow, atomic policy-only migration. AgentTeam never adds `env -u` proxy
wrappers to owner-attended commands.
**Consequences**: Normal AgentTeam native profiles behave like the owner's
terminal for network routing without expanding the general environment
allowlist or recording proxy values. G5 authentication can resume only after
the deterministic block passes, the local profiles are migrated, and no-call
doctor confirms policy parity in the normal environment.

## 0028 — 2026-08-24 — Claude Skill loading is explicitly permitted and remains bounded

**Context**: G5 Claude probe call 1 (capture
`probe-20260824T061711Z-971ee2af`) timed out after 180.64 seconds with zero-byte
stdout, stderr, and structured output; AgentTeam killed the process tree and
atomically marked the five assessed rows current-version `unverified`. The
owner declined call 2 while the evidence was diagnosed, so no other harness
ran. Anthropic HTTPS through the trusted proxy returned promptly, but the
recipe told Claude to load a Skill while `permission-mode=dontAsk` pre-approved
only `Read,Grep,Glob,LS`. Claude's official tools/permissions documentation says
Skills run through the built-in `Skill` tool and unapproved tools are denied in
`dontAsk`; upstream issue #35262 independently records a matching zero-byte
headless stall around deferred Skill invocation.
**Decision**: Pre-approve Claude's built-in `Skill` loader alongside the four
read tools in both probes and live adapter invocations. Retain explicit denies
for Write, Edit, NotebookEdit, Bash, WebFetch, and WebSearch; a loaded Skill
cannot bypass those denies. The deterministic Claude fake reports Skill
markers only when `Skill` is allowed, preventing the former false positive.
The first timeout counts against Claude's two-call G5 ceiling: only one further
Claude invocation may be owner-approved; any additional Claude prompt is
declined, and another failure leaves G5 open.
**Consequences**: The fixed recipe is faithful to the required Skill-delivery
claim without broadening write/network execution. The full credential-free
block remains green (392 passed, 3 expected Windows skips). Live evidence, not
the upstream issue, decides whether Claude 2.1.241 is ready.

## 0029 — 2026-08-24 — Grok's two-call evidence is retained and G5 stays open

**Context**: The continued attended run proved Claude 2.1.241 on its second and
final invocation and Codex 0.149.1 on its first. Grok 1.0.5 confirmed
invocation 1 never reached a model: the CLI rejected a bare `-p` followed by
`--prompt-file` because `-p` aliases `--single <PROMPT>` and requires its own
value. After that defect was removed, Grok's second/final confirmed invocation
returned valid structured output and proved native auth, prompt-file, rules,
and the JSON-in-`text` location. It did not reproduce either random Skill
marker: it invented two shorter values derived from the Skill names. A no-call
`grok inspect --json` in the preserved workspace nevertheless listed both
`.grok/skills` and `.agents/skills` definitions as enabled and user-invocable.
The same live envelope also exposed camelCase `structuredOutput`, which the
pre-live parser did not recognize as the field-channel spelling.

**Decision**: Both confirmed Grok process invocations count against the strict
two-call ceiling even though the first failed before model dispatch. Decline
the next prompt, retain partial current-version evidence, keep both Skill rows
`unverified`, leave G5 open, and prohibit G6. Correct probe and live rendering
to use `--prompt-file` without bare `-p`; recognize both `structuredOutput` and
`structured_output` as the same field capability; explicitly reference the
two probe Skills by their documented slash names; and make deterministic fakes
reject the malformed argv and require those references. Manually reconcile
the reviewed Claude/Codex/Grok envelope shapes into sanitized fixtures while
keeping identifiers, prompts, markers, commands, reasoning, model names, and
usage values synthetic. Do not retroactively mark the camelCase field or either
Skill path verified from review alone.

**Consequences**: Claude is ready with five verified rows and Codex with seven.
Grok native auth is verified and six rows are usable, but required Assistant
execution still fails closed because its Skill ladder has no verified channel.
Another Grok call requires an explicit owner-approved gate revision or a new
version assessment plan; it is not a hidden retry. Raw owner captures remain
outside git, and hosted CI remains fake and credential-free.

## 0030 — 2026-08-24 — Ready profiles may be explicitly and authoritatively reassessed

**Context**: The owner approved a revised G5 assessment after ADR 0029. A
corrected Grok 1.0.5 call under capture
`probe-20260824T070542Z-60bf6738` exited 0 in 16.562 seconds and reproduced the
instruction marker plus both independent Skill markers. It verified eight
required rows, including the `structuredOutput` field channel; JSON-in-`text`
remains an unverified alternative. This made all three current profiles ready,
but ordinary `doctor --probe` correctly skipped Claude and Codex because their
evidence was already current. The owner wants one fresh, visible assessment of
all three before closing G5.

**Decision**: Preserve skip-ready behavior for normal `doctor --probe`. Add
repeatable `--harness` selection (`claude` aliases `claude-code`) and explicit
`--reprobe-ready`. Selected profiles always run in profile order after all
three native profiles preflight; nonselected rows report `not-selected`.
Invalid/duplicate selectors and either new option without `--probe` fail with
exit 2 before a call or profile mutation. A forced assessment is authoritative:
every assessed failure atomically downgrades prior evidence, the existing
two-call ceiling remains, and each prompt warns about replacement. The owner
will run exactly the selected all-three command and approve only each first
prompt; an unexpected second-call prompt is declined for review.

**Consequences**: The prior Grok blocker is resolved for the currently observed
version, but G5 remains open until the fresh all-three reassessment succeeds
and its local capture is reviewed. A failure is not masked by older evidence.
No G6 call, commit, push, credential read, proxy override, or automatic capture
promotion is authorized by this decision.

## 0031 — 2026-08-24 — G5 closes on the authoritative all-three capture

**Context**: The owner ran the exact selected `--reprobe-ready` command from a
normal terminal. Capture `probe-20260824T075919Z-1edf636a` contains exactly
three terminal call-1 directories and no fallbacks: Claude Code 2.1.241 passed
in 10.363 seconds with five verified rows; Codex 0.149.1 passed in 20.490
seconds with seven; Grok 1.0.5 passed in 17.195 seconds with eight required
rows and field structured output. All artifact hashes recompute, directories
are 0700, files are 0600, and sanitized no-call doctor exits 0 with all three
profiles ready, no conflicts, and no stale rows.

**Decision**: Close M1a gate G5. G5 requires a current complete execution path,
not exhaustive behavioral proof of every vendor fallback: all base requirements
and one current verified channel in each required ladder must pass. Unused
fallbacks may correctly remain `observed`; Grok's unselected JSON-in-`text`
alternative remains `unverified` because the field location was the successful
current output. Preserve all earlier failed/partial captures as evidence and
keep raw captures outside git.

**Consequences**: G6 is now unblocked but does not start automatically; its
Ubuntu subscription-backed acceptance cycle still needs its own attended
execution confirmation and existing budget/stop rules. This closure authorizes
the requested local commit only, not a push, G6 invocation, raw-capture
promotion, credential inspection, or package publication.

## 0032 — 2026-08-24 — Independent G5 review at `317bb52`: closure verified, two CI regressions fixed, pre-G6 tasks filed

**Context**: The owner asked to "resume and review G5". A Claude (Fable 5)
session executed an owner-approved review plan over the four unpushed
commits `549804f..317bb52`: installed-CLI verification, a full owner-host
evidence audit (all five probe captures — 45/45 recorded artifact hashes
recomputed, 0700/0600 verified, per-call rows reconciled; `profiles.yaml`
rows and the sanctioned no-call doctor cross-checked with a non-mutation
hash guard; nine call directories = Claude 3 / Codex 2 / Grok 4, each traced
to its ADR 0028/0029/0030 + Q12 approval), the complete
`.github/workflows/ci.yml` step list executed locally in both dependency
modes, four read-only code-review subagents reconciled by the reviewer, and
a fixture-literal cross-grep proving the promoted fixtures share nothing
with the raw captures but protocol vocabulary. Record:
`docs/reviews/2026-08-24-g5-review-at-317bb52.md`.
**Decision**: (1) The G5 closure (ADR 0031) stands: the owner-host evidence
is genuine and matches every recorded number. (2) Two CI-breaking
regressions found by the review are fixed immediately, each in its own
commit: review R1/R2 — `from click import Abort` was an undeclared
dependency (the locked typer 0.27.1 vendors Click; external `click` arrives
only via the optional clawteam extra), which broke mypy, pytest, and every
`atm` command in core mode and made a real prompt Ctrl-C exit 1 instead of
the contractual 130 — fixed by `from typer import Abort` (code + test); and
review R8 — the G5 home-existence preflight fails the CI
deterministic-acceptance step, whose disposable fake vendor homes only
pytest's conftest ever provisioned — fixed by a `mkdir -p` in the step.
After both fixes the full step list passes locally in core mode (392 passed
+ 4 skips) and extra mode (404 passed + 3 skips; compatibility 12).
(3) Review findings R3–R6 (managed-skills lease leak on early-return paths,
an unbounded probe kill-escalation branch, stale-verified channel selection
at render time, and the discarded live Codex `-o`/JSONL disagreement) are
filed as PLAN "G5.R" tasks that gate G6. (4) The plan-amendment record and
call-budget reconciliation (review R7) are handled as a separately approved
amendment (ADR 0033). (5) The owner conditionally approved a push of `main`
once the fixes landed and the two-mode block was green, to obtain the nine
hosted CI checks on the G5 work.
**Consequences**: The push under (5) is the first publication of the G5
work; G6 remains gated on the G5.R tasks and its own attended execution
decision. Hygiene findings H1–H13 stay recorded in the review document;
only items the owner acts on become tasks.

## 0033 — 2026-08-24 — The approved M1a plan's G5 amendments are recorded and its probe budget reconciled

**Context**: Review R7 (ADR 0032): during G5 the approved plan
`docs/plans/m1a-direct-harness-poc.md` (r3, approved at `0f3e478` per
ADR 0021) was amended in place in `695a4a4`/`5efce91` under the substance of
ADRs 0026–0030, but no amendment record existed (the ADR 0022 convention),
the header still claimed unamended r3, and four passages still said "at most
two probe calls per harness" although the ADR-gated attended spend was nine
calls — making the §12 across-M1a arithmetic (2×3 + 8 + 2×8 = 30)
over-committed: 9 + 8 + 16 = 33 would breach the 30-call hard ceiling.
**Decision**: The plan gains (shown to the owner as a diff and approved
before commit): a header amendment note; a §22 "Amendments during G5
execution" table mapping every amended section to its ADR and commit; a §12
amendment paragraph restating the budget — the two-call bound is
per-assessment (ADR 0030), nine calls are spent, **21 of the 30-call ceiling
remain**, one acceptance cycle plus one confirmed rerun fit, and the
ceiling binds before the rerun allowance; and the §18 stop rule updated to
match. QUESTIONS' ADR 0020 budget record carries the same annotation. The
revision stays "r3 as amended"; no gate name or non-G5 bound changes.
**Consequences**: Future amendments to approved plans follow the ADR 0022
convention at amendment time, not retroactively. A second G6 rerun now
requires an explicit owner ceiling decision, not just the rerun allowance.

## 0034 — 2026-08-24 — G6 steering scope and the third-cycle allowance

**Context**: The owner-confirmed second G6 cycle (`run-20260824-154050-7a98`)
passed the mechanical tier live for the first time but failed at synthesis
attribution (bare invocation ids in agreement sources — the committed
instructions' own rule 3 said "every asserting leg in `sources`") and, in
the first formal live semantic evaluation, on unsteered category vocabulary
(real defects located under labels outside the oracle aliases) and Grok's
zero-finding progress narration. 14 of the 30-call ceiling remain; ADR 0033
made any further rerun an explicit owner ceiling decision.
**Decision**: The owner selected the full G6.R5 steering scope: (1) the
example Assistant definition's working method gains kebab-case
defect-type-category, one-finding-per-defect, severity, and
final-complete-output discipline (the pinned example-package hash changes
from `fb9e98a3…` to `fd54eae7…`, re-pinned in the hash-identity test and
CI); (2) `review-task.md` restates the discipline; (3) the committed oracle
gains TRUE-synonym aliases only — `argument-injection` under
command-injection; `mutation-of-caller-data` and `caller-input-mutation`
under input-mutation — an approved acceptance-bar amendment, with generic
labels (e.g. `correctness`) explicitly kept out and a regression pinning
that. G6.R4 (same session) already unified the synthesis source-pair
convention across instructions, task document, and delivered schema
descriptions. The owner also authorized PREPARING a third live cycle (the
ADR 0020 second-rerun allowance, ≤8 calls within the 14 remaining), with
the final go given only at the repeated no-call gate.
**Consequences**: The oracle amendment is part of the acceptance bar; future
alias additions need the same explicit approval. A third-cycle failure for
the same semantic reason returns to review (plan §18). The consumed
one-rerun authorization and the held-push decision are recorded in
VERIFY/PROGRESS.

## 0035 — 2026-08-24 — §18 ruling: keep the all-three gate, grant Grok a turn budget, allow one beyond-allowance cycle

**Context**: Three owner-attended G6 cycles produced the same Grok mechanical
failure class while Claude and Codex delivered valid reviews twice
consecutively: headless `grok` 1.0.5 either answers in one turn (an empty
progress snapshot became cycle 2's structured output) or is
vendor-`cancelled` at `num_turns: 2` with `structuredOutput: null` (cycles 1
and 3) — a real multi-turn review can never finish. The installed CLI
documents `--max-turns <N>`; the live recipe passed no turn control. The
owner asked whether the probe-verified `structured-output-field` vs
unverified `structured-output-text` distinction mattered; answer recorded:
the fail-hard channel policy worked as designed, and no channel can deliver
a review that was never produced — the cancelled cycles' `text` held only
concatenated empty snapshots that do not even decode as one document.
Both ADR 0020 reruns are consumed; 11 of the 30-call ceiling remain.
**Decision**: The owner keeps the all-three gate and selects G6.R6: the Grok
live recipe gains an explicit generous `GROK_MAX_TURNS = 40` (also a hard
safety ceiling), implemented test-first with render regressions; and the
owner authorizes ONE beyond-allowance live cycle (≤8 calls within the 11
remaining), with the final go given only at the repeated no-call gate. If
the Grok leg fails again, the gate question returns to the owner — never an
automatic retry.
**Consequences**: The turn budget is dated capability evidence (revisit on
any Grok version drift). The ADR 0020 rerun allowance is exhausted; this
and any future cycle authorizations are individual owner ceiling decisions
(ADR 0033 discipline).

## 0036 — 2026-08-24 — PoC A live acceptance runs Claude + Codex; Grok's leg amended out on FAIL-HARD evidence

**Context**: Four owner-attended G6 cycles produced zero real Grok reviews:
three ended `cancelled` at `num_turns: 2` with `structuredOutput: null`
(cycles 1, 3, 4 — cycle 4 with `--max-turns 40` verified in argv, falsifying
the turn-budget hypothesis) and one accepted a single-turn empty progress
snapshot (cycle 2). The cancellation cause is unreachable from the recipe at
grok 1.0.5 / grok-4.6-build. Claude and Codex delivered three consecutive
valid legs, and the offline matcher over cycle 4 shows both identifying all
three seeded defects with exact oracle categories and zero invented
criticals. 8 of the 30-call ceiling remain.
**Decision**: The owner amends the PoC A live acceptance (plan §12/§14, ADR
0022 convention; §22 table row): the live cycle runs the Claude and Codex
legs plus Claude synthesis; `live-review.yaml` requests exactly those legs
(pinned by regression). Grok's FAIL-HARD evidence is recorded per the §18
falsification routing; the deterministic tier still exercises all three
harnesses through the fakes, and Grok's profile, adapter, recipe, and probes
remain intact — the all-three question returns when a future Grok CLI
version changes the headless behavior (RISKS R27/R33). Any live cycle under
the amended gate still requires its own explicit owner confirmation within
the remaining ceiling.
**Consequences**: A passing amended cycle can close G6's live acceptance
with the two-leg ensemble; the evidence bundle and G8 record must state the
amendment and Grok's FAIL-HARD explicitly. Restoring the three-leg gate
requires fresh probe evidence on a newer Grok CLI and an owner decision.

## 0037 — 2026-08-24 — Build-vs-reuse reaffirmed post-G6 after an owner challenge and a fresh reference survey

**Context**: After G6 closed, the owner challenged the strategy: why is
AgentTeam not built on top of the `~/Documents/00000` reference projects
(ClawTeam, ClawTeam-OpenClaw, the DSH team plugins, OpenClaw/Hermes
ecosystems with A2A and Telegram), and is the new framework claimed to be
better? A fresh file-level survey of all seven reference projects
(2026-08-24) and a digest of the M0 record produced the answer.
**Decision**: The recorded strategy stands, reaffirmed on fresh evidence.
(1) The M0 record already concedes the premise: coordination and messaging
are not new layers (fit-gap TE/MS roll-ups; "MS-01: rung 1 — nothing to
build") and greenfield O8 was ranked last ("do not build a mailbox
runtime" — the legacy ATM's own lesson). (2) The one genuinely overlapping
codebase, ClawTeam, was adopted as a component, not a foundation: pinned
optional extra behind the G4-qualified seam, staged as the M1b provider
under the open written-exit-criterion question. (3) The fresh survey
confirms the reference capabilities are disjoint: no project combines team
orchestration + A2A + Telegram + vendor-CLI driving; ClawTeam is dormant
since 2026-05-09 with zero Telegram code; the Telegram material
(openclaw-multi-agent-kit) is documentation-only; the DSH plugins cannot
drive external CLIs; OpenBot embeds its own model loops;
agent-team-manager-dev's core is `export {};` with A2A as an unimplemented
ADR. (4) PoC A uses no A2A by design (independent legs + synthesis); the
A2A/Telegram reuse points activate at M1b/M1c/surfaces, where they are
already scheduled. (5) The layer AgentTeam builds — portable definitions
composed across harnesses with evidence-grade invocation records — exists
in none of them ("no system composes harnesses"; every single-harness
system blocked at TE-03), and the G6 pass is its first live proof. No
"better than theirs" claim is made or needed: vendor CLIs are the reused
agent engines, ClawTeam the reused coordination candidate.
**Consequences**: The recorded reopening triggers stay authoritative
(Q4 upstream PRs; Q6 Hermes; architecture-options §6 triggers; ADR 0036's
Grok-CLI revisit). M1b must still write the ClawTeam exit criterion before
PoC B and build the local deterministic provider first (ADR 0018). Any
future "build on X instead" decision starts from this ADR's survey
evidence, not from scratch.

## 0038 — 2026-08-24 — G8 closes M1a: the direct-harness PoC is complete

**Context**: All M1a gates are done. G6 closed 2026-08-24 with the live PoC
passing BOTH acceptance tiers (`run-20260824-170359-58d9`: mechanical
cond-1/6/7/8 and semantic cond-2/3/4/5/9 all true; three invocations valid
on attempt 1, zero retries, exit 0). G7 closed the same day: final
credential-free matrices plus the new vendor-smoke job are 12/12 green at
`0864742` (run 32765672784), after the job's first two runs each caught a
real Windows product bug (bare-name launcher resolution `1555c5d`;
case-insensitive env baseline `0864742`); the pinned history secret scan at
`dd2ec0f` and `0864742` returned exactly the 3-hit enumerated benign
baseline.
**Decision**: M1a is **closed as a semantic PASS** under the owner-amended
gate — and, as ADR 0036 requires, this G8 record states explicitly: the
passing live ensemble is the **Claude Code and Codex legs plus Claude Code
synthesis**; **Grok's leg was amended out after four owner-attended cycles
of FAIL-HARD** (headless turn-cap, `cancelled` at `num_turns: 2`,
`--max-turns 40` falsified in-argv; zero real reviews at grok 1.0.5), while
Grok remains in profiles, probes, fakes, and the compatibility surface with
the all-three question returning on a future Grok CLI release. The
owner-reviewed sanitized evidence bundle is committed at
`docs/evidence/m1a-live-2026-08-24/` with its sibling record
`docs/evidence/m1a-live-2026-08-24.md` (regeneration command, acceptance
map, 25-of-30 call ledger); raw archives stay local-only. The M1b draft
`docs/plans/m1b-team-foundation.md` (r0, proposed, NOT approved) names the
local deterministic coordination provider first and carries the draft
ClawTeam exit-criterion wording; per plan §18, M1a's approval scope ends
here and no M1b work begins without its own reviewed plan and explicit
owner approval.
**Consequences**: 5 of the 30-call live ceiling remain; every future live
call is an individual owner ceiling decision. The QUESTIONS exit-criterion
item stays open until M1b approval finalizes the wording. Future Grok
re-entry requires fresh probe evidence on a newer CLI plus an owner
decision (ADR 0036).

## 0039 — 2026-08-24 — M1b r1 independently reviewed: r2 resolves the findings; HB-03 constraints deferred out of M1b

**Context**: The expanded M1b plan r1 (`docs/plans/m1b-team-foundation.md`
at `14dc218`) received its independent review per the r0 approval
checklist. Verdict: do not approve yet — architecture direction sound,
seven approval-blocking findings and three hygiene items (recorded
verbatim in `docs/reviews/2026-08-24-m1b-plan-review-at-14dc218.md`,
commit `9802775`). The executing session re-verified every finding against
the tree at `14dc218` before any resolution work; all ten confirmed —
among them the §1-vs-§3 ClawTeam completion contradiction; the `DecidedBy`
enum change regenerating `harness-invocation-v1.schema.json` that r1
called unchanged; `decided_by: team` unsatisfiable in the r1 acceptance
fixture (every member reused `code-reviewer`, whose Assistant preference
outranks the team layer); and the seam's hard-coded `atm-lead` breaking
roster parity.
**Decision**: (1) The review is an immutable dated record in
`docs/reviews/` — closing the M1a-era gap of plan reviews leaving no
review artifact. (2) Plan revision r2 resolves all ten findings; the
r1 → r2 resolution table is plan §21. (3) On finding 3 the owner chose
**Defer**: HB-03 team-constraint semantics are deferred out of M1b
entirely — M1b ships the team preference layer only (user > Assistant >
team > default), `constraints` stays a reserved, fail-closed field, and
the HB-03 question (whether a team-level constraint binds above an
Assistant preference) stays open in QUESTIONS.md with its recorded
options; the register v3.4 amendment remains a docs-only follow-up after
the owner answers. (4) The glossary's CoordinationSubstrate `stop`
amendment (stop is a run-layer duty — stop-before-cleanup — not a
provider method) rides with the future G0 approval ADR, not with r2's
commit; normative discovery docs stay untouched until the protocol shape
is approved.
**Consequences**: r2 is proposed, NOT approved. Next: owner approval as
the G0 DECISIONS entry naming the plan file and r2's commit SHA (status
flip in the following commit), or a confirmation re-review of r2 at its
frozen SHA first — the owner's choice. Implementation stays blocked until
G0. Zero live calls were spent in M1b planning; 5 of the M1a 30 remain
untouched.

## 0040 — 2026-08-24 — M1b r2 independently reviewed: r3 resolves the findings; MemberResultV1 and the stable ClawTeam root adopted

**Context**: The second independent review — of r2 at `54728c8` — returned
"do not approve yet": six implementation-blocking gaps and three medium
corrections (recorded verbatim in
`docs/reviews/2026-08-24-m1b-plan-review-at-54728c8.md`, commit
`e89a75f`). The executing session re-verified every finding before
resolution; all nine confirmed — among them two self-contradictions in
the r2 text (the pending team record could not validate against its own
required substrate/snapshot fields; step 11 ordered the manifest before
the terminal record while the §11.4 invariant requires the reverse), the
structurally review-shaped member results (`HarnessAdapter.parse` returns
`NormalizedReviewV1`, so the `implementer` would have had to emit review
JSON), automatic handoffs contradicting the fixture's declared
reviewer/implementer independence (`no_message_edge`), the missing
green-CI completion path for a `failed-routed` ClawTeam disposition, and
the per-run ClawTeam data root breaking the seam's one-root-per-process
rule.
**Decision**: (1) The r2 review is an immutable dated record in
`docs/reviews/`. (2) Plan revision r3 resolves all nine findings; the
r2 → r3 resolution table is plan §21. (3) On finding 3 the owner chose
the larger path: **introduce `MemberResultV1` now** — a provider-neutral,
vendor-facing member-result contract (`summary`/`deliverables`/`risks`;
the schema inventory becomes three new + two regenerated files), with an
additive harness output-contract dispatch that leaves the live-proven
review path untouched, member-declared deliverables validated, hashed,
archived, and materialized for successors, and live vendor acceptance of
the new schema recorded as an explicit M1c handoff (M1b stays
zero-live-call). (4) On correction M3 the owner-approved plan adopts the
**stable `~/.agentteam/clawteam/` process root** with per-run opaque
namespaces — restoring the ADR 0015 one-root design that r2 had
accidentally deviated from. (5) Declared-independence edges get blinded
handoffs (artifact materialization without rationale, no message edge
created by the run layer itself), aligning the lifecycle with the
normative TC-03 means.
**Consequences**: r3 is proposed, NOT approved. Next: owner approval as
the G0 DECISIONS entry naming the plan file and r3's commit SHA (status
flip in the following commit), or another confirmation pass at r3's
frozen SHA — the owner's choice. Implementation stays blocked until G0.
Zero live calls spent; 5 of the M1a 30 remain untouched.

## 0041 — 2026-08-24 — M1b r3 independently reviewed: r4 resolves the findings; adapter-owned snapshot deletion after verified copy-out

**Context**: The third independent review — of r3 at `6d3f329`, whose
plan-text SHA-256 the reviewer cited and the executing session
re-verified (`8a75da96…c70e3e0`) — returned "do not approve yet": four
implementation blockers and three medium corrections (recorded verbatim
in `docs/reviews/2026-08-24-m1b-plan-review-at-6d3f329.md`, commit
`e066937`; blocker 4's heading was lost in transit and is reconstructed
in that record's disposition). All seven were re-verified against the
tree before resolution — among them: `schema_name_for` knows only
synthesis-vs-review and `write_review` is the only normalized-result
writer, so a valid MemberResultV1 had no pipeline or archive home; the
acceptance evaluator fails any leg whose target after-hash differs, so
the fixture's implementer writing its deliverable would fail the green
path; the abandon sweep terminalized tasks but not the required member
execution bindings; the failed-routed branch still left the
success-oriented ClawTeam suite red; and the qualification suite asserts
`snapshots/<space>` survives successful cleanup, contradicting r3's
cleanup description.
**Decision**: (1) The r3 review is an immutable dated record in
`docs/reviews/`. (2) Plan revision r4 resolves all seven findings; the
r3 → r4 resolution table is plan §21. Highlights: the member-result
pipeline is pinned end to end with `HarnessAdapter.parse()` untouched
and a canonical `legs/inv-<member>/member-result.json` archive home;
team-mode target semantics allow member-owned workspace mutation with
declared-deliverable-only propagation while direct-mode immutability is
unchanged; team-variant execution bindings become nullable-until-launch
with lifecycle validators; the committed `CLAWTEAM_DISPOSITION` gates
both the CLI and the success-oriented test suite under failed-routed;
the fault taxonomy exempts finalization-phase provider operations and
gains a `tasks()`-raise row; the containment allowlist is frozen to four
enumerated locations and scans case-insensitively. (3) **Snapshot
retention policy**: after a verified copy-out the ClawTeam adapter
deletes the provider-side snapshot from the stable root (deletion
failure is hygiene, green exits 0); a failed copy-out deliberately
retains the provider-side snapshot as the surviving evidence, its path
named in the failure detail.
**Consequences**: r4 is proposed, NOT approved. Next: owner approval as
the G0 DECISIONS entry naming the plan file and r4's commit SHA (status
flip in the following commit), or another confirmation pass at r4's
frozen SHA. Implementation stays blocked until G0. Zero live calls
spent; 5 of the M1a 30 remain untouched.

## 0042 — 2026-08-24 — M1b r4 independently reviewed: r5 adopts least-privilege writable tasks and closes the remaining lifecycle gaps

**Context**: The fourth independent review — of r4 at full commit
`3d0211a456cedb356aa512cb5f257b448dbb70e1`, plan SHA-256
`e1c7f222ce22785b37eb22fca553281d0936b5367313a3a7b9a1d38c587200c9`
— returned "do not approve yet": three high contract gaps, three medium
implementation gaps, and four consistency corrections. The immutable
review record landed separately at
`docs/reviews/2026-08-24-m1b-plan-review-at-3d0211a.md` (`84c7919`). The
highest-risk contradiction was concrete: r4 allowed an implementer to
write a deliverable while every real adapter remained read-only. It also
asked model validators to infer execution history absent from the record,
gave the snapshot-deleting provider no verified-copy-out signal, and did
not order publication before provider auto-unblock.

**Decision**: (1) Plan revision r5 resolves every fourth-review finding;
its r4 → r5 table is plan §21. (2) Workflow tasks gain explicit
`workspace_access` with a closed read-only default and a required resolved
run-record fact. The committed fixture grants write only to `implement`.
Team writable mappings are Claude `Write,Edit` under the existing denied
shell/web set and Codex `-s workspace-write`; team Grok renders use
generated fail-closed custom profiles extending `read-only` or
`workspace` for the matching grant. Direct and synthesis paths remain
unchanged. The mapping was checked without model calls against
installed Claude 2.1.243, Codex 0.149.1, and Grok 1.0.5, but live support
still requires fresh M1c probes and writable-deliverable acceptance. (3)
Null execution means no durable invocation allocation. Final render →
pending invocation → run binding → provider running → spawn is the one
order; models enforce representable rules and an archive verifier owns
the cross-file bijection. Render-only is state-free. (4) ADR 0041's
snapshot-deletion intent is implemented by
`cleanup(space, copy_out_verified=...) -> CleanupOutcome`: unverified
paths retain, outcomes/events carry no stable-root path, and hygiene
warnings remain non-masking. (5) Result persistence, canonical
deliverable archive/materialization, and ledger/send form a publication
barrier before provider completion. Deliverables require NFC,
platform-independent casefold collision checks, component-wise `lstat`,
renderer-path exclusion, and copy digest verification. (6) Containment
tests freeze exact declarative AST/token occurrences; the CLI is generic,
and the failed-routed reproduction is collected outside the skipped
success module.

**Consequences**: r5 is proposed, NOT approved. No product source,
schemas, discovery/register text, vendor invocation, or live capability
claim changes in this planning commit. M1b remains blocked until a later
G0 decision names the r5 file and commit SHA; its live-call budget remains
zero and the remaining five M1a calls are untouched. R36 tracks the
writable-client evidence boundary.
