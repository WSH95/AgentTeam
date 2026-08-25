# Verification

How to check the project is healthy. The commands in `AGENTS.md` are the
current credential-free local block; live model calls are always separate,
owner-attended gates.

## M1c G5 local audit and G6 qualification machinery — 2026-08-25

| Check | Result |
| --- | --- |
| Adversarial lifecycle audit | PASS locally — provider-returned identity and strict continuity are verified; unverifiable generations remain durably recoverable; cancellation, reset, recovery, event sequencing, duplicate/conflicting control ids, completion evidence, manifest finalization, workspace reservation, lease release, and close-retry faults preserve truthful terminal and cleanup facts |
| Library/archive integrity | PASS locally — staged Assistant/Team publication revalidates exact bytes under the library lock; symlinks are never followed or chmodded through; migration is exclusive-create; archive hashing is streamed/non-following; owner-only mode and audit-export failures fail closed |
| Permissions and controls | PASS locally — provider path classifications require structured paths entirely inside the supplied workspace; missing/escaping paths are unknown/outside; M1c has no full-access run grant; committed control batches remain terminal and completion controls apply last |
| Direct-ACP qualification machinery | PASS locally — the installed runtime marker binds the pinned lock and a streamed `node_modules` tree digest; qualification binds the runtime tree, sanitized child-environment value hash, config home, native version, platform, and command; unsafe cache modes and stale/tampered inputs fail closed. Bridge close failures preserve exact state for strict resume and retry. Packaged bridge SHA-256: `dfb75049910424486588409f9dd0fc29466ea8fa56d9f3547f9ec3a5da367b12` |
| Deterministic matrix | PASS — final named M1c selection **76 passed**; full core tree **735 passed + 4 expected skips** (optional ClawTeam absent and three Linux-skipped Windows launcher tests) in 75.25s |
| Static/package block | PASS — Ruff lint and format clean over 153 files; strict mypy clean over 149 source files; 25 schemas current; lock current; wheel/sdist build clean and contain the exact direct-ACP lock/package/bridge resources; Node syntax and `git diff --check` clean |
| Residual scope | REVIEWED — interactive projection embeds each portable Skill's `SKILL.md` but does not expose supporting scripts/assets as workspace paths. Full artifact projection belongs to M3; RISKS R38 records the boundary so M1c does not overclaim it |
| Gate/boundary | **G5/G6 remain open honestly** — local G5 evidence is green, but hosted Ubuntu/Windows/macOS evidence needs a semantic commit and explicit push approval. G6 machinery is ready, but the direct-ACP runtime is not installed and no install/download was authorized. No credential read, model/live call, commit, push, AGENTS/CLAUDE edit, or `.codex/` touch occurred |

Last verified: 2026-08-25 by Codex. The implementation is locally
review-ready. Do not close G5 until hosted evidence passes, or G6 until the
fresh installed-runtime, per-harness no-call qualification is recorded.

## M1c G3–G4 local deterministic close — 2026-08-25

| Check | Result |
| --- | --- |
| Retained lifecycle and recovery | PASS — fresh provider-owned sessions retain multi-turn context; same-run attach refuses prompts before strict continuity; reset closes/disposes the old generation and starts isolated context from an immutable snapshot plus deterministic `RunStateSummary`; provider crash, start failure, Ctrl-C cancellation, detach/EOF interruption, partial recovery, initialization failure, close failure, and exact close facts are durable and truthful |
| Shared workspace | PASS — one active turn per run; separate projects run concurrently while a durable canonical-path reservation rejects a second run on the same workspace; before/after tree + Git HEAD/status checkpoints are observational; dirty tracked/untracked bytes and HEAD are unchanged; shared latest code and unknown-attribution external drift are covered |
| Permissions and process ownership | PASS — Assistant/Member/run/provider ceilings intersect fail-closed; inside reads, attended one-time writes, machine-client denial, network/native-spawn/unknown denial, and outside/symlink escape denial are covered. The owned fake now launches a real parent/descendant tree and proves cross-platform tree termination; the external fake reports its limitations without fabricating deletion |
| Completion and controls | PASS — normalized multi-item work graph, transition/unblock/assignment validation, Lead-origin-only proposals, exact `done_when` evidence, reject/continue, attended accept/close, and provider-structured control application are green; queued control/event sequence is mechanically after the source turn terminal commit |
| TTY and NDJSON | PASS — Lead-default routing and the documented command shell are green; protocol negotiation, schema identity, contiguous client/server sequences, correlation, fragmented/malformed/oversized/partial-EOF frames, duplicate/out-of-order ids, permission round trips, terminal commands, machine-attendance denial, unsupported commands, and M1d dynamic-control denial remain synchronized |
| Catalog and archive | PASS — exact managed/unmanaged Assistant and Team resolution, one-Member synthetic Team, immutable definition/launch snapshots, archived launch recovery matching, owner-only local records, raw turn-event retention, manifest tamper/symlink detection, sanitized export without prompts/runtime/raw streams, list/status/export/cleanup CLI, and closed-only destructive cleanup are covered |
| Full local block | PASS — focused post-format matrix **37 passed**; full core tree **709 passed + 4 expected skips**; Ruff lint + format clean over 153 files; strict mypy clean over 149 files; 25 schemas current; wheel/sdist built offline from existing cached build requirements and include all direct-ACP resources plus interactive modules/schemas; `git diff --check` clean |
| CI and boundary | PASS locally — the six-leg Ubuntu/Windows/macOS scaffold now has a named M1c deterministic acceptance step in addition to the full suite. Hosted evidence remains G5. No direct-ACP runtime install, dependency/pin change, credential read, model/live call, commit, push, AGENTS/CLAUDE edit, or `.codex/` touch occurred |

Last verified: 2026-08-25 by Codex. G3 and G4 are locally complete; G5 now
owns the deterministic fault-matrix audit and hosted cross-platform evidence.

## M1c G2 local deterministic close — 2026-08-25

| Check | Result |
| --- | --- |
| Provider ownership seam | PASS — `MemberExecutionProvider` covers describe/doctor, open, correlated turn/events/result, queued/running/terminal cancellation, strict continuity, four-fact close, and exact run disposal; one provider owns each Member session/process/queue/cancel path |
| Deterministic ownership models | PASS — the owned-process fake launches and terminates a real child process tree and reports observable deletion; the external-host fake retains the same functional contract while truthfully reporting process/history limitations; multi-turn, cancellation, lost-context, strict-resume, and cleanup conformance are green |
| Direct ACP boundary | PASS — checked-in exact pins are `acpx@0.13.1`, `@agentclientprotocol/codex-acp@1.6.2`, and `@agentclientprotocol/claude-agent-acp@0.69.0`, each with lockfile SHA-512 integrity; the bridge imports only `acpx/runtime`, uses its session/turn/cancel/close primitives, defaults permissions to deny, and contains no ACP JSON-RPC/wire reimplementation, PTY, global-package, or `npx` fallback |
| Install/doctor boundary | PASS — installation is explicit, `npm ci`-only, content-addressed, atomically published, and package/resource/version verified; chat never installs. The zero-call doctor fails/marks unsupported honestly for a missing runtime and records `model_calls: 0`; the strict initialize/open/load identity/turn/close path is covered through the correlated fake bridge without a model call |
| Distribution | PASS — `bridge.mjs`, `package.json`, and the complete `package-lock.json` are present in both the built wheel and sdist; Node syntax check passed |
| Local matrix | PASS — focused G2 suite **13 passed**; full tree **685 passed + 4 expected skips**; Ruff clean; strict mypy clean over 138 files; 25 schemas current; wheel/sdist build and `git diff --check` clean |
| Boundary | PASS — temporary npm registry metadata/source inspection was owner-approved and used only to freeze/verify the candidate API and lock; no runtime was installed in AgentTeam or owner state, no provider/model prompt or credential read occurred, no live call/push/AGENTS/CLAUDE/`.codex/` change occurred |

Last verified: 2026-08-25 by Codex. G2 is locally complete. The optional
runtime remains uninstalled; fresh current-profile no-call qualification stays
at G6, and G7 remains separately owner-attended.

## M1c G1 local deterministic close — 2026-08-25

| Check | Result |
| --- | --- |
| Schema identity | PASS — 25 checked-in schemas dispatch through a registry keyed by `(kind, schema_version)`; TeamTemplate v1 and v2 coexist and `interactive-run-record` is a distinct kind |
| V1 compatibility | PASS — all 12 original V1 schema files are pinned to their pre-M1c SHA-256 and remained byte-identical; existing `atm run`, TeamRun, Assistant/team validation, archive, and optional-provider tests stayed green |
| Interactive contracts | PASS — TeamTemplateV2, request/run, session, turn, work, control request/receipt, completion, event, provider capability/doctor, and catalog records are closed; model-only lifecycle/action/graph invariants have negative tests |
| Library/migration | PASS — owner-home-selectable locked catalog, content-addressed immutable objects, hard coordinate collision, idempotent import, all-or-nothing exact Team references, active revisions, and CLI import/list/show; V1 migration defaults to faithful per-Member layout, requires an explicit shared-layout flag, writes a new candidate/diff, and refuses overwrite |
| Local matrix | PASS — full core tree **672 passed + 4 expected skips**; Ruff clean; strict mypy clean over 127 files; 25 schema reproduction/meta-schema/parity tests green; wheel and sdist built from the existing local build cache; `git diff --check` clean |
| Boundary | PASS — no new Python/Node dependency, network download, provider process, credential read, model/live call, push, AGENTS/CLAUDE edit, or `.codex/` touch |

Last verified: 2026-08-25 by Codex. G1 is locally complete; the semantic commit
is proposed under the configured ask-before-commit policy. G2 may proceed
without installing the optional direct-ACP runtime.

## M1b G7 milestone close — 2026-08-25

`CLAWTEAM_DISPOSITION=parity-green`

| Check | Result |
| --- | --- |
| Gate/commit index | PASS — G0 `84a60e3`; G1 `9f52dc1`; G2 `d9c93ac`; G3 `8d3f998`; G4 acceptance `8d3b3ae`, cross-platform fix `2d7b9f6`, evidence close `892fd3b`; G5 provider `688fffa`, evidence close `17b2c4f`; G6 measurement `24c6079`; G7 is the semantic commit carrying this entry |
| Provider disposition | PASS — the registry and this close record explicitly agree on `parity-green`; optional support remains qualified pending the separate pre-M1c owner accept/drop decision |
| Hosted matrix | PASS — run [32812856864](https://github.com/WSH95/AgentTeam/actions/runs/32812856864), freshly read back at close as `completed/success`, is 12/12 green at full product SHA `688fffa019a09ca21156d5e663bfd51f364b10db`: six scaffold, three ClawTeam, and three credential-free vendor-smoke jobs across Ubuntu/macOS/Windows. G7 changes documentation/steward state only, so no later product SHA requires a replacement run |
| Final optional matrix | PASS — pinned extra installed from the lock; `tests/compatibility` **31 passed**; full tree **625 passed + 3 expected Windows-only skips**; this includes qualification, shared provider conformance, and the complete CLI lifecycle |
| Final core matrix | PASS — extra removed and independently confirmed absent; full tree **594 passed + 4 expected skips** (clean compatibility skip plus three Windows-only tests) |
| Static/package/CLI block | PASS — lock current; Ruff lint and format clean over 124 files; strict mypy clean over 120 source files; 12 schemas current and export round-trip clean; wheel/sdist built; workflow parsed with exactly `scaffold`, `clawteam`, and `vendor-smoke`; Assistant/team validation, direct/team render-only, version, and pinned package-hash checks green; `git diff --check` clean |
| Live-call ledger | PASS — M1a's reviewed ledger remains **25 spent / 5 remaining**; **zero spent in M1b**. M1a's remaining calls never became an M1b or M1c allowance |
| M1c handoff | PASS — `docs/plans/m1c-dynamic-member-poc.md` is draft r0 and explicitly **PROPOSED — NOT APPROVED**. It names an unapproved 18-call budget ask, the pending ClawTeam exit-criterion decision, and the first live `member-result-v1` plus writable declared-deliverable acceptance per then-supported harness |
| Milestone result | **PASS — M1b G0–G7 complete.** Team foundation is implemented and deterministically evidenced; M1c remains a separately reviewed/approved milestone and no M1c implementation began |

Last verified: 2026-08-25 by Codex. The working environment was restored to
core-only after the optional matrix; the pre-existing untracked `.codex/`
directory remained untouched.

## M1b G6 exit-criterion measurement — 2026-08-25

| Check | Result |
| --- | --- |
| Numerator | **516 physical LOC** — `src/agentteam/compat/` is 233 (the G4 qualification baseline reproduces exactly: `clawteam.py` 228 + `__init__.py` 5); `src/agentteam/coordination/clawteam.py` is 283 |
| Denominator | **486 physical LOC** — `src/agentteam/coordination/local.py` only, per the approved symmetric deletion rule |
| Ratio and ceiling | **PASS — 516 / 486 = 86/81 = 1.061728395× ≤ 1.5×**; the ceiling is 729 LOC and measured headroom is 213 LOC |
| Test LOC context | Reported but excluded from the ratio as approved: ClawTeam `tests/compatibility/` **558 LOC**; local `tests/integration/test_coordination_local.py` **163 LOC** |
| Anti-gaming boundary | PASS — the frozen AST/text occurrence inventory remains green (**2 passed**); shared protocol/registry/domain/run code stays excluded from both sides and no provider glue moved into the run or command layers |
| Qualification context | PASS — G5 disposition is `parity-green`; hosted run 32812856864 is 12/12 green, including the complete conformance/lifecycle suite on all three optional-provider OS legs |
| Caveat packet | READY, undecided — owner must choose before M1c PoC B: accept all four in writing (two rosters; no parent link for nested teams; cleanup never stops processes; every containment is caller-written code, not configuration) or drop ClawTeam support without replacement; QUESTIONS carries the two explicit choices |
| Boundary | PASS — measurement and documentation only; zero live/model calls, credential reads, source/schema/dependency/AGENTS/CLAUDE/M1c changes; the five M1a calls remain untouched |

Pinned production commands, recorded verbatim from approved plan section 10:

```text
find src/agentteam/compat src/agentteam/coordination/clawteam.py -name '*.py' -exec cat {} + | wc -l
cat src/agentteam/coordination/local.py | wc -l
```

Independent `wc -l` file enumeration reproduced every subtotal; exact
`fractions.Fraction` arithmetic asserted `516/486 == 86/81` and the ceiling.

Last verified: 2026-08-25 by Codex. G6 prepares but does not take the owner
decision; M1b may proceed to G7, while PoC B may not begin until that decision.

## M1b G5 hosted evidence — 2026-08-25 (gate closed, parity-green)

| Check | Result |
| --- | --- |
| Optional three-OS matrix | PASS — run [32812856864](https://github.com/WSH95/AgentTeam/actions/runs/32812856864) at full SHA `688fffa019a09ca21156d5e663bfd51f364b10db`: Ubuntu, macOS, and Windows Python 3.11 all passed the pinned-extra qualification + provider conformance + complete three-member CLI lifecycle step |
| Containment/lifecycle result | PASS — every optional leg exercised the logical lead, stable process root, opaque namespace, roster/status/error/message reconciliation, exact cleanup handshake, all twelve section-13 conditions, stop-before-cleanup ordering, and forbidden-backend import assertions |
| Core regression matrix | PASS — all six scaffold legs (three OSes × Python 3.11/3.13) passed lock, core-only sync, Ruff, format, mypy, full tests with clean optional skip, build, schemas, CLI smoke, hash identity, and named direct+team acceptance |
| Whole workflow | PASS — all 12 jobs green, including the three unchanged credential-free vendor-smoke legs; no vendor login, model invocation, secret, or live call |
| Gate result | PASS — committed `CLAWTEAM_DISPOSITION` is `parity-green`; G5 is closed and the measured G6 exit-criterion decision may begin after this closure commit |

Last verified: 2026-08-25 by Codex. G5 product commit is `688fffa`; this
steward checkpoint records the hosted result.

## M1b G5 local verification — 2026-08-25 (pre-push)

| Check | Result |
| --- | --- |
| Optional provider | PASS — thin `coordination/clawteam.py` adapter behind the generic registry and qualified seam; logical lead reaches upstream; stable `AGENTTEAM_HOME/clawteam` process root; opaque `atm-<hex8>` namespaces; exact pin/version and honest `namespace` isolation |
| Shared conformance | PASS — **31 compatibility tests total** cover the existing 12 qualification/hostile-hook scenarios, shared protocol lifecycle, full-roster reconciliation, deterministic task order and remaining blockers, `running ↔ in_progress`, lock/lookup/message translations, snapshot restore, post-close inoperability, and two-space isolation |
| Cleanup containment | PASS — both handshake values are exact and path-free; false retains evidence; true removes only `snapshots/<space>`; a neighboring subtree survives; upstream cleanup and exact deletion are independently attempted; injected deletion failure retains evidence and reports only the closed warning code |
| Section 13 lifecycle | PASS — the same normalized twelve-condition helper used by local acceptance runs the committed three-member fake workflow through the public CLI over the optional provider; roster/DAG/messages/snapshot/member records/access/selection/isolation/immutability/publication/transport/ledger/blinding all pass; `processes-stopped` precedes provider cleanup |
| Containment and optionality | PASS — direct upstream imports remain frozen in `compat/clawteam.py`; run/commands contain no provider-specific token; the core environment has no optional package and skips the compatibility directory cleanly; the locked extra is unchanged |
| Local matrices | PASS — extra installed: full pytest **625 passed + 3 platform skips**; extra absent: full pytest **594 passed + 4 expected skips**; Ruff lint/format clean over 124 files; strict mypy clean over 120 source files; schemas and lock current; workflow YAML parses; wheel/sdist build; `git diff --check` clean |
| Debug record | PASS — first provider-conformance attempt exposed that upstream `restore()` returns a summary rather than the protocol's original opaque bundle; the adapter now reads/preserves the bundle, performs restore, and returns that bundle; immediate conformance rerun and both full matrices passed |
| Boundary | PASS — deterministic fakes only; zero model/live calls, credential reads, schema/lock-pin/AGENTS/CLAUDE/M1c changes; hosted three-OS evidence still pending; pre-existing `.codex/` untouched |

Last verified: 2026-08-25 by Codex. G5 remains open until the candidate is
fast-forward pushed and required hosted CI is green.

## M1b G4 hosted evidence — 2026-08-25 (gate closed)

| Check | Result |
| --- | --- |
| Core matrix | PASS — run [32811023030](https://github.com/WSH95/AgentTeam/actions/runs/32811023030) at full SHA `2d7b9f6e298ced033ebdab21698eff3d7a4ad439`: all six scaffold legs green (ubuntu/windows/macos × Python 3.11/3.13) |
| Named lifecycle evidence | PASS on every scaffold leg — full pytest, `atm team validate`, direct and state-free team render-only smoke, and `Deterministic direct + team acceptance via the CLI (sections 13-14)` all succeeded; the named execution pins completed tasks, exact access grants, team-layer selection, snapshot digest, cross-OS deliverable digest, and ledger count |
| Cross-platform debug | PASS — first run 32810234923 proved the new lifecycle acceptance itself green on both Windows versions but exposed Linux-forced launcher semantics and cross-drive temp refs in G3 fault fixtures; `2d7b9f6` uses the real host platform, a Windows-supported Claude/Codex parallel shape, and same-drive copied packages; both Windows full suites then passed |
| Whole workflow | PASS — all 12 jobs green: six scaffold, three optional ClawTeam compatibility, and three credential-free vendor-smoke jobs; no vendor model invocation or live call |
| Gate result | PASS — G4's deterministic three-Member lifecycle is proven through the public CLI on every required core leg; local provider remains the product path; G5 may begin after the semantic closure commit |

Last verified: 2026-08-25 by Codex. G4 is complete at product commits
`8d3b3ae` + `2d7b9f6`; this steward checkpoint records the hosted result.

## M1b G4 local verification — 2026-08-25 (pre-push)

| Check | Result |
| --- | --- |
| Section 13 acceptance | PASS — the committed three-member request runs through the public CLI over local coordination and real fake processes; the test mechanically asserts roster parity, DAG closure/unblocking, roster-bounded transport, digest-linked reproducible snapshot, per-member bindings/results/access, team-decided mixed selection, terminal independence, definition/target facts, publication ordering, byte-identical transport, ledger consistency, and blinded deliverable handoff |
| Exact grants and artifacts | PASS — both Claude members carry the exact read-only allow/deny sets; the Codex implementer carries `workspace-write` plus explicit network denial; the fake-created `implementation.txt` is source/archive/materialized byte-identical and pinned at SHA-256 `d3b0ba50…b903fd`; all three member-result artifacts and bindings verify |
| Cross-platform fixes found by acceptance | PASS — Skill-free Assistants no longer create an undeclared workspace Skill marker, so the implementer launch baseline equals the pristine target; the fake deliverable writes fixed LF bytes rather than platform-translated text; assertions use platform-native path parsing and no POSIX-only facts |
| CLI/CI path | PASS locally — `atm team validate`, direct render-only, state-free team render-only, direct two-tier acceptance, and team lifecycle execution all passed with the exact workflow commands; the scaffold step now runs both direct and team acceptance and pins the team snapshot/deliverable/ledger facts; hosted evidence pending |
| Hosted attempt 1 | FAIL, diagnosed — run 32810234923 at `8d3b3ae`: all 10 non-Windows jobs green; both Windows scaffold legs failed in the full test step because G3 fault fixtures forced `platform="linux"` while launching real Windows processes, and two temporary templates formed relative refs across the runner's `C:` temp and `D:` checkout drives. The new section-13 acceptance passed on both Windows legs. Fixed by using the real host platform, a Claude/Codex-only parallel fault fixture, and same-drive copied Assistant packages; focused 44 and full 594+4 green locally; rerun pending |
| Local block | PASS — new acceptance **2 passed**; targeted acceptance/render/hash block **59 passed**; full pytest **594 passed + 4 expected skips**; Ruff lint and format clean over 121 files; strict mypy clean over 117 source files; schemas current; lock current; workflow YAML parses; wheel and sdist built; `git diff --check` clean |
| Boundary | PASS — deterministic fakes only; no model/live call, credential read, dependency/schema/optional-provider/vendor-smoke/AGENTS/CLAUDE/M1c change; one owner-approved fast-forward push for hosted CI; pre-existing `.codex/` untouched |

Last verified: 2026-08-25 by Codex. At this pre-push checkpoint G4 remained
open; the hosted closure is recorded immediately above.

## M1b G3 team runner and lifecycle — 2026-08-25

| Check | Result |
| --- | --- |
| Dispatch and preflight | PASS — `atm run` discriminates `team-run-request`; team mode rejects every direct-only shaping flag through the request-file channel; transitive validation/resolution/selection and disposable all-member rendering finish before execution; `--render-only` writes only stubs and creates no archive, space, workspace, invocation, binding, or process |
| Exact member rendering | PASS — output contract and invocation scope are explicit; user > Assistant > team > default preference precedence is pinned; Claude receives the exact read/write tool grants, Codex the exact sandbox/network pair, and Grok a nonce-scoped project profile with collision, symlink, malformed-global, malformed-nonce, and Windows refusal negatives; standalone direct rendering remains regression-covered |
| Lifecycle and data flow | PASS — declaration-order DAG registration and readiness waves; durable pending invocation + binding before provider running/spawn; structured `MemberResultV1` extraction; canonical deliverable archive/materialization; ledger-before-send, claim-and-embed, and blinded handoffs; completion publication barrier; snapshot copy-out, cleanup handshake, package/template re-hash, terminal sweep, manifest-last finalization, and archive binding verification |
| Failure truthfulness | PASS — causal task failure cascades eagerly while unrelated work continues; infrastructure abort cancels allocated work and abandons never-launched work; SIGINT cancels and gathers active process trees before `processes-stopped`; schema outcome remains truthful across structured-output, workspace, deliverable, transport, and provider failures; pending ClawTeam disposition and forward-reference ordering are covered |
| Fault matrix | PASS — provider runtime operations, completion faults before/after delegation, bounded-wait timeout, cleanup warning, allocation/binding/spawn/result/deliverable/materialization/ledger/snapshot copy windows, cancellation, and a parallel five-task cascade are injected deterministically over the local provider |
| Local block | PASS — focused **54 passed**; full pytest **592 passed + 4 expected skips**; Ruff lint and format clean over 120 files; strict mypy clean over 116 source files; schemas current; lock current; wheel and sdist built; `git diff --check` clean |
| Boundary | PASS — no dependency, checked-in schema, CI, live/model call, credential read, push, AGENTS/CLAUDE, optional-provider implementation, or M1c change; pre-existing `.codex/` untouched |

Last verified: 2026-08-25 by Codex. The G3 semantic commit carries this
entry; hosted lifecycle evidence belongs to G4.

## M1b G2 CoordinationSubstrate and local provider — 2026-08-24

| Check | Result |
| --- | --- |
| Shared seam | PASS — synchronous runtime-checkable `CoordinationSubstrate`; exact four-state protocol task vocabulary; frozen task/message/info/cleanup DTOs; closed snapshot/warning enums; named error taxonomy; injected-clock bounded `wait_for_tasks` helper |
| Shared conformance | PASS — lead/full-roster lifecycle; task DTOs and remaining-blocker auto-unblock; unknown refs; claim ownership; protocol-status rejection; deterministic mailbox claim; opaque snapshot/read/restore; both cleanup handshake values; path-free exact outcomes; post-close inoperability; external archive-copy survival; two-space no-crossover; bounded wait |
| Local guarantees | PASS — first space is canonical `coordination/space`; per-space `t-<seq>` ids; strict pending→running→completed transitions; atomic write/replace with failure cleanup; owner-only POSIX modes; consumed messages and all state retained; tombstone records the handshake and deletes nothing; IDs/order contain no wall-clock fact; member/snapshot path escape rejected; no background-runtime imports |
| Containment | PASS — AST import inventory keeps direct optional-package imports inside `compat/clawteam.py` (tests only under `tests/compatibility`); textual inventory has exactly the approved registry key/module and disposition store/load, one domain literal, zero occurrences in `domain/run.py` and commands; new optional-provider references cannot escape without failing core tests |
| Focused tests | PASS — 29 protocol/local/conformance/containment tests |
| Full local block | PASS — `uv lock --check`; Ruff lint and format clean over 115 files; strict mypy clean over 111 source files; schemas current; pytest **538 passed + 4 expected skips**; wheel and sdist built; `git diff --check` clean |
| Boundary | PASS — no schema, dependency, public CLI, harness, compatibility-seam, CI, credential, model-call, push, AGENTS/CLAUDE, or M1c change; `.codex/` untouched |

Last verified: 2026-08-25 by Codex. G1's semantic commit is `9f52dc1`.
The G2 commit is the semantic commit carrying this entry and is indexed by
later-gate evidence and at G7.

## M1b G1 team contracts and schemas — 2026-08-24

| Check | Result |
| --- | --- |
| Contract models | PASS — `TeamTemplateV1`, `TeamRunRequestV1`, and vendor-facing `MemberResultV1` are closed and registered; template roster/relationship/preference/independence/DAG/owner-bijection/placeholder/reserved rules and request goal/override rules have model negatives |
| Run-record extension | PASS — checked-in schema is a mode-discriminated `oneOf`; direct and team variants reject cross-fields at JSON-Schema level; direct variant body and serialized field order mechanically equal the pre-M1b contract; team lifecycle nullability, invocation-only/unique bindings, and success requirements have model negatives |
| Schema delta | PASS — exactly 12 checked-in schema files; exactly three additions (`team-template`, `team-run-request`, `member-result`) and only two pre-existing files regenerated (`run-record`, `harness-invocation`); `DecidedBy` adds `team`; shared `SubstrateKind` is defined in `domain/team.py` and imported by `domain/run.py` |
| Vendor dialect | PASS — `member-result-v1` is required-all, closed, ref-free/default-free/const-free/pattern-free/format-free and uses only the pinned structured-output keyword set; non-empty summary is enforced after extraction by the model |
| Reference CLI and fixtures | PASS — `atm team validate examples/teams/development.yaml --json` reports valid, 3 members, 3 tasks, hash `f49da7444910…`; all Assistant references hash and pass strict content checks; committed Skill-free implementer, three-member template, and team request match §13 |
| Focused tests | PASS — 154 tests covering schemas, vendor projection, domain rules, template/request validation, and `atm team validate` |
| Full local block | PASS — `uv lock --check`; Ruff lint clean and format clean over 108 files; strict mypy clean over 104 source files; schema check current; pytest **509 passed + 4 expected skips**; wheel and sdist built; `git diff --check` clean |
| Boundary | PASS — zero live/model calls, credential reads, dependency changes, CI changes, pushes, AGENTS/CLAUDE edits, or M1c work; pre-existing `.codex/` remains untracked and untouched |

Last verified: 2026-08-25 by Codex. Gate commit is the semantic G1 commit
carrying this entry; its SHA is indexed with later-gate evidence and at G7.

## M1b G0 approval — 2026-08-24

| Check | Result |
| --- | --- |
| Frozen plan identity | PASS — approved source is `docs/plans/m1b-team-foundation.md` at full commit `760a8ae8c7021b0427bf29c84f005bebdd453bf6`; both working-tree pre-flip content and `git show` recomputed SHA-256 `1776305f7bb0cca614efc13621b31d870a340444a70e06af168b5e7a86e356f6` |
| Independent review | PASS — five finding-bearing records are resolved and the sixth confirmation at `87d23c6` declares r6 G0-eligible with no implementation blockers |
| Owner decision | PASS — ADR 0044 records explicit approval and every plan §20 finalize-at-approval choice; the glossary stop-before-cleanup amendment is present |
| Pre-implementation baseline | PASS — lock current; Ruff clean; mypy clean over 98 source files; schemas current; pytest 453 passed + 4 expected skips; wheel and sdist built successfully using the task-local uv cache |
| Boundary | PASS — G0 is documentation/steward only; no product source/schema change, live call, credential read, push, or M1c work; pre-existing `.codex/` remains untracked and untouched |

Last verified: 2026-08-25 by Codex — M1b r6 approved; G1 may begin only
after the semantic G0 commit.

## G8 M1a close — 2026-08-24 (**M1a CLOSED as a semantic PASS**, ADR 0038)

| Check | Result |
| --- | --- |
| Evidence bundle | PASS — regenerated fresh from the passing archive, self-scanned clean, independently spot-checked (zero absolute paths, zero env values), **owner-reviewed and approved**, committed at `docs/evidence/m1a-live-2026-08-24/` (`f8b0779`) with the sibling G8 record `docs/evidence/m1a-live-2026-08-24.md` stating the ADR 0036 amendment, Grok's four-cycle FAIL-HARD, the regeneration command, and the 25-of-30 ledger. No raw or credential-shaped content is tracked (`.gitignore` rule intact) |
| M1b handover | PASS — `docs/plans/m1b-team-foundation.md` draft r0 (`856d525`), proposed and NOT approved: local deterministic provider first, ClawTeam provider second behind the qualified seam, draft exit-criterion wording (≤1.5× LOC + caveats accepted in writing); implementation gated on its own reviewed plan + owner approval (§21 convention) |
| Close rule | PASS — §14: G8 closes on semantic PASS (achieved; no waiver involved); §18: M1a's approval scope ends here, no M1b work begun |
| Boundary | PASS — zero live/model calls in G7/G8; 5 of 30 remain, each a future individual owner ceiling decision |

Last verified: 2026-08-24 by Claude — **M1a is complete**: one portable
Assistant definition executed unchanged across vendor harnesses with both
acceptance tiers PASS, deterministic evidence 12/12 green on hosted CI, and
a reviewed sanitized evidence bundle in the repository.

## G7 final CI matrices + vendor smoke — 2026-08-24 (closed)

| Check | Result |
| --- | --- |
| Core + provider matrices | PASS — already §16-final in shape since G4/G6 (6 scaffold legs 3 OS × py3.11/3.13; 3 ClawTeam legs); green in every run below |
| Vendor-smoke job | **PASS after two genuine product findings** — the job's purpose realized on day one. Run [32764172806](https://github.com/WSH95/AgentTeam/actions/runs/32764172806) (11/12) exposed that a profile's bare command name never PATH-resolves on win32 (CreateProcess appends only `.exe`; the npm `.cmd`-shim branch was unreachable for exactly the configuration every real Windows profile would use) — fixed in `1555c5d` with three cross-platform launcher regressions. Run [32764994137](https://github.com/WSH95/AgentTeam/actions/runs/32764994137) (11/12) then exposed the case-sensitive Windows env baseline: `dict(os.environ)` upper-cases keys, so `SystemRoot`/`SystemDrive` vanished from the child environment and node.exe cannot initialize at all — fixed in `0864742` (`baseline_environment`, case-insensitive on win32, shared by `build_environment` and `diagnostic_environment`; POSIX byte-identical). Final run [32765672784](https://github.com/WSH95/AgentTeam/actions/runs/32765672784) at `0864742`: **12/12 green** — the Windows leg verified npm-installed Claude Code `2.1.241 (Claude Code)` and Codex `codex-cli 0.149.1` through resolved `.cmd` shims: install presence, versions, required flag surfaces, `auth signed-out` (positively credential-free). Grok skipped per §16 with a recorded note (no verified non-interactive installer as of 2026-08-24) |
| History secret scan | PASS — pinned reproducible command (below) run at `dd2ec0f` and repeated at the final HEAD `0864742`: **exactly the 3-hit enumerated benign baseline** — deliberate fake `sk-…` fixtures (`f5e7cbb` tests/integration/test_cli_assistant.py, `4d6e082` tests/unit/test_package_load.py) and the enum source line `SECRETS = "secrets"` (`be5ce15` src/agentteam/domain/assistant.py). The G2 "0 hits" convention is upgraded to enumerated-baseline: any hit beyond these three blocks a push until reviewed; no allowlist is baked into the command |
| Boundary | PASS — no vendor login, model call, API key, or secret permission anywhere in CI; the two fixes are product code driven by hosted evidence; pushes executed under the owner's "push it. then complete M1a" instruction |

Pinned secret-scan command (run from the repository root):

```bash
git log -p --all | uv run --no-sync python -c "
import re, sys
from agentteam.domain.assistant import ProhibitedContentCheck
from agentteam.resolution.package import _HEURISTICS
secrets = _HEURISTICS[ProhibitedContentCheck.SECRETS]
private_key = re.compile(r'-----BEGIN(?: [A-Z]+)* PRIVATE KEY-----')
hits = 0
commit = path = None
for raw in sys.stdin.buffer:
    line = raw.decode('utf-8', errors='replace')
    if line.startswith('commit '):
        commit = line.split()[1][:12]
    elif line.startswith('+++ '):
        path = line[4:].strip()
    elif secrets.search(line) or private_key.search(line):
        hits += 1
        sys.stdout.write(f'{commit} {path}: {line[:160]}')
print(f'secret-scan hits: {hits}')
sys.exit(1 if hits else 0)
"
```

Last verified: 2026-08-24 by Claude — **G7 is closed**: final matrices green
12/12 at `0864742`, real-vendor Windows shim evidence recorded (R30), the
secret scan pinned and repeated at the pushed HEAD.

## G6 fifth live cycle — 2026-08-24 (**PASS**; G6 closed under the amended gate)

| Check | Result |
| --- | --- |
| Pre-run gate | PASS — doctor exit 0 (three profiles ready at the exact probe versions, zero conflicts, zero calls); package `fd54eae7…` + target `25f03027…` matched; proxy inherited; clean tree at `7e49c28`; fresh explicit owner final go under the ADR 0036 amended gate |
| Cycle | **PASS, exit 0** — `run-20260824-170359-58d9`: exactly three calls (Claude leg 119.928s, Codex leg 69.711s, Claude synthesis 40.064s), all `schema_outcome: valid` on attempt 1 with empty problems, zero retries. 25 of 30 calls spent; **5 remain** |
| Mechanical tier | **PASS** — cond-1 (independent fresh legs, one bundle, targets unmutated), cond-6 (package rehash), cond-7 (manifest), cond-8 (names-only records) |
| Semantic tier | **PASS** — cond-2 (each leg identified command injection plus other seeded defects with actionable rationales), cond-3 (union covers all three), cond-4 (zero invented criticals), cond-5 (synthesis lists all defects with six merged findings, five agreements, one disagreement, every source a valid `invocation_id:finding_id` pair — the G6.R4 steering held live), cond-9 (tiers separate) |
| Archive/privacy | PASS — manifest reconstructs with zero problems; recursive owner-only modes hold with zero violations (G6.R3's second in-vivo proof); the sanitizer bundle was produced and scanned CLEAN (held in the session scratchpad for owner review; promotion to `docs/evidence/m1a-live-<date>/` remains the G8 step); raw archive local-only and gitignored |
| Boundary | PASS — one owner-confirmed cycle under the amended gate; no retry, no API-mode fallback, no push. Every G6 remediation (R1–R6) and the ADR 0034–0036 amendments are now live-validated |

Hosted CI after the closure push: **PASS, 9/9** — run
[32755012269](https://github.com/WSH95/AgentTeam/actions/runs/32755012269)
at `58775a9` (`e722c15..58775a9` fast-forward pushed on explicit approval):
all six scaffold jobs (Ubuntu/Windows/macOS × Python 3.11/3.13) and all
three OS ClawTeam jobs green, covering the G6.R product changes, the
re-pinned `fd54eae7…` hash step, and deterministic acceptance in both tiers.

Last verified: 2026-08-24 by Claude — **G6 is closed**: the Ubuntu
subscription-backed live PoC passed both acceptance tiers under the
ADR 0036 amended gate (Claude + Codex legs + Claude synthesis), and the
closure push is hosted-CI green 9/9.

## G6 fourth live cycle — 2026-08-24 (FAIL exit 1; `--max-turns` hypothesis falsified)

| Check | Result |
| --- | --- |
| Pre-run gate | PASS — doctor exit 0 (three ready at the exact probe versions, zero conflicts, zero calls); package `fd54eae7…` + target `25f03027…` matched; proxy inherited; clean tree at `f2b8cb6`; fresh explicit owner final go under the ADR 0035 beyond-allowance authorization |
| Cycle | **FAIL, exit 1** — `run-20260824-165045-d353`, exactly three calls, zero retries, no synthesis. Claude 93.532s and Codex 69.566s both `schema_outcome: valid` with empty problems (their **third consecutive** clean live legs); Grok failed in 23.647s. 22 of 30 calls spent; **8 remain** |
| Grok falsification | `--max-turns 40` was verified present in the recorded argv — and the outcome is identical to cycles 1 and 3: `stopReason: cancelled` at `num_turns: 2`, `structuredOutput: null`, two concatenated empty per-turn snapshots in `text`, empty stderr. The turn-2 cancellation is NOT governed by `--max-turns`; the cause lives inside vendor CLI/model behavior unreachable from the recipe. Grok's live-review record: four cycles, zero real reviews (three cancelled@2, one single-turn empty snapshot). Dated capability evidence at grok 1.0.5 / grok-4.6-build (R33) |
| Boundary | PASS — the single ADR 0035 beyond-allowance cycle only; no retry, no API fallback, no push, hashes unchanged, raw evidence local-only. As committed, the Grok gate question returns to the owner; any further cycle is a new explicit owner ceiling decision |

Last verified: 2026-08-24 by Claude (owner-confirmed fourth cycle; the
turn-budget hypothesis is falsified; Claude/Codex 3/3 consecutive valid).

## G6.R6 Grok turn budget — 2026-08-24 (implemented locally; §18 ruling ADR 0035)

| Check | Result |
| --- | --- |
| Recipe | PASS — the Grok live recipe now passes `--max-turns 40` (`GROK_MAX_TURNS`, module constant with the dated-evidence comment); the probe recipe is untouched (single-turn, capability parity preserved); render regression pins the flag and a generous-bound floor (≥20) |
| Owner ruling | ADR 0035 — the all-three gate is kept; the owner's channel question (verified field vs unverified text) answered and recorded: the fail-hard policy worked as designed, and no output channel can deliver a review the cancelled agent loop never produced; ONE beyond-allowance cycle authorized with the final go at the repeated gate |
| Full local CI parity | PASS — core **pytest 447 passed + 4 skips**, optional-extra **459 + 3**, compatibility **12**; Ruff lint + format (102), strict mypy (98), schema check current, `git diff --check` clean; core restored. No live call |

Last verified: 2026-08-24 by Claude (G6.R6 test-first; effect on the turn-2
vendor cancellation is live-unprovable until the authorized cycle).

## G6 third live cycle — 2026-08-24 (FAIL exit 1; Grok turn-cap diagnosis)

| Check | Result |
| --- | --- |
| Pre-run gate | PASS — doctor exit 0 (three profiles ready at exactly 2.1.241 / 0.149.1 / 1.0.5, zero conflicts, zero calls); package `fd54eae7…` (re-pinned under ADR 0034) and target `25f03027…` matched; proxy names inherited; zero conflict variables; clean tree at `cd92bd7`; fresh explicit owner final go at the gate |
| Cycle | **FAIL, exit 1** — `run-20260824-161600-9d69`, 97.9s wall, exactly three calls, zero retries, no synthesis (§12 rule 10). Claude succeeded in 97.902s and Codex in 82.995s, both `schema_outcome: valid` with empty problems under the steered definition/task; Grok failed in 16.860s. 19 of 30 calls spent; **11 remain** |
| Grok diagnosis | The G6.R2 problems-surfacing worked: the invocation record carries `vendor structured output error: model did not produce structured output`. Raw evidence: `stopReason: cancelled`, `num_turns: 2`, and `text` holds two concatenated per-turn empty snapshots ("Starting review…", "Exploring the full module…", both `target_sha256: "placeholder"`, zero findings). Across the three cycles the vendor behavior is deterministic: a turn-1 answer becomes the output (cycle 2: `end_turn`, `num_turns: 1`, the empty snapshot); an attempt to continue is cancelled at turn 2 with no final object (cycles 1 and 3: `cancelled`, `num_turns: 2`, null field). The installed CLI documents `--max-turns <N>` ("Maximum number of agent turns") and describes `-p`/`--prompt-file` as "single-turn prompt"; the adapter passes no turn control, so the headless agent loop cannot complete a real multi-turn review before emitting its final structured object. Filed as candidate G6.R6, pending the plan-§18 owner revisit of the all-three gate |
| Boundary | PASS — this was the second and final ADR 0020 rerun; no retry, no API-mode fallback, no push, hashes unchanged post-run, raw evidence only in the local gitignored archive. **Both rerun allowances are now consumed: any further live cycle is a beyond-allowance explicit owner decision** (11 remaining fits one more ≤8-call cycle) |

Last verified: 2026-08-24 by Claude (owner-confirmed third cycle; Claude/Codex
legs valid twice consecutively; Grok FAIL-HARD with a mechanical turn-cap
diagnosis; §18 routing engaged — the owner revisits the all-three gate).

## G6.R5 leg-semantic steering — 2026-08-24 (implemented locally; owner-scoped)

| Check | Result |
| --- | --- |
| Definition/task | PASS — `methods.md` now mandates precise kebab-case defect-type categories (generic labels named and forbidden), one finding per defect at its primary location, `critical`/`high` reserved for demonstrated located defects, and exactly-once final structured output; `review-task.md` restates the discipline (progress notes and unfinished-review empty findings are not valid results). Example-package hash re-pinned `fb9e98a3…` → `fd54eae7…` in `test_hash_identity.py` and `ci.yml` (the test file documents exactly this procedure); strict content validation green at the new hash |
| Oracle aliases | PASS — owner-approved acceptance-bar amendment (ADR 0034): `argument-injection` under command-injection; `mutation-of-caller-data` and `caller-input-mutation` under input-mutation; a regression proves the live-observed synonyms now match the matcher and `correctness` still does not; oracle ids/windows untouched |
| Full local CI parity | PASS — core **pytest 446 passed + 4 skips**, optional-extra **458 + 3**, `tests/compatibility` **12**; Ruff lint + format (102 files), strict mypy (98 files), schema check current, `git diff --check` clean; environment restored to core |
| Boundary | PASS — deterministic only; no live/model call, no push; `AGENTS.md`/`CLAUDE.md` untouched. What only a live cycle can prove: model compliance with the steering |

Last verified: 2026-08-24 by Claude (G6.R5 test-first under the owner-selected
full scope; third-cycle preparation authorized with the final go at the gate).

## G6.R4 synthesis-attribution steering — 2026-08-24 (implemented locally)

| Check | Result |
| --- | --- |
| Steering | PASS — the instructions' contradictory rules are gone: one pair convention (`"<invocation-id>:<finding-id>"` for every `sources` entry in agreements *and* merged findings; bare invocation ids only in `inputs`/`asserted_by`/`not_asserted_by`, with at least one source pair per asserting leg); the task document restates the convention and the old "Refer to legs only by invocation id" steering line is removed; the schema `description` fields now carry the convention inside the delivered document (the projection keeps `description` for exactly this purpose) |
| Regressions | PASS — content pins on the instructions, the task builder output, and the delivered synthesis schema descriptions; canonical `synthesis-report-v1.schema.json` regenerated (+5 description lines) with a clean export round-trip; validator and fakes unchanged (already pair-correct) |
| Full local CI parity | PASS — core mode **pytest 444 passed + 4 skips**; optional-extra **456 passed + 3 skips**; `tests/compatibility` **12 passed**; Ruff lint + format (102 files), strict mypy (98 files), schema check current, `git diff --check` clean; environment restored to core. No live call |

Last verified: 2026-08-24 by Claude (G6.R4 test-first; the live-observed
bare-id agreements now have three deterministic steering surfaces against
them; only a live cycle can prove model compliance).

## G6 second live cycle — 2026-08-24 (FAIL exit 1; mechanical tier first live PASS)

| Check | Result |
| --- | --- |
| Pre-run gate | PASS — no-call doctor exit 0 (Claude `2.1.241` signed-in, Codex `0.149.1` signed-in, Grok `1.0.5` verified-by-probe; all ready, zero conflicts/staleness, zero calls); package `fb9e98a3…` and target `25f03027…` matched; six proxy names inherited; subscription policy rechecked (support.claude.com article 11145838, accessed 2026-08-24 — CLI on Pro/Max fully supported, no pause language, decline-API-credit guidance matches the no-fallback stop rule); fresh explicit owner confirmation for ONE rerun; pushes held on owner decision |
| Cycle | **FAIL, exit 1** — `run-20260824-154050-7a98`, 221.1s wall, exactly four calls (three concurrent legs + one synthesis), zero retries. Grok succeeded in 8.677s, Codex in 62.878s, Claude in 122.212s — all with `schema_outcome: valid` on attempt 1 and empty problems; synthesis (98.862s) returned a schema-valid report but failed attribution validation. 16 of 30 calls spent; **14 remain** |
| G6.R1/R2 in vivo | **PASS** — Claude accepted the projected review and synthesis schemas and produced valid structured output on both its invocations (the draft-07 `$schema` rejection is gone); Grok produced a valid structured-output *field* for the projected full review schema (the `structuredOutput: null` failure is gone); Codex stayed good on the projected file. The delivery projection is live-proven on all four invocations |
| G6.R3 in vivo | **PASS** — recursive walk of the real archive: zero mode violations (every directory 0700 and every file 0600, including `events.jsonl`, copied workspace trees, scratch, and vendor-written descendants); manifest reconstructs with zero problems; sanitizer to a temp copy completed with a clean scan; nothing promoted |
| Mechanical tier | **PASS — first live all-PASS**: cond-1 (independent fresh legs, one bundle, targets unmutated), cond-6 (package rehash equals bundle hash), cond-7 (manifest reconstructs), cond-8 (names-only records, raw evidence local) |
| Synthesis failure | Runtime FAIL — `agreements[].sources` carry bare invocation ids (`inv-claude-code`) where the contract requires `invocation_id:finding_id` pairs; `merged_findings[].sources` used the pair form correctly (`inv-claude-code:CR-001`), and disagreements used bare leg ids correctly. The task document's own line "Refer to legs only by invocation id" steers toward the error, and the synthesis instructions never state the pair convention — the deterministic fakes encode it, which is why no test caught it. Filed as G6.R4 |
| Semantic tier | FAIL (first formal live evaluation; recorded in `ensemble.json`) — cond-2: Codex identified 1 seeded defect and Grok 0; cond-3: the union misses `input-mutation`; cond-4: Claude's four high-severity non-matching findings count as invented; cond-5: attribution invalid. Diagnosis: leg `category` labels are unsteered free text — Claude and Codex both *located* the changelog.ts:4 and notes.ts:8 defects but labeled them `correctness`/`mutation-of-caller-data`/`argument-injection` outside the oracle alias lists; Grok emitted its structured object after 8.677s as a progress narration ("Starting review: loading the review skills…") with zero findings — final-output semantics unsteered. Filed as G6.R5 (definition/prompt work per plan §14 routing) |
| Boundary | PASS — exactly the one authorized rerun, no retry, no API fallback, no push, package/target hashes unchanged, raw evidence only in the local gitignored archive. Any further cycle requires a new explicit owner decision (ADR 0020's second-rerun allowance; ≤8 calls fits the 14 remaining) |

Last verified: 2026-08-24 by Claude (owner-confirmed second G6 cycle; mechanical
tier passed live for the first time; synthesis attribution and semantic
steering failures diagnosed from the archive; no further rerun started).

## G6.R rerun-blocker remediation — 2026-08-24 (implemented locally; no rerun)

| Check | Result |
| --- | --- |
| R1 vendor projection | PASS — `vendor_projection` strips `$schema`/`$id`/`title` in schema position only; `vendor_schema_min` (Claude/Grok argv) and the new `vendor_schema_text` (Codex `--output-schema` file, switched from canonical `render()`) deliver one intersection document for both the review and synthesis shapes; canonical checked-in schemas stay byte-identical (`schema check` + export round-trip clean); the property *named* `title` and `required` data lists are proven preserved; projected schemas re-validate the conftest instances and reject unknown fields; the fake Claude now rejects a `$schema` meta-reference with the recorded live stderr, making the observed failure a deterministic regression |
| R2 Grok diagnosis | PASS (deterministic scope) — the delivered construct set is pinned to the probe-proven `{type, properties, items, required, additionalProperties}` plus the semantically required residue `{enum, anyOf, description}`; the vendor's `structuredOutputError` now persists into invocation `problems` on every ladder rung (it was dropped); sanitized fixture `grok/structured-null-error.json` carries a decodable review in `text`, proving the verified-field refusal is policy, not inability; the fake's `structured-null` mode emits that fixture verbatim (no drift); a runner-level regression shows leg failed / no retry / error persisted / exit 1. Unprovable without the rerun: grok-4.6-build producing field output for the projected full schema; Claude 2.1.241 accepting the projected shapes |
| R2 docs verification | PASS — vendor documentation (all accessed 2026-08-24) confirms the projection: Claude Code validates `--json-schema` with **JSON Schema draft-07**, so the canonical Draft 2020-12 `$schema` declaration is the documented rejection cause (code.claude.com/docs/en/agent-sdk/structured-outputs; code.claude.com/docs/en/headless); OpenAI strict mode requires all-required + `additionalProperties:false` (already canonical policy here) and forbids root-level `anyOf` — ours sit on leaf properties (developers.openai.com/api/docs/guides/structured-outputs); xAI accepts 2020-12 and draft-07, documents `anyOf`/nullable, `enum`, and `description` support, never mentions `title`, and its source confirms the observed `structuredOutput: null` / `structuredOutputError` shape (docs.x.ai/developers/model-capabilities/text/structured-outputs; github.com/xai-org/grok-build). Nothing documented contradicts any delivered keyword |
| R3 recursive owner-only | PASS — `events.jsonl` is 0600 from its first byte (umask-proof opener); `copy_workspace` and `write_skills` re-tighten copied trees at write time (the persistent Claude config-home Skill channel lies outside any archive sweep); `RunArchive.secure_tree()` runs at both terminal paths (normal finalize and cancellation finalize) and never mid-run (would race live vendors); permission acceptance extended from selected record files to a full recursive walk including copied workspaces, scratch, the fake Codex `-o` file, and the synthesis leg. All mode assertions are POSIX-marked; win32 branches are tested as behavioral no-ops on Linux; no platform API monkeypatching |
| Independent review | PASS with dispositions — a high-effort subagent review of the full diff returned 10 findings, none refuted. Fixed: Grok vendor-error preservation on the text channel (+regression); fake/fixture unification (the fake emits the checked-in fixture verbatim); one `_SCHEMA_DATA_KEYS` constant shared by both schema traversals with the test importing it instead of mirroring; a shared `assert_owner_only_tree` conftest helper replacing four copied loops. Recorded, not changed: 0600 flattening strips execute bits from copied workspace/Skill files (new RISKS R34; no executable exists in the current target or Skills — verified — and the approved G6.R3 contract text binds until the owner revises it); the mid-run/crash-path window (0700 parents shield; sweep-at-finalize is deliberate); `suppress(OSError)` on chmods (house pattern; the post-run recursive verification is the operational backstop); four-site sweep extraction and finalize-walk perf noted as follow-ups |
| Full local CI parity | PASS — core mode: `uv lock --check`, frozen sync, Ruff lint + format (102 files), strict mypy (98 files), **pytest 441 passed + 4 skips**, schema check + export round-trip clean, wheel/sdist build, CLI help/version, strict Assistant validation, three-harness render-only smoke, pinned hash `fb9e98a3…`, deterministic acceptance both tiers. Optional-extra mode: **pytest 453 passed + 3 skips**, `tests/compatibility` **12 passed**. `git diff --check` clean; the environment was restored to core mode |
| Boundary | PASS — deterministic fakes and documentation lookups only; no owner credential/vendor-home read, no live/model call, no G6 rerun, no push. `AGENTS.md` and `CLAUDE.md` untouched |

Last verified: 2026-08-24 by Claude (G6.R1–R3 test-first remediation, review with
dispositions, docs verification, and two-mode local CI parity; no vendor call).

## G6 initial live cycle — 2026-08-24 (FAIL; no rerun)

| Check | Result |
| --- | --- |
| Pre-run gate | PASS — owner confirmed one attended cycle after no-call doctor reported Claude `2.1.241`, Codex `0.149.1`, and Grok `1.0.5` ready/current with no conflicts or staleness; package `fb9e98a3…` and target `25f03027…` matched; official Claude subscription/CLI guidance was refreshed; normal six proxy names inherited unchanged; no API fallback |
| Cycle | **FAIL, exit 1** — `run-20260824-142351-dfc0`, 67.496s wall time, exactly three concurrent first attempts, zero retries, no synthesis. Claude failed permanently in 1.307s, Codex succeeded in 67.470s, and Grok exited 0 but failed normalization in 15.431s. Three calls spent; **18 of the 30-call ceiling remain** |
| Claude | FAIL before structured output — stderr contains only `--json-schema is not a valid JSON Schema: no schema with key or ref "https://json-schema.org/draft/2020-12/schema"`; stdout empty, usage unavailable. `vendor_schema_min` passed the canonical `$schema`/`$id` metadata that the small G5 probe schema did not carry (G6.R1) |
| Codex | PASS leg — exit 0, schema valid, no parser problems; normalized review identified command injection, off-by-one, and caller-input mutation with actionable rationales, plus one medium stream-contract finding. Target stayed byte-identical; vendor cost unavailable |
| Grok | FAIL structured result — exit 0 using observed model `grok-4.6-build`; `structuredOutput` was null and `structuredOutputError` was `model did not produce structured output`, so the verified field-only parser correctly returned schema missing and did not consume unverified text (G6.R2) |
| Acceptance | Mechanical FAIL only on cond-1 (Claude/Grok leg failures); cond-6 package rehash, cond-7 manifest, and cond-8 names-only/raw-local checks PASS. Semantic tier unevaluated because synthesis did not run. All attempts terminal; selection `decided_by: user`, attendance `attended`, auth `native-subscription`, shared target hash unchanged |
| Archive/privacy | Manifest reconstructs with zero problems; tested sanitizer completed and its scan returned zero problems; raw streams remain only in the local gitignored run archive and nothing was promoted. Root mode is 0700, but `events.jsonl`, copied workspace trees, and adapter-created descendant files retained 0664/0775-style bits under that protected root, violating the explicit recursive owner-mode invariant (G6.R3) |
| Boundary | PASS — one cycle only, no retry/rerun, no API mode, no Assistant/request/fixture mutation, post-run hashes unchanged, no raw/sanitized run evidence tracked or uploaded, and no push. G6 remains open |

Last verified: 2026-08-24 by Codex (initial owner-attended G6 cycle failed
mechanically after three calls; archive/sanitizer reviewed locally; G6.R1–R3
filed; no rerun).

## G5.R pre-G6 remediation — 2026-08-24 (implemented locally)

| Check | Result |
| --- | --- |
| R3 managed-Skills lifetime | PASS — preparation and concurrent execution share one outer `try/finally`; both a later-leg workspace-copy mismatch and an unexpected archive-write exception prove an already-acquired Claude lease is closed |
| R4 bounded probe termination | PASS — POSIX always sends group SIGKILL after the SIGTERM grace; drains are bounded at 10s then 5s with direct-kill and abandoned-pipes fallback. A real parent-exits/descendant-ignores-SIGTERM case completes in under 5s and stops the descendant; a stuck-process double proves no unbounded `communicate()` remains |
| R5 channel currency | PASS — live preflight carries each observed CLI version into every leg and synthesis plan; adapters select only rows verified at that exact version, mixed-currency ladders fall back correctly, and `execute_run` rejects non-live plans or a missing observed version before archive creation. Render-only remains explicitly versionless |
| R6 problem persistence | PASS — invocation records and the regenerated V1 schema carry optional-default `problems`; normal and synthesis paths persist extractor/parser problems; Codex agreement is quiet while a deterministic live-shaped `-o`/JSONL mismatch remains telemetry on a succeeded invocation and survives sanitization |
| H9 named gaps | PASS — exact Claude allowed/disallowed tool sets and forbidden flags, ADR 0028's negative fake branch, Grok snake-case `structured_output`, all adapter channel-error ladders, live-preflight missing/failed-version/symlink/synthesis branches, and real `typer.confirm` EOF→130 are covered |
| Full local CI parity | PASS — core mode: `uv lock --check`, frozen sync, Ruff lint + format (101 files), strict mypy (97 files), **pytest 417 passed + 4 skips**, schema check + stable export, wheel/sdist build, CLI help/version, strict Assistant validation, three-harness render-only smoke, pinned hash `fb9e98a3…`, and deterministic acceptance both tiers. Optional-extra mode: the same checks, **pytest 429 passed + 3 skips**, and `tests/compatibility` **12 passed**. `git diff --check` is clean; the environment was restored to core mode |
| Hosted CI at `30c17b5` | **FAIL, corrected in `e722c15`** — run [32734735405](https://github.com/WSH95/AgentTeam/actions/runs/32734735405) finished 7/9 green: all three optional-ClawTeam jobs and all four Linux/macOS scaffold jobs passed; both Windows scaffold jobs reached Tests and failed the same single test. `test_probe_final_pipe_drain_is_bounded` forced the POSIX path and attempted to monkeypatch absent `os.killpg`; production Windows code was not implicated. The follow-up tests `_drain_terminated_probe_process` directly on every platform; focused 29 passed, full core 417+4, Ruff/format, and mypy/97 were green before the corrective push |
| Hosted CI after `e722c15` | **PASS, 9/9** — run [32735583747](https://github.com/WSH95/AgentTeam/actions/runs/32735583747): six scaffold jobs green (Ubuntu/Windows/macOS × Python 3.11/3.13), including both Windows suites and every lint/format/typecheck/test/build/schema/CLI/render/hash/deterministic-acceptance step; all three OS-specific optional-ClawTeam jobs green. This closes the test-only follow-up and G5.R |
| Boundary | PASS — deterministic local fakes and credential-free hosted CI only; no owner credential/vendor-home read, live vendor/model call, or G6 run. Commits `30c17b5` and `e722c15` were fast-forward pushed to `origin/main` on explicit approvals solely for CI; no other remote mutation occurred. `AGENTS.md` and `CLAUDE.md` are untouched |

Last verified: 2026-08-24 by Codex (G5.R deterministic remediation, two-mode
local CI parity, hosted failure diagnosis, and green 9/9 run 32735583747; no
vendor/model call or credential read).

## G5 independent review — 2026-08-24 (closure verified; two CI regressions fixed)

Review record: `docs/reviews/2026-08-24-g5-review-at-317bb52.md` (ADR 0032);
scope `549804f..317bb52`; owner-host evidence audited by the reviewer only,
`~/.agentteam/vendors/` never read, no vendor model call.

| Check | Result |
| --- | --- |
| Owner-host evidence | PASS — all five captures: 45/45 manifest-recorded artifact SHA-256s recompute, every dir 0700 / file 0600, statuses/durations match every cited number (180640 ms SIGKILL timeout; 44 ms exit-2 reject; 12362 ms exit-0/assessment-failed; 16562 ms; final 10363/20490/17195 ms); final capture exactly one call per harness; 9 call dirs total = Claude 3 / Codex 2 / Grok 4, each traced to ADR 0028/0029/0030 + Q12; 21 of the 30-call ceiling remain |
| Installed CLIs | PASS — `2.1.241 (Claude Code)`, `codex-cli 0.149.1`, `grok 1.0.5 (5115b46bc9)` byte-match the claims and the profile rows; every adapter/probe flag present in `--help` |
| Profiles + doctor | PASS — rows Claude 5v/3o, Codex 7v/2o, Grok 8v/1o/1u, version-bound, `proxy_policy: inherit`, names only; no-call doctor exit 0, all ready, `conflicts_set: []`, six inherited proxy names, provably non-mutating (before/after content hash) |
| Fixture promotion | PASS — zero distinctive fixture literals appear in the raw captures (only shared vendor protocol vocabulary); hygiene caveats H1/H2 recorded in the review |
| CI parity at `317bb52` | **FAIL, now fixed** — R1: `from click import Abort` was an undeclared dependency (typer 0.27.1 vendors Click; external click arrives only via the clawteam extra): core-mode mypy 2 errors, pytest 7 collection errors, every `atm` command dead — all six scaffold legs would have failed; fixed in `739be1a` (also restores prompt Ctrl-C → exit 130, review R2). R8: the deterministic-acceptance step lacked the fake vendor homes the new live preflight requires — fixed in `83f2b3b` |
| Post-fix full CI step list (local) | PASS, 0 failures — core mode: lock check, frozen sync, bare-dot Ruff + format, strict mypy, **pytest 392 passed + 4 skips**, schema check + export round-trip, `uv build`, `atm --help/--version`, `assistant validate --strict-content`, three-harness render-only smoke, pinned hash `fb9e98a3…`, deterministic acceptance both tiers; extra mode: **pytest 404 passed + 3 skips** and `tests/compatibility` 12 passed; `git diff --check` clean; owner `profiles.yaml` hash unchanged across the whole suite |
| Code vs ADR 0026–0030 contracts | PASS with recorded findings — ceilings, evidence semantics (call-2 unresolved-only vs authoritative downgrade), capture lifecycle, redaction (value-absence sweep), atomic locked profile updates, proxy inherit/deny, Claude/Grok argv all verified at cited lines; R3–R6 (lease leak on early-return paths, unbounded kill-escalation branch, stale-verified channel selection, discarded live Codex `-o`/JSONL disagreement) filed as PLAN G5.R pre-G6 tasks |
| Boundary | PASS — nothing pushed at review time; no tracked capture/secret/proxy-value/absolute path in the range; no G6 run; AGENTS.md/CLAUDE.md untouched; review wrote only `docs/reviews/`, steward records, and the two owner-ruled fixes |

Hosted evidence (failure history recorded, not hidden; each fix push
separately owner-approved):

- Run 32722979375 at `cc81b51` (the approved `03635e7..cc81b51` push):
  **7 of 9 green**; both Windows scaffold legs failed at **Typecheck** —
  mypy analyzing under the runner's native `platform=win32` rejects the G5
  POSIX-only branches (`fcntl.flock`, `os.killpg`, `os.fchmod`, `SIGKILL`),
  flips the win32 type-ignores to unused, and marks POSIX statements
  unreachable (~20 analysis errors; no Windows test ran). Fix `0dfbca9`:
  `[tool.mypy] platform = "linux"` so all nine legs type-check the identical
  code view as the green local runs; Windows runtime behavior stays proven
  by pytest on the Windows legs.
- Run 32723369374 at `0dfbca9`: Typecheck green everywhere; the Windows
  legs reached **Tests** — the first real-Windows execution of the G5
  paths — and failed 3 of 384: the sanitized-bundle round trip
  **fail-closed correctly** on `inv-codex.json` (the Codex
  `model_instructions_file` path is embedded via `json.dumps`, so its
  Windows spelling carries doubled backslashes and the raw-path redaction
  needle missed it), and two profile-init tests asserted the POSIX
  login-command form while win32 intentionally prints PowerShell-quoted
  commands. Fix `5d27d2f`: the redaction also replaces each needle's
  JSON-escaped spelling (identical on POSIX) with a Windows-shaped
  regression test that runs on every OS, and the two tests assert the
  platform-appropriate form. Local suite after: 405 passed + 3 skips.
- Run 32724844619 at `5d27d2f`: **all nine checks green** — six scaffold
  legs (ubuntu/windows/macos × 3.11/3.13) and the three-OS `clawteam` job.
  First complete hosted evidence for the G5 work.

Last verified: 2026-08-24 by Claude (Fable 5) independent review session
(read-only evidence audit + credential-free local execution; no vendor model
call; no credential or proxy value read).

## G5 deterministic and owner-host verification — 2026-08-24 (gate closed)

| Check | Result |
| --- | --- |
| Credential-free block | PASS — `ruff check .`; `ruff format --check .` (101 files); strict `mypy src tests` (97 files); `pytest -q --tb=short` (**404 passed, 3 Windows-only skips on Ubuntu**); `python -m agentteam.schema check`; `uv build` produced `agentteam-0.1.0a0` wheel + sdist; `git diff --check` clean |
| Profile initialization | PASS deterministically — refuses overwrite/symlinked homes/unmarked nonempty Claude Skill roots and existing vendor configs; creates profile/vendor/Skill directories 0700 and files 0600 on POSIX; profile writes are atomic; Codex is seeded for file-backed ChatGPT-only login, Grok compatibility discovery is disabled, and POSIX/PowerShell login commands are tested |
| No-call doctor | PASS deterministically — executable/version/home/expected-version/help-flag/conflict checks, sanitized Claude/Codex auth status parsing, Grok probe-only auth, names-only JSON, no profile mutation, and exit 1 vs 2 paths are covered |
| Attended probes | PASS against stdlib-only fakes — all harnesses preflight before any call; TTY required; confirmation immediately precedes each invocation; profile order and ≤2 calls/harness enforced; prompt decline/Ctrl-C → 130; primary/fallback markers, signed-out/missing flags, malformed output, timeout, Codex `-o` vs JSONL disagreement, Grok camel/snake structured fields and JSON-in-`text`, bare-`-p` rejection, explicit Skill references, partial evidence, and two-call exhaustion are covered. Selectable authoritative re-probes additionally cover aliases/duplicates, invalid option combinations, `not-selected`/`already-ready`, all-three/default selection, forced evidence downgrade, partial cancellation, and profile-order execution independent of flag order |
| Persistence and runtime integration | PASS — captures are pending-first then terminal under owner-only `probes/YYYY-MM-DD/<id>/...`, with redacted command, raw streams/output, hashes, and sanitized result; assessed rows update atomically without disturbing owner settings or never-assessed rows; live runs require current version-bound verified native-auth/channels and persistent homes; render-only remains synthetic; Claude config-home Skills hold an exclusive managed lease through invocation, immediately mark an accepted empty root, preserve unmanaged content, and clean managed payload in `finally` |
| Terminal proxy correction | PASS — `profile init` seeds explicit `inherit`; all present standard uppercase/lowercase proxy names pass unchanged through diagnostics, probes, and live environments independently of custom conflict lists; explicit `deny` rejects them; API/base/provider conflicts stay fail-closed; doctor and captures report names only. Regression coverage includes `NO_PROXY`, doctor exit paths, probe capture redaction, and live preflight. |
| Build note | PASS after the sandboxed isolated build could not fetch a missing Hatchling requirement; the explicitly approved `uv build` rerun with dependency-network access succeeded. No package was published. |
| Boundary | PASS — deterministic tests invoke local fakes only; owner-host calls were separately attended and captured. No credential file or proxy value was read/copied, no API-key/CI call or G6 run occurred, and nothing was pushed. The final all-three reassessment passed and closes G5; G6 remains a separate owner-attended gate. |

The runtime/profile boundary is committed as `549804f`; the profile lifecycle
and bounded probe boundary is committed as `695a4a4`. The commit carrying this
verification records the proxy correction, live-found recipe fixes, and
authoritative re-probe extension. None has been pushed in this session.

Owner-host pre-login checkpoint (2026-08-24): PASS for profile schema and
0700/0600 permissions; actual versions Claude 2.1.241, Codex 0.149.1, Grok
1.0.5 (5115b46bc9); sanitized doctor found no binary/home/flag issue and the
expected signed-out/unverified state when proxy names were omitted. This does
**not** validate the live network policy: the owner uses Sing-box intentionally,
so authentication is paused until proxy inheritance is decided and doctor
honors that policy. The Claude login command was cancelled with exit 130; no
probe/model call or credential-file inspection occurred.

Owner-host proxy-correction checkpoint (2026-08-24): PASS. The owner selected
trusted terminal/Sing-box inheritance (ADR 0027); the three existing profile
rows were changed atomically from `deny` to `inherit` with all other fields
asserted unchanged and mode retained as 0600. No-call doctor ran in the normal
environment and reported the six present standard uppercase/lowercase proxy
names (including `NO_PROXY`/`no_proxy`) as inherited, `conflicts_set: []` for
all three harnesses, healthy executable/version/home/flag checks, Claude/Codex
signed out, and Grok unverified. Exit 1 is expected until login/probes; no
credential file, proxy value, vendor model, or probe call was read or invoked.

Owner-host login checkpoint (2026-08-24): PASS. The owner completed the
printed Claude, Codex, and Grok native-login commands sequentially in their
dedicated config homes with the normal proxy environment intact. Sanitized
post-login doctor reports Claude and Codex `signed-in`, Grok `unverified` as
designed until a structured probe, `conflicts_set: []`, and the same six
inherited proxy names for every harness. Exit 1 is readiness-only. AgentTeam
did not inspect credential files; no probe/model call occurred at this
checkpoint.

Owner-host Claude probe checkpoint (2026-08-24): FAIL, safely bounded. Call 1
under capture `probe-20260824T061711Z-971ee2af` ran for 180.64 seconds, emitted
zero-byte stdout/stderr/output, timed out, and was tree-killed (`SIGKILL`). Its
five assessed capability rows are current-version `unverified`; call 2 was
declined during diagnosis and the command exited 130, so Codex/Grok made zero
calls. Sanitized evidence showed `Skill` missing from Claude's `allowedTools`
despite a prompt requiring Skill invocation under `dontAsk`. ADR 0028 fixes
this in probe/live recipes and makes the fake withhold Skill markers unless
permission is present. Post-fix full block: Ruff/format, strict mypy, schemas,
build, **392 passed + 3 skips**. Anthropic `/v1/messages` credential-free GET
through the inherited proxy returned HTTP 405 in 1.13s, ruling out a generally
broken HTTPS route; no response body or proxy/credential value was captured.
The one remaining Claude invocation was reserved until the fix passed the full
credential-free block.

Owner-host attended continuation checkpoint (2026-08-24): PARTIAL PASS; G5
remains open. Capture `probe-20260824T063407Z-53c52838` used Claude's second
and final actual invocation: exit 0 in 174.77s and all five rows verified
(`headless-json`, `structured-output`, `native-auth`,
`append-system-prompt-file`, `skills-config-home`). Codex call 1 exited 0 in
25.79s and verified all seven rows, including authoritative `-o`, schema,
workspace Skill, JSONL, and matching final agent-message telemetry. Grok's
first confirmed invocation exited 2 in 44ms before model dispatch because the
recipe supplied bare `-p` before `--prompt-file`; the captured stderr states
that `--single <PROMPT>` requires a value. The owner declined the offered
fallback, preserving prior results and exit 130.

After removing bare `-p` from probe and live argv, Grok's second/final
confirmed invocation under `probe-20260824T064233Z-139f93bd` exited 0 in
12.36s. It verified native auth, prompt-file headless mode, `--rules`,
structured output, and JSON encoded in `text` (six current rows total). The
response reproduced the random instruction marker but supplied two invented,
wrong-length Skill-like values. A credential-free `grok inspect --json` in the
preserved probe workspace independently listed both intended Skills as enabled,
user-invocable project sources at `.grok/skills/.../SKILL.md` and
`.agents/skills/.../SKILL.md`; discovery therefore worked, but body delivery
did not. The owner declined the next displayed prompt because it would have
been Grok's third confirmed invocation. Final no-call doctor: Claude ready
(5 verified), Codex ready (7), Grok auth `verified-by-probe` with 6 verified / 3
unverified and exactly one readiness problem — no verified Skill channel.

Capture review and fixture promotion (2026-08-24): PASS with sanitization.
All three capture roots are 0700, manifests are 0600, and every recorded
artifact SHA-256 recomputes. The Claude result envelope, Codex command-event +
final-message JSONL shape, and Grok camelCase `structuredOutput` envelope were
manually reconciled into parser fixtures. Identifiers, prompts, random markers,
commands, reasoning, model names, and usage/cost values are synthetic; raw
captures remain outside git. Post-promotion parser tests pass, and the full
credential-free block remains 392 passed + 3 expected skips. ADR 0029 records
the stop decision and the implementation correction. G6 is prohibited.

Owner-approved corrected Grok checkpoint (2026-08-24): PASS. Capture
`probe-20260824T070542Z-60bf6738` call 1 exited 0 in 16.562 seconds. Its
sanitized result assessed nine rows and verified eight required rows:
headless JSON, native auth, prompt file, rules instructions, both independent
workspace Skill paths, structured output, and the field output location.
JSON-in-`text` is the sole unverified alternative. Manifest/artifact files are
0600 and the result is terminal; raw streams remain owner-only and unpromoted.
No-call readiness is now Claude 5, Codex 7, and Grok 8 verified required rows.

Selectable authoritative re-probe checkpoint (2026-08-24): PASS
deterministically. Normal `--probe` still performs zero calls for ready
profiles. `--reprobe-ready` plus repeatable `--harness` can reassess selected
ready profiles in profile order; nonselected rows remain explicit, all three
still preflight, and assessed failure replaces current evidence atomically.
Focused suites passed 37 tests; the final full block passed Ruff/format, strict
mypy, schema reproduction, **404 tests + 3 expected Windows skips**, wheel and
sdist build, and `git diff --check`. At that checkpoint, the owner-attended
all-three capture was the only remaining G5 item; no G6 run had occurred.

Final authoritative all-three checkpoint (2026-08-24): PASS; **G5 closed**.
Capture `probe-20260824T075919Z-1edf636a` used one call per harness and no
fallback calls. Claude Code 2.1.241 passed in 10.363 seconds and verified its
five primary rows; Codex 0.149.1 passed in 20.490 seconds and verified seven
rows, including authoritative `-o` and matching JSONL telemetry; Grok 1.0.5
passed in 17.195 seconds and verified eight required rows, both Skill bodies,
and field structured output. All three manifests are terminal with exit 0;
all recorded artifact hashes recompute (`0` mismatches); every capture
directory is 0700 and file 0600. Sanitized no-call doctor exits 0: Claude
5 verified / 3 observed, Codex 7 / 2, Grok 8 / 1 observed / 1 unverified;
all are ready with no conflicts, missing flags, version mismatch, staleness, or
readiness problem. The non-verified rows are unused fallback inventory and do
not weaken the proven primary paths. No raw capture was tracked, no credential
or proxy value was read, and G6 was not invoked (ADR 0031).

Last verified: 2026-08-24 by Codex (credential-free fakes + attended owner-host G5 probes).

## G4 evidence — 2026-08-23 (gate closed)

| Check | Result |
| --- | --- |
| Core matrix with the G4 suites | PASS — run 32681299831 (https://github.com/WSH95/AgentTeam/actions/runs/32681299831) at `b8d5f9d`: **all six scaffold legs green** (ubuntu/windows/macos × 3.11/3.13) on the first push — full pytest (incl. `tests/acceptance`), the pinned example-package hash identity step (cross-OS identity `fb9e98a3…`), and the deterministic-acceptance step (full fake ensemble via the CLI; run succeeded, both tiers PASS) |
| Optional ClawTeam matrix | PASS — the **`clawteam` job green on all three OSes** (py3.11, `uv sync --frozen --all-groups --extra clawteam`, `tests/compatibility` only): the seam's 12 qualification scenarios incl. hostile-hook containment passed on real ubuntu/windows/macos runners; the core legs never install the extra and their pytest shows the suite skipping cleanly |
| Failure history (evidence, not hidden) | none — first push green on all nine checks |
| Boundaries | PASS — no model call, no vendor login, no credential; ClawTeam exercised in-process against temporary data roots only |

G4 of the approved M1a plan is complete: the fan-out/synthesis state machine
passes locally and in CI incl. solo mode, selection precedence, three Skills
per harness, and example-package hash identity; the optional ClawTeam seam
passes its compatibility suite on three OSes and its qualification report is
committed; the deterministic-acceptance, hash-identity, and ClawTeam jobs are
in CI.

Last verified: 2026-08-23 by Claude (Fable 5) session.

## G4 local verification — 2026-08-23 (pre-push)

Execution followed the owner-approved G4 per-gate execution plan (design
decisions D1–D12; strict red-first TDD throughout). Commits: `e699c91`
feat(run), `48cac73` test(poc), `b8d5f9d` test(substrate).

| Check | Result |
| --- | --- |
| Local block | PASS — `uv lock --check`; frozen sync; bare-dot `ruff check`/`format --check`; `mypy` strict (86 files, incl. the compat seam and both conftests); `pytest` **354 passed + 3 Windows-only skips** with the clawteam extra, **342 passed + 4 skips** in core mode (the compatibility suite skips cleanly); `uv build` (wheel ships `agentteam/synthesis/instructions.md`); `python -m agentteam.schema check` + export round-trip clean; both new CI steps executed locally verbatim (pinned hash assert; full fake ensemble via the CLI → both tiers PASS) |
| G4 gate items (plan §3) | Complete fan-out/synthesis state machine green locally: §12 steps 4–12 (pending archive before side effects; per-leg isolated copies with verified hashes; all renders before any launch; concurrent legs; one same-harness transient-only retry; synthesis over labelled reports only; attribution validated; package re-hash; atomic finalize; stable exit codes 0/1/2/3/130); solo mode (`decided_by: assistant`, `kind: invocation`, synthesis skipped unless explicit); selection precedence; three Skills rendered per harness (injection records assert all `skill:*` parts); example-package hash identity pinned (`fb9e98a3…`); ClawTeam seam passes its 12-scenario local suite (hostile hooks contained) and the qualification report is written (`docs/evidence/clawteam-qualification-2026-08-23.md`); deterministic-acceptance + hash-identity steps and the `clawteam` job added to CI |
| §14 acceptance (deterministic) | Both tiers PASS end-to-end over the committed fixture/oracle via the real CLI; `semantic-miss` and `invent-critical` exit 3 with mechanics green; target mutation and the package-mutation stop rule exit 1; the retried cycle stays at 6 ≤ 8 calls; oracle never copied into a leg workspace or synthesis input |
| Safety asserts (tests) | no `env_values` key in any archived record; events carry no absolute paths; the sanitized bundle scans clean (no value, no source path, no raw stream) and every emitted record re-validates; POSIX archives 0o700/0o600; SIGINT finalizes cancelled records and exits 130; the compatibility suite never touches the owner's real `~/.clawteam` (session-scoped guard) and the seam refuses it outright |
| Deviations (recorded per the G4 plan, D1–D12 + execution) | (1) `RunRequestV1.acceptance.oracle` additive optional field, schema regenerated; (2) request-file paths resolve request-relative, flag paths CWD-relative; (3) target hashing is a raw-bytes tree hasher with `files_written`-derived exclusions — not the V1 package contract; (4) mechanical failures (leg failure, target mutation, package re-hash mismatch) exit 1 — exit 3 is semantic-only, and the run record then stays `succeeded` with the verdict in the ensemble's semantic tier; (5) oracle carries `aliases`; oracle + archive manifest are internal models (schema set stays nine); (6) `instruction_hash` = LF-normalised SHA-256 of `synthesis/instructions.md`; (7) cond-7/cond-8 are structural in-record checks (artifact re-hash; `env_values`-key scan) — full disk reconstruction and value-absence are proven by tests and the sanitizer; (8) single-leg runs skip synthesis unless the request sets `synthesis` explicitly, and solo runs carry no acceptance tiers; (9) `extract_structured` is an internal adapter helper beyond the §9 four-method protocol; (10) fake `target_sha256` is informational, never compared to the computed tree hash; (11) §16 CI reading: acceptance + hash-identity as named core-matrix steps/tests, one new `clawteam` job, `scaffold` job id kept; (12) `ClawTeamCompat._reset_for_tests` escape hatch; no clawteam `filterwarnings` ignores were needed on py3.11; (13) `test_without_render_only_exits_2_until_g4` replaced by the live launch-path test; (14) launcher argv prefix (interpreter/executable paths) now redacted to the launcher token in every command record — a G3 gap the sanitizer's own scan caught; (15) ClawTeam teams are created with an empty `user` (a user name prefixes inbox directories and desynchronises send/receive); (16) mypy gains `explicit_package_bases` for the second conftest |
| Probe items left for G5 (unchanged) | Claude skill-channel #1 + `--append-system-prompt-file`; Codex final-event shape (adapter uses `-o`); Grok structured-output location (parser tolerates both) + auth |

Last verified: 2026-08-23 by Claude (Fable 5) session (fakes only; no vendor
binary executed by tests; ClawTeam exercised in-process against temp roots).

## G3 evidence — 2026-08-23 (gate closed)

| Check | Result |
| --- | --- |
| Scaffold matrix with the G3 suites | PASS — run 32674468887 (https://github.com/WSH95/AgentTeam/actions/runs/32674468887) at `37219bb`: **all six legs green** (ubuntu/windows/macos x 3.11/3.13). The Windows legs executed the Windows-only `.cmd` shim suite against real runners (resolved-shim branch through real `node`, allowlisted branch through `cmd.exe`, refused branch pre-launch) — first real-shim-environment evidence |
| CI smoke | PASS on every leg — `atm assistant validate examples/assistants/code-reviewer --strict-content` and the three-harness `atm run --render-only` against `ci-fake.yaml` |
| Failure history (evidence, not hidden) | run 32672319094: all legs at Lint (fakes' one-line constants; CI lints bare `.`, local block had been scoped to src/tests) → `42c43be`; run 32673977915: ubuntu+macos green, Windows failed one platform-naive test assertion (`Path("/abs/x")` is drive-relative on Windows) → `37219bb`. Each fix pushed on its own owner approval |
| Boundaries | PASS — no model call, no vendor login, no credential; the only vendor-binary execution in CI is `node` running the synthetic test shim |

G3 of the approved M1a plan is complete: adapters pass argv/env/parser tests
against deterministic fakes incl. Skill-channel rendering, selection with
`decided_by`, and the Windows-only `.cmd` shim fake; the tests are in CI; no
model call.

Last verified: 2026-08-23 by Claude (Fable 5) session.

## G3 local verification — 2026-08-23 (pre-push)

Execution followed the owner-approved G3 execution plan (fact sheet verified
against installed CLIs; design agent + my pass; strict red-first TDD).
Commits: `4d6e082` feat(harness), `f5e7cbb` feat(cli) — local only.

| Check | Result |
| --- | --- |
| Local block (3.11 + fresh 3.13 env) | PASS — `uv lock --check`, frozen sync, `ruff check`/`format --check`, `mypy` strict, `pytest` 212 passed + 3 Windows-only skips, `uv build`, `python -m agentteam.schema check`, `atm --help/--version`, and the two CI smoke lines run locally (validate --strict-content; three-harness render-only against `ci-fake.yaml`) |
| G3 gate items (plan §3) | adapters pass argv/env/parser tests against deterministic fakes (golden argv per harness; fakes observe argv/env/stdin; round trips valid); Skill-channel rendering per harness (config-home / .agents / .grok channels, `.agentteam-managed` marker, required-skill failure before launch); selection with `decided_by` incl. hard exit-2 failures; the Windows-only `.cmd` suite is in the tree and runs on the windows CI legs; all tests ride the CI pytest step; **no model call anywhere** |
| Safety asserts (tests) | render-only writes only under the output dir (package/workspace digests unchanged); `invocation.render.json` has no `env_values` (excluded at the model level); doctor output is names-only (value-leak test); conflict env vars fail closed |
| Deviations (recorded per the G3 plan) | `python-script` launcher-policy enum (additive schema regen); `parse() -> ParsedLegV1`; extra `feat(cli)` commit; Codex `-c approval_policy="never"` (no `-a` on `exec` 0.149.0); Codex pre-probe instruction channel = workspace `AGENTS.md`; Grok prompt-file preamble (`--rules` is inline-only); minified inline schema for Claude/Grok, file schema for Codex; conflict env lists as seeded profile data; Claude inline `--append-system-prompt` fallback until the G5 probe |
| Probe items left for G5 (by design) | Claude skill-channel #1 + `--append-system-prompt-file`; Codex final-event shape (adapter uses `-o`); Grok structured-output location (parser tolerates both) + auth |

Last verified: 2026-08-23 by Claude (Fable 5) session (fakes only; no vendor
binary executed by tests).

## G2 evidence — 2026-08-23 (gate closed)

| Check | Result |
| --- | --- |
| Repository | PASS — https://github.com/WSH95/AgentTeam is PUBLIC with license `mit`, default branch `main` (`gh repo view --json visibility,licenseInfo,defaultBranchRef`); created and first pushed on the owner's explicit approvals (DECISIONS 0024) |
| Pushed history | `main @ d9440f8`; first push was `8660e6a` (the secret-scanned SHA, 0 hits); `671c2d9` and `d9440f8` are CI fixes, each pushed on its own owner approval |
| Scaffold smoke matrix | PASS — run 32667607711 (https://github.com/WSH95/AgentTeam/actions/runs/32667607711) at `d9440f8`: **all six legs green** — ubuntu-latest/windows-latest/macos-latest x Python 3.11/3.13 (lock check, frozen sync, interpreter assert, ruff, ruff format, mypy, pytest 91, uv build, schema check, export round-trip `git diff --exit-code -- schemas`, `atm --help/--version`) |
| CI failure history (evidence, not hidden) | run 32667232109 at `8660e6a`: all legs failed at job setup — `astral-sh/setup-uv` has no floating `v10` tag → pinned to the v10.0.1 commit (`671c2d9`); run 32667352498 at `671c2d9`: macOS+Windows green, Ubuntu legs failed at the argument-less `uv python find` diagnostic (resolves `.python-version` 3.11; never auto-installs; image ships no 3.11/3.13) → explicit `uv python install <matrix>` + versioned `find` (`d9440f8`) |
| Boundaries | PASS — CI ran with `contents: read` only; no credential, vendor login, or model call anywhere; no package published |

G2 of the approved M1a plan is complete. Gate evidence per plan §3: frozen
`uv.lock`; package builds; checked-in schemas reproduce (all six legs);
`atm --help`/`--version` pass; pre-first-push checklist passed; public
repository created with MIT and pushed after explicit approval; scaffold
smoke matrix green on three OSes.

Last verified: 2026-08-23 by Claude (Fable 5) session.

## G2 local verification — 2026-08-23 (pre-push)

Execution followed the owner-approved G2 plan (drafted, independently reviewed
twice, critiqued, then approved 2026-08-23 in-session). Commits: `cc0cc5f`
chore(core) scaffold, `be5ce15` feat(domain) records+schemas; both local only.

| Check | Result |
| --- | --- |
| Local verification block (3.11) | PASS — `uv lock --check`; `uv sync --frozen --all-groups`; `ruff check .`; `ruff format --check .`; `mypy` (strict + pydantic plugin) clean; `pytest` 91 passed; `uv build`; `python -m agentteam.schema check` current; `export` round-trip leaves `git diff -- schemas` empty; `atm --help`/`--version` |
| Fresh 3.13 environment | PASS — same block (pytest 91, mypy, ruff, schema check, `atm --version`) on CPython 3.13.14 in a scratch `UV_PROJECT_ENVIRONMENT` |
| Commit 3 standalone | PASS — scratch `git worktree` at `cc0cc5f`: sync, pytest (6), ruff, mypy, `atm --version` |
| Package contents | PASS — wheel: `agentteam/py.typed` present, no `tests/`; sdist: `/src/agentteam`, `/schemas` (+README), `/README.md`, `/LICENSE`, `/pyproject.toml` only (anchored includes); wheel smoke `uv run --isolated --no-project --with <wheel> atm --version` prints `atm 0.1.0a0` |
| Schema parity | PASS — nine files reproduce byte-for-byte and are LF on disk (`git ls-files --eol`: all new tracked files `i/lf`); Draft 2020-12 metaschema valid; minimal instances of all nine records validate via `jsonschema` and unknown fields fail both sides; no pattern uses look-around; vendor-facing files have `$defs` inlined, enum-not-const, all properties required |
| Contract fixes vs approved plan | PASS — severity `critical..info` + finding `category` (§14); `default_harness` + tier/reasoning mappings (§11); target hashes (§12/§14); `undeliverable_required_parts`, observed harness, `refused` launcher branch (§9/§11); overrides keyed by harness id (§2/§8); archive-contract manifest validator (§7); terminal ⇒ `finished_at`; execution `ref`↔`kind`; AwareDatetime everywhere |
| Deviations recorded | `api-test` spelling; `clawteam` extra with direct git ref (owner choice; not PyPI-uploadable, nothing published); AGENTS.md table: `Live PoC` deferred to G4, `Schemas` row added (ADR 0023); finding `category` extends §7's field list; invocation attempt identity = `invocation_id` + `retry.attempt`; §7 "bundle hash" = `effective_definition_hash` (+ Member `package_hash`); vendor-envelope fallback decided by G5 probes |
| Pre-first-push checklist (§16) | LICENSE (MIT) + `docs/provenance.md` (no ATM code copied; dependency + ClawTeam MIT notices) PASS; name checks 2026-08-23: GitHub `WSH95/AgentTeam` 404, PyPI `agentteam` 404, local `atm` absent — re-run immediately before creation; history secret scan: see the line below |
| History secret scan | recorded at the STOP question: `git log -p --all` at the final local HEAD through the key-shaped regex set + private-key headers; result and scanned SHA quoted in the push approval; pushed HEAD must equal that SHA |
| Public-visibility facts (not secrets) | commit author e-mail; `Claude-Session:` trailers; 43 `/home/wsh/...` paths in dated docs; tracked `.project-steward/{state.json,config.toml,backend.json}`; candidate-context wording in history — accepted with ADR 0019 (public at G2) |

Last verified: 2026-08-23 by Claude (Fable 5) session (no model call, no
credential read, no ClawTeam install, no push).

## G1 rename and documentation-hygiene verification — 2026-08-23

| Check | Result |
| --- | --- |
| Move (plan §4 items 1–2) | PASS — the owner moved the repository between sessions; at session start the working directory was `/home/wsh/Documents/AgentTeam`, `/home/wsh/Documents/assistant-team-system-dev` no longer existed, `main @ 025d02a` matched the handoff, the tree was clean, no merge/rebase was in progress, and `command -v atm` found no executable on `PATH` |
| Root files (plan §4 item 4) | PASS — `README.md` states alpha/pre-implementation status and links the steward files including QUESTIONS; `LICENSE` is MIT with `Copyright (c) 2026 ShuhanWang`; `.gitattributes` is `* text=auto eol=lf`; `git ls-files --eol` showed all 56 tracked files `i/lf w/lf`, so no renormalisation occurred; `.gitignore` adds Python/`uv` build and cache paths plus `.agentteam/` and `.env*` outside the steward-managed block |
| Identity amendments (plan §4 item 3) | PASS — only living documents changed (discovery landing page, `product-intent.md` frontmatter, one `legacy-atm-disposition.md` question note, PROJECT.md); panel, critic, evidence, decision, and progress text was not rewritten — `git grep -w ats` still lists the same historical files; `CLAUDE.md` remains the thin `@AGENTS.md` adapter; `AGENTS.md` untouched |
| Hygiene list (plan §4 item 6; review H3, H6, H8–H12, R7, R19) | PASS except the deferred item — PROJECT.md success criteria + volatile pins/scope decision moved out (H3); glossary defines HarnessAdapter, CoordinationSubstrate, Run/direct run, `atm`, legacy ATM, `independence {declared, achieved}` (H10/R10/R16); DECISIONS 0022 adds append-only amendment markers for 0007/0009/0012 (R19); VERIFY M0.1 counts corrected and PROGRESS re-sorted newest-first (H9); RISKS has ID/Owner/Status columns, 33 rows R01–R33 (H12); 10 critic files carry closure notes and the fix-pass file a provenance note, the three FAIL blockers spot-checked (H8); `minimal-poc-plan.md` banner confirmed and its pre-r3 Claude bullet amended (H6); both READMEs link QUESTIONS and `config.toml` names where its pointer lives (H11). **Deferred by design:** the HB-03 register amendment (R7) waits for the owner's QUESTIONS answer |
| Local toolchain baseline (moved here from PROJECT.md) | PASS — read-only `--version` checks, no model call: Claude Code 2.1.241, Codex 0.149.0, Grok Build 1.0.5, OpenClaw 2026.7.1-2, Hermes 0.20.4, `uv` 0.11.26 with uv-managed CPython 3.11.16 and 3.13.14, system `python3` 3.8.10; Ubuntu host without tmux |
| Local Markdown targets | PASS — 53 tracked Markdown files scanned, 30 local links checked, 0 broken |
| Markdown fences | PASS — 60 fence markers across 53 files, 0 unbalanced |
| Secret-pattern scan | PASS — 0 API-key-shaped values and 0 private-key headers across tracked files |
| Scope | PASS — commit 1 touched root files, living docs, and steward state; commit 2 is docs/steward only (`.md` plus `config.toml`); no source, dependency, CI workflow, repository, AGENTS.md, credential, model call, or push |
| Patch hygiene | PASS — `git diff --check` exits 0 for both commits |

Last verified: 2026-08-23 by Claude (Fable 5) session (documentation-only; no
credential values or model prompts used).

## G0 approval record — 2026-08-23

| Check | Result |
| --- | --- |
| Approval artefact | PASS — DECISIONS 0021 names `docs/plans/m1a-direct-harness-poc.md` r3 and commit `0f3e478`; the status line was flipped in the following commit |
| Steward consistency | PASS — PLAN M1a marked approved; QUESTIONS current gate = G1; HANDOFF carries the exact G1 move commands and the fresh-session instruction |
| Scope | PASS — documentation/steward only; no move, code, dependency, repository, or push |
| Patch hygiene | PASS — `git diff --check` exits 0 |

Last verified: 2026-08-23 by Claude (Fable 5) session.

## Current M1a r3 review-resolution verification — 2026-08-23

| Check | Result |
| --- | --- |
| Documentation-only scope | PASS — `docs/plans/m1a-direct-harness-poc.md` (r3), one sentence in `docs/discovery/team-execution-model.md` §4 (v2.3), Project Steward records; no code, rename, dependency, credential, model call, CI, remote change, or push |
| Review claims verified read-only | PASS — `claude --help` (2.1.241): `--safe-mode` disables skills/plugins/hooks/MCP, `--bare` never reads OAuth; `codex exec --help` (0.149.0): `--ignore-rules` = execpolicy `.rules` only; `grok inspect` (1.0.5) in a scratch dir lists `.grok/skills/` and `.agents/skills/` as project skill roots; scratch dir removed |
| r3 edit coverage | PASS — header/§1/§2/§3/§6.1/§7/§9/§11/§12/§14/§15/§16/§17/§18/§19/§21/§22 updated; gate names unchanged; status still *proposed* |
| Decision consistency | PASS — ADR 0020 ↔ QUESTIONS (budget, Claude channel) ↔ PLAN gate lines ↔ RISKS rows ↔ HANDOFF next steps |
| Patch hygiene | PASS — `git diff --check` exits 0 |

Last verified: 2026-08-23 by Claude (Fable 5) session (documentation-only).

## Current M1 plan-merge verification — 2026-08-23

| Check | Result |
| --- | --- |
| Documentation-only scope | PASS — `docs/plans/m1a-direct-harness-poc.md` (r2), a banner on `docs/plans/m1-agentteam-direct-slice.md`, and Project Steward records only; no code, rename, dependency, credential, model call, CI, remote change, or push |
| r2 edit coverage | PASS — every row of the approved edit list is present (header, §1–§4, §6–§19, §21, new §22); gate names G0–G8 unchanged; status still *proposed* |
| Decision consistency | PASS — ADR 0019 ↔ QUESTIONS closures ↔ PLAN M1a lines ↔ HANDOFF next steps; ADRs 0012–0018 not reopened |
| `gh` authentication | PASS — `gh auth status` read-only: account `WSH95`, `repo` scope, SSH; no token value recorded |
| Local Markdown targets | see the session's checks recorded in HANDOFF (links in touched documents resolve; future `schemas/`/`examples/` paths are named, not linked) |
| Patch hygiene | PASS — `git diff --check` exits 0 |

Last verified: 2026-08-23 by Claude (Fable 5) session (documentation-only).

## Current provider-neutral documentation verification — 2026-08-23

| Check | Result |
| --- | --- |
| Documentation-only scope | PASS — architecture, planning, evidence, and Project Steward records only; no product code, dependency, credential operation, model call, CI workflow, remote change, or push |
| Prospective-route neutrality | PASS — 0 candidate model, endpoint, credential-variable, or key-prefix identifiers; the provider-name inventory has exactly 1 occurrence, confined to the factual ClawTeam preset list |
| Generic contract retention | PASS — provider/profile/protocol/model fields remain conceptual; credentials remain environment-name-only; API mode remains separate from native auth with no fallback |
| CI and approval boundary | PASS — M1a hosted CI remains deterministic and credential-free; no API-test route is selected or approved and product implementation remains review-gated |
| Decision/history traceability | PASS — ADR 0017 records the neutrality rule; candidate-context history remains recoverable from Git while unrelated third-party capability evidence is preserved |
| Local Markdown targets | PASS — 50 tracked Markdown files scanned, 12 local links checked, 0 broken |
| Markdown fences | PASS — 60 fence markers across 50 tracked Markdown files, 0 unbalanced files |
| Secret-pattern scan | PASS — 0 common API-key-shaped values and 0 private-key headers |
| Patch hygiene | PASS — `git diff --check` exits 0 |

Validation removes tentative route selection from current tracked documentation;
it does not choose or test a provider/model, change CI, approve M1a, or run a
vendor harness.

Last verified: 2026-08-23 by Codex (documentation-only; no credential values or
model prompts used).

## Current Python/optional-provider rebaseline verification — 2026-08-23

| Check | Result |
| --- | --- |
| Documentation-only scope | PASS — only architecture/plan/Project Steward records changed (`state.json` metadata included); no product source, dependency install, rename, credential operation, model call, remote change, push, or generated product artifact |
| Architecture-decision coverage | PASS — Python `>=3.11`/`uv`/Hatchling; checked-in JSON Schema edge; `atm` then M2 MCP; built-in shell-free direct runner; optional exact-pinned in-process ClawTeam boundary; one data root/namespace-only claim; M1b–M4 obligations |
| ClawTeam boundary consistency | PASS — full revision `01198332ef9270c32c5460b8a178f964fc0df451` and `mcp>=1,<2` appear in the proposed plan/decision records; M1a excludes ClawTeam process backends and confines imports to one compatibility module |
| Guarded instruction change | PASS — the owner-approved `AGENTS.md` diff changes only the title, product description, and primary stack above managed blocks; command/task/session managed blocks are byte-unchanged |
| Historical/current-state separation | PASS — living landing/model/steward documents point to the re-baselined M1a proposal; former TypeScript/CLI-first mechanics remain only as explicitly superseded decisions or labelled M0 evidence |
| Frozen requirement matrix | PASS without re-judgment — `existing-systems-fit-gap.md` is untouched and the `product-intent.md` diff is below the frozen register; the prior 54×11 structural regression remains applicable |
| Local Markdown targets | PASS — 50 Markdown files scanned, 12 local links checked, 0 broken |
| Markdown fences | PASS — 60 fence markers across 50 Markdown files, 0 unbalanced files |
| Secret-pattern scan | PASS — 0 API-key-shaped values and 0 private-key headers in the documentation/steward scope |
| Patch hygiene | PASS — `git diff --check` exits 0 |

Validation establishes a coherent documentation and plan rebaseline. It does
not approve product implementation, install/test ClawTeam, execute a vendor
harness, or provide Windows/macOS/live-runtime evidence.

Last verified: 2026-08-23 by Codex (documentation-only; no credential values or
model prompts used).

## Previous M1a planning verification — 2026-08-23 (superseded stack baseline)

| Check | Result |
| --- | --- |
| M0.1 commit boundary | PASS — `3407ec9` contains the completed 22-file documentation review; the worktree was clean immediately afterward |
| Planning-only scope | PASS — proposed implementation plan plus Project Steward plan/decision/question/risk/handoff/verification state only; no product code, dependency, rename, AGENTS/CLAUDE edit, credential operation, model call, remote change, or push |
| Required decision coverage | PASS — AgentTeam/`atm`; TypeScript/Node; Claude + Codex + Grok direct-first; native subscription profiles; model/effort precedence; full local evidence; deterministic CI/live Ubuntu split; API-test and ClawTeam deferral |
| Current runtime baseline | PASS — local Node 24.16.0, npm 11.13.0, pnpm 11.22.0, Claude Code 2.1.241, Codex 0.149.0, and Grok Build 1.0.5 rechecked without a model call |
| Volatile primary-source check | PASS — Node 22/24 remain LTS; Claude auth/env precedence and Codex model/effort/profile configuration rechecked; Anthropic's Help Center says the separate Agent SDK/`claude -p` credit change is paused |
| Local Markdown targets | PASS — the five project-local plan sources and the PLAN-to-plan link resolve |
| Markdown fences | PASS — 14 fence markers (7 balanced blocks) in the proposed plan |
| Secret-pattern scan | PASS — 0 candidate-route-key-shaped values and 0 private-key headers in the planning/steward scope |
| Patch hygiene | PASS — `git diff --check` exits 0 |

The proposed plan is
`docs/plans/m1a-direct-harness-poc.md`. Validation establishes that it is a
complete, internally linked planning artifact; it does not approve the plan or
provide implementation/live-runtime evidence.

Last verified: 2026-08-23 by Codex (planning-only; no credential values or
model prompts used).

## Current M0.1 verification — 2026-08-22

| Check | Result |
| --- | --- |
| Current local CLI baseline | PASS — Claude Code 2.1.241, Codex 0.149.0, Grok Build 1.0.5, OpenClaw 2026.7.1-2 |
| Sanitized native-auth status | PASS for Claude subscription OAuth and Codex ChatGPT login; Grok active login not tested |
| Fit-gap structural regression | PASS — 54 register IDs map one-to-one to 54 matrix rows; 11 non-empty system cells per row; priorities and cell syntax valid; 0 errors |
| Canonical architecture answer | PASS — exactly 3 copies and 0 byte-level line mismatches across `architecture-options.md`, `minimal-poc-plan.md`, and discovery `README.md` |
| Local Markdown links | PASS — 47 Markdown files scanned, 12 local `.md` links checked, 0 broken. *Correction (2026-08-23, G1 hygiene, review H9; re-counted with `git ls-tree 3407ec9`): 49 tracked Markdown files existed at `3407ec9` — the scan silently excluded `AGENTS.md` and `CLAUDE.md`.* |
| Placeholder inventory | PASS with 3 intentional matches — all mark the still-open implementation-language decision (`PROJECT.md` once; `reuse-vs-build-analysis.md` twice). *Correction (2026-08-23, G1 hygiene, review H9; re-scanned at `3407ec9`): 5 `TBD` markers, not 3 — `AGENTS.md:5` and `evidence/panel/proposal-B-independent-layer.md:42` were missed; all five concerned the then-open implementation-language decision, so the PASS reading stands with the corrected count.* |
| Secret-pattern scan | PASS — 0 candidate-route-key-shaped values and 0 private-key headers |
| Patch hygiene | PASS — `git diff --check` exits 0 |

The fit-gap regression is deliberately **structural**, not a second semantic
review of all 594 system cells. It confirms that documentation edits did not
drop, duplicate, shift, or corrupt a requirement row. The M0 matrix is trusted
except for the targeted AD-07 semantic correction documented in
`docs/discovery/evidence/m0-product-architecture-review-2026-08-22.md` F9.

No model prompt, API-test-provider request, live ClawTeam run, live OpenClaw run, or
Windows/macOS execution was performed. Hosted CI coverage is a future
milestone requirement, not evidence already obtained. No credential value or
authentication file was inspected.

Last verified: 2026-08-22 by Codex (credential-free documentation review).

## Historical M0 note

The W3 critic/fix-pass artifacts remain historical evidence. Current project
state does not rely on the former future-dated owner-read-through claim or the
former claim that no placeholder markers existed.
