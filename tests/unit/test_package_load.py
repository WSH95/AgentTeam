"""Package loading, reference checks, and prohibited-content heuristics (plan sections 7-8)."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentteam.resolution.package import PackageError, check_package, load_package

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = REPO_ROOT / "examples" / "assistants" / "code-reviewer"


def _mini_package(root: Path, **definition_overrides: object) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "persona.md").write_text("A careful reviewer.\n", encoding="utf-8")
    (root / "principles.md").write_text("Prefer evidence.\n", encoding="utf-8")
    body = {
        "schema_version": 1,
        "kind": "assistant-definition",
        "id": "mini",
        "version": 1,
        "summary": "Minimal.",
        "persona": "persona.md",
        "purpose": ["review"],
        "principles": "principles.md",
    }
    body.update(definition_overrides)
    import yaml

    (root / "assistant.yaml").write_text(yaml.safe_dump(body), encoding="utf-8")
    return root


def test_example_package_loads_and_checks_clean() -> None:
    loaded = load_package(EXAMPLE)
    assert loaded.definition.id == "code-reviewer"
    assert [a.ref for a in loaded.definition.artifacts] == [
        "code-review",
        "security-review",
        "test-analysis",
    ]
    assert check_package(loaded, strict_content=True) == []


def test_missing_definition_file_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(PackageError, match=r"assistant\.yaml"):
        load_package(tmp_path)


def test_ambiguous_yaml_and_json_is_an_error(tmp_path: Path) -> None:
    root = _mini_package(tmp_path / "p")
    (root / "assistant.json").write_text("{}", encoding="utf-8")
    with pytest.raises(PackageError, match="both"):
        load_package(root)


def test_schema_violations_are_reported_with_locations(tmp_path: Path) -> None:
    root = _mini_package(tmp_path / "p", version=0)
    with pytest.raises(PackageError, match="version"):
        load_package(root)


def test_missing_referenced_instruction_file_is_a_problem(tmp_path: Path) -> None:
    root = _mini_package(tmp_path / "p", methods="methods.md")
    problems = check_package(load_package(root), strict_content=False)
    assert any("methods.md" in p and "missing" in p for p in problems)


def test_agent_skill_without_skill_md_is_a_problem(tmp_path: Path) -> None:
    root = _mini_package(
        tmp_path / "p",
        artifacts=[
            {
                "ref": "code-review",
                "kind": "agent-skill",
                "source": {"vendored": "skills/code-review"},
            }
        ],
    )
    (root / "skills" / "code-review").mkdir(parents=True)
    (root / "skills" / "code-review" / "notes.txt").write_text("x\n", encoding="utf-8")
    problems = check_package(load_package(root), strict_content=False)
    assert any("SKILL.md" in p for p in problems)


def test_strict_content_flags_prohibited_content(tmp_path: Path) -> None:
    root = _mini_package(tmp_path / "p")
    (root / "principles.md").write_text(
        "Look at /home/wsh/Documents/secret-project for context.\n"
        "Use key sk-abcdefghijklmnopqrstuvwx1234 when needed.\n",
        encoding="utf-8",
    )
    problems = check_package(load_package(root), strict_content=True)
    assert any("workspace-paths" in p and "principles.md" in p for p in problems)
    assert any("secrets" in p for p in problems)


def test_strict_content_respects_the_definitions_check_list(tmp_path: Path) -> None:
    root = _mini_package(tmp_path / "p", prohibited_content=["secrets"])
    (root / "persona.md").write_text("See /home/user/project for details.\n", encoding="utf-8")
    problems = check_package(load_package(root), strict_content=True)
    assert problems == []  # workspace-paths check disabled by the definition


def test_non_strict_skips_heuristics_but_checks_references(tmp_path: Path) -> None:
    root = _mini_package(tmp_path / "p")
    (root / "persona.md").write_text("See /home/user/project.\n", encoding="utf-8")
    assert check_package(load_package(root), strict_content=False) == []


def test_runtime_memory_and_session_id_heuristics(tmp_path: Path) -> None:
    root = _mini_package(tmp_path / "p")
    (root / "principles.md").write_text(
        "Recall MEMORY.md from the last run.\n"
        "session 6f9619ff-8b86-4d01-b42d-00cf4fc964ff said so.\n",
        encoding="utf-8",
    )
    problems = check_package(load_package(root), strict_content=True)
    assert any("runtime-memory" in p for p in problems)
    assert any("session-identifiers" in p for p in problems)
