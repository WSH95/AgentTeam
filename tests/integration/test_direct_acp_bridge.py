"""Python-side direct-ACP bridge correlation and strict-continuity contract."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest

from agentteam.domain.common import HarnessId
from agentteam.domain.interactive import CleanupFact
from agentteam.execution import direct_acp
from agentteam.execution.direct_acp import DirectAcpError, DirectAcpProvider
from agentteam.execution.protocol import OpenMemberSpec, ProviderTurnStatus, TurnSpec

FAKE_BRIDGE = r"""
import json
import sys

handles = {}
for line in sys.stdin:
    command = json.loads(line)
    base = {"protocol_version": 1, "id": command["id"]}
    name = command["command"]
    if name == "initialize":
        print(json.dumps({**base, "type": "response", "ok": True}), flush=True)
    elif name == "open_member":
        observed = "opaque-1"
        expected = command.get("resume_session_id")
        if expected is not None and expected != observed:
            print(json.dumps({**base, "type": "response", "ok": False,
                              "error": "strict continuity mismatch"}), flush=True)
        else:
            handles[command["session_key"]] = observed
            print(json.dumps({**base, "type": "response", "ok": True,
                              "opaque_session_id": observed,
                              "continuity_verified": True, "handle": {}}), flush=True)
    elif name == "verify_continuity":
        ok = handles.get(command["session_key"]) == command["opaque_session_id"]
        print(json.dumps({**base, "type": "response", "ok": True,
                          "continuity_verified": ok}), flush=True)
    elif name == "start_turn":
        print(json.dumps({**base, "type": "turn_started"}), flush=True)
        print(json.dumps({**base, "type": "turn_event",
                          "event": {"type": "text_delta", "text": "hello"}}), flush=True)
        print(json.dumps({**base, "type": "turn_result",
                          "result": {"status": "completed", "stopReason": "end_turn"}}),
              flush=True)
    elif name in {"cancel_turn", "close_member"}:
        if name == "close_member":
            handles.pop(command["session_key"], None)
        print(json.dumps({**base, "type": "response", "ok": True}), flush=True)
    elif name == "shutdown":
        print(json.dumps({**base, "type": "response", "ok": True}), flush=True)
        break
"""


def _spec(tmp_path: Path, *, resume: str | None = None) -> OpenMemberSpec:
    workspace = tmp_path / "workspace"
    workspace.mkdir(exist_ok=True)
    return OpenMemberSpec(
        run_id="run-direct-acp-1",
        member="lead",
        session_id="session-lead-1",
        generation=1,
        workspace=workspace,
        state_dir=tmp_path / "runtime" / "session-lead-1",
        harness=HarnessId.CODEX,
        executable=("codex-acp",),
        resume_session_ref=resume,
    )


async def test_bridge_provider_correlates_turn_and_deletes_exact_state(tmp_path: Path) -> None:
    bridge = tmp_path / "fake_bridge.py"
    bridge.write_text(FAKE_BRIDGE, encoding="utf-8")
    provider = DirectAcpProvider(
        runtime_path=tmp_path / "installed",
        node=sys.executable,
        bridge_path=bridge,
    )
    session = await provider.open_member(_spec(tmp_path))
    assert session.provider_session_ref == "opaque-1"
    assert await provider.verify_continuity(session)
    turn = await provider.start_turn(
        session, TurnSpec(turn_id="turn-1", request_id="request-1", text="hello")
    )
    events = [event async for event in turn]
    result = await turn.result()
    assert [(event.event, event.text) for event in events] == [("text_delta", "hello")]
    assert result.status is ProviderTurnStatus.COMPLETED
    assert result.stop_reason == "end_turn"
    close = await provider.close_member(session, "done")
    assert close.logical_session is CleanupFact.CONFIRMED
    assert close.process is CleanupFact.CONFIRMED
    assert close.local_state is CleanupFact.CONFIRMED
    assert close.provider_history is CleanupFact.UNKNOWN
    assert not session.state_dir.exists()
    assert await provider.dispose_run(session.run_id) is CleanupFact.CONFIRMED


async def test_bridge_provider_fails_before_prompt_on_resume_mismatch(tmp_path: Path) -> None:
    bridge = tmp_path / "fake_bridge.py"
    bridge.write_text(FAKE_BRIDGE, encoding="utf-8")
    provider = DirectAcpProvider(
        runtime_path=tmp_path / "installed",
        node=sys.executable,
        bridge_path=bridge,
    )
    (tmp_path / "runtime" / "session-lead-1").mkdir(parents=True)
    with pytest.raises(DirectAcpError, match="strict continuity mismatch"):
        await provider.open_member(_spec(tmp_path, resume="opaque-other"))
    assert provider.sessions == {}


async def test_bridge_close_failure_keeps_resume_state_for_exact_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bridge = tmp_path / "fake_bridge.py"
    bridge.write_text(FAKE_BRIDGE, encoding="utf-8")
    provider = DirectAcpProvider(
        runtime_path=tmp_path / "installed",
        node=sys.executable,
        bridge_path=bridge,
    )
    session = await provider.open_member(_spec(tmp_path))
    client = provider.clients[session.session_id]
    original_request = client.request

    async def fail_logical_close(command: str, **payload: object) -> dict[str, object]:
        if command == "close_member":
            raise DirectAcpError("injected logical close failure")
        return await original_request(command, **payload)

    monkeypatch.setattr(client, "request", fail_logical_close)
    first = await provider.close_member(session, "first close")
    assert first.logical_session is CleanupFact.FAILED
    assert first.process is CleanupFact.CONFIRMED
    assert first.local_state is CleanupFact.UNKNOWN
    assert session.state_dir.is_dir()
    assert await provider.dispose_run(session.run_id) is CleanupFact.FAILED

    resumed = await provider.open_member(_spec(tmp_path, resume=session.provider_session_ref))
    assert await provider.verify_continuity(resumed)
    second = await provider.close_member(resumed, "retry close")
    assert second.logical_session is CleanupFact.CONFIRMED
    assert second.local_state is CleanupFact.CONFIRMED
    assert not session.state_dir.exists()
    assert await provider.dispose_run(session.run_id) is CleanupFact.CONFIRMED


FAKE_ACPX_RUNTIME = r"""
export function createAgentRegistry({ overrides = {} } = {}) {
  return { resolve: (name) => overrides[name], list: () => Object.keys(overrides) };
}

export function createRuntimeStore() {
  const records = new Map();
  return {
    load: async (id) => records.get(id),
    save: async (record) => records.set(record.acpxRecordId, record),
  };
}

export function createAcpRuntime(options) {
  return {
    doctor: async () => ({ ok: true, message: "fake initialize passed" }),
    ensureSession: async (input) => {
      if (input.resumeSessionId !== undefined && input.resumeSessionId !== "backend-1") {
        throw new Error(`wrong strict resume id: ${input.resumeSessionId}`);
      }
      const handle = {
        sessionKey: input.sessionKey,
        backendSessionId: "backend-1",
        agentSessionId: "different-agent-id",
        acpxRecordId: input.sessionKey,
      };
      await options.sessionStore.save({
        acpxRecordId: input.sessionKey,
        agentCapabilities: {
          loadSession: true,
          promptCapabilities: { embeddedContext: true },
        },
      });
      return handle;
    },
    getCapabilities: async () => ({ controls: ["session/status"] }),
    getStatus: async () => ({ summary: "ready" }),
    close: async () => {},
    startTurn: () => { throw new Error("a model prompt must never run in qualification"); },
  };
}
"""


async def test_packaged_bridge_no_call_qualification_proves_backend_id_resume(
    tmp_path: Path,
) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is unavailable")
    runtime = tmp_path / "runtime"
    package = runtime / "node_modules" / "acpx"
    package.mkdir(parents=True)
    (runtime / "bridge.mjs").write_bytes(direct_acp._resource_bytes("bridge.mjs"))
    (package / "package.json").write_text(
        '{"name":"acpx","type":"module","exports":{"./runtime":"./runtime.js"}}\n',
        encoding="utf-8",
    )
    (package / "runtime.js").write_text(FAKE_ACPX_RUNTIME, encoding="utf-8")
    config_home = tmp_path / "config-home"
    config_home.mkdir()
    target = direct_acp.DirectAcpQualificationTarget(
        harness=HarnessId.CODEX,
        runtime_path=runtime,
        command=(node, "unused-fake-agent.mjs"),
        environment={**os.environ, "PATH": str(Path(node).parent)},
        native_version="fake 1.0.0",
        expected_version="fake 1.0.0",
        config_home_variable="CODEX_HOME",
        config_home=config_home,
        fingerprint="c" * 64,
    )

    result = await direct_acp._qualify_direct_acp_target(target, node=node)

    assert result.runtime_controls == ("session/status",)
    assert result.agent_capabilities == (
        "loadSession",
        "promptCapabilities.embeddedContext",
    )
