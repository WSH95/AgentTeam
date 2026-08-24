#!/usr/bin/env python3
"""Deterministic fake harness for AgentTeam tests. Stdlib only; no model call.

Behaviour is selected by $FAKE_MODE (ok | rate-limit | rate-limit-once | hang |
malformed | schema-invalid | exit-130 | mutate-target | invent-critical |
semantic-miss); $FAKE_MODE_CODEX overrides it for this vendor only. A
synthesis-shaped invocation (the `--output-schema` file names
`synthesis-report`) makes the fake parse the labelled-reports document and
emit a synthesis report derived from the actual labels. When $FAKE_OBSERVE is
set, the fake records its argv, cwd, selected env names/values, and stdin to
that path as JSON.
"""

import json
import os
import re
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

KEEP_ENV = ("CODEX_HOME",)
CONFIG_HOME_VAR = "CODEX_HOME"
MODE_VAR = "FAKE_MODE_CODEX"
VERSION = "codex-cli 0.149.0"

HEADER = re.compile(r"^### leg (\S+) harness (\S+)$")


def emit(body, stdin_text):
    out_file = None
    argv = sys.argv
    if "-o" in argv:
        out_file = argv[argv.index("-o") + 1]
    events = [
        {"type": "thread.started", "thread_id": "fake-thread"},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(body)}},
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
    sentinel = os.path.join(home, ".fake-rate-limited")
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
    stdin_text = read_stdin()
    observe(stdin_text)
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
    emit(review_body(mode), stdin_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
