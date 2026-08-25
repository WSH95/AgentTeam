"""Frozen import and textual containment for the optional provider boundary."""

from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "src" / "agentteam"
TEST_ROOT = REPO_ROOT / "tests"


def _imports() -> Counter[tuple[str, str, tuple[str, ...]]]:
    occurrences: Counter[tuple[str, str, tuple[str, ...]]] = Counter()
    for root in (SOURCE_ROOT, TEST_ROOT):
        for path in sorted(root.rglob("*.py")):
            relative = path.relative_to(REPO_ROOT).as_posix()
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".", 1)[0] == "clawteam":
                            occurrences[(relative, alias.name, ())] += 1
                elif (
                    isinstance(node, ast.ImportFrom)
                    and node.module is not None
                    and (
                        node.module.split(".", 1)[0] == "clawteam"
                        or node.module.startswith("agentteam.compat")
                    )
                ):
                    names = tuple(alias.name for alias in node.names)
                    occurrences[(relative, node.module, names)] += 1
    return occurrences


def test_ast_imports_stay_inside_the_frozen_boundary() -> None:
    occurrences = _imports()
    for (path, module, _names), count in occurrences.items():
        assert count >= 1
        if module.split(".", 1)[0] == "clawteam":
            assert path == "src/agentteam/compat/clawteam.py" or path.startswith(
                "tests/compatibility/"
            )
        if module.startswith("agentteam.compat"):
            assert path == "src/agentteam/coordination/clawteam.py" or path.startswith(
                "tests/compatibility/"
            )

    production_direct = Counter(
        {
            key: count
            for key, count in occurrences.items()
            if key[0] == "src/agentteam/compat/clawteam.py"
        }
    )
    assert production_direct == Counter(
        {
            ("src/agentteam/compat/clawteam.py", "clawteam", ()): 1,
            ("src/agentteam/compat/clawteam.py", "clawteam.events", ("global_bus",)): 2,
            ("src/agentteam/compat/clawteam.py", "clawteam.events.bus", ("EventBus",)): 1,
            ("src/agentteam/compat/clawteam.py", "clawteam.team.manager", ("TeamManager",)): 4,
            ("src/agentteam/compat/clawteam.py", "clawteam.store.file", ("FileTaskStore",)): 4,
            ("src/agentteam/compat/clawteam.py", "clawteam.team.models", ("TaskStatus",)): 1,
            (
                "src/agentteam/compat/clawteam.py",
                "clawteam.team.mailbox",
                ("MailboxManager",),
            ): 1,
            (
                "src/agentteam/compat/clawteam.py",
                "clawteam.transport.file",
                ("FileTransport",),
            ): 1,
            (
                "src/agentteam/compat/clawteam.py",
                "clawteam.team.snapshot",
                ("SnapshotManager",),
            ): 3,
        }
    )


def test_case_insensitive_text_occurrences_match_the_frozen_inventory() -> None:
    init_path = SOURCE_ROOT / "coordination" / "__init__.py"
    team_path = SOURCE_ROOT / "domain" / "team.py"
    run_path = SOURCE_ROOT / "domain" / "run.py"
    allowed = {
        init_path,
        team_path,
        SOURCE_ROOT / "coordination" / "clawteam.py",
    }
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        count = text.casefold().count("clawteam")
        if count and not path.is_relative_to(SOURCE_ROOT / "compat"):
            assert path in allowed, path.relative_to(REPO_ROOT)

    init_text = init_path.read_text(encoding="utf-8")
    team_text = team_path.read_text(encoding="utf-8")
    assert init_text.casefold().count("clawteam") == 4
    assert team_text.casefold().count("clawteam") == 2
    assert run_path.read_text(encoding="utf-8").casefold().count("clawteam") == 0
    for path in (SOURCE_ROOT / "commands").rglob("*.py"):
        assert path.read_text(encoding="utf-8").casefold().count("clawteam") == 0

    init_tree = ast.parse(init_text)
    init_literals = [node.value for node in ast.walk(init_tree) if isinstance(node, ast.Constant)]
    assert init_literals.count("clawteam") == 1
    assert init_literals.count("agentteam.coordination.clawteam") == 1
    disposition_contexts = Counter(
        type(node.ctx).__name__
        for node in ast.walk(init_tree)
        if isinstance(node, ast.Name) and node.id == "CLAWTEAM_DISPOSITION"
    )
    assert disposition_contexts == Counter({"Store": 1, "Load": 1})

    team_literals = [
        node.value for node in ast.walk(ast.parse(team_text)) if isinstance(node, ast.Constant)
    ]
    assert team_literals.count("clawteam") == 1
