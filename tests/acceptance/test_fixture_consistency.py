"""The committed review target, the committed oracle, and the fakes agree
(plan section 14): windows sit inside the files, every fake leg identifies
command injection plus one other seeded defect through the real matcher, the
union covers all three, and nothing critical sits outside the oracle."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from agentteam.domain.common import HarnessId
from agentteam.harness import get_adapter
from agentteam.resolution.profiles import load_profile_set, resolve_profile_path
from agentteam.run.acceptance import (
    critical_findings_outside,
    identified_defects,
    load_oracle,
)

Builder = Callable[..., Any]

REPO_ROOT = Path(__file__).resolve().parents[2]
ORACLE_PATH = REPO_ROOT / "fixtures" / "review-target.oracle.json"
TARGET = REPO_ROOT / "fixtures" / "review-target"
CI_FAKE = REPO_ROOT / "examples" / "profiles" / "ci-fake.yaml"


def test_oracle_windows_sit_inside_the_committed_files() -> None:
    oracle = load_oracle(ORACLE_PATH)
    assert {defect.id for defect in oracle.defects} == {
        "command-injection",
        "off-by-one",
        "input-mutation",
    }
    for defect in oracle.defects:
        target_file = TARGET / defect.file
        assert target_file.is_file(), defect.file
        line_count = len(target_file.read_text(encoding="utf-8").splitlines())
        assert defect.line_end <= line_count, defect.id


def test_the_oracle_lives_outside_the_leg_workspace() -> None:
    assert ORACLE_PATH.parent == TARGET.parent
    assert not (TARGET / "review-target.oracle.json").exists()
    assert "oracle" not in {p.name for p in TARGET.rglob("*")}


@pytest.mark.parametrize("harness", [HarnessId.CLAUDE_CODE, HarnessId.CODEX, HarnessId.GROK])
async def test_each_fake_leg_satisfies_its_semantic_slice(
    render_context_builder: Builder, tmp_path: Path, harness: HarnessId
) -> None:
    profile_set = load_profile_set(CI_FAKE)
    profile = next(p for p in profile_set.profiles if p.harness is harness)
    executable = resolve_profile_path(CI_FAKE, profile.executable)
    profile = profile.model_copy(update={"executable": str(executable)})
    ctx = render_context_builder(
        harness.value,
        tmp_path,
        profile=profile,
        parent_env={
            "HOME": str(tmp_path),
            "PATH": "/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "FAKE_MODE": "ok",
        },
    )
    adapter = get_adapter(harness)
    leg = adapter.parse(await adapter.invoke(adapter.render(ctx)))
    assert leg.review is not None, leg.problems
    oracle = load_oracle(ORACLE_PATH)
    identified = identified_defects(leg.review, oracle)
    assert "command-injection" in identified
    assert len(identified) >= 2
    assert critical_findings_outside(leg.review, oracle) == []


async def test_the_fake_union_covers_all_three_defects(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    oracle = load_oracle(ORACLE_PATH)
    union: set[str] = set()
    profile_set = load_profile_set(CI_FAKE)
    for harness in HarnessId:
        profile = next(p for p in profile_set.profiles if p.harness is harness)
        executable = resolve_profile_path(CI_FAKE, profile.executable)
        profile = profile.model_copy(update={"executable": str(executable)})
        leg_dir = tmp_path / harness.value
        leg_dir.mkdir()
        ctx = render_context_builder(
            harness.value,
            leg_dir,
            profile=profile,
            parent_env={
                "HOME": str(leg_dir),
                "PATH": "/usr/bin:/bin",
                "LANG": "C.UTF-8",
                "FAKE_MODE": "ok",
            },
        )
        adapter = get_adapter(harness)
        leg = adapter.parse(await adapter.invoke(adapter.render(ctx)))
        assert leg.review is not None
        union |= identified_defects(leg.review, oracle)
    assert union == {defect.id for defect in oracle.defects}
