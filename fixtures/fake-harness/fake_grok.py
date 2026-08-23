#!/usr/bin/env python3
"""Deterministic fake harness for AgentTeam tests. Stdlib only; no model call.

Behaviour is selected by $FAKE_MODE (ok | rate-limit | hang | malformed |
schema-invalid | exit-130). When $FAKE_OBSERVE is set, the fake records its
argv, cwd, selected env names/values, and stdin to that path as JSON.
"""

import json
import os
import sys
import time

REVIEW = json.loads("""
{
  "schema_version": 1,
  "kind": "normalized-review",
  "target_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "findings": [
    {
      "id": "f1",
      "severity": "critical",
      "category": "command-injection",
      "file": "src/run.ts",
      "line": 12,
      "title": "Shell command built from user input",
      "rationale": "The task string reaches exec() unescaped."
    }
  ],
  "summary": "One critical finding.",
  "verdict": "request-changes"
}
""")
BAD_REVIEW = json.loads("""
{
  "schema_version": 1,
  "kind": "normalized-review",
  "target_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "findings": [
    {
      "id": "f1",
      "severity": "critical",
      "category": "command-injection",
      "file": "src/run.ts",
      "line": 12,
      "title": "Shell command built from user input",
      "rationale": "The task string reaches exec() unescaped."
    }
  ],
  "summary": "One critical finding.",
  "verdict": "maybe"
}
""")


KEEP_ENV = ("GROK_HOME", "GROK_MEMORY")
VERSION = "grok 1.0.5 (fake)"


def emit(body, stdin_text):
    import json as _json
    import sys as _sys

    result = {
        "text": "see structured output",
        "stopReason": "end_turn",
        "sessionId": "fake-grok",
        "requestId": "req-1",
        "num_turns": 1,
        "usage": {
            "input_tokens": 70,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
            "output_tokens": 30,
            "reasoning_tokens": 5,
            "total_tokens": 105,
        },
        "modelUsage": {"fake-grok-model": {"inputTokens": 70, "outputTokens": 30, "modelCalls": 1}},
        "structured_output": body,
    }
    _sys.stdout.write(_json.dumps(result))
    _sys.stdout.flush()


def observe(stdin_text):
    path = os.environ.get("FAKE_OBSERVE")
    if not path:
        return
    payload = {
        "argv": sys.argv,
        "cwd": os.getcwd(),
        "env": {k: v for k, v in os.environ.items() if k.startswith("FAKE_") or k in KEEP_ENV},
        "stdin": stdin_text,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)


def read_stdin():
    if sys.stdin is None or sys.stdin.isatty():
        return None
    try:
        return sys.stdin.read()
    except Exception:
        return None


def main():
    if "--version" in sys.argv:
        sys.stdout.write(VERSION + "\n")
        return 0
    stdin_text = read_stdin()
    observe(stdin_text)
    mode = os.environ.get("FAKE_MODE", "ok")
    if mode == "rate-limit":
        sys.stderr.write("429 Too Many Requests\n")
        return 1
    if mode == "hang":
        time.sleep(60)
        return 0
    if mode == "exit-130":
        return 130
    if mode == "malformed":
        sys.stdout.write("not json at all\n")
        return 0
    body = BAD_REVIEW if mode == "schema-invalid" else REVIEW
    emit(body, stdin_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
