# Discovery phase (M0) — AgentTeam

Status: **M0 discovery delivered; M0.1 review and 2026-08-23 Python architecture rebaseline applied; M1a implementation approved (G0, DECISIONS 0021) and under way gate by gate**. Historical panel, critic, evidence, and progress records are preserved as dated records. The G2 scaffold (packaging, `atm` CLI skeleton, V1 schemas) exists at the repository root; the runner arrives with G3-G4.

> **Naming amendment (2026-08-23, G1).** The product is **AgentTeam** (repository `WSH95/AgentTeam`, CLI `atm`; ADR 0012); "legacy ATM" denotes the superseded agent-team-manager experiment. Dated M0 records — panel proposals, judges, critics, evidence, the historical PoC plan, and PoC sketches in living documents — use the working name "Assistant Team System" and the working CLI name `ats`; they were deliberately not rewritten. Where a discovery document still describes Claude's subscription-compatible isolation as `--safe-mode --no-session-persistence`, the approved M1a plan §11 (revision r3) supersedes it: `--safe-mode` disables Skills, plugins, hooks, and MCP servers, so the recipe is a fresh `CLAUDE_CONFIG_DIR` plus `--setting-sources user`, `--strict-mcp-config`, tool restriction, and `--no-session-persistence`.

## The question this phase answers

> What is the smallest new software layer that genuinely needs to be built — given ClawTeam, the ClawTeam-OpenClaw fork, OpenClaw, Claude Code, Codex, Hermes, Grok and the other reference systems?

Current architecture direction (from `architecture-options.md` §5):

**The smallest new software layer is** AgentTeam: a thin, format-independent Assistant/Team core with two declared seams, `HarnessAdapter` and `CoordinationSubstrate`. It owns the portable data no candidate supplies—Assistant definitions, TeamTemplates, overlays and reviewed proposals, harness policies and invocation/ensemble records, artifact locks/resolution reports, and TeamRun rosters/nesting/archive. The selected architecture baseline is Python `>=3.11` with `uv`; closed JSON Schemas, the `atm` CLI, and a later MCP server keep every external edge language-neutral. The direct Claude Code/Codex/Grok runner is built in. Coordination systems are optional providers: ClawTeam `0.3.0@01198332ef9270c32c5460b8a178f964fc0df451` is the first seam to qualify through an optional extra, not a mandatory core dependency or harness launcher. DSH/OpenClaw/Hermes integrations remain possible edge packages/providers. PoC A is M1a; PoC B, PoC C, evolution/artifact portability, and operational Assistants are committed later milestones rather than optional backlog ideas.

The component rationale and M-row coverage remain in `architecture-options.md` §5; §5.0.2 records the Python/optional-provider amendment. `minimal-poc-plan.md` preserves the former detailed component/run proposal as history. The approved implementation plan is [`../plans/m1a-direct-harness-poc.md`](../plans/m1a-direct-harness-poc.md) (revision r3; approval artefact DECISIONS 0021).

**Current gate.** M1a is approved for product implementation (G0 done 2026-08-23). G1 — the directory rename to `/home/wsh/Documents/AgentTeam`, root `README.md`/`LICENSE`/`.gitattributes`/`.gitignore`, identity amendments, and the documentation-hygiene commit — is the current work; G2 (Python/`uv` scaffold, then the public repository and first push after an explicit approval) follows. Open owner questions live in [`../../.project-steward/QUESTIONS.md`](../../.project-steward/QUESTIONS.md); gates and tasks in [`../../.project-steward/PLAN.md`](../../.project-steward/PLAN.md).

## Reading order

| # | Document | Owns | Status |
|---|---|---|---|
| 0 | [`evidence/glossary.md`](evidence/glossary.md) | normative terminology | M0 snapshot |
| 1 | [`product-intent.md`](product-intent.md) | requirement register (frozen 2026-08-22, 54 rows), lifecycle principles, historical PoC coverage sketches, current constraints | v3.3; register frozen, current constraints applied |
| 2 | [`assistant-domain-model.md`](assistant-domain-model.md) | Assistant ≠ Skill ≠ harness; definition content; ephemeral Assistants; evolution overlays | M0 model + current auth/version amendments |
| 3 | [`team-execution-model.md`](team-execution-model.md) | TeamTemplate vs TeamRun; hidden members; nested TeamRun; long-running ops | v2.3; Python/optional-provider amendment applied; §4 execution-binding amendment (M1a r3) |
| 4 | [`harness-broker-model.md`](harness-broker-model.md) | HarnessProfile/Capability/SelectionPolicy/Broker/Invocation; definition-injection matrix; ensemble | v2.2; Python runner boundary applied |
| 5 | [`existing-systems-fit-gap.md`](existing-systems-fit-gap.md) | requirement × system matrix, 8 layers + XC, per-layer roll-ups, 54 gaps | v2.1 targeted AD-07/ATM/current-version correction; structural regression PASS (54 × 11, 0 errors; see VERIFY) |
| 6 | [`reuse-vs-build-analysis.md`](reuse-vs-build-analysis.md) | per gap: reuse rung, source, license; fork classification; new-by-evidence | v2.2; selected optional-provider scope recorded |
| 7 | [`architecture-options.md`](architecture-options.md) | 8 options on one rubric; panel + dissent; **the smallest-layer direction** | v2.2; Python/optional-provider amendment applied |
| 8 | [`minimal-poc-plan.md`](minimal-poc-plan.md) | historical M0 PoC A/B/C proposal and constraints | historical; superseded by the approved M1a plan |
| 9 | [`legacy-atm-disposition.md`](legacy-atm-disposition.md) | keep / demote / discard per ATM concept | M0 disposition + owner reuse authorization |

## Evidence files (`evidence/`)

The original ten M0 evidence files remain dated snapshots. The current review adds one verification addendum and appends current findings to the two affected evidence files; historical panel/critic records are unchanged.

| File | Covers |
|---|---|
| `clawteam-model.md` | ClawTeam team/task/mailbox/lifecycle models, templates, SKILL protocol, nested-team walk-through |
| `clawteam-spawn-platform.md` | adapters, backends, injection, resume, liveness, library seams, platform, tests, license |
| `clawteam-probe-log.md` | scratch-venv probe on this tmux-less host |
| `clawteam-openclaw-fork-delta.md` | fork features classified vs upstream |
| `openclaw-native-and-telegram-verification.md` | kit conventions + verification of OpenClaw/Telegram claims |
| `harness-cli-capabilities-a.md` / `-b.md` | HarnessCapability checklist + definition-injection matrix (claude/codex/grok; openclaw/hermes) |
| `dsh-agent-teams-and-gui.md` | DSH plugin designs |
| `claude-agent-teams-hermes-openbot.md` | Claude Code native teams, Hermes, OpenBot |
| `atm-salvage.md` | ATM requirements/evidence/ADR ideas (no architecture) |
| `m0-product-architecture-review-2026-08-22.md` | current CLI/auth/CI/provider/Telegram verification and owner constraints |
| `panel/` | architecture panel records: 3 proposals, 2 judges, owner tiebreak (complete note) |
| `critics/` | W3 adversarial critic findings (9 per-document + completeness) and the owner decisions D1–D15 that bound the fix pass |

## Conventions

- Requirements are authored only in `product-intent.md` and cited by ID elsewhere.
- Fit cells: `S C P Xs XL M n/a ?` with confidence suffix `! ~ w` and `[ev:<file>#F<n>]` citations.
- Citations: `repo/path:line` (local), URL + access date (web), `probe-log §n` (probes); otherwise UNVERIFIED.
