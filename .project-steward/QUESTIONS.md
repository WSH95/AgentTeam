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

## Raised by the architecture panel (2026-08-22) — owner decisions, not answered by the session

Numbered Q1–Q10 to match `docs/discovery/architecture-options.md` §7 (Q11 resolved).

- [ ] Q1. Implementation language for the layer (language-agnostic CLI coupling assumed; Python makes vendoring `platform_compat.py`/`model_resolution.py` and the in-process ClawTeam fallback natural; TypeScript turns dsh-gui modules into candidates).
- [ ] Q2. Windows/macOS probe: who provides hosts, and is a passing smoke (wrapper + one `clawteam spawn subprocess`, `skip_permissions=false`, no `--task`) a precondition for accepting the architecture or the first PoC task? (TE-08 is M and unverified everywhere.)
- [ ] Q3. Acceptable enforcement levels for PoC pass: TC-05 as gate + convention + `CLAWTEAM_BIN` shim + post-hoc reconciliation; TE-05 as namespace/data-dir isolation with `independence.achieved` recorded — or must mechanical enforcement be demonstrated?
- [ ] Q4. File the nine bounded ClawTeam PRs (getuid guard, `mcp<2`, logs+exit code, parent link, `TeamMember.hidden`, cleanup stops processes, Hermes/Grok branches, `launch` errors + per-member profile + `blocked_by`, inbox ACL) now, later, or never? Upstream dormant since 2026-05-09; buys goodwill, not capability.
- [ ] Q5. Unattended-run credentials for PoC A Run 3 / ensembles: API keys (documented automation path) vs subscription OAuth for Claude Code / Codex / Grok (vendor ToS pages returned 403 to verification).
- [ ] Q6. PoC B: include a Hermes Member (exercises profile-clone adapter and `--source tool`) or Claude Code + Codex only?
- [ ] Q7. ATM licence statement (owner's own repo, no LICENSE file) so ADR 0022 schema text can be reused at rung 4 rather than re-derived.
- [ ] Q8. PoC budget and a deterministic no-op-harness tier as the first pass criterion before live-LLM runs?
- [ ] Q9. Ensemble synthesis harness for PoC A Run 3 (third harness, one of the two legs, or the Lead) and the Codex cost derivation rule (`cost_source: derived|unavailable`).
- [ ] Q10. May the Member coordination protocol be ClawTeam-CLI-specific for the PoC (cheapest) or must it be rendered per substrate from day one (avoids editing every definition on a substrate swap)?
- [x] Q11. Solo runs: may PoC A run through the `direct` launcher outside ClawTeam, or must every run be a ClawTeam team? — **Answered by the owner tiebreak (2026-08-22):** PoC A runs on the `direct` launcher; the `direct` path is in scope from day one.
