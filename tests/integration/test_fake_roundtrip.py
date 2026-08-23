"""render -> invoke(fake) -> parse round trips (plan section 15; no model call)."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from agentteam.domain.common import HarnessId
from agentteam.domain.run import SchemaOutcome
from agentteam.harness import get_adapter
from agentteam.resolution.profiles import load_profile_set, resolve_profile_path

Builder = Callable[..., Any]

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_FAKE = REPO_ROOT / "examples" / "profiles" / "ci-fake.yaml"


def _fake_ctx(
    builder: Builder, tmp_path: Path, harness: HarnessId, mode: str, observe: Path
) -> Any:
    profile_set = load_profile_set(CI_FAKE)
    profile = next(p for p in profile_set.profiles if p.harness is harness)
    executable = resolve_profile_path(CI_FAKE, profile.executable)
    profile = profile.model_copy(update={"executable": str(executable)})
    parent_env = {
        "HOME": str(tmp_path),
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "FAKE_OBSERVE": str(observe),
        "FAKE_MODE": mode,
    }
    return builder(harness.value, tmp_path, profile=profile, parent_env=parent_env)


@pytest.mark.parametrize("harness", [HarnessId.CLAUDE_CODE, HarnessId.CODEX, HarnessId.GROK])
async def test_ok_round_trip_produces_a_valid_review(
    render_context_builder: Builder, tmp_path: Path, harness: HarnessId
) -> None:
    observe = tmp_path / "observed.json"
    ctx = _fake_ctx(render_context_builder, tmp_path, harness, "ok", observe)
    adapter = get_adapter(harness)
    rendered = adapter.render(ctx)
    raw = await adapter.invoke(rendered)
    leg = adapter.parse(raw)
    assert raw.exit_code == 0, raw.stderr
    assert leg.schema_outcome is SchemaOutcome.VALID, leg.problems
    assert leg.review is not None
    assert leg.review.findings[0].category == "command-injection"

    observed = json.loads(observe.read_text(encoding="utf-8"))
    # the fake saw exactly the rendered argv (minus the interpreter prefix)
    assert observed["argv"][1:] == rendered.argv[2:]
    # config-home env var reached the child and points inside the write root
    config_var = ctx.profile.environment.config_home_variable
    assert observed["env"][config_var] == str(ctx.config_root)
    # secrets/etc never leak: only baseline+passthrough+config-home names
    assert "SECRET_THING" not in observed["env"]
    if rendered.stdin_text is not None:
        assert observed["stdin"] == rendered.stdin_text


@pytest.mark.parametrize("harness", [HarnessId.CLAUDE_CODE, HarnessId.CODEX, HarnessId.GROK])
async def test_schema_invalid_mode_is_detected(
    render_context_builder: Builder, tmp_path: Path, harness: HarnessId
) -> None:
    ctx = _fake_ctx(
        render_context_builder, tmp_path, harness, "schema-invalid", tmp_path / "obs.json"
    )
    adapter = get_adapter(harness)
    rendered = adapter.render(ctx)
    raw = await adapter.invoke(rendered)
    leg = adapter.parse(raw)
    assert leg.schema_outcome is SchemaOutcome.INVALID
    assert leg.review is None


async def test_rate_limit_mode_classifies_transient(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    from agentteam.domain.run import RetryClassification
    from agentteam.harness.process import classify_failure

    ctx = _fake_ctx(
        render_context_builder, tmp_path, HarnessId.CODEX, "rate-limit", tmp_path / "obs.json"
    )
    adapter = get_adapter(HarnessId.CODEX)
    rendered = adapter.render(ctx)
    raw = await adapter.invoke(rendered)
    assert raw.exit_code == 1
    assert classify_failure(raw) is RetryClassification.TRANSIENT
