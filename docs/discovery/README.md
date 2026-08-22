# Discovery phase (M0) — Assistant Team System

Status: **in progress** (2026-08-21). Discovery only — no production code. Ends with a STOP for product/architecture review.

## The question this phase answers

> What is the smallest new software layer that genuinely needs to be built — given ClawTeam, the ClawTeam-OpenClaw fork, OpenClaw, Claude Code, Codex, Hermes, Grok and the other reference systems?

Answer: *(filled when `architecture-options.md` is complete)*.

## Reading order

| # | Document | Owns | Status |
|---|---|---|---|
| 0 | [`evidence/glossary.md`](evidence/glossary.md) | normative terminology | written |
| 1 | [`product-intent.md`](product-intent.md) | requirement register, lifecycle principles, PoC acceptance criteria | register + criteria written; prose pending W1 |
| 2 | [`assistant-domain-model.md`](assistant-domain-model.md) | Assistant ≠ Skill ≠ harness; definition content; ephemeral Assistants; evolution overlays | pending |
| 3 | [`team-execution-model.md`](team-execution-model.md) | TeamTemplate vs TeamRun; hidden members; nested TeamRun; long-running ops | pending |
| 4 | [`harness-broker-model.md`](harness-broker-model.md) | HarnessProfile/Capability/SelectionPolicy/Broker/Invocation; definition-injection matrix; ensemble | pending |
| 5 | [`existing-systems-fit-gap.md`](existing-systems-fit-gap.md) | requirement × system matrix, 8 layers | pending |
| 6 | [`reuse-vs-build-analysis.md`](reuse-vs-build-analysis.md) | per gap: reuse rung, source, license | pending |
| 7 | [`architecture-options.md`](architecture-options.md) | options compared; **the smallest-layer answer** | pending |
| 8 | [`minimal-poc-plan.md`](minimal-poc-plan.md) | PoC A/B/C definitions | pending |
| 9 | [`legacy-atm-disposition.md`](legacy-atm-disposition.md) | keep / demote / discard per ATM concept | pending |

## Evidence files (`evidence/`)

Uniform schema (frontmatter + numbered findings `F1…Fn` with verification level and requirement IDs + negative findings + platform/license notes). Evidence files state facts and never recommend.

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

## Conventions

- Requirements are authored only in `product-intent.md` and cited by ID elsewhere.
- Fit cells: `S C P Xs XL M n/a ?` with confidence suffix `! ~ w` and `[ev:<file>#F<n>]` citations.
- Citations: `repo/path:line` (local), URL + access date (web), `probe-log §n` (probes); otherwise UNVERIFIED.
