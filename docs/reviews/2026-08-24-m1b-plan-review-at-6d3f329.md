---
title: Independent review of the M1b team-foundation plan r3 at commit 6d3f329
status: final review record — findings dated 2026-08-24, valid for the tree at `6d3f329` only
date: 2026-08-24
reviewer: independent review session at the owner's request; the verdict below was delivered verbatim by the owner on 2026-08-24 (reflowed from terminal line-wrapping; wording unchanged; one transit artifact preserved — see §0). The reviewer supplied the reviewed plan text's SHA-256, re-verified by the executing session — `git show 6d3f329:docs/plans/m1b-team-foundation.md | sha256sum` = `8a75da96c9b31371ec3f33f364237e1f5f57dde59e161424a31e620c9c70e3e0`
scope: docs/plans/m1b-team-foundation.md revision r3 as committed in `6d3f329` (`docs(plans): M1b r3 - resolve the r2 review findings`), read against the repository at that SHA; third review round following the r1 and r2 records
decisions_recorded_in: `.project-steward/DECISIONS.md` 0041 (2026-08-24); the later G0 approval remains its own entry
companion: none
---

# Independent review — M1b plan r3 at `6d3f329`

## 0. Verdict and how to read this

This file records the third-round review verdict verbatim as delivered.
The verdict announces "four implementation blockers and three medium
corrections"; in transit, blocker 4's heading line was lost — the text
jumps from item 3's recommendation into a `File:` anchor and blocker 4's
body, then resumes at item 5. The body is preserved below exactly as
delivered, with one bracketed marker at the damage point; §2 states the
reconstructed reading. Resolutions are tracked in the plan's r4 revision
record (§21) and ADR 0041 — this file is a dated record and is not edited
after the fact; follow-ups live in `.project-steward/`.

## 1. Verdict (verbatim)

do not approve r3 yet. Reviewed frozen commit
6d3f329a5e169657edb1e822669340d4013f8fee and plan SHA-256
8a75da96…e0e3e0.

R3 addresses most r2 findings, but four implementation blockers and three
medium corrections remain.

### Approval blockers

1. High — MemberResultV1 lacks a decision-complete output pipeline.
   File: docs/plans/m1b-team-foundation.md:236

   "Additive output-contract dispatch" does not define the interface.
   Today, RenderContext has only a synthesis discriminator, normal
   rendering always selects the review schema, and HarnessAdapter.parse()
   returns a review-shaped result (src/agentteam/harness/rendering.py:79,
   src/agentteam/harness/protocol.py:35). The plan also never gives the
   validated result a canonical archive path; the archive only has
   write_review() (src/agentteam/run/archive.py:135). With raw retention
   disabled, a successful MemberResultV1 may not survive at all.

   Specify an internal output-contract discriminator, use
   StructuredExtractor plus MemberResultV1.model_validate() for team runs
   while leaving direct parse() unchanged, and archive
   legs/inv-<member>/member-result.json with a member-result artifact
   reference.

2. High — deliverable creation conflicts with the existing
   target-mutation contract.
   File: docs/plans/m1b-team-foundation.md:895

   The fixture requires the implementer to write a workspace deliverable,
   but the current mechanical contract fails when target.after !=
   target.before (src/agentteam/run/acceptance.py:121). R3 adjusts the
   successor's baseline but never states whether mutation of the
   producing member's workspace is valid. Reusing current behavior makes
   the committed green fixture fail.

   Define team-mode target semantics explicitly. Recommended: record
   before/after hashes but allow mutation in isolated team workspaces;
   only validated, declared regular files propagate. Keep direct-mode
   immutability unchanged. Test declared writes, undeclared writes,
   missing paths, directories, symlinks, duplicates, and path collisions.

3. High — the abandon sweep closes tasks but not member execution
   bindings.
   File: docs/plans/m1b-team-foundation.md:983

   Every member has a required execution reference, yet workspace
   failure, render-preflight failure, or a cascade may prevent that
   member from ever launching. The new sweep terminalizes only tasks[];
   the terminal record can therefore contain a dangling inv-<member>
   reference or leave a pre-created invocation pending. The fault matrix
   asserts terminal tasks, not terminal/resolvable executions.

   Recommended: make the team member's execution binding nullable until
   launch, with lifecycle validators—success requires every binding;
   failed/cancelled permits null only when the owned task never launched.
   Alternatively introduce an explicit not-launched invocation state.
   Cover step-5, step-7a, cascade, fault-abort, and cancellation paths.
   [transit artifact: blocker 4's heading line was lost here; its body
   follows]
   File: docs/plans/m1b-team-foundation.md:1296

   In this branch the registry rejects substrate: clawteam with exit 2,
   while the ClawTeam job still unconditionally gains success-oriented
   lifecycle tests. Strict-xfailing only the original failing
5. Medium — successful ClawTeam cleanup is described inaccurately.
   File: docs/plans/m1b-team-foundation.md:676

   R3 says cleanup removes the run namespace and only failed cleanup
   leaves unmanaged data. The qualified seam explicitly verifies that
   snapshots/<space> survives successful cleanup
   (tests/compatibility/test_clawteam_qualification.py:102). Either
   specify adapter-owned deletion after copy-out or document successful
   snapshot retention and its cleanup/GC policy.

6. Medium — the fault taxonomy still contradicts its cleanup rule and
   misses the underlying polling operation.
   File: docs/plans/m1b-team-foundation.md:960

   "Any provider operation raises" is defined as a failed fault abort,
   but cleanup raising later preserves exit 0 on a green run. Also, wait
   is implemented over tasks(), while the claimed exhaustive matrix tests
   a wait timeout but not a tasks() exception.

   Exempt cleanup explicitly from fault-abort semantics, give the cleanup
   row its expected status/exit code, and add a separate tasks()-raise
   row alongside the timeout row.

7. Medium — the containment allowlist is not actually frozen.
   File: docs/plans/m1b-team-foundation.md:1201

   The domain enum and provider registry must mention clawteam outside
   the two measured implementation files. Without enumerating exact
   declarative exceptions, the test either rejects required source or
   permits the allowlist to expand around the LOC boundary.

   List exact allowed paths/occurrences and scan case-insensitively;
   outside the two measured modules, allow only the provider
   identifier/schema declaration and registry metadata.

## 2. Disposition

Every finding was independently re-verified against the tree at `6d3f329`
by the executing session before any resolution work (all seven confirmed;
fresh anchors this round: `schema_name_for` selects only
synthesis-vs-review; `write_review` is the only normalized-result writer;
acceptance cond-1 fails on `target.after != target.before`; the
qualification suite asserts `snapshots/<space>` survives successful
cleanup). **Reconstructed blocker 4** (heading lost in transit; body
intact): *under a `failed-routed` G5 disposition, the plan's ClawTeam CI
job still unconditionally collects the new success-oriented provider
lifecycle/conformance tests, so strict-xfailing only the original failing
scenario leaves required CI red — the failed branch needs a
disposition-driven gate for the whole success-oriented suite.*
Resolutions land as plan revision r4; the M5 policy choice (adapter-owned
snapshot deletion after a verified copy-out) is recorded in ADR 0041.
This record is valid for `6d3f329` only.
