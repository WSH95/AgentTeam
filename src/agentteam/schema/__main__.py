"""`python -m agentteam.schema export|check [--dir DIR]` - maintainer tooling, not the `atm` CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentteam.schema import DEFAULT_SCHEMA_DIR, check_all, write_all


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m agentteam.schema")
    parser.add_argument(
        "--dir",
        type=Path,
        default=DEFAULT_SCHEMA_DIR,
        help="schema directory (default: ./schemas, relative to the working directory)",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("export", "write the V1 JSON Schemas into DIR"),
        ("check", "exit 1 if any checked-in schema is missing, stale, or orphaned"),
    ):
        p = sub.add_parser(command, help=help_text)
        p.add_argument("--dir", dest="dir", type=Path, default=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.command == "export":
        for path in write_all(args.dir):
            print(f"wrote {path}")
        return 0
    problems = check_all(args.dir)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        return 1
    print(f"schemas in {args.dir} are current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
