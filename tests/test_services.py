from datetime import datetime
from pathlib import Path

from bot.models.voice_note import VoiceNote
from bot.services.deepgram import extract_transcript, _render_speakers
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


def test_extract_transcript_with_speakers() -> None:
    payload = {
        "results": {
            "channels": [
                {"alternatives": [{"transcript": "Привет Как дела"}]}
            ],
            "utterances": [
                {"speaker": 0, "transcript": "Привет"},
                {"speaker": 1, "transcript": "Как дела"},
            ],
        }
    }

    assert extract_transcript(payload) == "Спикер 1: Привет\nСпикер 2: Как дела"


def test_render_speakers_merges_same_speaker() -> None:
    utterances = [
        {"speaker": 0, "transcript": "Привет"},
        {"speaker": 0, "transcript": "друг"},
        {"speaker": 1, "transcript": "Привет"},
    ]

    assert _render_speakers(utterances) == "Спикер 1: Привет друг\nСпикер 2: Привет"


def test_render_speakers_without_speaker_info() -> None:
    utterances = [
        {"speaker": None, "transcript": "Просто текст"},
    ]

    assert _render_speakers(utterances) == "Спикер: Просто текст"


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
