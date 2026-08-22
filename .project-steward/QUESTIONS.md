# Open questions

Questions an agent could not answer from the repository and must not
guess. Check off with the answer inline once resolved.

- [ ] Implementation language for M1+ (Python beside ClawTeam vs TypeScript vs other) — decide after the M0 architecture review.
- [ ] Final project name (working name "Assistant Team System"; do not assume "ATM").
- [ ] Engage HKUDS/ClawTeam upstream with issues/PRs (e.g. nested teams, `os.getuid()` Windows crash in `spawn/adapters.py`, `clawteam run --profile` ImportError)? Owner decision.
- [ ] API budget / accounts for PoCs A–C (Codex, Claude Code, optionally OpenClaw/Hermes/Grok).
- [ ] Must Grok / Hermes / OpenClaw be first-class in PoC A, or is Codex + Claude Code sufficient for the first pass?
- [ ] Should discovery docs be bilingual (EN/中文) or English only? (Assumed English only for M0.)
