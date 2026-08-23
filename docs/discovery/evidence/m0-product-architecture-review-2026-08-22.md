---
id: ev:m0-product-architecture-review-2026-08-22
topic: M0 product/architecture review, current CLI verification, and owner-supplied constraints
systems: [Assistant Team System, Claude Code, Codex CLI, Grok Build, OpenClaw, Telegram, ATM]
date: 2026-08-22
confidence: high for local CLI/help results; mixed where explicitly marked web-only or untested
status: current
---

# M0 product/architecture review — verification addendum

## 1. Scope and method

This addendum records the product/architecture review performed after the M0
discovery package was delivered. It supplements the dated M0 evidence rather
than rewriting the panel and critic records.

Methods were deliberately credential-free and non-mutating:

- local `--version`, headless-command `--help`, and authentication-status
  commands for the installed harnesses;
- official vendor documentation for authentication, headless execution,
  custom providers, Telegram platform changes, and GitHub-hosted runners;
- read-only searches of the installed OpenClaw 2026.7.1-2 documentation and
  distribution;
- repository consistency checks (`git diff --check`, placeholder scan, and a
  secret-pattern filename/value scan).

No model prompt or API-test-provider request was sent. No credential value,
account identifier, or authentication file was read into this report.

## 2. Findings

### F1. Installed harness baseline changed after M0

- `claude --version` -> Claude Code **2.1.241**.
- `codex --version` -> Codex CLI **0.149.0**.
- `grok --version` -> Grok Build **1.0.5** (`5115b46bc9`).
- `openclaw --version` -> OpenClaw **2026.7.1-2** (`0790d9f`).

The M0 evidence remains a valid dated snapshot of the versions it inspected;
current architecture and capability documents must use the values above and
cite this addendum for the refresh.

Level: verified locally. Requirements: HB-01, HB-08, XC-02.

### F2. Native subscription authentication is present for Codex and Claude

- `codex login status` reported `Logged in using ChatGPT`.
- Sanitized `claude auth status --json` fields reported
  `loggedIn=true`, `authMethod=claude.ai`, `subscriptionType=max`, and
  `apiProvider=firstParty`.
- `grok login --help` confirms OAuth and device-code flows, but Grok exposes no
  equivalent non-network status command used in this review. Active Grok
  authentication therefore remains unverified.

The confirmed product boundary is: native and unattended live ATS runs use
each vendor CLI's subscription OAuth on an owner-operated persistent host.
ATS does not offer vendor login to other users, copy native credential stores,
or put subscription credentials on GitHub-hosted runners.

Level: verified locally for Codex/Claude; verified capability, unverified
active state for Grok. Requirements: AR-04, HB-07, XC-01.

### F3. Current headless and isolation flags support a three-harness first pass

- Codex 0.149.0: `codex exec`, `--ephemeral`, `--ignore-user-config`,
  `--ignore-rules`, `--output-schema`, and `--json` are present.
- Claude Code 2.1.241: `-p/--print`, `--safe-mode`,
  `--no-session-persistence`, `--json-schema`, and structured output are
  present. `--bare` explicitly disables OAuth/keychain reads and is therefore
  not an isolation mode for subscription-backed native runs.
- Grok Build 1.0.5: `-p/--single`, `--json-schema`, `--max-turns`,
  `--no-subagents`, `--system-prompt-override`, `--verbatim`,
  `--permission-mode`, and `--sandbox` are present.

The confirmed first-pass harness set is Claude Code + Codex + Grok Build.
This is a scope constraint for later PoC planning, not a completed PoC design.

Level: verified locally. Requirements: HB-01, HB-02, HB-08, TE-02.

### F4. Native subscription mode and API-test mode are separate

All three CLIs can be pointed at a non-default provider, but their protocol
skins differ:

- Codex custom providers use a Responses-compatible `base_url` and an
  environment-key reference.
- Claude Code gateways use the Anthropic Messages interface.
- Grok supports custom model/provider configuration for OpenAI-compatible
  endpoints.

No API-test provider, endpoint, or model is selected. A future provider profile
must keep provider id, base URL, protocol, model, and credential
environment-variable name as data. It must never contain the key value. A
test-gateway API key is not a fallback for a failed native subscription-OAuth
run.

Any future API-test canary is deferred until the owner separately selects and
approves a route. No result, cost, availability, or native-harness equivalence
is claimed.

Safe key handling for a later approved canary: do not paste the key into chat,
prompts, repository files, command arguments, or logs. Set it locally through a
process environment/secret store under an owner-selected environment-variable
name. ATS receives only that name, checks presence without echoing the value,
and redacts it from invocation records. Rotate the key if it is ever exposed.
No key is needed now.

Sources (accessed 2026-08-22):

- https://learn.chatgpt.com/docs/config-file/config-reference
- https://code.claude.com/docs/en/llm-gateway
- https://docs.x.ai/build/overview

Level: observed from official docs; live compatibility unverified.
Requirements: HB-01, HB-02, AR-04, XC-02.

### F5. Cross-platform verification is split into CI plumbing and live behavior

The owner cannot provide physical Windows or macOS hosts. GitHub-hosted
Windows/macOS runners will therefore test deterministic process plumbing,
paths, quoting, exit handling, records, archives, and the relevant ClawTeam
subprocess path. Hosted CI receives no live model or subscription credentials.

Passing those jobs may support an OS-plumbing claim; it cannot support a live
harness-authentication or model-behavior claim. Live subscription-backed
acceptance remains on the persistent Ubuntu host unless an authenticated host
is later supplied.

Source (accessed 2026-08-22):
https://docs.github.com/en/actions/reference/runners/github-hosted-runners

Level: owner constraint + observed official runner capability. Requirements:
TE-08, XC-02.

### F6. Telegram added capabilities that M0 did not fully inventory

Telegram's 2026 platform now includes:

- managed bots created through a user-authorized MTProto flow and controlled
  by an approved manager bot;
- guest bots that can be mentioned in chats where they are not members;
- opt-in bot-to-bot communication;
- Communities that group channels, groups, and bots at the client/product
  layer; and
- ephemeral commands/messages visible only to the bot and one group member.

Sources (accessed 2026-08-22):

- https://core.telegram.org/api/bots/managed-bots
- https://core.telegram.org/api/bots/guest-mode
- https://telegram.org/blog/ai-bot-revolution-11-new-features
- https://telegram.org/blog/communities-editor-invisible-messages
- https://core.telegram.org/bots/api

Read-only searches of the installed OpenClaw 2026.7.1-2 docs and distribution
found no guest-chat, managed-bot creation, or Telegram ephemeral-message
handling symbols. Current OpenClaw docs do cover mature DMs/groups, topics,
multi-account routing, streaming, and rich-message delivery. Consequently each
new Telegram feature is recorded as **platform available / OpenClaw support
unverified**, not as an OpenClaw capability. None changes MS-04: surface
topology still must not define Team semantics.

Level: web for Telegram; local negative search + installed docs for OpenClaw.
Requirements: MS-02, MS-04, XC-02.

### F7. ATM reuse is authorized for this project

The owner states that ATM is their own locally developed project and explicitly
authorizes ATS to copy or adapt its code and documentation. The absence of a
standalone ATM LICENSE file is therefore not an internal reuse blocker.

Reuse must still record the ATM source path/commit and whether material was
copied or adapted. Third-party code and dependencies embedded in ATM retain
their own license and notice obligations. This permission does not itself
choose a public ATS license.

Level: owner-supplied. Requirements: XC-01, XC-03, AR-06.

### F8. Current-state verification claims need correction

- `.project-steward/VERIFY.md` claimed a full owner read-through dated
  2026-08-23; this review did not establish that event and current-state docs
  must not rely on it.
- The same file claimed there were no placeholder markers, while current
  discovery prose still explicitly marks the implementation language as
  undecided.
- `git diff --check` passed.
- No tracked file contains a candidate-route-key-shaped value or private-key
  header.

Historical progress, panel, and critic artifacts remain unchanged; current
indexes and verification state carry the correction.

Level: verified locally. Requirements: XC-04.

### F9. Targeted fit-gap review disposition

The existing 54 x 11 matrix structural lint is trusted for the snapshot it
tested. The semantic review does not reopen every cell. It corrects the one
identified method violation where AD-07 explicitly ignored its own
hidden-if-desired clause, updates affected derived text, and records why the
new Telegram features do not change current MS cells. The original structural
lint is then rerun as regression testing.

Level: document review. Requirements: AD-07, MS-02, MS-04, XC-04.

### F10. Advisory PoC controls and production enforcement are different claims

The owner accepts advisory controls in a proof of concept when every bypass is
visible in the run record and audit output. A production capability may be
claimed only when the relevant boundary is mechanically enforced. A hidden
Member is hidden from the user-facing roster/UI; that projection is not an
authorization, confidentiality, or isolation boundary.

Level: owner-supplied. Requirements: AD-07, TC-03, TC-04, TC-05, TE-05,
XC-04.

## 3. Limitations and deferred verification

- No API-test-provider request; no assertion about any prospective provider or
  model's availability, behavior, price, or compatibility.
- No live Codex, Claude, Grok, OpenClaw, or ClawTeam model invocation.
- No active Grok-authentication proof.
- No Windows/macOS execution; only the future CI approach is fixed.
- No PoC implementation plan is approved by this addendum.
