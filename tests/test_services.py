from datetime import datetime
from pathlib import Path

from bot.models.voice_note import VoiceNote
from bot.services.deepgram import extract_transcript
from bot.services.gdrive import build_document


def test_extract_transcript_ok() -> None:
    payload = {
        "results": {
            "channels": [
                {"alternatives": [{"transcript": "Привет мир"}]}
            ]
        }
    }

    assert extract_transcript(payload) == "Привет мир"


def test_build_markdown_with_audio() -> None:
    note = VoiceNote(
        transcript="Тестовый текст",
        file_path=Path("/tmp/audio.ogg"),
        original_filename="audio.ogg",
        mime_type="audio/ogg",
        created_at=datetime(2026, 1, 2, 3, 4),
    )

    markdown = build_document(note, "https://drive.example/file", "md")

    assert "Дата: 2026-01-02 03:04" in markdown
    assert "## Текст" in markdown
    assert "Тестовый текст" in markdown
    assert "## Файл" in markdown


def test_build_text_plain() -> None:
    note = VoiceNote(
        transcript="Текст без разметки",
        file_path=Path("/tmp/audio.ogg"),
        original_filename="audio.ogg",
        mime_type="audio/ogg",
        created_at=datetime(2026, 2, 3, 4, 5),
    )

    text_body = build_document(note, None, "txt")

    assert "#" not in text_body
    assert "Текст:" in text_body
    assert "Текст без разметки" in text_body
