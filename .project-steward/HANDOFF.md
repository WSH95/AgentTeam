---
updated_at: 2026-08-23T11:25:39Z
updated_by: cli
session_status: closed
branch: main
last_commit: 972aa95
---
# Handoff

## Now

**The two M1 plans are merged.** `docs/plans/m1a-direct-harness-poc.md` is now
revision **r2** (status still *proposed*) and the single candidate plan;
`docs/plans/m1-agentteam-direct-slice.md` is superseded (banner; body kept as a
dated record). ADR 0019 records the merge and the owner's decisions: three
Skills rendered per harness in M1a; hard semantic bar with mechanical/semantic
traceability; reviewed sanitized evidence bundle per live cycle; `OverlayV1`
deferred to M3 with reserved fields; G1 renames the directory to
`/home/wsh/Documents/AgentTeam` first, then G2 creates the **public**
`WSH95/AgentTeam` (MIT) and pushes the scaffold after an explicit approval, so
CI runs from the scaffold. r2 also fixes r1 gaps found by an independent
cross-check (review/synthesis schemas in the vendors' dialect intersection,
Codex instruction-channel ladder, Windows `.cmd` shims and environment
baseline, CRLF/hash identity, oracle outside the workspace, local state layout,
"call" definition and total budget, `attendance`/`auth_mode`). The earlier
independent review (`docs/reviews/2026-08-23-m0-review-at-3407ec9.md`, ADR 0018)
stands as the dated record behind these changes. `gh` is authenticated
(account `WSH95`, `repo` scope) — the former G7 blocker is gone.

The owner-requested provider-neutral documentation amendment is complete and
validated. Current tracked documentation selects no prospective API-test
provider, endpoint, model, credential-variable name, or provider URL. Generic
provider-profile fields, environment-only secret injection, redaction, and the
no-native-auth-fallback boundary remain intact. The sole remaining provider-name
occurrence is the factual ClawTeam built-in preset inventory, not a testing
selection. ADR 0017 records this policy and Git history retains the earlier
candidate-context wording.

The architecture remains Python `>=3.11` with `uv` and Hatchling, checked-in
JSON Schema records, the `atm` CLI and M2 MCP edge, a built-in shell-free direct
harness runner, and optional coordination providers. ClawTeam is the first
optional provider, exact-pinned and confined to one owned compatibility module;
it never launches harnesses and initially claims namespace separation only.

This handoff is included in the local commit
`docs(plan): merge independent proposal into M1a r2; record merge decisions`;
`last_commit` above is its pre-change baseline because a commit cannot record its
own final SHA.
The M1a direct harness plan remains **proposed for multi-agent review and is not
approved for product implementation**. No product code exists.

## In flight

Nothing is in flight. The expected documentation-only dirty set for this
session consists of `docs/plans/m1a-direct-harness-poc.md` (r2), a banner on
`docs/plans/m1-agentteam-direct-slice.md`, and appended Project Steward
decision (ADR 0019), question, plan, risk, verification, progress and handoff
records. No source scaffold, dependency install, repository move, credential
operation, model invocation, CI workflow change, remote creation, or push
occurred.

Validation for this session: `git diff --check` clean; links in the touched
documents resolve (future `schemas/`/`examples/` paths in r2 are named, not
linked); no code fences unbalanced; zero key/private-key patterns in changed
files; `project-steward doctor` reports no failures. The 54×11 fit-gap matrix
and the discovery documents are untouched.

## Next steps

1. Have the other agents review `docs/plans/m1a-direct-harness-poc.md` **r2**
   against its section 21 checklist and section 22 merge record, the original
   requirements, and ADRs 0014–0019. Do not start G1 during review.
2. Apply only agreed plan/document corrections, rerun the checks in
   `.project-steward/VERIFY.md`, and commit the review resolution.
3. After the owner explicitly approves the final reviewed plan, record a
   DECISIONS entry naming the plan file and the commit SHA of the approved
   text, flip the status line to `approved` in the following commit, and only
   then begin product work.
4. Execute G1 only under that approval and in a fresh, sole session (the move
   changes the path that Claude Code project settings/memory and the steward
   runtime are keyed on): confirm a clean tree and absent target, move the same
   repository to `/home/wsh/Documents/AgentTeam`, add root product files
   (`README.md`, `LICENSE`, `.gitattributes`, `.gitignore`), land the
   documentation-hygiene docs-only commit (M1a §4 item 6), and preserve
   historical evidence. The managed AGENTS command-table update requires its
   own shown diff/approval after the scaffold exists.
5. G2: Python/`uv` foundation, then create the public `WSH95/AgentTeam`
   repository (MIT) and push the scaffold after explicit approval; core CI
   matrix green on three OSes from the scaffold.
6. Follow G3–G8 in order. Native login, live subscription calls, and every
   further push remain separate visible gates.

## Blockers

- Product implementation is blocked on multi-agent review of M1a r2 and the
  explicit owner approval entry; the merge does not satisfy G0.
- (Resolved 2026-08-23) GitHub CLI authentication is in place (account
  `WSH95`, `repo` scope, SSH protocol); repository creation at G2 still needs
  its own explicit approval.
- Grok Build 1.0.5 exposes login but no status command; dedicated-profile auth
  is proved by the first controlled live leg at G6, not by documentation.
- The optional ClawTeam extra has not been installed or qualified in this
  documentation task; that evidence belongs to G4.
- API-test timing and target remain intentionally undecided and do not block
  M1a.

## Key files

- `docs/plans/m1a-direct-harness-poc.md` — **r2**, the single candidate M1a
  plan (merged; section 22 = merge record); proposed, not approved.
- `docs/plans/m1-agentteam-direct-slice.md` — superseded independent proposal
  (banner; dated record).
- `docs/reviews/2026-08-23-m0-review-at-3407ec9.md` — independent review of
  the `3407ec9` baseline (findings R1–R22, H1–H14; decisions in ADR 0018).
- `docs/discovery/architecture-options.md` — current architecture constraints;
  prospective API testing is explicitly unselected.
- `docs/discovery/harness-broker-model.md` — provider-neutral execution-mode
  and profile contract.
- `docs/discovery/minimal-poc-plan.md` — historical M0 proposal with the current
  provider-neutral constraint applied.
- `.project-steward/PLAN.md` — M1a gates and the committed M1b–M4 roadmap.
- `.project-steward/DECISIONS.md` — ADR 0019 records the plan merge and its
  owner decisions; ADR 0018 the independent review; ADR 0017 the neutrality
  policy; ADRs 0014–0016 the Python/optional-provider architecture and roadmap.
- `.project-steward/QUESTIONS.md` — records the undecided API-test timing and
  target without selecting a route.
- `.project-steward/VERIFY.md` — current neutrality and documentation checks.
- `.project-steward/RISKS.md` — optional-provider/global-state, platform,
  dynamic-gate, API-test, Python/DSH, and exact-Git-dependency risks.
- `docs/discovery/evidence/m0-product-architecture-review-2026-08-22.md` —
  historical review addendum, narrowly neutralized in candidate context.
- `docs/discovery/evidence/clawteam-probe-log.md` — factual preset inventory;
  its provider-name occurrence is intentionally preserved.

## Tried and rejected

- Do not name a tentative provider, endpoint, model, credential-variable name,
  or provider URL in future API-test/CI candidate context before owner approval.
- Do not erase unrelated third-party capability evidence merely because a name
  could also be used by a future test route.
- Do not use API mode as a fallback for subscription auth and do not ask the
  owner to paste an API key into chat.
- Do not fork/vendor ClawTeam merely to pass qualification; failure stays
  isolated to its optional-provider qualification and later provider work.
- TypeScript/Node remains a superseded core decision; ClawTeam-over-CLI and its
  subprocess backend remain historical, unselected mechanics.
- Do not move the core to TypeScript for a future DSH edge; consider a small
  native edge package only if DSH becomes a primary harness.

## Warnings

- Earlier candidate-context wording remains in Git history. It contained no
  credential value; rewriting history would be a separate destructive action
  and was not requested.
- The repository is still named `assistant-team-system-dev` at
  `/home/wsh/Documents/assistant-team-system-dev`; the AgentTeam move is G1,
  not completed work.
- A future API-test route needs a fresh evidence check and explicit selection;
  do not infer one from factual provider inventories or old commits.
- Historical panel, critic, and M0 PoC records retain dated CLI-first/TypeScript
  wording by design; living documents carry the supersession amendments.
- Exact-pinned ClawTeam uses alpha, process-global seams. Preserve the optional
  boundary, reset/contain hooks, and never overclaim namespace isolation.
- Full live evidence will be sensitive local state: gitignored, owner-only,
  and never automatically committed or uploaded.
- The commit is local only. Never push without explicit approval.
- The independent review is dated to `3407ec9`; its findings are now folded
  into M1a r2 (section 22) — treat the review as a record, not an open list.
- r2 names future paths (`schemas/…`, `examples/…`, `fixtures/…`,
  `docs/evidence/…`) that do not exist yet; they are deliverables, not links.
