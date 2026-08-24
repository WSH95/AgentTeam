"""Cross-OS example-package hash identity (plan sections 14 and 16).

This single pinned constant, asserted on every CI leg, is the cross-OS
identity evidence: the same committed package must hash identically on
Ubuntu, Windows, and macOS. Editing anything under
`examples/assistants/code-reviewer/` changes the hash on purpose; regenerate
the constant with:

    uv run python -c "from pathlib import Path; \
from agentteam.resolution.archive import hash_package; \
print(hash_package(Path('examples/assistants/code-reviewer')).package_hash)"
"""

from __future__ import annotations

from pathlib import Path

from agentteam.resolution.archive import hash_package

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE = REPO_ROOT / "examples" / "assistants" / "code-reviewer"

EXAMPLE_PACKAGE_HASH = "fb9e98a34a99f146d5519baf1ed7707e1267625ebd56a6e2fdac797123cb1b5a"


def test_the_committed_example_package_hash_is_pinned() -> None:
    digest = hash_package(PACKAGE)
    assert digest.package_hash == EXAMPLE_PACKAGE_HASH


def test_the_bundle_manifest_pins_the_same_hash() -> None:
    from datetime import UTC, datetime

    from agentteam.domain.bundle import AssistantRefV1
    from agentteam.resolution.archive import build_bundle_manifest
    from agentteam.resolution.package import load_package

    loaded = load_package(PACKAGE)
    digest = hash_package(PACKAGE)
    bundle = build_bundle_manifest(
        assistant=AssistantRefV1(
            id=loaded.definition.id,
            version=loaded.definition.version,
            package_hash=digest.package_hash,
        ),
        digest=digest,
        created_at=datetime(2026, 8, 23, 12, 0, tzinfo=UTC),
    )
    assert bundle.effective_definition_hash == EXAMPLE_PACKAGE_HASH
