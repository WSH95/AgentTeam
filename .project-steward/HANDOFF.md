---
updated_at: 2026-08-23T06:16:37Z
updated_by: cli
session_status: closed
branch: main
last_commit: 3407ec9
---
# Handoff

## Now

M0.1 is closed in commit `3407ec9` (`docs(discovery): apply M0 product
architecture review`). Starting from that clean boundary, a concrete AgentTeam
M1a direct-harness PoC plan has been written at
`docs/plans/m1a-direct-harness-poc.md` and synchronized with Project Steward
decisions, questions, risks, and verification. The plan is **proposed for
multi-agent review and is not approved for implementation**. The owner asked
to commit this proposed planning baseline so other agents can review one stable
Git state; that commit does not approve G1 or any later implementation gate.

The proposed M1a proves solo direct execution plus a required parallel
Claude/Codex/Grok review ensemble and separate Claude synthesis. It fixes the
TypeScript/Node stack, V1 contracts, `atm` CLI, native subscription-profile
boundary, model/effort precedence, full-local-evidence policy, fake-harness CI,
Ubuntu live acceptance, call/time limits, publication gate, and hard stop
before ClawTeam. No product code exists.

## In flight

No implementation is in flight. Multi-agent review of the committed proposed
plan is pending. The planning commit contains the new plan plus its explanatory
Project Steward records. No rename, AGENTS/CLAUDE edit, dependency install,
login, credential read/write, model invocation, remote creation, or push
occurred.

## Next steps

1. Review `docs/plans/m1a-direct-harness-poc.md` against its section 20
   checklist. Confirm that review comments concern this direct-first M1a slice,
   not the historical M0 A/B/C schedule.
2. Apply agreed plan-only corrections and rerun the planning checks recorded in
   `.project-steward/VERIFY.md`. Do not begin G1 while review is open.
3. When the owner explicitly approves the final reviewed text, change its
   status to `approved`, record the implementation approval, and commit any
   review resolutions before G1.
4. Only after that commit, execute G1 in the plan: recheck a clean tree and
   absent target path, re-show the exact guarded AGENTS.md diff, obtain its
   explicit approval, then rename/re-baseline the project.
5. Follow G2–G8 in order. Native logins, live subscription calls, public GitHub
   repository creation, and push each remain visible gates; never infer them
   from general implementation approval.

## Blockers

- M1a implementation is blocked only on multi-agent review resolution and the
  owner's explicit approval of the proposed plan.
- GitHub CLI authentication was previously invalid; this matters only at G7
  and must be repaired by the owner without sharing a token.
- Grok exposes login but no status command in installed 1.0.5; dedicated-profile
  auth is proven by the first controlled live leg at G6. This is not a planning
  blocker.
- The API-test canary and its replaceable model/base URL remain deferred and do
  not block M1a.

## Key files

- `docs/plans/m1a-direct-harness-poc.md` — exact proposed implementation plan
  and review checklist.
- `.project-steward/PLAN.md` — G0–G8 milestone checklist and M1b stop boundary.
- `.project-steward/DECISIONS.md` — owner-confirmed identity/stack and
  direct-three-harness decisions (0012–0013).
- `.project-steward/QUESTIONS.md` — only later ClawTeam/Hermes/API-canary
  questions remain open.
- `.project-steward/VERIFY.md` — M0.1 evidence plus planning-only validation.
- `docs/discovery/evidence/m0-product-architecture-review-2026-08-22.md` —
  dated CLI/auth/CI/platform evidence underlying the plan.
- `docs/discovery/minimal-poc-plan.md` — historical proposal, not the current
  schedule.

## Tried and rejected

- Do not inherit the historical M0 PoC A/B/C ordering or start with ClawTeam;
  M1a is direct-first and M1b requires a separate plan.
- Do not assume Anthropic's announced separate Agent SDK/`claude -p` monthly
  credit exists. The June 15 Help Center update says that change is paused;
  budget live work by calls and time.
- Do not use API mode as a fallback for failed subscription auth and do not ask
  the owner to paste an API key into chat.
- Do not use ACP in M1a; keep it as a later transport behind the adapter seam.

## Warnings

- Committing the proposed plan makes it portable for review; it does not change
  the plan's `not approved for implementation` status.
- The repository is still named `assistant-team-system-dev` and remains at
  `/home/wsh/Documents/assistant-team-system-dev`; AgentTeam rename is G1, not
  completed work.
- AGENTS.md and CLAUDE.md are unchanged. The exact future AGENTS.md diff is in
  plan section 4 and must be shown/approved immediately before application.
- Similar public names exist. Recheck `WSH95/AgentTeam`, npm/package, and local
  `atm` availability at their gates; do not change the owner-selected identity
  silently.
- Full live evidence will be sensitive local state: gitignored, owner-only,
  never automatically committed or uploaded.
- The M0.1 and proposed-plan commits are local only. Never push without
  explicit approval.
