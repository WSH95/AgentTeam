# Discovery phase (M0) — Assistant Team System

Status: **M0 discovery delivered; M0.1 product/architecture review applied** (2026-08-22). Historical panel, critic, and progress records are preserved; the nine living discovery documents now carry the verified CLI/platform refresh, confirmed owner constraints, and targeted AD-07 correction recorded in [`evidence/m0-product-architecture-review-2026-08-22.md`](evidence/m0-product-architecture-review-2026-08-22.md). No production or PoC code exists. The detailed PoC shape remains provisional.

## The question this phase answers

> What is the smallest new software layer that genuinely needs to be built — given ClawTeam, the ClawTeam-OpenClaw fork, OpenClaw, Claude Code, Codex, Hermes, Grok and the other reference systems?

Current architecture direction (from `architecture-options.md` §5):

**The smallest new software layer is** a thin, format-independent Assistant/Team layer — working name `ats` — that owns only the data no existing system has and reaches everything else through two declared seams. It owns, as substrate-neutral data: Assistant definitions (closed schema + exclusion validator), TeamTemplates composing Assistants by reference, Base/User/Reviewed-Evolution overlays with a deterministic resolver and a Proposal/review record, HarnessProfiles plus a HarnessSelectionPolicy resolved per invocation (user > Assistant > team > default), a HarnessInvocation ledger and an Ensemble record with per-invocation attribution, an artifact manifest + lock + per-host resolution report, and a TeamRun record with user-visible and archive rosters, a dynamic-member gate, a nesting contract, and an archive. It declares **HarnessAdapter** {profile data, injection recipe, invoke, parse} and **CoordinationSubstrate** {create_space, add_member, create/update/wait task, send/receive, snapshot, stop, cleanup}. Five harness targets remain planned; Claude Code, Codex, and Grok Build are required in the first pass, while Hermes and OpenClaw are deferred. The single planned CoordinationSubstrate implementation is a ClawTeam CLI adapter (pinned 0.3.0@0119833, `mcp<2`, subprocess backend, no tmux, never `launch`, never `--task` through `spawn`, `skip_permissions=false`), plus a small `direct` launcher for solo runs and independent harness invocations. The HarnessBroker lives inside this layer, not as a ClawTeam backend or plugin. The layer builds no second team substrate, ClawTeam fork, library-seam coupling, Surface adapter, artifact installer, UI, message bus, task store, or liveness registry. ClawTeam supplies the task DAG, inboxes, pid registry, worktrees, and snapshot; harnesses supply execution. **M (≈4–6k LOC including profile data) remains a discovery estimate; the first-pass slice, detailed PoC runs, synthesis design, implementation language, sequencing, and slice LOC must be re-baselined before implementation.**

The current component rationale and M-row coverage are in `architecture-options.md` §5. Its owner assumptions remain historical context with explicit current amendments. `minimal-poc-plan.md` preserves the former detailed component/run proposal, clearly marked provisional; it is input to a later re-baselined plan, not the schedule.

**Current gate.** Documentation review is complete. No production or PoC implementation is authorized by these documents; the detailed PoC plan must be reviewed and approved separately before implementation.

## Reading order

| # | Document | Owns | Status |
|---|---|---|---|
| 0 | [`evidence/glossary.md`](evidence/glossary.md) | normative terminology | M0 snapshot |
| 1 | [`product-intent.md`](product-intent.md) | requirement register (frozen 2026-08-22, 54 rows), lifecycle principles, historical PoC coverage sketches, current constraints | v3.3; register frozen, current constraints applied |
| 2 | [`assistant-domain-model.md`](assistant-domain-model.md) | Assistant ≠ Skill ≠ harness; definition content; ephemeral Assistants; evolution overlays | M0 model + current auth/version amendments |
| 3 | [`team-execution-model.md`](team-execution-model.md) | TeamTemplate vs TeamRun; hidden members; nested TeamRun; long-running ops | M0 model + current CI/auth amendments |
| 4 | [`harness-broker-model.md`](harness-broker-model.md) | HarnessProfile/Capability/SelectionPolicy/Broker/Invocation; definition-injection matrix; ensemble | M0 model + current provider/auth amendments |
| 5 | [`existing-systems-fit-gap.md`](existing-systems-fit-gap.md) | requirement × system matrix, 8 layers + XC, per-layer roll-ups, 54 gaps | v2.1 targeted AD-07/ATM/current-version correction; structural regression PASS (54 × 11, 0 errors; see VERIFY) |
| 6 | [`reuse-vs-build-analysis.md`](reuse-vs-build-analysis.md) | per gap: reuse rung, source, license; fork classification; new-by-evidence | M0 analysis + ATM permission amendment |
| 7 | [`architecture-options.md`](architecture-options.md) | 8 options on one rubric; panel + dissent; **the smallest-layer direction** | v2.1; direction retained, detailed PoC provisional |
| 8 | [`minimal-poc-plan.md`](minimal-poc-plan.md) | historical M0 PoC A/B/C proposal and constraints | provisional; not an approved implementation plan |
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
