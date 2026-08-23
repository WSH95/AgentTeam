---
updated_at: 2026-08-23T14:54:54Z
updated_by: cli
session_status: closed
branch: main
last_commit: 762ad67
---
# Handoff

## Now

**G0 is done: M1a r3 is approved.** The owner approved revision r3 on
2026-08-23 ("I approve the r3"); DECISIONS 0021 names
`docs/plans/m1a-direct-harness-poc.md` and the approved text's commit
`0f3e478`, and the plan's status line now reads *approved for product
implementation*. Implementation starts with **G1 in a fresh, sole session in
the new directory** (see Next steps); this session deliberately did not move
the directory, add root files, scaffold, create a repository, or push.

**M1a r3 is ready for re-review.** The multi-agent review of r2 returned "do
not approve yet" (five blocking findings + corrections; architecture confirmed).
All are resolved in `docs/plans/m1a-direct-harness-poc.md` **r3** (ADR 0020):
Claude recipe without `--safe-mode` (verified: it disables Skills/plugins) —
fresh config home + `--setting-sources user` + strict MCP + tool restriction,
Skill channel probe-selected at G5; Grok `.grok/skills/` primary with
`.agents/skills/` fallback (both listed by `grok inspect` 1.0.5); Codex
`--ignore-rules` is `.rules`-only; pre-first-push checklist at G2 and CI that
grows gate by gate (G7 = final matrices + vendor-smoke job); Member bound to one
execution (invocation or ensemble) with `team-execution-model.md` §4 amended;
Windows launcher policy (resolve `.cmd` shims to `node` + script; fail-closed
allowlist) with a `.cmd` fake test and `PATH` in the baseline; computed-only
`effective_definition_hash`; required Skills fail before launch; promotion-only
parser fixtures; waiver closes as failed/abandoned, never PASS; complete
selection algorithm; V1 archive contract; Q5 kept for M4; **budget ceiling
approved by the owner: one cycle + ≤ 2 owner-confirmed reruns, ≤ 30 calls**.

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
`docs(plan): mark M1a r3 approved; hand off to G1 in a fresh session`;
`last_commit` above is its pre-change baseline because a commit cannot record its
own final SHA.
The M1a direct harness plan remains **proposed for multi-agent review and is not
approved for product implementation**. No product code exists.

## In flight

Nothing is in flight. This session's dirty set is the plan status flip and
Project Steward records (DECISIONS 0021 was committed separately as
`762ad67`). No source scaffold, dependency install, repository move, credential
operation, model invocation, CI workflow change, remote creation, or push
occurred.

## Next steps

1. **Owner, in a terminal (G1 steps 1–2 of the plan — move, never copy):**

   ```
   test ! -e /home/wsh/Documents/AgentTeam && git -C /home/wsh/Documents/assistant-team-system-dev status --porcelain | wc -l   # must print 0
   mv /home/wsh/Documents/assistant-team-system-dev /home/wsh/Documents/AgentTeam
   git -C /home/wsh/Documents/AgentTeam log --oneline -n 1 && git -C /home/wsh/Documents/AgentTeam status --short   # same HEAD, clean
   ```

   Then `cd /home/wsh/Documents/AgentTeam && claude` and say "resume". Do not
   keep another session open on the old path.
2. **Fresh session — rest of G1:** root `README.md` (alpha status), `LICENSE`
   (MIT, `Copyright (c) 2026 ShuhanWang`), `.gitattributes`
   (`* text=auto eol=lf`), implementation `.gitignore`; identity updates in
   PROJECT.md / discovery landing page / new product docs with amendment notes
   (no blanket `ats`/`ATM` replacement); commit
   `chore(project): rename project to AgentTeam`; then the documentation-hygiene
   docs-only commit (plan §4 item 6). The managed AGENTS command-table update
   waits for the scaffold and needs its own shown diff/approval.
3. **G2:** Python/`uv` foundation (pyproject, Hatchling, `uv.lock`, `src/agentteam/`,
   checked-in schemas, `atm --help/--version`); pre-first-push checklist
   (history secret scan, licence/notices, `docs/provenance.md`, name checks);
   create the public `WSH95/AgentTeam` repository (MIT) and push the scaffold
   **only after explicit approval at that moment**; scaffold smoke matrix green
   on three OSes.
4. G3–G8 in order per the approved plan; live reruns each separately confirmed
   (ceiling 30 calls); every further push is its own visible gate.

## Blockers

- None for G1. The directory move must happen between sessions (a running
  session's paths go stale); the first push waits for its G2 approval moment.
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

- `docs/plans/m1a-direct-harness-poc.md` — **r3, approved** (DECISIONS 0021;
  approved text `0f3e478`); section 22 = merge record + r3 resolutions.
- `docs/discovery/team-execution-model.md` — v2.3; §4 execution-binding
  amendment (one invocation or one ensemble per Member at a time).
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
- `.project-steward/DECISIONS.md` — ADR 0021 is the G0 approval artefact;
  ADR 0020 the r3 review resolutions and budget ceiling; ADR 0019 the plan
  merge; ADR 0018 the independent review; ADR 0017 the neutrality policy;
  ADRs 0014–0016 the Python/optional-provider architecture and roadmap.
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
- `--safe-mode` must not return to the Claude recipe: it disables Skills,
  plugins, hooks, and MCP servers (verified in 2.1.241 `--help`); the
  subscription-compatible isolation is the fresh config home plus
  `--setting-sources user` and strict MCP.
