# Verification

How to check the project is healthy. Agents run these before claiming
"validated" in HANDOFF.md.

| Check | Command | Expected |
| --- | --- | --- |
| Build | `n/a (discovery phase — no code)` | exits 0 |
| Tests | `n/a (discovery phase — no code)` | all pass |
| Lint | `n/a (discovery phase — no code)` | clean |

M0 discovery validation (no code): (1) fit-gap cell lint — 54 register rows × 11 systems, 0 malformed cells, `S`/`C` cells carry `!` outside the ATM column; (2) answer paragraph byte-identical (md5) across architecture-options §5 / minimal-poc-plan §1 / README, §5 component table identical in architecture-options and minimal-poc-plan; (3) W3 critics: 9 per-document + completeness; after the fix pass all re-checks PASS; (4) owner full read-through 2026-08-23; (5) no TODO/TBD placeholders in docs/discovery/*.md.

Last verified: 2026-08-23 (owner; checks 1–5 above).
