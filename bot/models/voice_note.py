"""Dataclass representing a voice note payload."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class VoiceNote:
    """Keeps everything we need to save a voice note later."""

    transcript: str
    file_path: Path
    original_filename: str
    mime_type: str
    created_at: datetime
