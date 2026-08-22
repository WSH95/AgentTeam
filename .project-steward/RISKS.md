# Risks

Known risks and mitigations. Review at wrap-up when something changed.

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| ClawTeam's tmux/Linux bias (tmux default backend; POSIX-only keepalive; `os.getuid()` on Windows) makes the cross-platform goal depend on its subprocess backend or our own | high | high | Probe the subprocess backend on this tmux-less host in W1; document per-path platform limits (XC-02); keep the option of an independent thin layer open |
| ClawTeam-OpenClaw fork has structurally diverged (re-inlined per-CLI flags; 5 xfail tests) — selective reuse may be hard to keep merged | medium | medium | Classify fork features in W1; prefer upstream-friendly extension; reuse isolated modules (`platform_compat.py`, `model_resolution.py`) only with license + merge-cost notes |
| OpenClaw/Telegram behavior has drifted from the kit's and ATM's claims (2026.3.x vs installed 2026.7.1-2) | high | medium | Local-first verification against the installed CLI, then web with URL+date; every claim gets confirmed/changed/unverifiable |
| Evidence volume overwhelms synthesis fidelity (drafters invent abstractions no substrate supports) | medium | high | Evidence schema with requirement IDs; domain models drafted after fit-gap rows exist with a mandatory "mapping to substrates" section; adversarial critics |
| ATM sunk-cost leakage (demoted concepts re-enter as architecture) | medium | medium | Glossary blocklist; critics grep for demoted nouns; ATM used only via `atm-salvage.md` |
| Harness CLIs change flags between versions (Claude Code, Codex, OpenClaw move fast) | high | low–medium | Pin versions in every HarnessCapability table; record the date; treat capability tables as HarnessProfile data, not constants |
| Workflow cost/time (≈36–45 agents) exceeds expectations | medium | low | Each workflow ≤10 agents; resume via run IDs; owner holds anchors |
| ClawTeam upstream dormant (last commit 2026-05-09, 22 open PRs; `clawteam-mcp` broken by unpinned `mcp`) — bug fixes and PRs may never land | high | medium | Pin 0.3.0@0119833 + `mcp<2`; couple only to the CLI surface behind the CoordinationSubstrate seam; file PRs as intent; keep O6 vendoring (store/transport, ~300 lines MIT) as fallback |
| Windows path unverified on every candidate (ClawTeam `os.getuid()`, POSIX keepalive, cmd.exe prompt truncation; harness vendor docs only) | high | high | Never pass `--task` through `clawteam spawn`; `skip_permissions=false`; wrapper captures exit codes; named Windows/macOS smoke as a PoC precondition (owner decision) |
| Harness CLI drift (weekly releases; Codex `developer_instructions` path unverified; Grok flags partly undocumented) | high | medium | HarnessProfiles as data with verification levels; per-adapter `--help` smoke test on each version bump; day-one probes listed in the PoC plan |
| Dynamic-member gate bypassable by a Lead calling `clawteam spawn` directly (TC-05) | medium | medium | Run-scoped `CLAWTEAM_BIN` shim + post-hoc roster/registry reconciliation; label enforcement level honestly; upstream hook PR filed |
| Model-facing tool-call non-compliance (duplicate hops, omitted calls, prose instead of a tool call) breaks autonomous choreography on some model/harness pairs — ATM U2 0/2 on DeepSeek/OpenClaw | medium | high | Reliability as a HarnessProfile dimension (HB-01); protocol state in the DAG and structured `ats`/`clawteam` calls, never prose; deterministic no-op-harness tier before live PoC runs (owner Q8); ensembles (HB-05) |
| Compliance vs mechanical failures conflated in evidence (ATM lesson) | medium | medium | HarnessInvocation record separates mechanical outcome (exit code, output) from semantic verification; PoC criteria name both |
| An aborted run leaves no record and no postmortem (ATM exit-137) | medium | medium | Terminal status for every HarnessInvocation and TeamRun, written before the first side effect (XC-04, TE-07) |
| LLM-dependent end-to-end evidence is flaky and costly (ATM R11) | high | medium | Deterministic Tier 0 separated from live Tier 1 in `minimal-poc-plan.md`; per-cycle budget caps |

Further ATM-derived candidate rows (R3, R5–R10) are listed in `docs/discovery/legacy-atm-disposition.md` §4; merge on demand.
