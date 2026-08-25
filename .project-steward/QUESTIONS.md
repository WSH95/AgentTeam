# Open questions

Questions that require an owner decision or later credentialed evidence. Agents
must not guess. Answered items remain here for traceability.

## Open

- [ ] Q4. Whether/when to file the bounded ClawTeam issues/PRs. Plan capability as if none merges.
- [ ] Q6. Whether a later mixed-team expansion should include Hermes, and what evidence should gate that expansion. Hermes and OpenClaw are deferred from the first pass.
- [ ] Timing and target for any deferred API-test canary. No provider,
  endpoint, or model is selected; no key is needed unless a canary is
  separately approved.

## Current gate

M1a r3 is **approved** (DECISIONS 0021). G1 done (ADR 0022); **G2 done and
closed 2026-08-23** (ADR 0023/0024). **G3 done and closed 2026-08-23** (six
legs green at `37219bb`, run 32674468887). **G4 done and closed 2026-08-23**
(per-gate plan approved in-session; commits `e699c91`/`48cac73`/`b8d5f9d`;
**all nine CI checks green at `b8d5f9d`**, run 32681299831 — six scaffold
legs plus the three-OS `clawteam` job; both deterministic acceptance tiers
PASS; VERIFY "G4 evidence"; ClawTeam qualification report under
`docs/evidence/`). **G5 closed 2026-08-24** after the owner-approved
authoritative all-three capture verified current native auth plus required
instruction/Skill/output channels for Claude, Codex, and Grok in one call each
(`probe-20260824T075919Z-1edf636a`; ADR 0031). No-call doctor reports all three
ready, no conflicts, and no stale rows. G6 is the next gate but has not started;
every push and every future live call remains separately approved. The
2026-08-24 independent review at `317bb52` verified the closure evidence,
fixed two CI-breaking regressions (`739be1a`/`83f2b3b`; ADR 0032), and filed
the PLAN "G5.R" pre-G6 tasks; the plan's call-budget wording is reconciled by
the ADR 0033 amendment. **G6 closed 2026-08-24** after five owner-gated live
cycles: R1–R6 remediations (ADR 0034/0035), the ADR 0036 gate amendment
(Claude + Codex legs; Grok FAIL-HARD recorded, revisited on a future CLI),
and a fifth-cycle two-tier PASS (`run-20260824-170359-58d9`); 25 of the
30-call ceiling spent, 5 remain. **G7 and G8 closed the same day
(ADR 0038): M1a is COMPLETE as a semantic PASS** — final matrices +
vendor-smoke 12/12 at `0864742` (two real Windows bugs caught and fixed),
pinned secret scan at the enumerated baseline, the owner-reviewed sanitized
bundle committed (`docs/evidence/m1a-live-2026-08-24/`), and the M1b draft
proposed-not-approved. Next milestone work (M1b) requires its own reviewed
plan and explicit owner approval. **The M1b plan is at draft r6
(`760a8ae`, 2026-08-24)** after five finding rounds plus a sixth
confirmation, all recorded
immutably in `docs/reviews/` (r1 at `14dc218`: 7 blocking + 3 hygiene →
r2, ADR 0039; r2 at `54728c8`: 6 blocking + 3 medium → r3, ADR 0040; r3
at `6d3f329`, text SHA-256 verified: 4 blockers + 3 medium → r4, ADR
0041; r4 at `3d0211a`, plan SHA-256 verified: 3 high + 3 medium + 4
consistency corrections → r5, ADR 0042; r5 at full `12ca6c7`, plan
SHA-256 `95ff6ab3…a44acf4`: 3 stated high gaps plus the adjudicated
terminal-pairing blocker, 2 medium gaps, and consistency corrections → r6,
ADR 0043). Owner decisions so far: HB-03 constraint semantics deferred out
of M1b entirely (ADR 0039; the question below stays open);
`MemberResultV1` introduced now and the stable `~/.agentteam/clawteam/`
process root restored per ADR 0015 (ADR 0040); adapter-owned snapshot
deletion after verified copy-out (ADR 0041), now made executable by the
ADR 0042 cleanup handshake; r5 also adopts explicit least-privilege
workspace grants, durable-allocation execution bindings, a completion
publication barrier, canonical deliverable paths, and occurrence-level
containment. r6 adds explicit team-member render scope; exact disjoint
Claude sets; collision-safe project-local Grok profiles with Windows
refusal; launch-time handoff-inclusive baselines; shared substrate typing;
and causal failed / interrupted cancelled / never-allocated abandoned task
pairings. A sixth independent review confirmed r6 at `760a8ae` (plan
SHA-256 `1776305f…e356f6`) as G0-eligible with no remaining
implementation blockers (`docs/reviews/2026-08-24-m1b-plan-review-at-760a8ae.md`).
The ClawTeam exit-criterion wording (plan §10) finalizes at approval.
Next: owner G0 as a DECISIONS entry naming the file + r6 SHA
`760a8ae8c7021b0427bf29c84f005bebdd453bf6`.

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

- [ ] Write the ClawTeam exit criterion before PoC B (review R2/R13): for example,
  the ClawTeam provider stays only if provider + workarounds are ≤ 1.5× the local
  deterministic provider's LOC and the two-roster / on-exit-noise caveats are
  accepted in writing; otherwise the local provider becomes the product path.
  *2026-08-24: M1b plan r1 §10 carries the r0 wording verbatim plus a pinned
  measurement rule (production code only, `wc -l`; shared seam excluded from
  both sides; test LOC reported as context, not counted); finalizes at M1b
  approval, decision before PoC B.*
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
