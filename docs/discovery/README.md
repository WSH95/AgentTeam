# Discovery phase (M0) — Assistant Team System

Status: **in progress** (2026-08-22): all nine documents drafted; adversarial critic pass (W3) and owner read-through pending. Discovery only — no production code. Ends with a STOP for product/architecture review.

## The question this phase answers

> What is the smallest new software layer that genuinely needs to be built — given ClawTeam, the ClawTeam-OpenClaw fork, OpenClaw, Claude Code, Codex, Hermes, Grok and the other reference systems?

Answer (from `architecture-options.md` §5, adopted 2026-08-22 after the architecture panel):

**The smallest new software layer is** a thin, format-independent Assistant/Team layer — working name `ats` — that owns only the data no existing system has and reaches everything else through two declared seams with one implementation each. It owns, as substrate-neutral data: Assistant definitions (closed schema + exclusion validator), TeamTemplates composing Assistants by reference, Base/User/Reviewed-Evolution overlays with a deterministic resolver and a Proposal/review record, HarnessProfiles as data plus a HarnessSelectionPolicy resolved per invocation (user > Assistant > team > default), a HarnessInvocation ledger and an Ensemble synthesis record with per-invocation attribution, an artifact manifest + lock + per-host resolution report, and a TeamRun record with two roster projections (user-visible vs archive), a dynamic-member gate, a nesting contract (parent link, result carrier, isolation level recorded, stop-before-cleanup) and an archive. It declares exactly two seams — **HarnessAdapter** {profile data, injection recipe, invoke, parse} and **CoordinationSubstrate** {create_space, add_member, create/update/wait task, send/receive, snapshot, stop, cleanup} — implemented once each today: five harness adapters (claude-code, codex, grok, hermes, openclaw) that render each definition into that harness's own flags or prepared directory, and one ClawTeam adapter over the ClawTeam *CLI* (pinned 0.3.0@0119833, `mcp<2`, subprocess backend, no tmux, never `launch`, never `--task` through `spawn`, `skip_permissions=false`), plus a trivial `direct` launcher (own subprocess, file-delivered prompts, no DAG) for solo runs and ensemble legs. The HarnessBroker runs inside this layer as a library/CLI called by the run layer and by the `direct` launcher — not as a ClawTeam backend or plugin; gated operations (`member add`, `nest`, `result`) are CLI commands the Lead calls. It builds no second team substrate, no ClawTeam fork, no library-seam coupling, no Surface adapter, no artifact installer, no UI, no message bus, no task store, no liveness registry. ClawTeam supplies the task DAG, inboxes, pid registry, worktrees and snapshot; the harnesses supply execution. Size: **M (≈4–6k LOC including profile data) with the PoC-A slice ≈2–3k** — schemas + overlay resolver + claude-code and codex adapters + broker resolve/record + `direct` launcher/wrapper + ledger + Ensemble record; the run layer is gated on PoC A passing; operational mode and the Proposal generator come after PoC C.

The component table, what is explicitly not built, and what is deferred until after the PoCs are in `architecture-options.md` §5; the PoCs that would falsify this are in `minimal-poc-plan.md`.

## Reading order

| # | Document | Owns | Status |
|---|---|---|---|
| 0 | [`evidence/glossary.md`](evidence/glossary.md) | normative terminology | written |
| 1 | [`product-intent.md`](product-intent.md) | requirement register (frozen 2026-08-22, 54 rows), lifecycle principles, PoC acceptance criteria | written (v3) |
| 2 | [`assistant-domain-model.md`](assistant-domain-model.md) | Assistant ≠ Skill ≠ harness; definition content; ephemeral Assistants; evolution overlays | draft (awaiting W3 critics) |
| 3 | [`team-execution-model.md`](team-execution-model.md) | TeamTemplate vs TeamRun; hidden members; nested TeamRun; long-running ops | draft (awaiting W3 critics) |
| 4 | [`harness-broker-model.md`](harness-broker-model.md) | HarnessProfile/Capability/SelectionPolicy/Broker/Invocation; definition-injection matrix; ensemble | draft (awaiting W3 critics) |
| 5 | [`existing-systems-fit-gap.md`](existing-systems-fit-gap.md) | requirement × system matrix, 8 layers + XC, per-layer roll-ups, 54 gaps | merged draft (owner-reviewed; awaiting W3 critics) |
| 6 | [`reuse-vs-build-analysis.md`](reuse-vs-build-analysis.md) | per gap: reuse rung, source, license; fork classification; new-by-evidence | draft (awaiting W3 critics) |
| 7 | [`architecture-options.md`](architecture-options.md) | 8 options on one rubric; panel + dissent; **the smallest-layer answer** | draft (awaiting W3 critics) |
| 8 | [`minimal-poc-plan.md`](minimal-poc-plan.md) | PoC A/B/C definitions, platform matrix, stop criteria | draft (awaiting W3 critics) |
| 9 | [`legacy-atm-disposition.md`](legacy-atm-disposition.md) | keep / demote / discard per ATM concept | draft (awaiting W3 critics) |

## Evidence files (`evidence/`)

Uniform schema (frontmatter + numbered findings `F1…Fn` with verification level and requirement IDs + negative findings + platform/license notes). Evidence files state facts and never recommend. **All ten written (2026-08-21/22, ≈48k words, 288 findings).**

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
| `panel/` | architecture panel records: 3 proposals, 2 judges, owner tiebreak |

## Conventions

- Requirements are authored only in `product-intent.md` and cited by ID elsewhere.
- Fit cells: `S C P Xs XL M n/a ?` with confidence suffix `! ~ w` and `[ev:<file>#F<n>]` citations.
- Citations: `repo/path:line` (local), URL + access date (web), `probe-log §n` (probes); otherwise UNVERIFIED.
