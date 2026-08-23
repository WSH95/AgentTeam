# Open questions

Questions that require an owner decision or later credentialed evidence. Agents
must not guess. Answered items remain here for traceability.

## Open

- [ ] Q1. Implementation language for M1+ (Python, TypeScript, or other).
- [ ] Q4. Whether/when to file the bounded ClawTeam issues/PRs. Plan capability as if none merges.
- [ ] Q6. Whether a later mixed-team expansion should include Hermes, and what evidence should gate that expansion. Hermes and OpenClaw are deferred from the first pass.
- [ ] Q8. Live-run budget/accounts and whether the deterministic no-op tier is a precondition or a scored acceptance tier.
- [ ] Q9. Ensemble/synthesis design, including synthesizer choice and Codex `cost_source: derived|unavailable` policy.
- [ ] Q10. Whether Member coordination text may be ClawTeam-specific in the PoC or must be rendered per substrate immediately.
- [ ] Final project name (working name "Assistant Team System"; do not assume "ATM").
- [ ] English-only vs bilingual discovery/product documentation.
- [ ] Detailed PoC choices: run count, schemas, acceptance evidence, sequence/gates, implementation slice, and LOC re-baseline.
- [ ] Timing and target for the deferred API-test canary. The current OpenRouter `stealth/ox-alpha` route is temporary/replaceable and unverified; no key is needed until a canary is explicitly approved.

## Answered in the 2026-08-22 product/architecture review

- [x] Q2. Windows/macOS verification uses GitHub-hosted CI. Test deterministic direct-path plumbing at its milestone and ClawTeam subprocess plumbing at its milestone. Do not put live credentials in CI or claim live auth/model behavior from it.
- [x] Q3. Advisory controls may pass a PoC only when bypassability is visible and audited; production claims require mechanical enforcement. Hidden is a UI projection, not an access-control boundary.
- [x] Q5. Native and unattended live runs use each vendor CLI's subscription OAuth on the owner's persistent host. ATS does not broker third-party login or copy credential stores. API-test mode is separate and never a native-auth fallback.
- [x] Q7. ATM is owner-authored and internally reusable by ATS without a separate licence grant. Record copy/adaptation provenance and retain third-party notices/terms; public licensing is still separate.
- [x] Q11. Solo/direct execution remains in scope.
- [x] First-pass harnesses are Claude Code + Codex + Grok Build. Hermes/OpenClaw are deferred.
- [x] The current API model is test-only and replaceable; no availability, price, behavior, or compatibility claim exists until a canary is run.
- [x] Register-gap disposition: AR-06 added; isolation folded into TC-03; approval integrity into EV-05; export/import into AR-03; platform-vs-harness into XC-02; trust zones deferred.
