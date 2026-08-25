---
title: Sixth independent review of the M1b team-foundation plan r6 at commit 760a8ae
status: final review record — findings dated 2026-08-25, valid for the tree at `760a8ae` only
date: 2026-08-25
reviewer: independent confirmation of r6 at the owner's request; findings rechecked against the frozen tree and installed CLI help/guides with no model calls
scope: docs/plans/m1b-team-foundation.md revision r6 as committed in `760a8ae` (`docs(plans): M1b r6 - close the r5 review findings`), read against the repository at that SHA; sixth review round, confirmation of r6 after the r1–r5 records
reviewed_commit: 760a8ae8c7021b0427bf29c84f005bebdd453bf6
reviewed_plan_sha256: 1776305f7bb0cca614efc13621b31d870a340444a70e06af168b5e7a86e356f6
decisions_recorded_in: later G0 approval remains its own DECISIONS entry; no new ADR — r6 resolutions already live in ADR 0043
companion: none
---

# Sixth independent review — M1b plan r6 at `760a8ae`

## 0. Verdict

r6 is G0-eligible. Do not approve r5. This confirmation froze r6 at full
commit `760a8ae8c7021b0427bf29c84f005bebdd453bf6` and plan SHA-256
`1776305f7bb0cca614efc13621b31d870a340444a70e06af168b5e7a86e356f6`. The
r5 hashes cited in the r6 header re-verified exactly. Every fifth-review
finding is closed in the r6 text. There are no remaining implementation
blockers. Residual notes below are not approval conditions.

Owner G0 is a separate DECISIONS entry naming
`docs/plans/m1b-team-foundation.md` and `760a8ae8c7021b0427bf29c84f005bebdd453bf6`.
This record does not flip the plan to `approved`, start product source,
spend live calls, or authorize a push. It is not edited after the fact.

## 1. Fifth-review disposition

| # | r5 finding | r6 resolution | This pass |
| --- | --- | --- | --- |
| H1 | Claude writable allow/deny overlap | Disjoint sets: writable allows `Read,Grep,Glob,LS,Skill,Write,Edit` and denies `NotebookEdit,Bash,WebFetch,WebSearch`; `dontAsk` retained | closed (`docs/plans/m1b-team-foundation.md:1047-1052`) |
| H2 | Grok unkeyed; persistent `GROK_HOME` write | Independent `invocation_scope: standalone \| team-member`; team Grok writes guarded project `.grok/sandbox.toml` with a per-render nonce profile; never writes `$GROK_HOME`; fail-closed on existing leaf, malformed global file, or name collision | closed (`:163-169`, `:1060-1089`) |
| H3 | `target.before` taken at step 5 | Step 5 is copy verification only; invocation baseline is launch-time after handoff materialization and final render, with the same `files_written` exclusions as `after`; acceptance cond-8 updated | closed (`:967-970`, `:1032-1038`, `:1447-1455`) |
| B4 | succeeded invocation paired with `abandoned` task | Run-only task `cancelled`; causal `failed` / interrupted allocated `cancelled` / never-allocated `abandoned`; pre- and post-commit provider-completion rows; no successor launch | closed (`:1190-1198`, `:1244-1258`, `:1293-1305`, `:1654-1670`) |
| M4 | containment omitted `domain/run.py` | Shared `SubstrateKind` in `domain/team.py`; `domain/run.py` frozen at zero `clawteam` tokens | closed (`:1563-1566`) |
| M6 | Windows team-Grok unpinned | Step-3 exit 2, no run directory; unit coverage injects platform facts | closed (`:955-958`, `:1707`) |
| C1 | `wait` counted as a provider method | Eleven runtime-invoked provider methods plus the protocol `wait` helper | closed (`:1625-1630`, `:1934-1935`) |
| C2 | Codex network / direct Grok precision | Team Codex pins `-c sandbox_workspace_write.network_access=false`; direct Grok remains `--sandbox read-only` with no project sandbox file | closed (`:1053-1059`, `:1086-1089`) |

No-call recheck on this host: Claude Code 2.1.243 still lists `dontAsk`;
Codex CLI 0.149.1 accepts `workspace-write` and the binary carries
`[sandbox_workspace_write] network_access`; Grok 1.0.5 documents custom
profiles, project `.grok/sandbox.toml`, and built-in warn-and-continue
versus custom fail-closed.

## 2. Residual notes (not approval-blocking)

1. Barrier step 4 and lifecycle 7b both say “materialize” handoffs. On
   the sequential fixture both copies are archive-verified, so the green
   path holds. G3 should treat 7b as verify-or-idempotent-recopy after
   render, not a second source of truth.
2. Exclusive-create of `<workspace>/.grok/sandbox.toml` refuses any
   workspace that already has that leaf. That is the fifth-review fail-
   closed rule. A live repo that already ships the file cannot run team
   Grok until a later merge policy exists. The committed `review-target`
   fixture is unaffected.
3. The historical r5 C1 row in plan §21 still says “twelve operations
   and four reviews”. Frozen history; do not rewrite it.

## 3. Sound areas not reopened

- Zero live calls in M1b; live writable/member-result evidence remains M1c.
- `HarnessAdapter.parse()` remains untouched.
- Cleanup handshake, failed-routed gating, owner bijection, HB-03 deferred,
  stable `~/.agentteam/clawteam/` root, and direct/synthesis byte-identity.
- R36 and R37 are evidence boundaries, not live-support claims.

## 4. Disposition

G0 may proceed by naming this frozen r6 SHA. Product implementation stays
blocked until that entry exists. No r7 is required for the fifth-review
findings.
