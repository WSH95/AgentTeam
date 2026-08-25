import readline from "node:readline";

import {
  createAcpRuntime,
  createAgentRegistry,
  createRuntimeStore,
} from "acpx/runtime";

const PROTOCOL_VERSION = 1;
const handles = new Map();
const pendingPermissions = new Map();
const activeTurnIds = new Map();
let runtime;
let runtimeStore;
let initialized = false;
let permissionSequence = 0;
let sessionSequence = 0;

function emit(message) {
  process.stdout.write(`${JSON.stringify({ protocol_version: PROTOCOL_VERSION, ...message })}\n`);
}

function requireRuntime() {
  if (!initialized || !runtime) {
    throw new Error("bridge is not initialized");
  }
  return runtime;
}

function opaqueSessionId(handle) {
  return handle.backendSessionId;
}

function capabilityPaths(value, prefix = "", depth = 0) {
  if (depth > 5 || value === null || value === undefined || value === false) {
    return [];
  }
  if (value === true || typeof value === "string" || typeof value === "number") {
    return prefix ? [prefix] : [];
  }
  if (Array.isArray(value)) {
    return value.length > 0 && prefix ? [prefix] : [];
  }
  if (typeof value !== "object") {
    return [];
  }
  return Object.entries(value).flatMap(([key, nested]) =>
    capabilityPaths(nested, prefix ? `${prefix}.${key}` : key, depth + 1),
  );
}

async function initialize(command) {
  if (initialized) {
    throw new Error("bridge is already initialized");
  }
  if (!command.state_dir || !command.cwd) {
    throw new Error("initialize requires state_dir and cwd");
  }
  const registry = createAgentRegistry({ overrides: command.agents ?? {} });
  runtimeStore = createRuntimeStore({ stateDir: command.state_dir });
  runtime = createAcpRuntime({
    cwd: command.cwd,
    sessionStore: runtimeStore,
    agentRegistry: registry,
    permissionMode: "deny-all",
    nonInteractivePermissions: "deny",
    onPermissionRequest: async (request) => {
      const permissionId = `permission-${++permissionSequence}`;
      const turnId = activeTurnIds.get(request.sessionId);
      if (!turnId) {
        return { outcome: "reject_once" };
      }
      emit({
        id: turnId,
        type: "permission_request",
        permission_id: permissionId,
        session_id: request.sessionId,
        tool_kind: request.inferredKind ?? null,
        tool_name: request.raw?.toolCall?.name ?? null,
        tool_title: request.raw?.toolCall?.title ?? null,
        tool_input: request.raw?.toolCall?.rawInput === undefined
          ? null
          : JSON.stringify(request.raw.toolCall.rawInput),
      });
      return await new Promise((resolve) => {
        const timeout = setTimeout(() => {
          pendingPermissions.delete(permissionId);
          resolve({ outcome: "reject_once" });
        }, 30_000);
        pendingPermissions.set(permissionId, {
          sessionId: request.sessionId,
          resolve: (outcome) => {
            clearTimeout(timeout);
            resolve({ outcome });
          },
        });
      });
    },
  });
  initialized = true;
  emit({ id: command.id, type: "response", ok: true });
}

async function openMember(command) {
  const current = requireRuntime();
  const runtimeSessionKey = command.resume_session_id === undefined
    ? command.session_key
    : `${command.session_key}-resume-${process.pid}-${++sessionSequence}`;
  const handle = await current.ensureSession({
    sessionKey: runtimeSessionKey,
    agent: command.agent,
    mode: "persistent",
    resumeSessionId: command.resume_session_id ?? undefined,
    cwd: command.cwd,
    sessionOptions: command.session_options ?? undefined,
  });
  const observed = opaqueSessionId(handle);
  const continuityVerified =
    command.resume_session_id === undefined || observed === command.resume_session_id;
  if (!continuityVerified) {
    await current.close({
      handle,
      reason: "strict continuity mismatch",
      discardPersistentState: true,
    });
    emit({
      id: command.id,
      type: "response",
      ok: false,
      error: "strict continuity mismatch",
      expected_session_id: command.resume_session_id,
      observed_session_id: observed ?? null,
    });
    return;
  }
  handles.set(command.session_key, handle);
  emit({
    id: command.id,
    type: "response",
    ok: true,
    handle,
    opaque_session_id: observed,
    continuity_verified: continuityVerified,
  });
}

async function qualify(command) {
  const current = requireRuntime();
  const doctor = await current.doctor();
  if (!doctor.ok) {
    emit({
      id: command.id,
      type: "response",
      ok: false,
      error: "ACP initialize/close probe failed",
    });
    return;
  }
  const base = `qualification-${process.pid}-${++sessionSequence}`;
  let fresh;
  let resumed;
  let freshClosed = false;
  try {
    fresh = await current.ensureSession({
      sessionKey: `${base}-fresh`,
      agent: command.agent,
      mode: "persistent",
      cwd: command.cwd,
    });
    const expected = opaqueSessionId(fresh);
    if (typeof expected !== "string" || expected.length === 0) {
      throw new Error("fresh ACP session has no stable backend session id");
    }
    await current.close({
      handle: fresh,
      reason: "AgentTeam no-call qualification reconnect",
      discardPersistentState: false,
    });
    freshClosed = true;
    resumed = await current.ensureSession({
      sessionKey: `${base}-resume`,
      agent: command.agent,
      mode: "persistent",
      resumeSessionId: expected,
      cwd: command.cwd,
    });
    if (opaqueSessionId(resumed) !== expected) {
      throw new Error("strict ACP resume/load returned a different backend session id");
    }
    const runtimeCapabilities = await current.getCapabilities({ handle: resumed });
    const status = await current.getStatus({ handle: resumed });
    const record = runtimeStore
      ? await runtimeStore.load(resumed.acpxRecordId ?? resumed.sessionKey)
      : undefined;
    await current.close({
      handle: resumed,
      reason: "AgentTeam no-call qualification close",
      discardPersistentState: true,
    });
    resumed = undefined;
    emit({
      id: command.id,
      type: "response",
      ok: true,
      lifecycle: {
        initialize: true,
        new_session: true,
        strict_resume: true,
        status: Boolean(status),
        close_session: true,
      },
      runtime_controls: Array.isArray(runtimeCapabilities?.controls)
        ? runtimeCapabilities.controls.filter((value) => typeof value === "string")
        : [],
      agent_capabilities: capabilityPaths(record?.agentCapabilities).sort(),
    });
  } finally {
    if (resumed) {
      await current.close({
        handle: resumed,
        reason: "AgentTeam failed qualification cleanup",
        discardPersistentState: true,
      }).catch(() => {});
    } else if (fresh && !freshClosed) {
      await current.close({
        handle: fresh,
        reason: "AgentTeam failed qualification cleanup",
        discardPersistentState: true,
      }).catch(() => {});
    }
  }
}

async function startTurn(command) {
  const current = requireRuntime();
  const handle = handles.get(command.session_key);
  if (!handle) {
    throw new Error(`unknown session key: ${command.session_key}`);
  }
  const identities = [
    handle.sessionKey,
    handle.agentSessionId,
    handle.backendSessionId,
    handle.acpxRecordId,
  ]
    .filter((value) => typeof value === "string");
  for (const identity of identities) {
    activeTurnIds.set(identity, command.id);
  }
  try {
    const turn = current.startTurn({
      handle,
      text: command.text,
      mode: command.mode ?? "prompt",
      requestId: command.request_id,
      timeoutMs: command.timeout_ms ?? undefined,
    });
    emit({ id: command.id, type: "turn_started", request_id: turn.requestId });
    void turn.promptStarted.then(() => {
      emit({ id: command.id, type: "prompt_started", request_id: turn.requestId });
    });
    for await (const event of turn.events) {
      emit({ id: command.id, type: "turn_event", event });
    }
    const result = await turn.result;
    emit({ id: command.id, type: "turn_result", result });
  } finally {
    for (const identity of identities) {
      activeTurnIds.delete(identity);
    }
  }
}

function rejectPendingPermissions(handle, outcome = "cancel") {
  const identities = new Set([
    handle.sessionKey,
    handle.agentSessionId,
    handle.backendSessionId,
    handle.acpxRecordId,
  ].filter((value) => typeof value === "string"));
  for (const [permissionId, pending] of pendingPermissions.entries()) {
    if (identities.has(pending.sessionId)) {
      pendingPermissions.delete(permissionId);
      pending.resolve(outcome);
    }
  }
}

async function dispatch(command) {
  if (command.protocol_version !== PROTOCOL_VERSION || typeof command.id !== "string") {
    throw new Error("unsupported or missing bridge protocol identity");
  }
  switch (command.command) {
    case "initialize":
      await initialize(command);
      return;
    case "doctor": {
      const report = await requireRuntime().doctor();
      emit({ id: command.id, type: "response", ok: report.ok, report });
      return;
    }
    case "qualify":
      await qualify(command);
      return;
    case "open_member":
      await openMember(command);
      return;
    case "verify_continuity": {
      const handle = handles.get(command.session_key);
      if (!handle) {
        emit({ id: command.id, type: "response", ok: false, continuity_verified: false });
        return;
      }
      await requireRuntime().getStatus({ handle });
      emit({
        id: command.id,
        type: "response",
        ok: true,
        continuity_verified: opaqueSessionId(handle) === command.opaque_session_id,
      });
      return;
    }
    case "start_turn":
      await startTurn(command);
      return;
    case "cancel_turn": {
      const handle = handles.get(command.session_key);
      if (!handle) {
        throw new Error(`unknown session key: ${command.session_key}`);
      }
      rejectPendingPermissions(handle);
      await requireRuntime().cancel({ handle, reason: command.reason ?? "cancelled" });
      emit({ id: command.id, type: "response", ok: true });
      return;
    }
    case "permission_response": {
      const pending = pendingPermissions.get(command.permission_id);
      if (!pending) {
        throw new Error(`unknown permission id: ${command.permission_id}`);
      }
      pendingPermissions.delete(command.permission_id);
      const allowed = new Set(["allow_once", "allow_always", "reject_once", "reject_always", "cancel"]);
      pending.resolve(allowed.has(command.outcome) ? command.outcome : "reject_once");
      emit({ id: command.id, type: "response", ok: true });
      return;
    }
    case "close_member": {
      const handle = handles.get(command.session_key);
      if (!handle) {
        throw new Error(`unknown session key: ${command.session_key}`);
      }
      rejectPendingPermissions(handle);
      await requireRuntime().close({
        handle,
        reason: command.reason ?? "AgentTeam run close",
        discardPersistentState: true,
      });
      handles.delete(command.session_key);
      emit({ id: command.id, type: "response", ok: true });
      return;
    }
    case "shutdown":
      emit({ id: command.id, type: "response", ok: true });
      process.exitCode = 0;
      input.close();
      return;
    default:
      throw new Error(`unknown bridge command: ${command.command}`);
  }
}

const input = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
input.on("line", (line) => {
  let command;
  try {
    command = JSON.parse(line);
  } catch (error) {
    emit({ id: null, type: "response", ok: false, error: `invalid JSON: ${error.message}` });
    return;
  }
  void dispatch(command).catch((error) => {
    emit({
      id: typeof command.id === "string" ? command.id : null,
      type: "response",
      ok: false,
      error: error instanceof Error ? error.message : String(error),
    });
  });
});
