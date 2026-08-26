# Development utilities

`m1c_g7_live.py` is the internal attended driver for the one-time M1c G7
qualification. It is not included in the wheel and is not a public `atm`
command.

Run it only after the exact candidate commit is pushed and all eight default
non-Windows CI jobs are green, with no other coding-agent or interactive run
active:

```bash
uv run --no-sync python dev/m1c_g7_live.py \
  --candidate-head <40-character-commit> \
  --hosted-run <green-workflow-run-id>
```

The driver requires an attended Linux terminal. Claude Code, Codex, and Grok
each retain their own fresh default-no five-prompt lifecycle confirmation. A
fourth default-no confirmation gates the exact Codex → Claude → Grok → Grok
workflow, and every workspace mutation is shown for a one-time attended
decision. The first cancellation or mechanical failure stops the matrix; the
driver never retries or spends a diagnostic prompt.

The pinned ACP bridge expires each pending tool permission after 30 seconds.
Start the workflow only when you can answer every exact-path mutation prompt
inside that window; a timeout is a first mechanical failure, not a retry case.

Raw archives and a partial attempt ledger stay below the owner-only
`$AGENTTEAM_HOME/m1c-g7/` tree. A successful run atomically stages only the
scanner-clean seven audit bundles, three attestations, revalidation record,
and exact 19/23 ledger in `docs/evidence/m1c-live-<UTC-date>/`.
