"""The committed synthesis instruction (plan section 6): its LF-normalised
SHA-256 travels in every `EnsembleRecordV1.synthesis.instruction_hash`."""

from __future__ import annotations

from pathlib import Path

INSTRUCTIONS_FILE = Path(__file__).with_name("instructions.md")
