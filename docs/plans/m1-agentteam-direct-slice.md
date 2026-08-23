---
title: M1 — AgentTeam direct-path slice (re-baselined PoC A) + the design contract — independent proposal
status: independent proposal for comparison with the owner's M1a plan; NOT approved for implementation until a DECISIONS entry names this file and a commit SHA
date: 2026-08-23
author: Claude (Fable 5) session, as the second half of `docs/reviews/2026-08-23-m0-review-at-3407ec9.md`
depends_on: the review above (findings R1–R22, H1–H14); `docs/discovery/product-intent.md` §3–§4 (register, PoC A acceptance sketch); `docs/discovery/architecture-options.md` §5 (the retained direction); `docs/discovery/minimal-poc-plan.md` §2–§3, §7 (historical PoC A mechanics and FAIL-HARD routing, re-baselined here); `.project-steward/DECISIONS.md` 0012 (the owner's 2026-08-23 decisions this plan builds on)
relation_to_m1a: written without reading `docs/plans/m1a-direct-harness-poc.md`; the owner merges or selects
---

# M1 — AgentTeam direct-path slice (PoC A) + the design contract

## 1. Why this slice first

- The product's core claim — one portable Assistant definition executed *unchanged* on interchangeable harnesses, every invocation recorded, ensemble + synthesis with per-harness attribution — is provable with **no team substrate at all** (brief §17 PoC A; `architecture-options.md` §5 already runs PoC A on the `direct` launcher).
- It builds exactly the components every later milestone needs (definition package, HarnessProfiles, selection policy, HarnessAdapter seam, launcher/wrapper, invocation ledger, Ensemble record) and de-risks the two unknowns that would send the project "back to architecture-options" (the Codex injection channel; bundle identity across channels).
- It is testable deterministically on Ubuntu / Windows / macOS in credential-free CI (Tier 0), which is the only CI the owner can have (M0.1 F5).
- It defers the ClawTeam question (review R2) to M2, where the owner has decided it is settled by measurement, not argument (DECISIONS 0012).

## 2. Decisions this plan builds on (owner, 2026-08-23, DECISIONS 0012) and what it proposes

| Topic | Status |
|---|---|
| Implementation language | **Decided:** Python ≥3.11 managed by `uv`; `src/` layout; stdlib-first (+`pydantic` for closed schemas, `pyyaml`, `typer` or `argparse`). Rationale: the only substrate M2 may couple to in-process (ClawTeam fallback) is Python; Hermes is Python; subprocess/Windows handling is mature; `uv tool install` gives a one-command CLI install. |
| Tiers (former Q8) | **Decided:** Tier 0 (deterministic `noop` adapter + fixtures) is the automated tier and a CI precondition on all three OSes; Tier 1 (live, attended, owner host, budget-capped) is acceptance evidence and the only tier that can PASS a PoC; never CI. |
| Harness set for PoC A | **Decided:** all three — Claude Code + Codex + Grok Build (M0.1 F3 stands). Consequence: three adapters in the slice; Grok's injection / structured-output / auth probes are day-one blockers; the HB-08 "adapter-only diff" is still *measured* when Grok is added last, as an informational signal. Hermes / OpenClaw deferred (unchanged). |
| Tiebreak assumptions (a)–(l) | **Decided:** historical, session-authored panel inputs. This plan restates only what it needs: CLI-only coupling to harnesses (former (a)) and `cost_source: unavailable\|derived` for Codex (former (l)). None of the ClawTeam mechanics apply to M1. |
| ClawTeam (M2) | **Decided:** defer + measure — see §8. |
| First real use | **Decided:** code/dev teams → PoC A → PoC B → PoC C in the brief's order; no early operational slice. |
| Name | **Decided:** AgentTeam, CLI `atm`. *Proposed:* Python package `agentteam`; "legacy ATM" denotes the superseded project; check PyPI/npm name availability before anything is published (web, with owner approval). |
| Documentation language | **Decided:** English only. |
| Synthesis (Q9) | *Proposed, Q9 stays open:* PoC A synthesis on `claude-code` by default (structured output + reported cost); synthesiser bias recorded in the Ensemble record; Codex `cost_source: unavailable` (no USD derivation in M1). |
| Coordination text (Q10) | n/a in M1 (no team); decided in the M2 design. Stays open. |

## 3. Re-baselined PoC A (satisfies "first pass must include Claude Code, Codex, Grok Build")

**Definition under test.** One `code-reviewer` Assistant package with **three** Skills (`code-review`, `security-review`, `test-analysis` — the brief's own §2 composition), `persona.md`, `principles.md`, `harness-policy.yaml` (`preferred: [codex, claude-code, grok]`, `requires_capabilities: [headless, structured_output]`), permission intent `filesystem: read-only, network: deny, shell: allow`. No overlays: user-level choices arrive as run flags.

**Fixture.** `fixture-a/`: a throwaway git repo (small Python package with tests) whose last commit plants three defects (off-by-one; unsafe shell call; behaviour change without a test); target = `target.diff` + checkout at `head`; `target_sha256` recorded. Review schema `{target_sha256, findings[]{id, severity, file, line?, title, rationale}, summary, verdict}`; synthesis schema `{inputs[], agreements[]{title, sources[]}, disagreements[]{title, asserted_by[], not_asserted_by[], severity_conflict?}, merged_findings[]}`.

**Runs.** Run 1 → Codex (`decided_by: assistant`); Run 2 → Claude Code (`--harness claude-code`, `decided_by: user`); Run 3 → Grok Build (`--harness grok`, `decided_by: user`); Run 4 → `--ensemble codex,claude-code,grok`: three legs sharing one `bundle_id`, each in its own workspace and isolated state dir, then one synthesis invocation (structured schema) whose prompt carries the three `review.json` labelled by invocation id.

**Pass — mechanical (architecture gate).**
1. Definition unchanged: content hash of the definition directory identical at every snapshot (before, after each run, after cleanup); `git status --porcelain` empty in the definitions repo.
2. Every leg produced a review of the same target: `review.json` validates for Runs 1–3 and all three Run-4 legs; each `target_sha256` equals the fixture's.
3. Synthesis lists agreements and disagreements with per-harness attribution: output validates; every `sources` / `asserted_by` id resolves to a ledger record naming harness + version; `agreements[]` non-empty and `disagreements[]` non-empty or an explicit recorded "none".
4. Every invocation recorded: exactly **7** closed records (Run 1, Run 2, Run 3, leg a, leg b, leg c, synthesis), each with terminal status, non-null exit code, `decided_by`, teed output, and — decisive — the **same `bundle_hash`** on all six legs (different channels carried one definition).
5. Portability: `atm assistant export` → `import` → `validate` yields the same content hash on all three CI OSes (Tier 0; review R12-ii).

**Reported — semantic (gates "product-useful", not architecture).** Planted-defect recall per harness (proposed threshold ≥ 2/3), synthesis agreement count, `degraded[]` per leg. A semantic miss means the definition or prompt needs work, not the architecture.

**Budget.** `--max-budget-usd` per Claude / Grok invocation; ≤ 3 Tier-1 cycles; every cycle's ledger records are committed under `docs/evidence/` (review H13).

## 4. Work breakdown (each task one commit-sized unit; *done when* in bold)

| # | Task | Done when |
|---|---|---|
| T0 | Rename + steward cleanup not already covered by DECISIONS 0012: PROJECT.md charter (name; move volatile pins/decisions out; add success criteria — H3); README pointer + QUESTIONS link (H11); glossary additions (HarnessAdapter, CoordinationSubstrate, `atm`, "legacy ATM" convention — H10); status/amendment markers on DECISIONS 0007/0009 (R19); VERIFY count fixes (H9); RISKS columns (H12); critic closure note (H8); `minimal-poc-plan.md` archived or rewritten (H6); HB-03 register amendment (R7); AGENTS.md managed block only with a diff + explicit approval | **steward files consistent; AGENTS.md change approved or deferred** |
| T1 | Design spec `docs/design/agentteam-m1-design.md` (3–5 pages): objects (Assistant definition package layout + closed schema; HarnessProfile; policy layers; HarnessInvocation; Ensemble; **TeamRun record where a solo run = one Member with substrate `none`** — R16), HarnessAdapter protocol, CLI verbs, on-disk layout (`~/.agentteam/` + per-run dirs + `ledger/`), JSON Schemas, Tier 0/1 strategy, PoC A acceptance checks (§3), M1 non-goals | **spec self-reviewed; owner approves it before coding** |
| T2 | Scaffold: `pyproject.toml` (uv), `src/agentteam/`, `tests/`, ruff + pytest, GitHub Actions matrix (ubuntu / windows / macos) running Tier 0 only, `atm --version` | **CI green on 3 OSes** |
| T3 | Assistant definition package: loader, closed-schema validator (structural exclusion list mechanical; content heuristics advisory), content hash, credential-free `export` / `import`; the three-Skill `code-reviewer` example; `atm assistant validate\|show\|export\|import` | **validator rejects each exclusion-list key; export→import→validate round-trip yields the same hash on all 3 CI OSes** |
| T4 | HarnessProfiles (`claude-code`, `codex`, `grok`, `noop`) with verification levels + `resolve()` user > assistant > (team slot) > default, `decided_by`; `atm harness list\|check` (`--version` / `--help` smoke → level) | **unit tests for precedence / exclusion / force; `check` updates levels** |
| T5 | HarnessAdapter seam + adapters `noop`, `claude-code`, `codex`, then `grok` last (HB-08 diff recorded): render bundle → channels (+`degraded[]`), argv list with `shell=False`, multi-line parts by file, parse session id / usage / outcome | **Tier 0 round-trip on 3 OSes; same `bundle_hash` from all three real adapters' recipes; Grok added with an adapter-only diff (informational)** |
| T6 | `direct` launcher + wrapper + ledger: per-invocation workspace, isolation knobs (`--safe-mode --no-session-persistence`, `--ephemeral --ignore-user-config`, isolated `CLAUDE_CONFIG_DIR` / `CODEX_HOME` / Grok home), tee, record opened before spawn / closed with exit code; `atm run --assistant X [--harness Y] --target T --task …`, `atm ledger list\|show` | **an aborted invocation still leaves a terminal record (test kills the child)** |
| T7 | Ensemble: `--ensemble a,b,c` → N legs (one `bundle_id`) + synthesis invocation (structured schema) + Ensemble record; `atm ensemble show` | **Tier 0 ensemble produces agreements / disagreements with leg ids** |
| T8 | Tier 1 (attended, owner host): **day-one probes first, each recorded into its HarnessProfile row** — Codex `-c developer_instructions` honoured + positional prompt without a TTY; Claude `--append-system-prompt-file` (evidence: not in `--help`) + `--safe-mode --no-session-persistence` under the wrapper; Grok definition injection (`--rules` / `--system-prompt-override`), `--json-schema`, active auth → then PoC A Runs 1–4 on `fixture-a`; `--max-budget-usd` caps; results as `docs/evidence/m1-poc-a-<date>.md` with committed ledger records | **mechanical criteria PASS for all three harnesses (architecture gate) or a FAIL-HARD report naming the falsified row; semantic tier reported** |
| T9 | Wrap: DECISIONS (seam v1; probe outcomes), VERIFY (exact commands), HANDOFF, PLAN with the M2 preview and the ClawTeam exit criterion drafted | **steward closed; commit proposed** |

Estimated size: ≈ 2–3k LOC including tests and profile data for three adapters (overlays / AR / run layer are out; the third adapter adds back roughly what their removal saved).

**FAIL-HARD routing** (kept from `minimal-poc-plan.md` §7): no Codex injection channel at all (neither `-c developer_instructions` nor `AGENTS.md` in `CODEX_HOME`) → HB-02 falsified → back to architecture-options; definition hash changes → find the writer (injection fix, not architecture); synthesis cannot attribute → record / schema fix; Grok channel or auth fails → report; the owner decides whether Grok stays required (it is the owner's F3 decision to revisit).

## 5. M1 non-goals (explicit)

No ClawTeam; no TeamRun / run layer beyond the one-Member record; no overlays or Proposals (the `effective_hash` field exists and equals the Base hash); no artifact lock or installer (manifest parsed, not resolved); no Surfaces; no Hermes / OpenClaw; no UI; no operational mode (stays after PoC C by the owner's decision).

## 6. Open questions this plan leaves open

Q4 (whether/when to file the bounded ClawTeam PRs — moot until M2 decides ClawTeam's fate); Q6 (Hermes in a later mixed-team expansion); Q9 (synthesis design and Codex cost policy — default proposed in §2); Q10 (Member coordination text — M2); the API-test canary timing; the PyPI/npm name check for `atm` / `agentteam`.

## 7. Verification of this plan's execution

- Tier 0: `uv run pytest` green on ubuntu / windows / macos runners with no credentials; the portability round-trip (T3) and the bundle-hash identity (T5) are CI tests.
- Tier 1: the evidence document + committed ledger records for every cycle; every PASS criterion of §3 quoted with the record ids that satisfy it; FAIL-HARD reports name the falsified register row.
- Steward: DECISIONS entry per decision taken; VERIFY lists the exact commands; HANDOFF rewritten at wrap.

## 8. M2 preview (owner decision: defer + measure; not planned in detail here)

Run layer + **CoordinationSubstrate seam designed from TeamRun needs** (task DAG + wait, inbox, roster projections, archive). Two implementations from day one: (a) a local deterministic substrate (file-based; Tier 0 / CI; candidate product default if it stays small — panel dissent 3 territory); (b) the ClawTeam CLI adapter per `architecture-options.md` §5 (`0.3.0@0119833`, `mcp<2`, never `launch`, never `--task`, `skip_permissions=false`). **A written exit criterion before PoC B starts** — for example: ClawTeam stays only if its adapter plus workarounds are ≤ 1.5× the local substrate's LOC *and* the two-roster and on-exit-noise caveats are accepted in writing; otherwise the local substrate becomes the product path and ClawTeam is dropped (review R2, R13). The Lead is invoked fresh per decision point with a RunStateSummary (review R6) unless PoC B shows a resident Lead is needed. Then PoC C, then EV / AR / LO.
