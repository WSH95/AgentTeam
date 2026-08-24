"""Shared deterministic doctor/probe behavior for the three fake CLIs."""

import json
import os
import re
import sys
import time
from pathlib import Path

MARKER = re.compile(r"ATM_(?:INSTRUCTION|SKILL)_[A-F0-9]{24}")

HELP = {
    "claude": """
--output-format --json-schema --append-system-prompt --append-system-prompt-file
--plugin-dir --setting-sources --mcp-config --strict-mcp-config --permission-mode
--no-session-persistence --allowedTools --disallowedTools
""",
    "codex": """
--ephemeral --ignore-user-config --ignore-rules --skip-git-repo-check
--output-schema --output-last-message -o --json --sandbox -s --cd -C --config -c
""",
    "grok": """
--prompt-file --output-format --no-subagents --sandbox --rules
--system-prompt-override --json-schema
""",
}


def probe_mode(vendor):
    return os.environ.get(f"FAKE_PROBE_MODE_{vendor.upper()}") or os.environ.get(
        "FAKE_PROBE_MODE", "ok"
    )


def is_probe(vendor, argv):
    if "--json-schema" in argv:
        value = argv[argv.index("--json-schema") + 1]
        if "instruction_markers" in value:
            return True
    if vendor == "codex" and "--output-schema" in argv:
        value = argv[argv.index("--output-schema") + 1]
        return "instruction_markers" in _read(Path(value))
    return False


def emit_probe(vendor, argv):
    mode = probe_mode(vendor)
    if mode == "timeout":
        time.sleep(60)
        return 0
    if mode == "malformed":
        sys.stdout.write("not probe json\n")
        return 0
    if mode == "exit-error":
        sys.stderr.write("deterministic probe failure\n")
        return 1

    if vendor == "claude":
        instructions, skills = _claude_markers(argv)
        primary = "--append-system-prompt-file" in argv
    elif vendor == "codex":
        instructions, skills = _codex_markers(argv)
        primary = any(value.startswith("model_instructions_file=") for value in argv)
    else:
        instructions, skills = _grok_markers(argv)
        primary = "--rules" in argv
    if mode == "fallback-error" and not primary:
        sys.stderr.write("deterministic fallback probe failure\n")
        return 1
    if mode == "fallback" and primary:
        instructions = []
        if vendor == "claude":
            skills = []
    if mode == "fallback-error" and primary:
        skills = []
    if mode == "missing-skill":
        skills = []

    body = {
        "instruction_markers": sorted(set(instructions)),
        "skill_markers": sorted(set(skills)),
    }
    if vendor == "claude":
        sys.stdout.write(json.dumps({"type": "result", "structured_output": body}))
    elif vendor == "codex":
        output = Path(argv[argv.index("-o") + 1])
        output.write_text(json.dumps(body), encoding="utf-8")
        event_body = dict(body)
        if mode == "event-mismatch":
            event_body["instruction_markers"] = []
        events = [
            {"type": "thread.started", "thread_id": "probe-thread"},
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": json.dumps(event_body)},
            },
            {"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1}},
        ]
        sys.stdout.write("\n".join(json.dumps(event) for event in events) + "\n")
    else:
        if mode in {"text", "grok-text"}:
            sys.stdout.write(json.dumps({"type": "result", "text": json.dumps(body)}))
        else:
            sys.stdout.write(json.dumps({"type": "result", "structured_output": body}))
    sys.stdout.flush()
    return 0


def _claude_markers(argv):
    instruction_text = ""
    if "--append-system-prompt-file" in argv:
        instruction_text = _read(Path(argv[argv.index("--append-system-prompt-file") + 1]))
    elif "--append-system-prompt" in argv:
        instruction_text = argv[argv.index("--append-system-prompt") + 1]
    roots = [Path(os.environ.get("CLAUDE_CONFIG_DIR", ".")) / "skills"]
    if "--plugin-dir" in argv:
        roots.append(Path(argv[argv.index("--plugin-dir") + 1]) / "skills")
    roots.append(Path.cwd() / ".claude" / "skills")
    return _markers(instruction_text), _markers_from_roots(roots)


def _codex_markers(argv):
    texts = []
    for value in argv:
        if value.startswith("model_instructions_file="):
            raw = value.partition("=")[2]
            try:
                path = Path(json.loads(raw))
            except json.JSONDecodeError:
                path = Path(raw.strip('"'))
            texts.append(_read(path))
        elif value.startswith("developer_instructions="):
            raw = value.partition("=")[2]
            try:
                texts.append(str(json.loads(raw)))
            except json.JSONDecodeError:
                texts.append(raw)
    texts.append(_read(Path.cwd() / "AGENTS.md"))
    roots = [Path.cwd() / ".agents" / "skills"]
    return _markers("\n".join(texts)), _markers_from_roots(roots)


def _grok_markers(argv):
    text = ""
    for flag in ("--rules", "--system-prompt-override"):
        if flag in argv:
            text += argv[argv.index(flag) + 1]
    roots = [Path.cwd() / ".grok" / "skills", Path.cwd() / ".agents" / "skills"]
    return _markers(text), _markers_from_roots(roots)


def _markers_from_roots(roots):
    found = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("SKILL.md"):
            found.extend(_markers(_read(path)))
    return found


def _markers(text):
    return MARKER.findall(text)


def _read(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""
