# Open questions

Questions an agent could not answer from the repository and must not
guess. Check off with the answer inline once resolved.

- [ ] Implementation language for M1+ (Python beside ClawTeam vs TypeScript vs other) — decide after the M0 architecture review.
- [ ] Final project name (working name "Assistant Team System"; do not assume "ATM").
- [ ] Engage HKUDS/ClawTeam upstream with issues/PRs (e.g. nested teams, `os.getuid()` Windows crash in `spawn/adapters.py`, `clawteam run --profile` ImportError)? Owner decision.
- [ ] API budget / accounts for PoCs A–C (Codex, Claude Code, optionally OpenClaw/Hermes/Grok).
- [ ] Must Grok / Hermes / OpenClaw be first-class in PoC A, or is Codex + Claude Code sufficient for the first pass?
- [ ] Should discovery docs be bilingual (EN/中文) or English only? (Assumed English only for M0.)

- [x] Should ATM register-gap candidates (lock layer, local-modification safety, approval-hash integrity, isolation posture, export/import archive, trust zones) become new rows? — **Answered 2026-08-22 (owner/session decision):** one new row AR-06 (artifact lock/fingerprint, S); isolation posture folded into TC-03; approval integrity/bounded proposals into EV-05; export/import into AR-03; platform-vs-harness dimensions into XC-02; trust zones not added (security posture is a later-phase concern; noted in RISKS).
