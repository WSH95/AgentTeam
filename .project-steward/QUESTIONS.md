# Open questions

Questions that require an owner decision or later credentialed evidence. Agents
must not guess. Answered items remain here for traceability.

## Open

- [ ] Q4. Whether/when to file the bounded ClawTeam issues/PRs. Plan capability as if none merges.
- [ ] Q6. Whether a later mixed-team expansion should include Hermes, and what evidence should gate that expansion. Hermes and OpenClaw are deferred from the first pass.
- [ ] Timing and target for any deferred API-test canary. No provider,
  endpoint, or model is selected; no key is needed unless a canary is
  separately approved.
- [x] **M1c direct-ACP runtime installation timing.** G6's explicit installer
  and no-call qualification machinery are implemented, but the pinned runtime
  remains absent. On 2026-08-25 the owner approved continuing the remaining
  M1c gates, including this separately identified exact-pin install/download
  action. No pin change or model call is authorized by that decision.
- [ ] **ClawTeam exit-criterion owner decision — required at M1d D0,
  not required for M1c.** G6 measured **516 / 486 = 86/81 =
  1.061728395×**, below the approved `1.5×` ceiling (729 LOC; 213 LOC
  headroom). Current disposition is `parity-green`; hosted G5 run 32812856864
  passed all three optional OS legs. Choose exactly one:
  - **Accept:** keep optional ClawTeam support and accept in writing all four
    caveats: (1) two rosters, (2) no parent link for nested teams, (3) cleanup
    never stops processes, and (4) every containment is caller-written code,
    not configuration.
  - **Drop:** remove ClawTeam support without replacement; the local
    deterministic provider remains the product path.
  M1b G0 finalized this criterion; G6 prepared the packet and made no owner
  decision. ADR 0045 moves the final ruling to M1d D0 so M1c can establish
  the provider boundary first.
- [x] **M1c live-call ceiling.** ADR 0045 approves a conditional hard ceiling:
  18 Claude/Codex attempted prompts, or 23 only if Grok first passes G6's
  strict ACP no-call gate. This is not a call go: G7 still requires a green
  deterministic/no-call gate and fresh attended owner approval. M1d has zero
  calls. M1a's five remaining calls do not transfer.
- [ ] **M1c G7 fresh attended go.** Revised G6 is green for Claude Code,
  Codex, and Grok at zero calls, but this implementation approval does not
  authorize `atm runtime qualify-live`. The owner must explicitly choose
  whether to begin the bounded lifecycle order; each harness requires its own
  fresh confirmation and stops on its first mechanical failure.

## Current gate

M1a and M1b are complete. M1c r3 and M1d r2 are frozen and approved. M1c
G0–G5 are closed; revised G6 is locally green with all three exact current
profiles staged at zero calls and persistent/recovery still unknown. The G6
semantic commit and hosted evidence are pending. No live call is authorized;
G7 needs the separate attended go above. M1d source work waits for M1c G8 plus
D0's ClawTeam/native-spawn ruling. HB-03 remains deferred.

## Answered during G5 owner setup

- [x] Q12. Authorize a corrected Grok assessment, then add an explicit,
  selectable authoritative re-probe mode and retest Claude, Codex, and Grok
  once each before G5 closes. The corrected Grok assessment passed under
  `probe-20260824T070542Z-60bf6738`; the final all-three reassessment then
  passed under `probe-20260824T075919Z-1edf636a` and closed G5 (ADR 0030/0031).

- [x] G5 network policy: the three standard native profiles inherit the
  owner's trusted terminal/Sing-box proxy unchanged, including `NO_PROXY`;
  explicit `deny` remains available for isolated/custom profiles. Doctor,
  probes, and live runs use one policy and expose names only (ADR 0027).

## Answered in the 2026-08-22 product/architecture review

- [x] Q2. Windows/macOS verification uses GitHub-hosted CI. Test deterministic direct-runner plumbing at M1a and the optional ClawTeam import/coordination seam separately. Do not put live credentials in CI or claim live auth/model behavior from it.
- [x] Q3. Advisory controls may pass a PoC only when bypassability is visible and audited; production claims require mechanical enforcement. Hidden is a UI projection, not an access-control boundary.
- [x] Q5. Native and unattended live runs use each vendor CLI's subscription OAuth on the owner's persistent host. AgentTeam does not broker third-party login or copy credential stores. API-test mode is separate and never a native-auth fallback.
- [x] Q7. ATM is owner-authored and internally reusable by AgentTeam without a separate licence grant. Record copy/adaptation provenance and retain third-party notices/terms; public licensing is still separate.
- [x] Q11. Solo/direct execution remains in scope.
- [x] First-pass harnesses are Claude Code + Codex + Grok Build. Hermes/OpenClaw are deferred.
- [x] No API-test provider, endpoint, or model is currently selected; no
  availability, price, behavior, or compatibility claim exists until a canary
  is run.
- [x] Register-gap disposition: AR-06 added; isolation folded into TC-03; approval integrity into EV-05; export/import into AR-03; platform-vs-harness into XC-02; trust zones deferred.

## Answered in the 2026-08-23 M1a planning pass

- [x] Q1 (superseded on 2026-08-23). The earlier TypeScript/Node choice was replaced after the in-process ClawTeam architecture review; see the current answer below and ADR 0014.
- [x] Q8. Deterministic fake-harness acceptance is a mandatory precondition;
  Ubuntu live acceptance is a separate required gate. One acceptance cycle is
  bounded to eight model calls and never repeats automatically.
- [x] Q9. Use three independent Claude/Codex/Grok legs followed by a separate
  Claude synthesis. Codex cost is `unavailable`; do not derive USD from token
  tables. Treat vendor-reported cost as telemetry, not subscription billing.
- [x] Q10. Portable coordination source text is substrate-neutral; render
  substrate mechanics outside the Assistant definition.
- [x] The final product name is AgentTeam; repository `WSH95/AgentTeam`, CLI
  `atm`, and eventual local directory `/home/wsh/Documents/AgentTeam`.
- [x] English is the canonical product-documentation language.
- [x] M1a is the direct-first three-harness PoC in
  `docs/plans/m1a-direct-harness-poc.md`; its direct core remains independent
  while an optional ClawTeam seam is qualified early.

## Answered in the 2026-08-23 Python/optional-provider rebaseline

- [x] Q1 revision. Use Python `>=3.11`, `uv`, and Hatchling for the core;
  define external records with JSON Schema; keep `atm` as the CLI; add MCP in
  M2. DG/DT TypeScript is reference material, not vendored core code.
- [x] ClawTeam is an optional extra, exactly pinned to
  `01198332ef9270c32c5460b8a178f964fc0df451` plus `mcp>=1,<2`; all imports
  live in one owned compatibility/provider module, and its subprocess backend
  is never used. M1a qualifies the seam without making it a core dependency.
- [x] ClawTeam uses one process-scoped data root with opaque AgentTeam team
  namespaces. The initial claim is namespace separation only, not mechanical
  per-run filesystem isolation.
- [x] The roadmap commits M1b TeamRun foundations, M1c dynamic-member PoC B,
  M2 nested TeamRun PoC C plus MCP, M3 evolution/artifacts, and M4 operations;
  each still needs a reviewed implementation plan and owner approval.
- [x] The owner approved the exact one-time `AGENTS.md` identity/stack wording
  shown during planning; the managed command block remains unchanged until
  product scaffolding exists.

## Raised by the 2026-08-23 independent review of `3407ec9`

See `docs/reviews/2026-08-23-m0-review-at-3407ec9.md` and ADR 0018.

- [x] Two candidate M1 plans → merged into `docs/plans/m1a-direct-harness-poc.md`
  revision r2; the independent proposal is superseded (ADR 0019).
- [x] Overlay (`OverlayV1`) in M1a → deferred to M3 with reserved fields
  (ADR 0019). R15 (user-specific preferences in the Base vs overlay-only)
  must be answered before M3 starts.
- [x] Repository timing → public `WSH95/AgentTeam` (MIT) created and first
  pushed at G2 after the G1 rename; that push is its own explicit approval
  moment (ADR 0019). `gh` is authenticated (verified 2026-08-23).
- [x] Live-call budget ceiling → one initial acceptance cycle after G5, at most
  two reruns each separately confirmed by the owner, probes ≤ 2 per harness,
  hard ceiling 30 calls (ADR 0020). *2026-08-24, ADR 0033: the probe line
  became per-assessment under ADR 0030; the attended G5 spend was nine calls
  (Claude 3 / Codex 2 / Grok 4), so 21 of the 30 remain and the ceiling binds
  before the rerun allowance.*
- [x] Claude Skill channel under the isolated config home: the corrected second
  and final G5 invocation verified `$CLAUDE_CONFIG_DIR/skills/`; plugin and
  workspace fallbacks were not needed (ADR 0020/0028/0029).

- [x] Write the ClawTeam exit criterion before PoC B (review R2/R13): for example,
  the ClawTeam provider stays only if provider + workarounds are ≤ 1.5× the local
  deterministic provider's LOC and the two-roster / on-exit-noise caveats are
  accepted in writing; otherwise the local provider becomes the product path.
  *2026-08-24: M1b plan r1 §10 carries the r0 wording verbatim plus a pinned
  measurement rule (production code only, `wc -l`; shared seam excluded from
  both sides; test LOC reported as context, not counted); finalizes at M1b
  approval, decision before PoC B.* *2026-08-24, ADR 0044: the criterion and
  measurement rule are finalized exactly as written. The later accept/drop
  ruling remains open above and is not part of G0.*
- [ ] HB-03 precedence: the frozen register says user > Assistant > default; the
  living documents say user > Assistant > team > default. Amend the register
  (v3.4) or the glossary, and decide whether a team-level *constraint*
  (reviewer ≠ implementer harness) binds above an Assistant preference (review R7).
  M1a r2 implements the register's three layers (user > assistant > default)
  with `team` reserved. **Still open after G1 (2026-08-23):** the plan allows
  the register amendment only after this answer, so G1 left `product-intent.md`
  HB-03 untouched; the amendment becomes a small docs-only follow-up whenever
  the owner answers (it does not block G2). *2026-08-24: M1b plan r1 §7/§20
  carry the resolution options (A filter-then-prefer, recommended; B
  preference-layer-only; C constraints-above-user, recommended against;
  or defer) — `constraints` stays a reserved-empty TeamTemplateV1 field
  until the owner answers; the register amendment stays a docs-only
  follow-up outside the M1b plan's commits.* *2026-08-24, later (ADR
  0039): the r1 review found option A unimplementable as planned and the
  owner chose **Defer** — M1b ships the team preference layer only,
  `constraints` stays a reserved fail-closed field, and this question
  remains open with the options above for whenever the owner answers;
  plan r2 §7/§19/§20 record the deferral.*
- [ ] User-specific preferences in the Base definition vs User-Overlay-only
  (`assistant-domain-model.md` §13 Q1; review R15) — decide before overlay work.
- [x] Tiebreak assumptions (a)–(l): historical, session-authored panel inputs,
  not owner decisions (ADR 0018).
- [x] First real use: code/dev teams; PoC A → B → C order; operational mode
  after PoC C (ADR 0018).
- [x] Grok Build stays a required first-pass harness (reaffirmed; review R4 is
  recorded as a dissent; its probes are day-one blockers). *Amended
  2026-08-24 (ADR 0036): after four owner-attended G6 cycles recorded Grok
  FAIL-HARD (headless turn-cap; `--max-turns` falsified), the PoC A live
  acceptance runs Claude + Codex legs; Grok stays in probes, fakes, and the
  deterministic tier, and the all-three question returns on a future Grok
  CLI version — review R4's dissent is vindicated on live evidence.*
