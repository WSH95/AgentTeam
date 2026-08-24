"""Request building and run preflight (plan sections 8, 11, 12 steps 1-3).

Request-file path fields resolve against the request file's directory; flag
paths resolve against the invoking CWD; CLI overrides merge per harness over
request-file overrides; the api-test guard applies to the harnesses actually
chosen; the oracle is resolved and checked but never copied anywhere.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from agentteam.domain.common import HarnessId
from agentteam.domain.profile import HarnessProfileV1, ProfileKind, Verification
from agentteam.domain.request import AcceptanceSettingsV1, HarnessOverrideV1, RunRequestV1
from agentteam.resolution.profiles import seed_default_profiles, write_profile_set
from agentteam.run.preflight import PreflightError, build_request, preflight

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPO_ROOT / "examples" / "assistants" / "code-reviewer"


def _installed(_profile: HarnessProfileV1) -> bool:
    return True


def _profiles_path(tmp_path: Path, *, api_test: frozenset[str] = frozenset()) -> Path:
    profile_set = seed_default_profiles()
    updated = [
        profile.model_copy(update={"kind": ProfileKind.API_TEST})
        if profile.harness.value in api_test
        else profile
        for profile in profile_set.profiles
    ]
    path = tmp_path / "profiles.yaml"
    write_profile_set(path, profile_set.model_copy(update={"profiles": updated}))
    return path


def _live_profiles_path(
    tmp_path: Path, *, version: str = "current-version", expected: str | None = None
) -> Path:
    profile_set = seed_default_profiles()
    updated = []
    for profile in profile_set.profiles:
        home = tmp_path / "vendors" / profile.harness.value
        home.mkdir(parents=True)
        updated.append(
            profile.model_copy(
                update={
                    "expected_version": expected,
                    "capabilities": [
                        row.model_copy(
                            update={
                                "verification": Verification.VERIFIED,
                                "cli_version": version,
                                "verified_at": datetime(2026, 8, 23, tzinfo=UTC),
                            }
                        )
                        for row in profile.capabilities
                    ],
                }
            )
        )
    path = tmp_path / "profiles.yaml"
    write_profile_set(path, profile_set.model_copy(update={"profiles": updated}))
    return path


def _request(tmp_path: Path, **overrides: Any) -> RunRequestV1:
    workspace = tmp_path / "workspace"
    workspace.mkdir(exist_ok=True)
    (workspace / "target.ts").write_text("export const x = 1\n", encoding="utf-8")
    task = tmp_path / "task.md"
    task.write_text("Review it.\n", encoding="utf-8")
    data: dict[str, Any] = {
        "schema_version": 1,
        "kind": "run-request",
        "mode": "direct",
        "assistant": str(PACKAGE_ROOT),
        "workspace": str(workspace),
        "task_file": str(task),
    }
    data.update(overrides)
    return RunRequestV1.model_validate(data)


# -- the acceptance block -----------------------------------------------------


def test_acceptance_settings_default_inert_and_closed(tmp_path: Path) -> None:
    request = _request(tmp_path)
    assert request.acceptance.oracle is None
    assert "acceptance" not in request.model_fields_set
    with pytest.raises(ValidationError):
        AcceptanceSettingsV1.model_validate({"oracle": None, "extra": 1})
    round_tripped = RunRequestV1.model_validate_json(
        _request(tmp_path, acceptance={"oracle": "oracle.json"}).model_dump_json()
    )
    assert round_tripped.acceptance.oracle == "oracle.json"


# -- build_request ------------------------------------------------------------


def _write_request_file(directory: Path, body: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "request.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def test_request_file_relative_paths_resolve_against_the_file(tmp_path: Path) -> None:
    request_dir = tmp_path / "requests"
    request_file = _write_request_file(
        request_dir,
        """
        schema_version: 1
        kind: run-request
        mode: direct
        assistant: ../assistants/reviewer
        workspace: ../../fixtures/target
        task_file: task.md
        output_dir: out
        acceptance: {oracle: ../oracle.json}
        """,
    )
    request = build_request(
        request_file=request_file,
        assistant=None,
        workspace=None,
        task_file=None,
        harnesses=[],
        model_overrides=[],
        effort_overrides=[],
        no_synthesis=False,
        output_dir=None,
    )
    base = request_dir.resolve()
    assert request.assistant == str((base / "../assistants/reviewer").resolve())
    assert request.workspace == str((base / "../../fixtures/target").resolve())
    assert request.task_file == str((base / "task.md").resolve())
    assert request.output_dir == str((base / "out").resolve())
    assert request.acceptance.oracle == str((base / "../oracle.json").resolve())


def test_flag_paths_resolve_against_cwd_and_override_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request_file = _write_request_file(
        tmp_path / "requests",
        """
        schema_version: 1
        kind: run-request
        mode: direct
        assistant: pkg-from-file
        workspace: ws-from-file
        task_file: task-from-file.md
        """,
    )
    invoke_dir = tmp_path / "invoke-here"
    invoke_dir.mkdir()
    monkeypatch.chdir(invoke_dir)
    request = build_request(
        request_file=request_file,
        assistant=Path("pkg"),
        workspace=None,
        task_file=None,
        harnesses=[],
        model_overrides=[],
        effort_overrides=[],
        no_synthesis=False,
        output_dir=Path("out"),
    )
    assert request.assistant == str((invoke_dir / "pkg").resolve())
    assert request.output_dir == str((invoke_dir / "out").resolve())
    assert request.workspace == str((tmp_path / "requests" / "ws-from-file").resolve())


def test_cli_overrides_merge_per_harness_over_file_overrides(tmp_path: Path) -> None:
    request_file = _write_request_file(
        tmp_path,
        """
        schema_version: 1
        kind: run-request
        mode: direct
        assistant: pkg
        workspace: ws
        task_file: task.md
        model_overrides:
          - {harness: codex, value: file-codex-model}
          - {harness: grok, value: file-grok-model}
        """,
    )
    request = build_request(
        request_file=request_file,
        assistant=None,
        workspace=None,
        task_file=None,
        harnesses=[],
        model_overrides=[HarnessOverrideV1(harness=HarnessId.CODEX, value="cli-codex-model")],
        effort_overrides=[],
        no_synthesis=False,
        output_dir=None,
    )
    by_harness = {o.harness: o.value for o in request.model_overrides}
    assert by_harness == {
        HarnessId.CODEX: "cli-codex-model",
        HarnessId.GROK: "file-grok-model",
    }


def test_no_synthesis_flag_overrides_the_file(tmp_path: Path) -> None:
    request_file = _write_request_file(
        tmp_path,
        """
        schema_version: 1
        kind: run-request
        mode: direct
        assistant: pkg
        workspace: ws
        task_file: task.md
        synthesis: {enabled: true, harness: claude-code}
        """,
    )
    request = build_request(
        request_file=request_file,
        assistant=None,
        workspace=None,
        task_file=None,
        harnesses=[],
        model_overrides=[],
        effort_overrides=[],
        no_synthesis=True,
        output_dir=None,
    )
    assert request.synthesis.enabled is False
    assert request.synthesis.harness is HarnessId.CLAUDE_CODE


def test_missing_required_fields_and_bad_files_raise_preflight_errors(tmp_path: Path) -> None:
    with pytest.raises(PreflightError, match="assistant"):
        build_request(
            request_file=None,
            assistant=None,
            workspace=Path("ws"),
            task_file=Path("t.md"),
            harnesses=[],
            model_overrides=[],
            effort_overrides=[],
            no_synthesis=False,
            output_dir=None,
        )
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("assistant: [unclosed", encoding="utf-8")
    with pytest.raises(PreflightError, match="YAML"):
        build_request(
            request_file=bad_yaml,
            assistant=None,
            workspace=None,
            task_file=None,
            harnesses=[],
            model_overrides=[],
            effort_overrides=[],
            no_synthesis=False,
            output_dir=None,
        )
    listing = tmp_path / "list.yaml"
    listing.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(PreflightError, match="mapping"):
        build_request(
            request_file=listing,
            assistant=None,
            workspace=None,
            task_file=None,
            harnesses=[],
            model_overrides=[],
            effort_overrides=[],
            no_synthesis=False,
            output_dir=None,
        )


# -- preflight ----------------------------------------------------------------


def test_overlay_refs_fail_preflight(tmp_path: Path) -> None:
    request = _request(tmp_path, overlay_refs=["overlay-1"])
    with pytest.raises(PreflightError, match="overlay"):
        preflight(request, profile_path=_profiles_path(tmp_path), installed=_installed)


def test_api_test_guard_applies_to_the_chosen_harness(tmp_path: Path) -> None:
    # Empty request harnesses: the assistant's preference picks claude-code,
    # whose profile is api-test — the G3 request-only guard missed this.
    request = _request(tmp_path)
    profiles = _profiles_path(tmp_path, api_test=frozenset({"claude-code"}))
    with pytest.raises(PreflightError, match="api-test"):
        preflight(request, profile_path=profiles, installed=_installed)


def test_missing_oracle_fails_and_present_oracle_resolves(tmp_path: Path) -> None:
    request = _request(tmp_path, acceptance={"oracle": str(tmp_path / "missing-oracle.json")})
    with pytest.raises(PreflightError, match="oracle"):
        preflight(request, profile_path=_profiles_path(tmp_path), installed=_installed)
    oracle = tmp_path / "oracle.json"
    oracle.write_text("{}", encoding="utf-8")
    resolved = preflight(
        _request(tmp_path, acceptance={"oracle": str(oracle)}),
        profile_path=_profiles_path(tmp_path),
        installed=_installed,
    )
    assert resolved.oracle_path == oracle


def test_effective_limits_lower_but_never_raise_the_caps(tmp_path: Path) -> None:
    profiles = _profiles_path(tmp_path)
    lowered = preflight(
        _request(tmp_path, limits={"attempt_seconds": 30, "transient_retries": 0}),
        profile_path=profiles,
        installed=_installed,
    )
    assert lowered.timeout_seconds == 30
    assert lowered.transient_retries == 0
    defaulted = preflight(_request(tmp_path), profile_path=profiles, installed=_installed)
    assert defaulted.timeout_seconds == 900
    assert defaulted.transient_retries == 1


def test_single_leg_runs_skip_synthesis_unless_explicitly_requested(tmp_path: Path) -> None:
    profiles = _profiles_path(tmp_path)
    solo = preflight(_request(tmp_path), profile_path=profiles, installed=_installed)
    assert len(solo.legs) == 1
    assert solo.synthesis_planned is False
    assert solo.synthesis_leg is None
    explicit = preflight(
        _request(tmp_path, synthesis={"enabled": True, "harness": "claude-code"}),
        profile_path=profiles,
        installed=_installed,
    )
    assert explicit.synthesis_planned is True
    assert explicit.synthesis_leg is not None
    ensemble = preflight(
        _request(tmp_path, harnesses=["claude-code", "codex", "grok"]),
        profile_path=profiles,
        installed=_installed,
    )
    assert len(ensemble.legs) == 3
    assert ensemble.synthesis_planned is True


def test_leg_plans_carry_resolved_models_with_cli_precedence(tmp_path: Path) -> None:
    request = _request(
        tmp_path,
        harnesses=["claude-code", "codex", "grok"],
        model_overrides=[{"harness": "codex", "value": "requested-codex-model"}],
    )
    resolved = preflight(request, profile_path=_profiles_path(tmp_path), installed=_installed)
    by_harness = {leg.harness: leg for leg in resolved.legs}
    assert by_harness[HarnessId.CODEX].requested.model == "requested-codex-model"
    synthesis = resolved.synthesis_leg
    assert synthesis is not None
    assert synthesis.harness is HarnessId.CLAUDE_CODE


def test_live_preflight_resolves_the_persistent_profile_home(tmp_path: Path) -> None:
    profiles = _live_profiles_path(tmp_path)
    resolved = preflight(
        _request(tmp_path),
        profile_path=profiles,
        installed=_installed,
        live=True,
        environ={},
        version_reader=lambda _profile: "current-version",
    )
    assert resolved.live_ready is True
    assert Path(resolved.legs[0].profile.config_home) == (tmp_path / "vendors" / "claude-code")


@pytest.mark.parametrize(
    ("recorded", "current", "expected", "match"),
    [
        ("old-version", "current-version", None, "stale"),
        ("current-version", "current-version", "required-version", "expected version"),
    ],
)
def test_live_preflight_rejects_stale_or_expected_version_mismatch(
    tmp_path: Path,
    recorded: str,
    current: str,
    expected: str | None,
    match: str,
) -> None:
    profiles = _live_profiles_path(tmp_path, version=recorded, expected=expected)
    with pytest.raises(PreflightError, match=match):
        preflight(
            _request(tmp_path),
            profile_path=profiles,
            installed=_installed,
            live=True,
            environ={},
            version_reader=lambda _profile: current,
        )


def test_live_preflight_rejects_incomplete_readiness_and_conflicting_env(
    tmp_path: Path,
) -> None:
    path = _live_profiles_path(tmp_path)
    # Reuse the already-versioned on-disk rows and make one required row unverified.
    from agentteam.resolution.profiles import load_profile_set

    profile_set = load_profile_set(path)
    claude = profile_set.profiles[0]
    rows = [
        row.model_copy(update={"verification": Verification.UNVERIFIED})
        if row.name == "structured-output"
        else row
        for row in claude.capabilities
    ]
    write_profile_set(
        path,
        profile_set.model_copy(
            update={
                "profiles": [
                    claude.model_copy(update={"capabilities": rows}),
                    *profile_set.profiles[1:],
                ]
            }
        ),
    )
    with pytest.raises(PreflightError, match="structured-output"):
        preflight(
            _request(tmp_path),
            profile_path=path,
            installed=_installed,
            live=True,
            environ={},
            version_reader=lambda _profile: "current-version",
        )
    with pytest.raises(PreflightError, match="ANTHROPIC_API_KEY"):
        preflight(
            _request(tmp_path),
            profile_path=_live_profiles_path(tmp_path / "conflict"),
            installed=_installed,
            live=True,
            environ={"ANTHROPIC_API_KEY": "never-record-this"},
            version_reader=lambda _profile: "current-version",
        )
