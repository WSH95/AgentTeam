---
title: M1c G7 deterministic candidate code review
status: final self-review record for the product tree at bc98735
date: 2026-08-26
reviewer: Codex iterative generation, critique, and synthesis pass; no local harness live calls
scope: changes from 990c162 through bc98735 for the M1c G7 driver, fixtures, audit export, NDJSON permission details, CI hold, tests, and Project Steward state
reviewed_commit: bc98735dd24bf793b4bbdeee7beee11a46a9d1a8
decision: ADR 0049
---

# M1c G7 deterministic candidate code review

## Verdict

The candidate is eligible for the exact eight-job non-Windows hosted gate.
There are no open high- or medium-severity findings in the reviewed scope.
This verdict does not substitute for hosted CI, start a live call, qualify
Windows, authorize a retry, or close G7/G8.

## Reviewed areas

| Area | Review result |
| --- | --- |
| `dev/m1c_g7_live.py` | Exact candidate/hosted binding, call accounting, confirmations, first-failure behavior, NDJSON correlation, permission scope, workspace bytes, source drift, archive truth, process cleanup, and atomic evidence staging reviewed |
| `src/agentteam/interactive/archive.py` | Export exclusions, model-aware redaction, path/session leak scanning, manifest integrity, source/destination containment, atomic failure behavior, and legacy batch coexistence reviewed |
| `src/agentteam/interactive/stream.py` | Backward-compatible permission-awaiting detail projection reviewed; fields are sufficient for attended exact-path decisions and do not alter the provider SPI |
| Fixtures and CI | Exact Assistant/Team hashes, Codex→Claude→Grok role binding, dev-only distribution boundary, and default eight-job Ubuntu/macOS matrix reviewed |
| Tests and evidence rehearsal | Unit correlation/drift/hosted/path gates, controller export/run-store regressions, and seven-bundle deterministic staging rehearsal reviewed |

## Findings closed during critique

| Severity | Finding | Resolution and proof |
| --- | --- | --- |
| High | A numeric GitHub run id alone did not prove that CI belonged to the candidate or contained the intended matrix | The driver reads `headSha/status/conclusion/jobs`, requires the exact candidate SHA and exact eight completed/success Ubuntu/macOS job names, and rejects Windows or any extra/missing job; unit regression included |
| High | Candidate cleanliness was rechecked after the workflow, so external source drift could spend later prompts | The exact HEAD/clean-tree gate now runs immediately before and after every workflow prompt and before each lifecycle command; a regression injects drift and proves only one workflow prompt is attempted |
| High | A write request listing `cwd` before its file could display `.` to the operator even though the exact file was also present | The confirmation is derived from the declared output contract, not provider input order, and names the exact relative file; the provider permission event must retain the same id/kind/path details |
| High | `abort()` waited synchronously for a receipt and could prevent cleanup escalation on a wedged stream | Abort is now send-and-close, followed by bounded wait, process-group TERM, process-group KILL, and a fail-closed cleanup error if reap remains unproved |
| High | A mid-workflow failure could leave the partial ledger at zero attempts | The owner-only ledger is atomically updated before every workflow prompt and records the run id as soon as negotiation establishes it |
| High | Scanner return values and source/export manifest relationships were not all enforced before promotion | Every lifecycle and workflow export scan is checked; source manifests, attested lifecycle manifest digests, export manifests, and final top-level scanning must pass before atomic rename |
| Medium | Evidence dates could form an unintended destination and the scanner missed `file://` local paths | Dates are canonical real UTC dates only; POSIX, drive-letter, UNC, and `file:` path forms now fail closed with regressions |
| Medium | Run listing ignored any non-interactive identity while trying to coexist with legacy batch archives | Only a valid `kind: run-record` legacy directory is skipped. Missing, unsafe, malformed, or unknown `run-*` identities now fail closed |
| Medium | Fixture preferences showed intended role routing, but archive acceptance did not verify the actual launches | The raw workflow archive must bind every Member to provider `direct-acp`, the exact expected harness, Assistant hash, and generation before sanitized promotion; the ledger records the validated bindings |
| Medium | The pinned bridge's 30-second permission expiry was implicit | The exact-path confirmation and operator guide now state the deadline. A timeout is explicitly a first mechanical failure, never a retry case |

## Validation

- Full tree: 774 passed, 4 expected skips in 110.33 seconds.
- Ruff lint clean; 158 files format-clean.
- Strict mypy clean over 152 source files; targeted dev/test mypy also clean.
- All 26 schemas current; lock current; wheel and sdist build clean.
- Packaged Node bridge syntax clean; wheel contains no `dev/` files.
- Assistant hash:
  `d54e35114f56ee67d72a5dcfa560d8d13139be93e07ca27887bd0dd26a4ee29e`.
- Team hash:
  `b1002f133a3d5fd9dd82456f6c375dcca49e4cc26e69fe2ea7015c068d115ada`.
- Deterministic evidence rehearsal: seven scanner-clean bundles and exact
  19/23 ledger with diagnostics 0.
- Post-review deadline correction: 9 driver tests plus targeted Ruff/mypy
  clean; `git diff --check` clean.

## Residual boundaries

- Live lifecycle persistence, recall, isolation, writable tool enforcement,
  and cross-provider workflow behavior remain evidence gates, not deterministic
  claims.
- Every live confirmation remains default-no. Tool approvals must be answered
  within the pinned 30-second provider window.
- The first live failure stops the matrix. The four diagnostic prompts remain
  unspent unless the owner makes a new decision.
- Windows development/testing and live qualification remain paused. The manual
  CI input exists only to restore those legs after a later owner decision.
- Raw archives remain owner-only outside git. Sanitized output still requires
  final human review before the evidence commit and G8 close.

## Disposition

Commit this review and Project Steward checkpoint without changing product
source, then fast-forward push the resulting candidate. Begin attended G7 only
after that exact SHA's eight non-Windows hosted jobs are all green.
