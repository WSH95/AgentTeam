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
