# AgentTeam V1 JSON Schemas

Twelve closed JSON Schema (draft 2020-12) documents, generated deterministically
from the Pydantic models in `src/agentteam/domain/` and verified by
`python -m agentteam.schema check` (regenerate with `... export`). Every
record is a closed object (`additionalProperties: false`) carrying
`schema_version: 1` and a fixed `kind`. External consumers can read and
validate instances with any JSON Schema validator — no pattern uses
look-around, so RE2-based validators work too.

`normalized-review-v1.schema.json`, `synthesis-report-v1.schema.json`, and
`member-result-v1.schema.json` are
**vendor-facing**: they are passed directly to harness structured-output flags,
so they are post-processed into the vendors' dialect intersection (every
property required, `$defs`/`$ref` inlined, `enum` instead of `const`, no
defaults/patterns/formats, nullable-required optionals).

## Invariants the schemas cannot express (enforced by the models)

A JSON Schema validator alone does not check these; AgentTeam's models do:

- `bundle-manifest`: `files[].path` values are unique, NFC-normalised, sorted
  by code point, and free of case-fold collisions (V1 archive contract).
- `run-record` / `harness-invocation`: a terminal `status` requires
  `timing.finished_at`.
- `run-record`: the direct variant's `member.execution.ref` must match
  `member.execution.kind` (`inv-…` for invocations, `ens-…` for ensembles).
  In the team variant, namespace and achieved-independence presence agree;
  a snapshot requires a namespace; success requires namespace, achieved
  independence, snapshot, and an invocation binding for every member; every
  present binding is an invocation and execution refs are unique.
- `harness-invocation`: `usage.cost_amount` requires `usage.cost_source:
  vendor` and a `cost_currency` (cost is never fabricated).
- `harness-profile-set`: at most one profile per harness; `default_harness`
  must name a listed profile; capability names and hint mappings are unique.
- `run-request`: `harnesses` and per-harness overrides are unique; limits may
  lower but never raise the plan's caps (15-minute attempt, single retry).
- `assistant-definition`: artifact refs are unique; a harness cannot be both
  forbidden and preferred/allowed.
- `team-template`: roster names, relationship targets, preference keys,
  independence pairs, handoff vocabulary, task ids, owners, blockers, and the
  acyclic one-task-per-member skeleton agree; placeholders are limited to
  `{goal}`; mechanical independence and non-empty reserved fields fail closed.
- `team-run-request`: `model` or `effort` requires a same-object `harness`;
  override keys are checked against the resolved template roster.
- `member-result`: `summary` is non-empty (kept model-level so the delivered
  vendor schema stays within the live-proven structured-output keyword set).
- All timestamps are timezone-aware.
