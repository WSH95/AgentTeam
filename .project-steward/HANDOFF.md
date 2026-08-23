---
updated_at: 2026-08-23T09:19:12Z
updated_by: codex
session_status: closed
branch: main
last_commit: 9aff78f
---
# Handoff

## Now

The owner-approved documentation rebaseline is complete and ready for the
local commit `docs(architecture): adopt Python core and optional substrates`.
`last_commit` above is the pre-change baseline because this handoff is included
in the new commit and cannot contain that commit's final SHA.

AgentTeam now has one current architecture story: Python `>=3.11` with `uv`
and Hatchling; checked-in JSON Schema records; the `atm` CLI and M2 MCP edge; a
built-in shell-free direct harness runner; and coordination systems as optional
providers. ClawTeam is the first optional provider, pinned to full commit
`01198332ef9270c32c5460b8a178f964fc0df451` plus `mcp>=1,<2`, with every import
confined to one owned compatibility module. It never launches harnesses. The
initial provider claim is one process data root with opaque namespaces, not
mechanical filesystem isolation.

The rewritten M1a plan remains **proposed for multi-agent review and is not
approved for product implementation**. It covers direct Claude/Codex/Grok legs,
fresh Claude synthesis, deterministic and live gates, and early optional
ClawTeam seam qualification. The roadmap explicitly retains M1b TeamRun
foundation, M1c dynamic-member PoC B, M2 nested PoC C plus MCP, M3
evolution/artifacts, and M4 operations. No product code exists.

## In flight

Nothing is in flight. No source scaffold, dependency install, repository move,
credential operation, model invocation, remote creation, or push occurred.
The top identity/stack wording in `AGENTS.md` was changed exactly as the owner
approved; all managed blocks and `CLAUDE.md` are unchanged.

Documentation validation passes: 50 Markdown files, 12 local links with zero
broken, 60 balanced fence markers, zero key/private-key pattern matches, and
`git diff --check`. The 54×11 fit-gap matrix is untouched; the `product-intent`
diff is below its frozen register, so its existing structural regression was
retained rather than represented as a new semantic review.

## Next steps

1. Have the other agents review
   `docs/plans/m1a-direct-harness-poc.md`, especially section 21, against the
   original requirements and ADRs 0014–0016. Do not start G1 during review.
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
  explicit owner approval; this documentation commit does not satisfy G0.
- GitHub CLI authentication was previously invalid. This matters only at G7
  and must be repaired by the owner without sharing a token.
- Grok Build 1.0.5 exposes login but no status command; dedicated-profile auth
  is proved by the first controlled live leg at G6, not by documentation.
- The optional ClawTeam extra has not been installed or qualified in this
  documentation task; that evidence belongs to G4.
- The replaceable API-test canary remains deferred and does not block M1a.

## Key files

- `docs/plans/m1a-direct-harness-poc.md` — exact proposed implementation plan
  and review checklist.
- `.project-steward/PLAN.md` — M1a gates and committed M1b–M4 roadmap.
- `.project-steward/DECISIONS.md` — ADRs 0014–0016 supersede the TypeScript and
  CLI-only portions of earlier decisions without rewriting history.
- `.project-steward/QUESTIONS.md` — only ClawTeam PR timing, later Hermes scope,
  and the deferred API-test canary remain open.
- `.project-steward/RISKS.md` — optional-provider/global-state, platform,
  dynamic-gate, Python/DSH, and exact-Git-dependency risks.
- `.project-steward/VERIFY.md` — current documentation validation and historical
  verification records.
- `docs/discovery/architecture-options.md` — current architecture answer and
  owner-approved Python/optional-provider amendment.
- `docs/discovery/minimal-poc-plan.md` — explicitly historical M0 proposal.

## Tried and rejected

- TypeScript/Node remains a superseded decision, not the current core stack.
- ClawTeam-over-CLI and ClawTeam `SubprocessBackend` are historical evidence,
  not the selected execution path.
- Do not fork/vendor ClawTeam merely to pass qualification; failure is isolated
  to the optional provider and blocks only its qualification/M1b provider use.
- Do not use API mode as a fallback for subscription auth and do not ask the
  owner to paste an API key into chat.
- Do not move the core to TypeScript for a future DSH edge; consider a small
  native edge package only if DSH becomes a primary harness.

## Warnings

- The repository is still named `assistant-team-system-dev` at
  `/home/wsh/Documents/assistant-team-system-dev`; the AgentTeam move is G1,
  not completed work.
- Historical panel, critic, evidence, ADR 0007/0012, and M0 PoC text retains
  dated CLI-first/TypeScript wording by design. Living documents carry explicit
  supersession notes; do not globally rewrite history.
- Exact-pinned ClawTeam uses alpha, process-global seams. Preserve the optional
  boundary, reset/contain hooks, and never overclaim namespace isolation.
- Full live evidence will be sensitive local state: gitignored, owner-only,
  and never automatically committed or uploaded.
- The commit is local only. Never push without explicit approval.
