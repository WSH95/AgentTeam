#!/usr/bin/env python3
"""Deterministic fake harness for AgentTeam tests. Stdlib only; no model call.

Behaviour is selected by $FAKE_MODE (ok | rate-limit | rate-limit-once | hang |
malformed | schema-invalid | exit-130 | mutate-target | event-mismatch |
invent-critical | semantic-miss); $FAKE_MODE_CODEX overrides it for this vendor only. A
synthesis-shaped invocation (the `--output-schema` file names
`synthesis-report`) makes the fake parse the labelled-reports document and
emit a synthesis report derived from the actual labels. When $FAKE_OBSERVE is
set, the fake records its argv, cwd, selected env names/values, and stdin to
that path as JSON.
"""

import hashlib
import json
import os
import re
import sys
import time

from probe_support import HELP, emit_probe, is_probe, probe_mode

REVIEW = json.loads("""
{
  "schema_version": 1,
  "kind": "normalized-review",
  "target_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "findings": [
    {
      "id": "f1",
      "severity": "high",
      "category": "command-injection",
      "file": "src/publish.ts",
      "line": 5,
      "title": "Shell command interpolates caller input",
      "rationale": "Both tag and remote flow into the execSync command string."
    },
    {
      "id": "f2",
      "severity": "medium",
      "category": "input-mutation",
      "file": "src/notes.ts",
      "line": 8,
      "title": "Function mutates its input object",
      "rationale": "withFooter pushes into the caller's highlights array."
    }
  ],
  "summary": "Command injection plus caller-input mutation.",
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
      "severity": "high",
      "category": "command-injection",
      "file": "src/publish.ts",
      "line": 5,
      "title": "Shell command interpolates caller input",
      "rationale": "Both tag and remote flow into the execSync command string."
    }
  ],
  "summary": "One high finding.",
  "verdict": "maybe"
}
""")
INVENTED_FINDING = json.loads("""
{
  "id": "f9",
  "severity": "critical",
  "category": "phantom-race",
  "file": "src/extra.ts",
  "line": 1,
  "title": "Invented catastrophe",
  "rationale": "This finding matches nothing in any oracle."
}
""")
MEMBER_RESULT = {
    "schema_version": 1,
    "kind": "member-result",
    "summary": "Completed the assigned team task.",
    "deliverables": [],
    "risks": [],
}

KEEP_ENV = ("CODEX_HOME",)
CONFIG_HOME_VAR = "CODEX_HOME"
MODE_VAR = "FAKE_MODE_CODEX"
VERSION = "codex-cli 0.149.0"

HEADER = re.compile(r"^### leg (\S+) harness (\S+)$")


def emit(body, stdin_text, event_body=None):
    out_file = None
    argv = sys.argv
    if "-o" in argv:
        out_file = argv[argv.index("-o") + 1]
    events = [
        {"type": "thread.started", "thread_id": "fake-thread"},
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {
                "type": "agent_message",
                "text": json.dumps(event_body if event_body is not None else body),
            },
        },
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 90,
                "cached_input_tokens": 10,
                "output_tokens": 25,
                "reasoning_output_tokens": 8,
            },
        },
    ]
    sys.stdout.write("\n".join(json.dumps(e) for e in events) + "\n")
    sys.stdout.flush()
    if out_file:
        with open(out_file, "w", encoding="utf-8") as fh:
            json.dump(body, fh)


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


def resolve_mode():
    return os.environ.get(MODE_VAR) or os.environ.get("FAKE_MODE", "ok")


def rate_limited_once():
    home = os.environ.get(CONFIG_HOME_VAR)
    if not home:
        return True
    os.makedirs(home, exist_ok=True)
    scope = hashlib.sha256(os.getcwd().encode("utf-8")).hexdigest()[:16]
    sentinel = os.path.join(home, ".fake-rate-limited-" + scope)
    if os.path.exists(sentinel):
        return False
    with open(sentinel, "w", encoding="utf-8") as fh:
        fh.write("rate limited once\n")
    return True


def synthesis_requested():
    argv = sys.argv
    if "--output-schema" not in argv:
        return False
    schema_path = argv[argv.index("--output-schema") + 1]
    try:
        with open(schema_path, encoding="utf-8") as fh:
            return "synthesis-report" in fh.read()
    except OSError:
        return False


def member_result_requested():
    argv = sys.argv
    if "--output-schema" not in argv:
        return False
    schema_path = argv[argv.index("--output-schema") + 1]
    try:
        with open(schema_path, encoding="utf-8") as fh:
            return "member-result" in fh.read()
    except OSError:
        return False


def member_result_body(mode):
    body = json.loads(json.dumps(MEMBER_RESULT))
    if "inv-implementer" in os.getcwd().split(os.sep):
        if mode == "team-missing":
            body["deliverables"] = ["missing.txt"]
        elif mode == "team-directory":
            os.mkdir("declared-dir")
            body["deliverables"] = ["declared-dir"]
        elif mode == "team-symlink":
            with open("real.txt", "w", encoding="utf-8") as fh:
                fh.write("real\n")
            os.symlink("real.txt", "declared-link")
            body["deliverables"] = ["declared-link"]
        elif mode == "team-parent-symlink":
            os.mkdir("real-dir")
            with open("real-dir/value.txt", "w", encoding="utf-8") as fh:
                fh.write("real\n")
            os.symlink("real-dir", "linked-dir")
            body["deliverables"] = ["linked-dir/value.txt"]
        elif mode == "team-duplicate":
            with open("duplicate.txt", "w", encoding="utf-8") as fh:
                fh.write("duplicate\n")
            body["deliverables"] = ["duplicate.txt", "duplicate.txt"]
        elif mode == "team-case-collision":
            for name in ("Foo.txt", "foo.txt"):
                with open(name, "w", encoding="utf-8") as fh:
                    fh.write(name + "\n")
            body["deliverables"] = ["Foo.txt", "foo.txt"]
        elif mode == "team-nonnfc":
            name = "cafe\u0301.txt"
            with open(name, "w", encoding="utf-8") as fh:
                fh.write("decomposed\n")
            body["deliverables"] = [name]
        elif mode == "team-handoff-reserved":
            os.mkdir("handoff")
            with open("handoff/value.txt", "w", encoding="utf-8") as fh:
                fh.write("reserved\n")
            body["deliverables"] = ["handoff/value.txt"]
        else:
            # Bytes are pinned so the declared deliverable has one digest on
            # POSIX and Windows (text mode would translate LF on Windows).
            with open("implementation.txt", "wb") as fh:
                fh.write(b"deterministic team implementation\n")
            body["deliverables"] = ["implementation.txt"]
    if mode == "schema-invalid":
        body["summary"] = ""
    return body


def synthesis_document(stdin_text):
    return stdin_text or ""


def parse_labelled_reviews(document):
    legs = []
    lines = document.splitlines()
    index = 0
    while index < len(lines):
        match = HEADER.match(lines[index])
        if match is None:
            index += 1
            continue
        leg_id = match.group(1)
        fence = index + 1
        while fence < len(lines) and lines[fence].strip() != "```json":
            fence += 1
        body_end = fence + 1
        while body_end < len(lines) and lines[body_end].strip() != "```":
            body_end += 1
        try:
            review = json.loads("\n".join(lines[fence + 1 : body_end]))
        except json.JSONDecodeError:
            review = None
        if isinstance(review, dict):
            legs.append((leg_id, review))
        index = body_end + 1
    return legs


def build_synthesis_report(document):
    legs = parse_labelled_reviews(document)
    by_category = {}
    for leg_id, review in legs:
        for finding in review.get("findings", []):
            by_category.setdefault(finding.get("category", "unknown"), []).append((leg_id, finding))
    all_leg_ids = [leg_id for leg_id, _ in legs]
    agreements = []
    disagreements = []
    merged = []
    for index, (category, entries) in enumerate(sorted(by_category.items()), start=1):
        sources = [f"{leg_id}:{finding['id']}" for leg_id, finding in entries]
        asserting = sorted({leg_id for leg_id, _ in entries})
        first = entries[0][1]
        merged.append(
            {
                "id": f"m{index}",
                "severity": first["severity"],
                "category": category,
                "file": first["file"],
                "line": first["line"],
                "title": first["title"],
                "rationale": first["rationale"],
                "sources": sources,
            }
        )
        if len(asserting) >= 2:
            agreements.append({"title": first["title"], "sources": sources})
        else:
            disagreements.append(
                {
                    "title": first["title"],
                    "asserted_by": asserting,
                    "not_asserted_by": [x for x in all_leg_ids if x not in asserting],
                }
            )
    return {
        "schema_version": 1,
        "kind": "synthesis-report",
        "inputs": all_leg_ids,
        "agreements": agreements,
        "disagreements": disagreements,
        "merged_findings": merged,
    }


def review_body(mode):
    if mode == "schema-invalid":
        return BAD_REVIEW
    body = json.loads(json.dumps(REVIEW))
    if mode == "semantic-miss":
        body["findings"] = body["findings"][:1]
        body["summary"] = "Only the injection finding."
    elif mode == "invent-critical":
        body["findings"] = body["findings"] + [INVENTED_FINDING]
    return body


def main():
    if "--version" in sys.argv:
        sys.stdout.write(VERSION + "\n")
        return 0
    if "--help" in sys.argv:
        sys.stdout.write("--json\n" if probe_mode("codex") == "missing-flags" else HELP["codex"])
        return 0
    if sys.argv[1:3] == ["login", "status"]:
        logged_in = probe_mode("codex") != "signed-out"
        sys.stdout.write("Logged in using ChatGPT\n" if logged_in else "Not logged in\n")
        return 0 if logged_in else 1
    stdin_text = read_stdin()
    observe(stdin_text)
    if is_probe("codex", sys.argv):
        return emit_probe("codex", sys.argv)
    mode = resolve_mode()
    if mode == "rate-limit":
        sys.stderr.write("429 Too Many Requests\n")
        return 1
    if mode == "rate-limit-once" and rate_limited_once():
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
    if mode == "mutate-target":
        with open("fake-mutation.txt", "w", encoding="utf-8") as fh:
            fh.write("the fake harness wrote into the target\n")
    if synthesis_requested():
        emit(build_synthesis_report(synthesis_document(stdin_text)), stdin_text)
        return 0
    if member_result_requested():
        emit(member_result_body(mode), stdin_text)
        return 0
    body = review_body(mode)
    event_body = None
    if mode == "event-mismatch":
        event_body = json.loads(json.dumps(body))
        event_body["summary"] = "Conflicting JSONL telemetry."
    emit(body, stdin_text, event_body=event_body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
