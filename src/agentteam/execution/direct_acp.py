"""Thin Python owner around the pinned ``acpx/runtime`` Node bridge."""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from collections.abc import AsyncIterator, Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from typing import Any, Literal, cast

from agentteam.domain.common import HarnessId
from agentteam.domain.interactive import (
    CapabilityLevel,
    CleanupFact,
    CloseFactsV1,
    DoctorCheckV1,
    ProviderCapabilitiesV1,
    ProviderDoctorV1,
    ProviderLiveAttestationV1,
)
from agentteam.domain.profile import HarnessProfileV1
from agentteam.execution.protocol import (
    ActiveTurn,
    CancelDisposition,
    OpenMemberSpec,
    PermissionOutcome,
    ProviderDescriptor,
    ProviderEvent,
    ProviderSession,
    ProviderSuspendFacts,
    ProviderTurnResult,
    ProviderTurnStatus,
    RetireEmptyMemberSpec,
    TurnSpec,
)
from agentteam.harness.diagnostics import capture_version
from agentteam.harness.environment import build_environment
from agentteam.harness.launcher import resolve_launcher
from agentteam.resolution.profiles import (
    ProfileError,
    atomic_write_text,
    ensure_owner_directory,
    resolve_config_home,
    resolve_profile_executable,
)

RUNTIME_ID = "direct-acp"
MIN_NODE_VERSION = (22, 13, 0)
PROTOCOL_VERSION = 1
RESOURCE_PACKAGE = "agentteam.execution.resources.direct_acp"
RESOURCE_FILES = ("package.json", "package-lock.json", "bridge.mjs")
EXPECTED_PINS = {
    "acpx": "0.13.1",
    "@agentclientprotocol/codex-acp": "1.6.2",
    "@agentclientprotocol/claude-agent-acp": "0.69.0",
}
ACP_AGENT_PACKAGES = {
    HarnessId.CODEX: "@agentclientprotocol/codex-acp",
    HarnessId.CLAUDE_CODE: "@agentclientprotocol/claude-agent-acp",
}
QUALIFICATION_FORMAT = 2
LIVE_ATTESTATION_FORMAT = 1
QUALIFICATION_TIMEOUT_SECONDS = 60
SUSPENSION_MARKER = ".agentteam-suspended.json"


class DirectAcpError(RuntimeError):
    pass


@dataclass(frozen=True)
class DirectAcpQualificationTarget:
    harness: HarnessId
    runtime_path: Path
    command: tuple[str, ...]
    environment: Mapping[str, str]
    native_version: str
    expected_version: str | None
    config_home_variable: str
    config_home: Path
    fingerprint: str


@dataclass(frozen=True)
class DirectAcpQualificationResult:
    runtime_controls: tuple[str, ...]
    agent_capabilities: tuple[str, ...]
    empty_reconnect: Literal["strict-resume", "fresh-recreate"]


def default_runtime_base(environ: Mapping[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    configured = env.get("AGENTTEAM_HOME")
    home = Path(configured).expanduser() if configured else Path.home() / ".agentteam"
    return home / "runtimes" / RUNTIME_ID


def _resource_bytes(name: str) -> bytes:
    return resources.files(RESOURCE_PACKAGE).joinpath(name).read_bytes()


def runtime_lock_hash() -> str:
    digest = hashlib.sha256()
    for name in RESOURCE_FILES:
        data = _resource_bytes(name)
        digest.update(name.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(str(len(data)).encode("ascii"))
        digest.update(b"\x00")
        digest.update(data)
    return digest.hexdigest()


def _runtime_tree_hash(path: Path) -> str:
    root = Path(path) / "node_modules"
    if root.is_symlink() or not root.is_dir():
        raise DirectAcpError("runtime node_modules tree is missing or unsafe")
    digest = hashlib.sha256()
    try:
        for entry in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
            relative = entry.relative_to(root).as_posix()
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            if entry.is_symlink():
                digest.update(b"link\0")
                digest.update(os.readlink(entry).encode("utf-8", errors="surrogateescape"))
            elif entry.is_dir():
                digest.update(b"dir\0")
            elif entry.is_file():
                digest.update(b"file\0")
                with entry.open("rb") as handle:
                    while chunk := handle.read(1024 * 1024):
                        digest.update(chunk)
            else:
                raise DirectAcpError(f"runtime contains an irregular entry: {relative}")
            digest.update(b"\0")
    except OSError as error:
        raise DirectAcpError(f"cannot hash installed runtime: {error}") from None
    return digest.hexdigest()


def installed_runtime_tree_hash(path: Path) -> str:
    """Return the streamed installed-tree identity used by qualifications."""
    return _runtime_tree_hash(Path(path))


def installed_runtime_path(environ: Mapping[str, str] | None = None) -> Path:
    return default_runtime_base(environ) / runtime_lock_hash()


def resolve_acp_agent_command(
    runtime_path: Path,
    harness: HarnessId,
    *,
    node: str,
    native_executable: Path,
    platform: str = sys.platform,
) -> tuple[str, ...]:
    """Resolve only a pinned local ACP agent; never consult global npm state."""
    if harness is HarnessId.GROK:
        resolved = resolve_launcher(
            native_executable,
            ["agent", "stdio"],
            platform=platform,
        )
        if resolved.reason is not None:
            raise DirectAcpError(resolved.reason)
        return tuple(resolved.argv)
    package_name = ACP_AGENT_PACKAGES.get(harness)
    if package_name is None:
        raise DirectAcpError(f"no direct-ACP agent mapping for {harness.value}")
    package_root = Path(runtime_path) / "node_modules" / package_name
    manifest_path = package_root / "package.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise DirectAcpError(f"pinned ACP agent is not installed: {package_name}")
    try:
        manifest = json.loads(manifest_path.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise DirectAcpError(
            f"invalid pinned ACP agent manifest: {package_name}: {error}"
        ) from None
    expected = EXPECTED_PINS[package_name]
    if manifest.get("version") != expected:
        raise DirectAcpError(f"pinned ACP agent version mismatch: {package_name}@{expected}")
    binary = manifest.get("bin")
    if isinstance(binary, dict):
        values = [value for value in binary.values() if isinstance(value, str)]
        relative = values[0] if len(values) == 1 else None
    else:
        relative = binary if isinstance(binary, str) else None
    if relative is None:
        raise DirectAcpError(f"pinned ACP agent exposes no unambiguous binary: {package_name}")
    entry = (package_root / relative).resolve()
    if package_root.resolve() not in entry.parents or not entry.is_file() or entry.is_symlink():
        raise DirectAcpError(f"unsafe pinned ACP agent binary: {entry}")
    return node, str(entry)


def build_direct_acp_qualification_target(
    profile: HarnessProfileV1,
    *,
    profile_path: Path,
    runtime_path: Path,
    node: str,
    environ: Mapping[str, str],
    platform: str = sys.platform,
    runtime_tree_hash: str | None = None,
) -> DirectAcpQualificationTarget:
    """Resolve one exact current profile into a no-call qualification target."""
    try:
        executable = resolve_profile_executable(profile_path, profile.executable)
        config_home = resolve_config_home(profile_path, profile.config_home)
    except ProfileError as error:
        raise DirectAcpError(str(error)) from None
    try:
        executable_target = executable.resolve(strict=True)
        executable_stat = executable_target.stat()
    except (OSError, RuntimeError):
        raise DirectAcpError(
            f"agent executable is missing or unsafe: {profile.harness.value}"
        ) from None
    if not executable_target.is_file() or executable_target.is_symlink():
        raise DirectAcpError(f"agent executable is missing or unsafe: {profile.harness.value}")
    if platform != "win32" and not os.access(executable_target, os.X_OK):
        raise DirectAcpError(f"agent executable is not owner-executable: {profile.harness.value}")
    if not config_home.is_dir() or config_home.is_symlink():
        raise DirectAcpError(f"agent config home is missing or unsafe: {profile.harness.value}")
    concrete = profile.model_copy(
        update={"executable": str(executable), "config_home": str(config_home)}
    )
    version = capture_version(concrete, parent=environ, platform=platform)
    if version is None:
        raise DirectAcpError(f"agent --version failed: {profile.harness.value}")
    try:
        current_target = executable.resolve(strict=True)
        current_stat = current_target.stat()
    except (OSError, RuntimeError):
        raise DirectAcpError(
            f"agent executable changed during inspection: {profile.harness.value}"
        ) from None
    executable_identity = (
        executable_stat.st_dev,
        executable_stat.st_ino,
        executable_stat.st_size,
        executable_stat.st_mtime_ns,
        executable_stat.st_mode,
    )
    current_identity = (
        current_stat.st_dev,
        current_stat.st_ino,
        current_stat.st_size,
        current_stat.st_mtime_ns,
        current_stat.st_mode,
    )
    if current_target != executable_target or current_identity != executable_identity:
        raise DirectAcpError(f"agent executable changed during inspection: {profile.harness.value}")
    if profile.expected_version is not None and version != profile.expected_version:
        raise DirectAcpError(
            f"agent version mismatch for {profile.harness.value}: "
            f"expected {profile.expected_version!r}, found {version!r}"
        )
    try:
        child_environment, _record = build_environment(
            concrete,
            environ,
            platform=platform,
        )
    except ValueError as error:
        raise DirectAcpError(str(error)) from None
    if profile.harness in {HarnessId.CODEX, HarnessId.CLAUDE_CODE}:
        child_environment["PATH"] = (
            str(executable.parent) + os.pathsep + child_environment.get("PATH", "")
        )
    command = resolve_acp_agent_command(
        runtime_path,
        profile.harness,
        node=node,
        native_executable=executable,
        platform=platform,
    )
    identity = {
        "format": QUALIFICATION_FORMAT,
        "harness": profile.harness.value,
        "runtime_lock_hash": runtime_lock_hash(),
        "runtime_tree_hash": runtime_tree_hash or _runtime_tree_hash(runtime_path),
        "command": list(command),
        "native_executable": str(executable),
        "native_executable_target": str(executable_target),
        "native_executable_stat": list(executable_identity),
        "native_version": version,
        "expected_version": profile.expected_version,
        "config_home_variable": profile.environment.config_home_variable,
        "config_home": str(config_home),
        "environment_sha256": hashlib.sha256(
            json.dumps(
                sorted(child_environment.items()),
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest(),
        "platform": platform,
    }
    fingerprint = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return DirectAcpQualificationTarget(
        harness=profile.harness,
        runtime_path=runtime_path,
        command=command,
        environment=child_environment,
        native_version=version,
        expected_version=profile.expected_version,
        config_home_variable=profile.environment.config_home_variable,
        config_home=config_home,
        fingerprint=fingerprint,
    )


def verify_packaged_lock() -> list[str]:
    problems: list[str] = []
    package = json.loads(_resource_bytes("package.json"))
    lock = json.loads(_resource_bytes("package-lock.json"))
    dependencies = package.get("dependencies")
    root_dependencies = lock.get("packages", {}).get("", {}).get("dependencies")
    if dependencies != EXPECTED_PINS or root_dependencies != EXPECTED_PINS:
        problems.append("package and lock roots do not match approved exact pins")
    packages = lock.get("packages", {})
    for name, version in EXPECTED_PINS.items():
        row = packages.get(f"node_modules/{name}")
        if not isinstance(row, dict) or row.get("version") != version:
            problems.append(f"lock is missing exact {name}@{version}")
            continue
        if not isinstance(row.get("integrity"), str) or not row["integrity"].startswith("sha512-"):
            problems.append(f"lock has no sha512 integrity for {name}@{version}")
    return problems


def install_direct_acp(
    *,
    environ: Mapping[str, str] | None = None,
    platform: str = sys.platform,
    npm: str = "npm",
) -> Path:
    """Explicit download path. Uses only ``npm ci`` against the packaged lock."""
    problems = verify_packaged_lock()
    if problems:
        raise DirectAcpError("invalid packaged runtime lock: " + "; ".join(problems))
    destination = installed_runtime_path(environ)
    if destination.is_dir() and _installed_runtime_problems(destination) == []:
        return destination
    base = destination.parent
    if base.is_symlink() or destination.is_symlink():
        raise DirectAcpError(f"refusing symlinked runtime path: {destination}")
    ensure_owner_directory(base, platform=platform)
    staging = Path(tempfile.mkdtemp(prefix=".install-", dir=base))
    try:
        for name in RESOURCE_FILES:
            target = staging / name
            target.write_bytes(_resource_bytes(name))
            if platform != "win32":
                target.chmod(0o600)
        result = subprocess.run(
            [npm, "ci", "--ignore-scripts", "--omit=dev", "--no-audit", "--no-fund"],
            cwd=staging,
            env=dict(os.environ if environ is None else environ),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=600,
        )
        if result.returncode != 0:
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            raise DirectAcpError(f"npm ci failed ({result.returncode}): {detail}")
        runtime_tree_hash = _runtime_tree_hash(staging)
        atomic_write_text(
            staging / "agentteam-runtime.json",
            json.dumps(
                {
                    "runtime": RUNTIME_ID,
                    "lock_hash": runtime_lock_hash(),
                    "pins": EXPECTED_PINS,
                    "node_modules_sha256": runtime_tree_hash,
                },
                indent=2,
            )
            + "\n",
            platform=platform,
        )
        problems = _installed_runtime_problems(staging)
        if problems:
            raise DirectAcpError("installed runtime verification failed: " + "; ".join(problems))
        if destination.exists():
            raise DirectAcpError(f"invalid existing runtime must be moved aside: {destination}")
        os.replace(staging, destination)
        return destination
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _installed_runtime_problems(path: Path) -> list[str]:
    problems: list[str] = []
    if not path.is_dir() or path.is_symlink():
        return ["runtime directory is missing or unsafe"]
    for name in RESOURCE_FILES:
        resource = path / name
        if not resource.is_file() or resource.is_symlink():
            problems.append(f"missing or unsafe {name}")
        elif resource.read_bytes() != _resource_bytes(name):
            problems.append(f"packaged resource mismatch: {name}")
    for name, version in EXPECTED_PINS.items():
        package_file = path / "node_modules" / name / "package.json"
        if not package_file.is_file() or package_file.is_symlink():
            problems.append(f"installed package missing: {name}@{version}")
            continue
        try:
            observed = json.loads(package_file.read_bytes()).get("version")
        except (OSError, json.JSONDecodeError):
            observed = None
        if observed != version:
            problems.append(
                f"installed version mismatch: {name} expected {version}, got {observed}"
            )
    marker = path / "agentteam-runtime.json"
    if not marker.is_file() or marker.is_symlink():
        problems.append("AgentTeam runtime marker is missing")
    else:
        try:
            marker_payload = json.loads(marker.read_bytes())
        except (OSError, json.JSONDecodeError):
            marker_payload = None
        if not isinstance(marker_payload, dict):
            problems.append("AgentTeam runtime marker is invalid")
        else:
            if marker_payload.get("runtime") != RUNTIME_ID:
                problems.append("AgentTeam runtime marker id mismatch")
            if marker_payload.get("lock_hash") != runtime_lock_hash():
                problems.append("AgentTeam runtime marker lock mismatch")
            if marker_payload.get("pins") != EXPECTED_PINS:
                problems.append("AgentTeam runtime marker pins mismatch")
            try:
                current_tree_hash = _runtime_tree_hash(path)
            except DirectAcpError as error:
                problems.append(str(error))
            else:
                if marker_payload.get("node_modules_sha256") != current_tree_hash:
                    problems.append("installed runtime tree hash mismatch")
    return problems


def installed_runtime_problems(path: Path) -> list[str]:
    """Public read-only integrity check used before constructing a provider."""
    return _installed_runtime_problems(Path(path))


def _parse_node_version(text: str) -> tuple[int, int, int] | None:
    value = text.strip().removeprefix("v")
    parts = value.split(".")
    if len(parts) < 3:
        return None
    try:
        return int(parts[0]), int(parts[1]), int(parts[2].split("-", 1)[0])
    except ValueError:
        return None


def _direct_capabilities(
    *,
    qualified: bool,
    live_attested: bool = False,
    platform: str = sys.platform,
) -> ProviderCapabilitiesV1:
    staged = CapabilityLevel.SUPPORTED if qualified else CapabilityLevel.UNKNOWN
    persistent = (
        CapabilityLevel.SUPPORTED if qualified and live_attested else CapabilityLevel.UNKNOWN
    )
    return ProviderCapabilitiesV1(
        schema_version=1,
        kind="provider-capabilities",
        provider=RUNTIME_ID,
        version=EXPECTED_PINS["acpx"],
        persistent_turns=persistent,
        recovery=persistent,
        permission_events=staged,
        workspace_enforcement=staged,
        tool_filtering=CapabilityLevel.UNKNOWN,
        native_spawn_control=(
            CapabilityLevel.UNSUPPORTED if qualified else CapabilityLevel.UNKNOWN
        ),
        process_stop_observability=(staged if platform != "win32" else CapabilityLevel.UNKNOWN),
        local_state_deletion=staged,
        provider_history_deletion=CapabilityLevel.UNKNOWN,
    )


def qualification_path(
    harness: HarnessId,
    environ: Mapping[str, str] | None = None,
) -> Path:
    return default_runtime_base(environ) / "qualifications" / f"{harness.value}.json"


def live_attestation_path(
    harness: HarnessId,
    environ: Mapping[str, str] | None = None,
) -> Path:
    return default_runtime_base(environ) / "live-attestations" / f"{harness.value}.json"


def write_direct_acp_live_attestation(
    target: DirectAcpQualificationTarget,
    attestation: ProviderLiveAttestationV1,
    *,
    environ: Mapping[str, str] | None = None,
    platform: str = sys.platform,
) -> Path:
    expected = (
        attestation.provider == RUNTIME_ID
        and attestation.harness == target.harness
        and attestation.target_fingerprint == target.fingerprint
        and attestation.runtime_lock_hash == runtime_lock_hash()
        and attestation.native_version == target.native_version
        and attestation.platform == platform
    )
    if not expected:
        raise DirectAcpError("live attestation does not match the exact qualification target")
    path = live_attestation_path(target.harness, environ)
    ensure_owner_directory(path.parent, platform=platform)
    atomic_write_text(
        path,
        json.dumps(
            {
                "format": LIVE_ATTESTATION_FORMAT,
                "attestation": attestation.model_dump(mode="json"),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        platform=platform,
    )
    return path


def load_direct_acp_live_attestation(
    target: DirectAcpQualificationTarget,
    *,
    environ: Mapping[str, str] | None = None,
    platform: str = sys.platform,
) -> tuple[ProviderLiveAttestationV1 | None, list[str]]:
    path = live_attestation_path(target.harness, environ)
    if not path.is_file() or path.is_symlink():
        return None, [f"no safe live attestation for {target.harness.value}"]
    if platform != "win32":
        try:
            unsafe_mode = bool(path.stat().st_mode & 0o077)
        except OSError as error:
            return None, [f"cannot inspect live attestation: {error}"]
        if unsafe_mode:
            return None, [f"live attestation is not owner-only: {target.harness.value}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, [f"invalid live attestation: {error}"]
    problems: list[str] = []
    if not isinstance(payload, dict) or payload.get("format") != LIVE_ATTESTATION_FORMAT:
        problems.append("live attestation format is invalid")
    try:
        attestation = ProviderLiveAttestationV1.model_validate(
            payload.get("attestation") if isinstance(payload, dict) else None
        )
    except ValueError as error:
        return None, [*problems, f"invalid live attestation record: {error}"]
    expected = {
        "provider": RUNTIME_ID,
        "harness": target.harness,
        "target_fingerprint": target.fingerprint,
        "runtime_lock_hash": runtime_lock_hash(),
        "native_version": target.native_version,
        "platform": platform,
    }
    problems.extend(
        f"live attestation {name} is stale or mismatched"
        for name, value in expected.items()
        if getattr(attestation, name) != value
    )
    if attestation.status != "pass":
        problems.append(f"live attestation status is {attestation.status}")
    if not problems:
        problems.extend(
            _live_attestation_evidence_problems(
                attestation,
                environ=environ,
                platform=platform,
            )
        )
    return (attestation if not problems else None), problems


def _live_attestation_evidence_problems(
    attestation: ProviderLiveAttestationV1,
    *,
    environ: Mapping[str, str] | None,
    platform: str,
) -> list[str]:
    from agentteam.interactive.archive import InteractiveArchive, InteractiveArchiveError

    runs_root = default_runtime_base(environ).parents[1] / "runs"
    problems: list[str] = []
    for evidence in attestation.evidence:
        root = runs_root / evidence.run_id
        manifest = root / "manifest.sha256.json"
        if (
            root.is_symlink()
            or not root.is_dir()
            or manifest.is_symlink()
            or not manifest.is_file()
        ):
            problems.append(f"live evidence {evidence.run_id} is missing or unsafe")
            continue
        try:
            archive_problems = InteractiveArchive(root, platform=platform).verify_manifest()
            manifest_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()
        except (OSError, ValueError, InteractiveArchiveError) as error:
            problems.append(f"live evidence {evidence.run_id} is invalid: {type(error).__name__}")
            continue
        if archive_problems:
            problems.append(f"live evidence {evidence.run_id} manifest does not verify")
        if manifest_hash != evidence.manifest_sha256:
            problems.append(f"live evidence {evidence.run_id} manifest hash is mismatched")
        if platform != "win32":
            try:
                unsafe_mode = bool(root.stat().st_mode & 0o077) or any(
                    path.stat().st_mode & 0o077 for path in root.rglob("*")
                )
            except OSError:
                unsafe_mode = True
            if unsafe_mode:
                problems.append(f"live evidence {evidence.run_id} is not owner-only")
    return problems


def _write_direct_acp_qualification(
    target: DirectAcpQualificationTarget,
    report: ProviderDoctorV1,
    *,
    empty_reconnect: Literal["strict-resume", "fresh-recreate"] | None,
    environ: Mapping[str, str] | None,
    platform: str,
) -> None:
    payload = {
        "format": QUALIFICATION_FORMAT,
        "harness": target.harness.value,
        "fingerprint": target.fingerprint,
        "runtime_lock_hash": runtime_lock_hash(),
        "platform": platform,
        "native_version": target.native_version,
        "empty_reconnect": empty_reconnect,
        "report": report.model_dump(mode="json"),
    }
    atomic_write_text(
        qualification_path(target.harness, environ),
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        platform=platform,
    )


def load_direct_acp_qualification(
    target: DirectAcpQualificationTarget,
    *,
    environ: Mapping[str, str] | None = None,
    platform: str = sys.platform,
) -> tuple[ProviderDoctorV1 | None, list[str]]:
    """Load only a current, exact-profile, zero-call qualification record."""
    path = qualification_path(target.harness, environ)
    if not path.is_file() or path.is_symlink():
        return None, [f"no safe qualification record for {target.harness.value}"]
    if platform != "win32":
        try:
            unsafe_mode = bool(path.stat().st_mode & 0o077)
        except OSError as error:
            return None, [f"cannot inspect qualification record: {error}"]
        if unsafe_mode:
            return None, [f"qualification record is not owner-only: {target.harness.value}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, [f"invalid qualification record: {error}"]
    expected = {
        "format": QUALIFICATION_FORMAT,
        "harness": target.harness.value,
        "fingerprint": target.fingerprint,
        "runtime_lock_hash": runtime_lock_hash(),
        "platform": platform,
        "native_version": target.native_version,
    }
    problems = [
        f"qualification {name} is stale or mismatched"
        for name, value in expected.items()
        if payload.get(name) != value
    ]
    try:
        report = ProviderDoctorV1.model_validate(payload.get("report"))
    except ValueError as error:
        return None, [*problems, f"invalid qualification report: {error}"]
    if report.provider != RUNTIME_ID or report.model_calls != 0:
        problems.append("qualification report identity is invalid")
    if report.status != "pass":
        problems.append(f"qualification status is {report.status}")
    disposition = payload.get("empty_reconnect")
    if report.status == "pass" and disposition not in {
        "strict-resume",
        "fresh-recreate",
    }:
        problems.append("qualification empty reconnect disposition is invalid")
    if report.status != "pass" and disposition is not None:
        problems.append("failed qualification cannot claim an empty reconnect disposition")
    if report.capabilities.provider != RUNTIME_ID:
        problems.append("qualification capability identity is invalid")
    if report.status == "pass" and report.capabilities != _direct_capabilities(
        qualified=True,
        platform=platform,
    ):
        problems.append("qualification staged capabilities are invalid")
    return (report if not problems else None), problems


async def _qualify_direct_acp_target(
    target: DirectAcpQualificationTarget,
    *,
    node: str,
) -> DirectAcpQualificationResult:
    if target.runtime_path.is_symlink() or not target.runtime_path.is_dir():
        raise DirectAcpError("qualification runtime path is missing or unsafe")
    temporary_root = Path(tempfile.mkdtemp(prefix="agentteam-direct-acp-doctor-"))
    if sys.platform != "win32":
        temporary_root.chmod(0o700)
    workspace = temporary_root / "workspace"
    state_dir = temporary_root / "state"
    workspace.mkdir(mode=0o700)
    active_clients: list[_BridgeClient] = []

    async def start_client() -> _BridgeClient:
        client = _BridgeClient(
            argv=(node, str(target.runtime_path / "bridge.mjs")),
            cwd=workspace,
            environment=target.environment,
        )
        await asyncio.wait_for(client.start(), timeout=QUALIFICATION_TIMEOUT_SECONDS)
        active_clients.append(client)
        await asyncio.wait_for(
            client.request(
                "initialize",
                state_dir=str(state_dir),
                cwd=str(workspace),
                agents={target.harness.value: list(target.command)},
            ),
            timeout=QUALIFICATION_TIMEOUT_SECONDS,
        )
        return client

    async def stop_client(client: _BridgeClient) -> None:
        try:
            cleanup = await client.stop()
        finally:
            if client in active_clients:
                active_clients.remove(client)
        if cleanup is not CleanupFact.CONFIRMED:
            raise DirectAcpError("ACP qualification bridge cleanup was not confirmed")

    async def open_session(
        client: _BridgeClient,
        *,
        session_key: str,
        resume_session_id: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, object] = {
            "session_key": session_key,
            "agent": target.harness.value,
            "cwd": str(workspace),
        }
        if resume_session_id is not None:
            payload["resume_session_id"] = resume_session_id
        return await asyncio.wait_for(
            client.request("open_member", **payload),
            timeout=QUALIFICATION_TIMEOUT_SECONDS,
        )

    inspection: dict[str, Any]
    disposition: Literal["strict-resume", "fresh-recreate"]
    try:
        first = await start_client()
        fresh = await open_session(first, session_key="qualification-fresh")
        expected = fresh.get("opaque_session_id")
        if not isinstance(expected, str) or not expected:
            raise DirectAcpError("fresh ACP session has no stable backend session id")
        await asyncio.wait_for(
            first.request(
                "suspend_member",
                session_key="qualification-fresh",
                reason="AgentTeam no-call qualification restart",
            ),
            timeout=QUALIFICATION_TIMEOUT_SECONDS,
        )
        await stop_client(first)

        resumed_client = await start_client()
        try:
            resumed = await open_session(
                resumed_client,
                session_key="qualification-resume",
                resume_session_id=expected,
            )
        except DirectAcpError:
            await stop_client(resumed_client)
            if state_dir.is_symlink():
                raise DirectAcpError("ACP qualification state directory is unsafe") from None
            try:
                shutil.rmtree(state_dir)
            except FileNotFoundError:
                pass
            except OSError as error:
                raise DirectAcpError(
                    f"cannot retire empty ACP qualification state: {error}"
                ) from None
            replacement_client = await start_client()
            replacement = await open_session(
                replacement_client,
                session_key="qualification-replacement",
            )
            replacement_id = replacement.get("opaque_session_id")
            if not isinstance(replacement_id, str) or not replacement_id:
                raise DirectAcpError(
                    "replacement ACP session has no stable backend session id"
                ) from None
            inspection = await asyncio.wait_for(
                replacement_client.request(
                    "inspect_member", session_key="qualification-replacement"
                ),
                timeout=QUALIFICATION_TIMEOUT_SECONDS,
            )
            await asyncio.wait_for(
                replacement_client.request(
                    "close_member",
                    session_key="qualification-replacement",
                    reason="AgentTeam no-call qualification close",
                ),
                timeout=QUALIFICATION_TIMEOUT_SECONDS,
            )
            await stop_client(replacement_client)
            disposition = "fresh-recreate"
        else:
            if resumed.get("opaque_session_id") != expected:
                raise DirectAcpError(
                    "strict ACP resume/load returned a different backend session id"
                )
            inspection = await asyncio.wait_for(
                resumed_client.request("inspect_member", session_key="qualification-resume"),
                timeout=QUALIFICATION_TIMEOUT_SECONDS,
            )
            await asyncio.wait_for(
                resumed_client.request(
                    "close_member",
                    session_key="qualification-resume",
                    reason="AgentTeam no-call qualification close",
                ),
                timeout=QUALIFICATION_TIMEOUT_SECONDS,
            )
            await stop_client(resumed_client)
            disposition = "strict-resume"

        if not inspection.get("status"):
            raise DirectAcpError("ACP no-call status proof is incomplete")
        controls = inspection.get("runtime_controls")
        capabilities = inspection.get("agent_capabilities")
        if not isinstance(controls, list) or not all(isinstance(value, str) for value in controls):
            raise DirectAcpError("ACP runtime controls are malformed")
        if not isinstance(capabilities, list) or not all(
            isinstance(value, str) for value in capabilities
        ):
            raise DirectAcpError("ACP agent capabilities are malformed")
        return DirectAcpQualificationResult(
            runtime_controls=tuple(sorted(set(controls))),
            agent_capabilities=tuple(sorted(set(capabilities))),
            empty_reconnect=disposition,
        )
    finally:
        cleanup_failed = False
        for client in tuple(active_clients):
            try:
                cleanup = await client.stop()
            except Exception:
                cleanup = CleanupFact.FAILED
            cleanup_failed = cleanup_failed or cleanup is not CleanupFact.CONFIRMED
        shutil.rmtree(temporary_root, ignore_errors=True)
        if cleanup_failed:
            raise DirectAcpError("ACP qualification bridge cleanup was not confirmed")


async def doctor_direct_acp(
    *,
    environ: Mapping[str, str] | None = None,
    clock: Callable[[], datetime] | None = None,
    node: str = "node",
    platform: str = sys.platform,
    targets: tuple[DirectAcpQualificationTarget, ...] = (),
    setup_problems: Mapping[str, str] | None = None,
    runtime_path: Path | None = None,
) -> ProviderDoctorV1:
    checks: list[DoctorCheckV1] = []
    checked_at = (clock or (lambda: datetime.now(tz=UTC)))()
    lock_problems = verify_packaged_lock()
    checks.append(
        DoctorCheckV1(
            name="packaged-lock",
            status="pass" if not lock_problems else "fail",
            detail="; ".join(lock_problems) or None,
        )
    )
    env = os.environ if environ is None else environ
    node_path = shutil.which(node, path=env.get("PATH"))
    node_ok = False
    if node_path is None:
        checks.append(DoctorCheckV1(name="node-version", status="fail", detail="node not found"))
    else:
        try:
            node_result = subprocess.run(
                [node_path, "--version"],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                check=False,
                timeout=20,
            )
        except (OSError, subprocess.TimeoutExpired):
            node_result = subprocess.CompletedProcess([node_path, "--version"], 1, b"", b"")
        version = _parse_node_version(node_result.stdout.decode("utf-8", errors="replace"))
        node_ok = (
            node_result.returncode == 0 and version is not None and version >= MIN_NODE_VERSION
        )
        checks.append(
            DoctorCheckV1(
                name="node-version",
                status="pass" if node_ok else "fail",
                detail=node_result.stdout.decode("utf-8", errors="replace").strip() or None,
            )
        )
    resolved_runtime_path = (
        installed_runtime_path(environ) if runtime_path is None else Path(runtime_path)
    )
    install_problems = _installed_runtime_problems(resolved_runtime_path)
    installed = not install_problems
    corrupt_install = resolved_runtime_path.exists() and not installed
    checks.append(
        DoctorCheckV1(
            name="runtime-install",
            status=("pass" if installed else ("fail" if corrupt_install else "unsupported")),
            detail="; ".join(install_problems) or None,
        )
    )
    base_failed = bool(lock_problems) or not node_ok or corrupt_install
    base_ready = not base_failed and installed
    base_checks = tuple(checks)
    target_reports: list[ProviderDoctorV1] = []
    if base_ready:
        for target in targets:
            empty_reconnect: Literal["strict-resume", "fresh-recreate"] | None = None
            target_checks = [
                DoctorCheckV1(
                    name=f"{target.harness.value}-agent-version",
                    status="pass",
                    detail=target.native_version,
                )
            ]
            try:
                if target.runtime_path.resolve() != resolved_runtime_path.resolve():
                    raise DirectAcpError("qualification target runtime does not match install")
                qualification_result = await _qualify_direct_acp_target(
                    target, node=node_path or node
                )
            except (DirectAcpError, OSError, TimeoutError) as error:
                target_checks.append(
                    DoctorCheckV1(
                        name=f"{target.harness.value}-acp-lifecycle",
                        status="unsupported",
                        detail=str(error),
                    )
                )
                target_status: Literal["pass", "fail", "unsupported"] = "unsupported"
                target_capabilities = _direct_capabilities(
                    qualified=False,
                    platform=platform,
                )
            else:
                empty_reconnect = qualification_result.empty_reconnect
                details = [
                    *(f"control={value}" for value in qualification_result.runtime_controls),
                    *(f"agent={value}" for value in qualification_result.agent_capabilities),
                ]
                target_checks.extend(
                    [
                        DoctorCheckV1(
                            name=f"{target.harness.value}-acp-lifecycle",
                            status="pass",
                            detail=(
                                "initialize/new/"
                                f"{qualification_result.empty_reconnect}/status/close; "
                                "post-turn-resume=unproven"
                            ),
                        ),
                        DoctorCheckV1(
                            name=f"{target.harness.value}-declared-capabilities",
                            status="pass",
                            detail=", ".join(details) or "none declared",
                        ),
                    ]
                )
                target_status = "pass"
                target_capabilities = _direct_capabilities(
                    qualified=True,
                    platform=platform,
                )
            target_report = ProviderDoctorV1(
                schema_version=1,
                kind="provider-doctor",
                provider=RUNTIME_ID,
                checked_at=checked_at,
                status=target_status,
                capabilities=target_capabilities,
                checks=[*base_checks, *target_checks],
                model_calls=0,
            )
            _write_direct_acp_qualification(
                target,
                target_report,
                empty_reconnect=empty_reconnect,
                environ=environ,
                platform=platform,
            )
            target_reports.append(target_report)
            checks.extend(target_checks)
        for name, detail in sorted((setup_problems or {}).items()):
            checks.append(DoctorCheckV1(name=name, status="unsupported", detail=detail))
        if not targets and not setup_problems:
            checks.append(
                DoctorCheckV1(
                    name="qualification-targets",
                    status="unsupported",
                    detail="no current harness profile was selected",
                )
            )
    all_targets_pass = bool(target_reports) and all(
        report.status == "pass" for report in target_reports
    )
    qualified = base_ready and all_targets_pass and not setup_problems
    status: Literal["pass", "fail", "unsupported"] = (
        "fail" if base_failed else ("pass" if qualified else "unsupported")
    )
    return ProviderDoctorV1(
        schema_version=1,
        kind="provider-doctor",
        provider=RUNTIME_ID,
        checked_at=checked_at,
        status=status,
        capabilities=_direct_capabilities(qualified=qualified, platform=platform),
        checks=checks,
        model_calls=0,
    )


class _BridgeClient:
    def __init__(
        self,
        *,
        argv: tuple[str, ...],
        cwd: Path,
        environment: Mapping[str, str],
    ) -> None:
        self.argv = argv
        self.cwd = cwd
        self.environment = environment
        self.process: asyncio.subprocess.Process | None = None
        self.pending: dict[str, asyncio.Queue[dict[str, Any] | BaseException]] = {}
        self.reader_task: asyncio.Task[None] | None = None
        self.stderr_task: asyncio.Task[bytes] | None = None
        self.sequence = 0

    async def start(self) -> None:
        if self.process is not None:
            raise DirectAcpError("bridge already started")
        self.process = await asyncio.create_subprocess_exec(
            *self.argv,
            cwd=self.cwd,
            env=dict(self.environment),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=sys.platform != "win32",
            creationflags=(
                subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
                if sys.platform == "win32"
                else 0
            ),
        )
        self.reader_task = asyncio.create_task(self._read_stdout())
        assert self.process.stderr is not None
        self.stderr_task = asyncio.create_task(self.process.stderr.read())

    async def stream(self, command: str, **payload: Any) -> AsyncIterator[dict[str, Any]]:
        if self.process is None or self.process.stdin is None:
            raise DirectAcpError("bridge is not running")
        self.sequence += 1
        command_id = f"command-{self.sequence}"
        queue: asyncio.Queue[dict[str, Any] | BaseException] = asyncio.Queue()
        self.pending[command_id] = queue
        frame = {
            "protocol_version": PROTOCOL_VERSION,
            "id": command_id,
            "command": command,
            **payload,
        }
        self.process.stdin.write((json.dumps(frame, separators=(",", ":")) + "\n").encode())
        await self.process.stdin.drain()
        try:
            while True:
                message = await queue.get()
                if isinstance(message, BaseException):
                    raise message
                yield message
                if message.get("type") in {"response", "turn_result"}:
                    return
        finally:
            self.pending.pop(command_id, None)

    async def request(self, command: str, **payload: Any) -> dict[str, Any]:
        last: dict[str, Any] | None = None
        async for message in self.stream(command, **payload):
            last = message
        if last is None or not last.get("ok", last.get("type") == "turn_result"):
            detail = None if last is None else last.get("error")
            raise DirectAcpError(f"bridge {command} failed: {detail or 'no terminal response'}")
        return last

    async def stop(self) -> CleanupFact:
        process = self.process
        if process is None:
            return CleanupFact.NOT_APPLICABLE
        if process.returncode is None:
            with contextlib.suppress(DirectAcpError, BrokenPipeError):
                await asyncio.wait_for(self.request("shutdown"), timeout=2)
            if process.stdin is not None:
                process.stdin.close()
            try:
                await asyncio.wait_for(process.wait(), timeout=2)
            except TimeoutError:
                if sys.platform == "win32":
                    process.kill()
                else:
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGKILL)
                await process.wait()
        if self.reader_task is not None:
            await asyncio.gather(self.reader_task, return_exceptions=True)
        if self.stderr_task is not None:
            await asyncio.gather(self.stderr_task, return_exceptions=True)
        self.process = None
        return CleanupFact.CONFIRMED if process.returncode is not None else CleanupFact.FAILED

    async def _read_stdout(self) -> None:
        assert self.process is not None and self.process.stdout is not None
        try:
            while line := await self.process.stdout.readline():
                try:
                    message = json.loads(line)
                except json.JSONDecodeError as error:
                    raise DirectAcpError(f"bridge emitted malformed JSON: {error}") from None
                if message.get("protocol_version") != PROTOCOL_VERSION:
                    raise DirectAcpError("bridge protocol version mismatch")
                command_id = message.get("id")
                queue = self.pending.get(command_id)
                if queue is not None:
                    await queue.put(cast(dict[str, Any], message))
            if self.pending:
                raise DirectAcpError("bridge closed stdout with commands pending")
        except BaseException as error:
            for queue in tuple(self.pending.values()):
                await queue.put(error)


def _provider_event_from_bridge(value: object) -> ProviderEvent:
    if not isinstance(value, dict):
        return ProviderEvent(event="provider-event")
    event_name = value.get("type")
    text = value.get("text")
    data: dict[str, str] = {}
    for key in (
        "stream",
        "tag",
        "messageId",
        "toolCallId",
        "status",
        "title",
        "kind",
    ):
        observed = value.get(key)
        if isinstance(observed, (str, int, float, bool)):
            data[key] = str(observed)
    for key in ("rawInput", "rawOutput", "locations", "content", "meta"):
        if key in value:
            try:
                data[key] = json.dumps(
                    value[key],
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
            except (TypeError, ValueError):
                continue
    raw_input = value.get("rawInput")
    candidate: object = raw_input
    if isinstance(raw_input, dict):
        candidate = raw_input.get("control_request", raw_input)
    if isinstance(candidate, str):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict) and parsed.get("kind") == "control-request":
            data["control_request"] = candidate
    elif isinstance(candidate, dict) and candidate.get("kind") == "control-request":
        data["control_request"] = json.dumps(
            candidate,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    return ProviderEvent(
        event=event_name if isinstance(event_name, str) else "provider-event",
        text=text if isinstance(text, str) else None,
        data=data,
    )


class _BridgeTurn(ActiveTurn):
    def __init__(
        self,
        *,
        client: _BridgeClient,
        session_key: str,
        spec: TurnSpec,
    ) -> None:
        self.request_id = spec.request_id
        self.client = client
        self.session_key = session_key
        self.spec = spec
        self.events: asyncio.Queue[ProviderEvent | None] = asyncio.Queue()
        self.prompt_started = False
        self.terminal: asyncio.Future[ProviderTurnResult] = (
            asyncio.get_running_loop().create_future()
        )
        self.task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        terminal: ProviderTurnResult | None = None
        try:
            async for message in self.client.stream(
                "start_turn",
                session_key=self.session_key,
                request_id=self.spec.request_id,
                text=self.spec.text,
                timeout_ms=(
                    None if self.spec.timeout_seconds is None else self.spec.timeout_seconds * 1000
                ),
            ):
                if message.get("type") == "turn_event":
                    await self.events.put(_provider_event_from_bridge(message.get("event")))
                elif message.get("type") == "prompt_started":
                    self.prompt_started = True
                    await self.events.put(ProviderEvent(event="prompt-started"))
                elif message.get("type") == "permission_request":
                    await self.events.put(
                        ProviderEvent(
                            event="permission-request",
                            data={
                                key: str(message[key])
                                for key in (
                                    "permission_id",
                                    "session_id",
                                    "tool_kind",
                                    "tool_name",
                                    "tool_title",
                                    "tool_input",
                                )
                                if message.get(key) is not None
                            },
                        )
                    )
                elif message.get("type") == "turn_result":
                    result = message.get("result")
                    if not isinstance(result, dict):
                        raise DirectAcpError("bridge turn result is not an object")
                    status = ProviderTurnStatus(str(result.get("status")))
                    error = result.get("error")
                    terminal = ProviderTurnResult(
                        status=status,
                        stop_reason=cast(str | None, result.get("stopReason")),
                        error=(
                            cast(str, error.get("message"))
                            if isinstance(error, dict) and isinstance(error.get("message"), str)
                            else None
                        ),
                    )
            if terminal is None:
                raise DirectAcpError("bridge turn ended without a result")
            self.terminal.set_result(terminal)
        except BaseException as error:
            self.terminal.set_result(
                ProviderTurnResult(status=ProviderTurnStatus.FAILED, error=str(error))
            )
        finally:
            await self.events.put(None)

    async def __aiter__(self) -> AsyncIterator[ProviderEvent]:
        while True:
            event = await self.events.get()
            if event is None:
                return
            yield event

    async def result(self) -> ProviderTurnResult:
        return await self.terminal

    async def cancel(self, reason: str) -> CancelDisposition:
        if self.terminal.done():
            return CancelDisposition.TERMINAL
        await self.client.request("cancel_turn", session_key=self.session_key, reason=reason)
        return CancelDisposition.RUNNING if self.prompt_started else CancelDisposition.QUEUED

    async def respond_permission(self, permission_id: str, outcome: PermissionOutcome) -> None:
        if self.terminal.done():
            raise DirectAcpError("cannot answer a permission request after turn termination")
        await self.client.request(
            "permission_response",
            permission_id=permission_id,
            outcome=outcome.value,
        )


class DirectAcpProvider:
    """One bridge process/session owner per Member; no ACP wire code lives here."""

    def __init__(
        self,
        *,
        runtime_path: Path,
        environment: Mapping[str, str] | None = None,
        node: str = "node",
        bridge_path: Path | None = None,
        clock: Callable[[], datetime] | None = None,
        capabilities: ProviderCapabilitiesV1 | None = None,
        doctor_report: ProviderDoctorV1 | None = None,
        platform: str = sys.platform,
    ) -> None:
        self.runtime_path = Path(runtime_path)
        self.environment = dict(os.environ if environment is None else environment)
        self.node = node
        self.bridge_path = bridge_path or self.runtime_path / "bridge.mjs"
        self.clock = clock
        self.platform = platform
        self.capabilities = capabilities or _direct_capabilities(
            qualified=False,
            platform=platform,
        )
        self.doctor_report = doctor_report
        self.clients: dict[str, _BridgeClient] = {}
        self.sessions: dict[str, ProviderSession] = {}
        self.turns: dict[str, _BridgeTurn] = {}
        self.run_state_dirs: dict[str, set[Path]] = {}
        self.unresolved_closes: set[tuple[str, str]] = set()
        self.background_tasks: set[asyncio.Task[None]] = set()

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider_id=RUNTIME_ID,
            version=EXPECTED_PINS["acpx"],
            capabilities=self.capabilities,
        )

    async def doctor(self) -> ProviderDoctorV1:
        if self.doctor_report is not None:
            return self.doctor_report
        return await doctor_direct_acp(
            environ=self.environment,
            clock=self.clock,
            node=self.node,
            platform=self.platform,
            runtime_path=self.runtime_path,
        )

    async def open_member(self, spec: OpenMemberSpec) -> ProviderSession:
        if spec.session_id in self.sessions:
            raise DirectAcpError(f"session already exists: {spec.session_id}")
        if spec.state_dir.exists():
            if (
                spec.resume_session_ref is None
                or not spec.state_dir.is_dir()
                or spec.state_dir.is_symlink()
            ):
                raise DirectAcpError(f"fresh session state already exists: {spec.state_dir}")
        else:
            if spec.resume_session_ref is not None:
                raise DirectAcpError("resume state is missing")
            spec.state_dir.mkdir(parents=True)
        environment = dict(self.environment)
        environment.update(spec.environment)
        if spec.config_home_variable is not None and spec.config_home is not None:
            environment[spec.config_home_variable] = str(spec.config_home)
        client = _BridgeClient(
            argv=(self.node, str(self.bridge_path)),
            cwd=spec.workspace,
            environment=environment,
        )
        agent = spec.harness.value
        command = list(spec.executable)
        backend_opened = False
        try:
            await client.start()
            await client.request(
                "initialize",
                state_dir=str(spec.state_dir),
                cwd=str(spec.workspace),
                agents={agent: command},
            )
            session_options: dict[str, object] = {}
            if spec.system_prompt is not None:
                session_options["systemPrompt"] = {"append": spec.system_prompt}
            if spec.model is not None:
                session_options["model"] = spec.model
            if spec.allowed_tools:
                session_options["allowedTools"] = list(spec.allowed_tools)
            if spec.max_turns is not None:
                session_options["maxTurns"] = spec.max_turns
            response = await client.request(
                "open_member",
                session_key=spec.session_id,
                agent=agent,
                cwd=str(spec.workspace),
                resume_session_id=spec.resume_session_ref,
                session_options=session_options or None,
            )
            backend_opened = True
            opaque = response.get("opaque_session_id")
            if not isinstance(opaque, str) or not response.get("continuity_verified"):
                raise DirectAcpError("provider did not prove a stable opaque session id")
            if spec.resume_session_ref is not None:
                suspension_marker = spec.state_dir / SUSPENSION_MARKER
                if suspension_marker.is_symlink():
                    raise DirectAcpError("suspension marker is unsafe")
                suspension_marker.unlink(missing_ok=True)
        except BaseException:
            if backend_opened:
                with contextlib.suppress(Exception):
                    await client.request(
                        "close_member",
                        session_key=spec.session_id,
                        reason="AgentTeam failed Member open",
                    )
            await client.stop()
            if spec.resume_session_ref is None:
                shutil.rmtree(spec.state_dir, ignore_errors=True)
            raise
        session = ProviderSession(
            provider_id=RUNTIME_ID,
            run_id=spec.run_id,
            member=spec.member,
            session_id=spec.session_id,
            generation=spec.generation,
            provider_session_ref=opaque,
            workspace=spec.workspace.resolve(),
            state_dir=spec.state_dir.resolve(),
            continuity_verified=True,
            metadata={"session_key": spec.session_id},
        )
        self.clients[session.session_id] = client
        self.sessions[session.session_id] = session
        self.run_state_dirs.setdefault(spec.run_id, set()).add(session.state_dir)
        return session

    async def start_turn(self, session: ProviderSession, spec: TurnSpec) -> ActiveTurn:
        client = self._client(session)
        existing = self.turns.get(session.session_id)
        if existing is not None and existing.terminal.done():
            self.turns.pop(session.session_id, None)
        elif existing is not None:
            raise DirectAcpError(f"turn already active for {session.session_id}")
        turn = _BridgeTurn(client=client, session_key=session.session_id, spec=spec)
        self.turns[session.session_id] = turn

        async def clear_when_done() -> None:
            await turn.result()
            self.turns.pop(session.session_id, None)

        task = asyncio.create_task(clear_when_done())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        return turn

    async def cancel_turn(self, session: ProviderSession, reason: str) -> CancelDisposition:
        self._client(session)
        turn = self.turns.get(session.session_id)
        if turn is None:
            return CancelDisposition.TERMINAL
        return await turn.cancel(reason)

    async def verify_continuity(self, session: ProviderSession) -> bool:
        client = self._client(session)
        try:
            response = await client.request(
                "verify_continuity",
                session_key=session.session_id,
                opaque_session_id=session.provider_session_ref,
            )
        except DirectAcpError:
            return False
        return bool(response.get("continuity_verified"))

    async def suspend_member(self, session: ProviderSession, reason: str) -> ProviderSuspendFacts:
        client = self._client(session)
        active = self.turns.get(session.session_id)
        if active is not None and not active.terminal.done():
            return ProviderSuspendFacts(
                process=CleanupFact.FAILED,
                local_state_retained=False,
            )
        logical = True
        try:
            await client.request(
                "suspend_member",
                session_key=session.session_id,
                reason=reason,
            )
        except DirectAcpError:
            logical = False
        try:
            process = await client.stop()
        except Exception:
            process = CleanupFact.FAILED
        if self.background_tasks:
            await asyncio.gather(*tuple(self.background_tasks), return_exceptions=True)
        self.clients.pop(session.session_id, None)
        self.sessions.pop(session.session_id, None)
        self.turns.pop(session.session_id, None)
        retained = (
            logical
            and process in {CleanupFact.CONFIRMED, CleanupFact.NOT_APPLICABLE}
            and session.state_dir.is_dir()
            and not session.state_dir.is_symlink()
        )
        if retained:
            atomic_write_text(
                session.state_dir / SUSPENSION_MARKER,
                json.dumps(
                    {
                        "format": 1,
                        "provider": RUNTIME_ID,
                        "run_id": session.run_id,
                        "member": session.member,
                        "session_id": session.session_id,
                        "generation": session.generation,
                        "provider_session_ref": session.provider_session_ref,
                        "process": process.value,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                platform=self.platform,
            )
        else:
            self.unresolved_closes.add((session.run_id, session.session_id))
        return ProviderSuspendFacts(process=process, local_state_retained=retained)

    async def retire_empty_member(self, spec: RetireEmptyMemberSpec) -> CloseFactsV1:
        unknown = CloseFactsV1(
            logical_session=CleanupFact.UNKNOWN,
            process=CleanupFact.UNKNOWN,
            local_state=CleanupFact.UNKNOWN,
            provider_history=CleanupFact.UNKNOWN,
        )
        if spec.session_id in self.sessions:
            return unknown
        state_dir = spec.state_dir
        marker = state_dir / SUSPENSION_MARKER
        if state_dir.is_symlink() or not state_dir.is_dir() or marker.is_symlink():
            return unknown
        if self.platform != "win32":
            try:
                if marker.stat().st_mode & 0o077:
                    return unknown
            except OSError:
                return unknown
        try:
            payload = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return unknown
        expected = {
            "format": 1,
            "provider": RUNTIME_ID,
            "run_id": spec.run_id,
            "member": spec.member,
            "session_id": spec.session_id,
            "generation": spec.generation,
            "provider_session_ref": spec.provider_session_ref,
        }
        if not isinstance(payload, dict) or any(payload.get(k) != v for k, v in expected.items()):
            return unknown
        try:
            process = CleanupFact(str(payload.get("process")))
        except ValueError:
            return unknown
        if process not in {CleanupFact.CONFIRMED, CleanupFact.NOT_APPLICABLE}:
            return unknown
        try:
            shutil.rmtree(state_dir)
        except OSError:
            return unknown.model_copy(
                update={"process": process, "local_state": CleanupFact.FAILED}
            )
        self.run_state_dirs.get(spec.run_id, set()).discard(state_dir.resolve(strict=False))
        self.unresolved_closes.discard((spec.run_id, spec.session_id))
        return CloseFactsV1(
            logical_session=CleanupFact.NOT_APPLICABLE,
            process=process,
            local_state=CleanupFact.CONFIRMED,
            provider_history=CleanupFact.UNKNOWN,
        )

    async def close_member(self, session: ProviderSession, reason: str) -> CloseFactsV1:
        client = self._client(session)
        logical = CleanupFact.CONFIRMED
        try:
            await client.request("close_member", session_key=session.session_id, reason=reason)
        except DirectAcpError:
            logical = CleanupFact.FAILED
        process = await client.stop()
        if self.background_tasks:
            await asyncio.gather(*tuple(self.background_tasks), return_exceptions=True)
        self.clients.pop(session.session_id, None)
        self.sessions.pop(session.session_id, None)
        self.turns.pop(session.session_id, None)
        process_terminal = process in {CleanupFact.CONFIRMED, CleanupFact.NOT_APPLICABLE}
        close_identity = (session.run_id, session.session_id)
        if logical is CleanupFact.CONFIRMED and process_terminal:
            self.unresolved_closes.discard(close_identity)
        else:
            self.unresolved_closes.add(close_identity)
        if logical is CleanupFact.CONFIRMED and process_terminal:
            try:
                shutil.rmtree(session.state_dir)
            except FileNotFoundError:
                local = CleanupFact.NOT_APPLICABLE
            except OSError:
                local = CleanupFact.FAILED
            else:
                local = CleanupFact.CONFIRMED
        else:
            local = CleanupFact.UNKNOWN
        return CloseFactsV1(
            logical_session=logical,
            process=process,
            local_state=local,
            provider_history=CleanupFact.UNKNOWN,
        )

    async def dispose_run(self, run_id: str) -> CleanupFact:
        if self.background_tasks:
            await asyncio.gather(*tuple(self.background_tasks), return_exceptions=True)
        if any(session.run_id == run_id for session in self.sessions.values()):
            return CleanupFact.FAILED
        if any(owner == run_id for owner, _session_id in self.unresolved_closes):
            return CleanupFact.FAILED
        result = CleanupFact.CONFIRMED
        for path in self.run_state_dirs.pop(run_id, set()):
            if path.exists():
                try:
                    shutil.rmtree(path)
                except OSError:
                    result = CleanupFact.FAILED
        return result

    def _client(self, session: ProviderSession) -> _BridgeClient:
        if self.sessions.get(session.session_id) != session:
            raise DirectAcpError(f"unknown or replaced session: {session.session_id}")
        return self.clients[session.session_id]
