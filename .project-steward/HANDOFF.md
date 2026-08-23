---
updated_at: 2026-08-23T09:59:52Z
updated_by: cli
session_status: closed
branch: main
last_commit: 223beb6
---
# Handoff

## Now

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
`docs(architecture): keep API test route provider-neutral`; `last_commit` above
is its pre-change baseline because a commit cannot record its own final SHA.
The M1a direct harness plan remains **proposed for multi-agent review and is not
approved for product implementation**. No product code exists.

## In flight

Nothing is in flight. The expected documentation-only dirty set consists of
five architecture/plan/evidence documents plus Project Steward decision, plan,
question, risk, verification, progress, handoff, and metadata records. No source
scaffold, dependency install, repository move, credential operation, model
invocation, CI workflow change, remote creation, or push occurred.

Validation passes: 50 tracked Markdown files, 12 local links with zero broken,
60 balanced fence markers, zero candidate model/endpoint/credential/key-prefix
identifiers, exactly one provider-name occurrence in the factual ClawTeam
preset list, zero common key/private-key patterns, and `git diff --check`.
The 54×11 fit-gap matrix is untouched and was not semantically rerun.

## Next steps

1. Have the other agents review
   `docs/plans/m1a-direct-harness-poc.md`, especially section 21, against the
   original requirements and ADRs 0014–0017. Do not start G1 during review.
2. Apply only agreed plan/document corrections, rerun the checks in
   `.project-steward/VERIFY.md`, and commit the review resolution.
3. After the owner explicitly approves the final reviewed plan, change its
   status to `approved`, record G0/approval in Project Steward, and commit that
   decision before product work.
4. Execute G1 only under that approval: confirm a clean tree and absent target,
   move the same repository to `/home/wsh/Documents/AgentTeam`, add root product
   files, and preserve historical evidence. The future managed AGENTS command
   table update requires its own shown diff/approval after the scaffold exists.
5. Follow G2–G8 in order. Native login, live subscription calls, public GitHub
   repository creation, and every push remain separate visible gates.

## Blockers

- Product implementation is blocked on multi-agent plan review resolution and
  explicit owner approval; this documentation amendment does not satisfy G0.
- GitHub CLI authentication was previously invalid. This matters only at G7
  and must be repaired by the owner without sharing a token.
- Grok Build 1.0.5 exposes login but no status command; dedicated-profile auth
  is proved by the first controlled live leg at G6, not by documentation.
- The optional ClawTeam extra has not been installed or qualified in this
  documentation task; that evidence belongs to G4.
- API-test timing and target remain intentionally undecided and do not block
  M1a.

## Key files

- `docs/discovery/architecture-options.md` — current architecture constraints;
  prospective API testing is explicitly unselected.
- `docs/discovery/harness-broker-model.md` — provider-neutral execution-mode
  and profile contract.
- `docs/discovery/minimal-poc-plan.md` — historical M0 proposal with the current
  provider-neutral constraint applied.
- `docs/plans/m1a-direct-harness-poc.md` — exact proposed implementation plan
  and review checklist; CI language is provider-neutral.
- `.project-steward/PLAN.md` — M1a gates and the committed M1b–M4 roadmap.
- `.project-steward/DECISIONS.md` — ADR 0017 defines the neutrality policy;
  ADRs 0014–0016 retain the Python/optional-provider architecture and roadmap.
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
