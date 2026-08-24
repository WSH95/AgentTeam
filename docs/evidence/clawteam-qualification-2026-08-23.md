# ClawTeam compatibility qualification (M1a G4, plan §10)

Date: 2026-08-23. Qualified by the AgentTeam anti-corruption seam
`src/agentteam/compat/clawteam.py` and the suite `tests/compatibility/`,
run locally on Ubuntu and on the three-OS CI job (`clawteam`, py3.11).
This report and the seam are the inputs to the written ClawTeam exit
criterion M1b drafts before PoC B (ADR 0018). A failure here blocks
describing the provider as qualified and blocks M1b — never the direct core.

## Package identity

| Fact | Value |
| --- | --- |
| Package / version | `clawteam` 0.3.0 (alpha, untyped) |
| Pinned revision | `01198332ef9270c32c5460b8a178f964fc0df451` (github.com/HKUDS/ClawTeam) |
| Install | `uv sync --frozen --all-groups --extra clawteam` (never on core CI legs) |
| Achieved isolation level | **`namespace`** — opaque team names under one data root; nothing mechanical |

## Size (inputs to the M1b exit criterion)

| Unit | LOC |
| --- | --- |
| Compatibility module (`src/agentteam/compat/`) | 233 |
| Compatibility tests (`tests/compatibility/`, 3 files) | 281 |
| Qualification scenarios | 12 tests, all passing |

## Containments applied (mapped to §10 items 1–6)

1. **Extra-only import** — a missing package raises `ClawTeamUnavailableError`;
   the module imports clean without the extra and the whole test directory
   skips (`importorskip` in its conftest), proven on the six core CI legs.
2. **One fixed data root per process** — the seam sets `CLAWTEAM_DATA_DIR`
   before the first operation (so `get_data_dir()` never consults the config
   file) and rejects any second root (`DataRootFixedError`). The owner's
   default `~/.clawteam` is refused outright, at any nesting depth.
3. **Opaque names, explicit file primitives** — teams are `atm-<hex8>`;
   `FileTaskStore` and an explicitly constructed `FileTransport` (passed into
   `MailboxManager`) are the only coordination primitives, so the config's
   transport selection (p2p/ZeroMQ, Redis wake-ups) can never activate.
4. **Event bus initialized and cleared before any operation** — the global
   singleton is replaced with a fresh `EventBus` and the config-hook loader
   flag is marked spent, so `get_event_bus()` never loads user hooks.
5. **Never spawn/tmux/wsh, template launcher, keepalive, or CLI chain** —
   only `team.manager`, `store.file`, `team.mailbox`, `transport.file`,
   `team.snapshot`, and `events.{bus,global_bus}` are imported.
6. **Version/revision recorded** — `info()` returns the exact version, the
   pinned revision, and the `namespace` isolation level.

## Global-state hazards found (source-verified at the pin)

| Hazard | Source | Seam mitigation |
| --- | --- | --- |
| `config.json` is **always** `~/.clawteam/config.json`, regardless of data dir | `config.py` `config_path()` | tests run under a patched `HOME`/`USERPROFILE`; the seam refuses `~/.clawteam`-rooted data dirs; `CLAWTEAM_DATA_DIR` keeps `get_data_dir()` away from the config |
| First `get_event_bus()` loads shell/python hooks from that config, once per process | `events/global_bus.py` | bus replaced + loader marked spent before any operation (containment 4) |
| `get_data_dir()` falls back to `load_config().data_dir` when the env var is unset | `team/models.py` | the seam always sets the env var |
| `MailboxManager`'s default transport comes from env/config (can pick p2p) | `team/mailbox.py` `_default_transport` | explicit `FileTransport` always passed |
| Task events emitted asynchronously (2-thread pool) outside the store lock | `store/file.py` update path | cleared bus makes them no-ops; the hostile-hook test settles briefly and asserts state, not timing |
| `AgentIdentity.from_env` reads `CLAWTEAM_*` from the caller's environment | `identity.py` | seam passes explicit names/callers; tests clear `CLAWTEAM_*`/`CLAWTEAM_TRANSPORT` |
| A `user` on `create_team` prefixes inbox directories (`{user}_{agent}`), desynchronising send/receive | `team/manager.py` / transport paths | the seam creates teams with an empty user (recorded quirk) |
| `cleanup` deletes team state but never stops processes; workspace cleanup is best-effort | `team/manager.py` | the seam never spawns, so nothing can be orphaned |
| Unknown-alive lock semantics: a caller with no spawn-registry entry counts as alive | `store/file.py` | exercised as-is (lock scenario); callers are explicit |

## Results

| Scenario (§10) | Result |
| --- | --- |
| Team/member lifecycle, cleanup scoped to the data root | PASS |
| Task dependency auto-unblock (`blocked` → `pending` on blocker completion) | PASS |
| Task lock semantics (second caller refused; completion clears) | PASS |
| Mailbox send/receive (claim consumes; second receive empty) | PASS |
| Snapshot create/read (bundle keys config/tasks/events/sessions/costs/inboxes), survives cleanup, restores | PASS |
| Two namespaces, no API-level task/message crossover | PASS |
| **Hostile hook fixture: no user-configured hook callback executes** | PASS (bus replaced, 0 subscribers, loader spent; sentinel absent) |
| Owner's real `~/.clawteam` untouched by the whole suite | PASS (session-scoped guard) |
| Clean skip without the extra | PASS (core legs + local core-mode run) |

No warnings surfaced from the pinned package under `filterwarnings = ["error"]`
on Python 3.11; no `filterwarnings` ignores were added.

## Per-OS outcome

| OS | Python | Result | Evidence |
| --- | --- | --- | --- |
| Ubuntu (local) | 3.11 | 12 passed | local run 2026-08-23 |
| ubuntu-latest (CI) | 3.11 | pending first push | CI run id recorded at G4 close |
| windows-latest (CI) | 3.11 | pending first push | CI run id recorded at G4 close |
| macos-latest (CI) | 3.11 | pending first push | CI run id recorded at G4 close |

## Feed-forward to the M1b exit criterion (ADR 0018)

The seam is ~233 LOC against ~281 LOC of tests for namespace-level isolation
only. The M0 caveats stand: two rosters (ClawTeam's own member list vs any
layer view), no parent link for nested teams, cleanup does not stop
processes, and every containment above is caller-written code, not
configuration. M1b's written exit criterion should weigh this seam + its
workarounds against the planned local deterministic provider.
