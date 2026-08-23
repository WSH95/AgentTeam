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

REVIEW = {"schema_version": 1, "kind": "normalized-review", "target_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "findings": [{"id": "f1", "severity": "critical", "category": "command-injection", "file": "src/run.ts", "line": 12, "title": "Shell command built from user input", "rationale": "The task string reaches exec() unescaped."}], "summary": "One critical finding.", "verdict": "request-changes"}
BAD_REVIEW = {"schema_version": 1, "kind": "normalized-review", "target_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "findings": [{"id": "f1", "severity": "critical", "category": "command-injection", "file": "src/run.ts", "line": 12, "title": "Shell command built from user input", "rationale": "The task string reaches exec() unescaped."}], "summary": "One critical finding.", "verdict": "maybe"}


KEEP_ENV = ("CODEX_HOME",)
VERSION = "codex-cli 0.149.0"


def emit(body, stdin_text):
    import json as _json
    import sys as _sys

    out_file = None
    argv = _sys.argv
    if "-o" in argv:
        out_file = argv[argv.index("-o") + 1]
    events = [
        {"type": "thread.started", "thread_id": "fake-thread"},
        {"type": "turn.started"},
        {"type": "item.completed",
         "item": {"type": "agent_message", "text": _json.dumps(body)}},
        {"type": "turn.completed",
         "usage": {"input_tokens": 90, "cached_input_tokens": 10,
                   "output_tokens": 25, "reasoning_output_tokens": 8}},
    ]
    _sys.stdout.write("\n".join(_json.dumps(e) for e in events) + "\n")
    _sys.stdout.flush()
    if out_file:
        with open(out_file, "w", encoding="utf-8") as fh:
            _json.dump(body, fh)


def observe(stdin_text):
    path = os.environ.get("FAKE_OBSERVE")
    if not path:
        return
    payload = {
        "argv": sys.argv,
        "cwd": os.getcwd(),
        "env": {k: v for k, v in os.environ.items()
                if k.startswith("FAKE_") or k in KEEP_ENV},
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
