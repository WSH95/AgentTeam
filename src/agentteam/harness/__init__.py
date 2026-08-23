"""Direct harness core: adapters, environment, launcher, process runner (plan section 9)."""

from agentteam.domain.common import HarnessId
from agentteam.harness.claude import ClaudeAdapter
from agentteam.harness.codex import CodexAdapter
from agentteam.harness.grok import GrokAdapter
from agentteam.harness.protocol import HarnessAdapter


def get_adapter(harness: HarnessId) -> HarnessAdapter:
    adapters: dict[HarnessId, HarnessAdapter] = {
        HarnessId.CLAUDE_CODE: ClaudeAdapter(),
        HarnessId.CODEX: CodexAdapter(),
        HarnessId.GROK: GrokAdapter(),
    }
    return adapters[harness]


__all__ = ["ClaudeAdapter", "CodexAdapter", "GrokAdapter", "HarnessAdapter", "get_adapter"]
