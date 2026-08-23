# Progress log

Newest first. One short entry per semantic checkpoint — not per edit.

Ordering corrected 2026-08-23 (G1 documentation hygiene, review H9): entries are sorted newest-first by their stated timestamp; two entries had been appended out of order. Early session-written stamps (through 2026-08-22) are approximate — the "Phase 0 done" entry is stamped before the init commit it reports — so git history is authoritative for event order.

### 2026-08-23T21:30:22Z — cli
M1a G2 closed: public WSH95/AgentTeam created + pushed on explicit approvals (8660e6a scanned clean; CI fixes 671c2d9/d9440f8 each approved); scaffold smoke matrix green on all six legs (run 32667607711); VERIFY G2 evidence + PLAN ticked; next gate G3 starts with its own per-gate execution plan.

### 2026-08-23T21:25:22Z — cli
CI run 32667352498 after the setup-uv pin: macOS+Windows x 3.11/3.13 GREEN (proves UV_PYTHON beats .python-version for sync, the interpreter asserts passed, schemas reproduce cross-OS); both Ubuntu legs failed only at the diagnostic `uv python find` (no version argument -> reads .python-version 3.11; find never auto-installs and the Ubuntu image ships no 3.11/3.13). Fix: explicit `uv python install <matrix>` + `uv python find <matrix>`. DECISIONS 0024 records the repo creation/push approvals.

### 2026-08-23T21:22:24Z — cli
First push done on owner approval (repo https://github.com/WSH95/AgentTeam created public/MIT, main @ 8660e6a). CI run 32667232109 failed on all 6 legs at job setup: astral-sh/setup-uv has no floating v10 tag; fixed by pinning the action to the v10.0.1 commit SHA (20cfd1bf). Fix committed locally; next push awaits its own approval.

### 2026-08-23T21:15:06Z — cli
G2 commit 4 (feat(domain): portable definition, run-record, review/synthesis, and run schemas): nine V1 records under src/agentteam/domain (closed, schema_version+kind, AwareDatetime, archive-contract manifest validator, terminal=>finished_at, execution ref<->kind, no fabricated cost, severity critical..info + category per §14, default_harness + tier/reasoning mappings per §11, target hashes per §12, overrides keyed by harness id); exporter with vendor-facing $defs inlining + const->enum and orphan/missing/decode-aware check; nine schemas + schemas/README.md (model-only invariants); 85 new tests incl. jsonschema metaschema/instance parity, pattern parity (no lookaround), CRLF, orphan/tamper; CI schema steps; AGENTS.md command table updated per DECISIONS 0023. Local block green on 3.11 + 3.13. No push.

### 2026-08-23T21:13:37Z — cli
G2 commit 3 (chore(core): scaffold Python CLI package with uv; per the approved G2 execution plan): pyproject (agentteam 0.1.0a0, Hatchling>=1.27, Typer/Pydantic/PyYAML, clawteam extra @0119833+mcp<2, dev group, strict mypy+pydantic plugin, pytest strict flags, ruff excludes *.md), uv.lock (57 pkgs), .python-version 3.11, atm CLI skeleton (--help/--version, console script tested), py.typed, CI scaffold smoke matrix (3 OS x 3.11/3.13, uv 0.11.26 pinned, UV_PYTHON beats .python-version), docs/provenance.md (no ATM code copied; ClawTeam MIT notice), README status/dev section, .gitattributes CRLF rows for *.bat/*.cmd. Local block green on 3.11 and fresh 3.13. No push, no repo.

### 2026-08-23T15:50:30Z — cli
[auto-checkpoint] G2 scaffold in progress, uncommitted and green: pyproject/uv.lock/.python-version, `atm --help/--version`, nine domain models + checked-in JSON Schemas with reproduction check, 51 tests, ruff/mypy/build clean; PyPI/GitHub name checks 404. Paused at owner request before CI workflow, provenance, secret scan, commits 3-4, and the repo/push approval. No push, no repo, no model call.

### 2026-08-23T15:30:12Z — cli
G1 commit 2 (documentation hygiene, plan §4 item 6; ADR 0022): PROJECT.md success criteria + volatile pins/scope moved out (H3); glossary adds HarnessAdapter, CoordinationSubstrate, Run/direct run, `atm`, legacy ATM, independence {declared, achieved} (H10/R10/R16); DECISIONS 0022 amendment markers for 0007/0009/0012 (R19); VERIFY counts corrected + PROGRESS re-sorted (H9); RISKS ID/Owner/Status columns R01–R33 (H12); closure notes on 10 critic files + fix-pass provenance note (H8); MPP banner/`--safe-mode` amendment (H6); READMEs link QUESTIONS, config.toml pointer (H11). HB-03 register amendment deferred to the owner's answer (R7). G1 closed; next gate G2 (first push = explicit approval moment). No code, no repository, no push.

### 2026-08-23T15:18:28Z — cli
G1 commit 1: directory move verified (owner moved the repo to /home/wsh/Documents/AgentTeam between sessions; same HEAD 025d02a, clean, old path gone, no `atm` on PATH); root README (alpha), LICENSE (MIT, ShuhanWang), .gitattributes (`* text=auto eol=lf`, no renormalisation needed), implementation .gitignore added; identity amendments on the discovery landing page, product-intent title/status, and one legacy-atm-disposition note; dated M0 records untouched. No code, no repository, no push.

### 2026-08-23T14:54:54Z — cli
G0 done: owner approved M1a r3 (DECISIONS 0021 names the plan file and 0f3e478); plan status flipped to approved; PLAN/QUESTIONS/VERIFY/HANDOFF hand off to G1 in a fresh session in /home/wsh/Documents/AgentTeam (owner runs the move between sessions). No code, no move, no repo, no push.

### 2026-08-23T14:18:06Z — cli
M1a r3: resolved the multi-agent review findings on r2 (Claude recipe without --safe-mode, Grok .grok/skills primary, Codex --ignore-rules clarified, pre-first-push checklist + gate-by-gate CI growth, Member execution binding with TEM §4 amended, Windows launcher policy + .cmd fake, computed-only effective hash, required-Skill rule, promotion-only fixtures, waiver semantics, selection algorithm, V1 archive contract, Q5 in M4); owner approved the 30-call ceiling (1 cycle + ≤2 confirmed reruns); ADR 0020 + steward records. No code.

### 2026-08-23T11:25:39Z — cli
Merged the independent M1 proposal into docs/plans/m1a-direct-harness-poc.md revision r2 (single candidate; still proposed): selection precedence/decided_by, three Skills per harness, cross-OS hash identity, RunRecordV1, probe levels, falsification routing, evidence bundle, docs-hygiene list, overlay deferred to M3, public MIT repo at G2 after the G1 rename; cross-check gaps fixed; independent plan superseded; ADR 0019 + QUESTIONS/PLAN/RISKS/VERIFY updated. No code.

### 2026-08-23T10:13:36Z — cli
Independent review of the M0/M0.1 package at 3407ec9 (22 substantive + 14 hygiene findings; three read-only audits reconciled) written to docs/reviews/; independent M1 proposal written to docs/plans/m1-agentteam-direct-slice.md; owner decisions recorded as ADR 0018; QUESTIONS/PLAN/RISKS appended. No code; no edits to discovery documents or the M1a plan.

### 2026-08-23T09:59:52Z — cli
Kept prospective API-test documentation provider-neutral; preserved generic contracts and factual third-party evidence; validation passed

### 2026-08-23T09:19:12Z — codex
[auto-checkpoint] Re-baselined AgentTeam documentation and M1a proposal for Python/uv, language-neutral edges, a built-in direct runner, and an optional in-process ClawTeam provider; validation passed and product implementation remains review-gated.

### 2026-08-23T06:16:37Z — cli
Prepared and validated the owner-requested commit of the proposed M1a planning baseline; implementation remains unapproved

### 2026-08-23T06:04:09Z — cli
Committed M0.1 and drafted the detailed AgentTeam M1a direct-harness PoC plan for multi-agent review; no implementation started

### 2026-08-23T04:30:00Z — M0 discovery complete; STOP for product/architecture review
W3b fixers (8 docs) + re-checks all PASS; owner cross-document alignment (cells, carrier, stale notes), RISKS rows from ATM salvage merged, QUESTIONS numbered Q1–Q10, README answer + STOP, VERIFY updated. Final commit of the nine discovery documents + evidence. Session closed at the review gate.

### 2026-08-23T02:51:49Z — cli
[auto-checkpoint] No material project change after the completed M0.1 documentation handoff; final scope check passed and nothing is staged.

### 2026-08-23T02:48:03Z — [auto-checkpoint] M0.1 documentation review applied and validated: current CLI/auth/Telegram evidence, confirmed constraints, targeted AD-07 correction, and 54×11/link/secret/diff checks PASS; no code, live calls, key, or commit

### 2026-08-23T00:40:00Z — [auto-checkpoint] owner fixes committed (c01b910); W3b fixers relaunched; AGENTS.md update proposed
First fixer run hit a monthly spend limit with no edits; relaunched. Proposed a one-time AGENTS.md addition (discovery pointers + conventions) for user approval.

### 2026-08-22T22:10:00Z — [auto-checkpoint] W3 critics done; owner fixes applied; W3b fixers running
Critic verdicts: 7 PASS-WITH-MAJORS, 2 FAIL (architecture-options, legacy-atm-disposition), completeness FAIL — all traced to two owner-side causes (truncated tiebreak copy; non-existent `task update --metadata` verb) plus per-doc majors. Owner decisions D1–D15 written for the fix pass; fixers + re-checks launched.

### 2026-08-22T20:20:00Z — [auto-checkpoint] all 9 documents drafted; W3 critics running
W2b-1 panel (3 proposals, 2 judges; both endorsed "A's O2 scope with B's two seams"), owner tiebreak, W2b-2 synthesis → architecture-options.md + minimal-poc-plan.md committed (e15b6f2). Decision 0007, risks, owner questions recorded. W3 critics in progress.

### 2026-08-22T18:10:00Z — [auto-checkpoint] W2a-2 committed; architecture panel running
Five documents drafted and committed (700485a); product-intent wording touch (HB-03 "Assistant-level", §1.1 ATM claim narrowed). W2b-1 panel (3 architects + 2 judges) in progress.

### 2026-08-22T16:05:00Z — W2a-1 fit-gap matrix complete; paused by user request
Merged `docs/discovery/existing-systems-fit-gap.md` (54 req × 11 systems; 0 malformed cells; all register rows covered; 54 gaps, 55 evidence gaps). Two layer pairs were re-run after session/Fable limit cuts (W2a-1b/d). Next: W2a-2 drafters (scripts pre-written in scratchpad). Session closed for pause.

### 2026-08-22T15:20:00Z — [auto-checkpoint] W1 committed; fit-gap 2.5/4 sections; re-running the rest
W1 evidence committed (189ea87); register frozen (AR-06). W2a-1 fit-gap: TC+TE and MS+LO complete, HB+AR partial, AD+EV missing after session/Fable limit cuts; re-run on the session model in progress. Pause requested after W2a-1.

### 2026-08-22T02:40:00Z — [auto-checkpoint] W1 cut by session limit; W1b re-running 4 agents
W1 produced 6/10 evidence files (all complete); 8 agents reported "session limit" — 4 of them after writing their file. W1b launched for the 4 missing files. W2a/W2b/W3 workflow scripts pre-written in the scratchpad.

### 2026-08-22T01:42:57Z — project-steward init
Project initialized as a Project Steward managed project.

### 2026-08-21T18:40:00Z — [auto-checkpoint] Phase 0 done, W1 running
Plan approved; steward init committed (78272d8); glossary, requirement register (AD/TC/TE/HB/AR/EV/MS/LO/XC, 45 rows), PoC acceptance criteria and intent prose written; W1 evidence workflow (10 agents) launched; W2a scripts pre-written in scratchpad.
