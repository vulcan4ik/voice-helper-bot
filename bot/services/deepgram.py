"""Deepgram transcription service."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

import httpx


logger = logging.getLogger(__name__)


def extract_transcript(payload: dict[str, Any]) -> str:
    """Extract the transcript, labeling speakers when Deepgram reports them."""

    try:
        channels = payload["results"]["channels"]
        alternatives = channels[0]["alternatives"]
        transcript = alternatives[0]["transcript"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Unexpected Deepgram response format") from exc

    utterances = payload.get("results", {}).get("utterances") or []
    labeled = _render_speakers(utterances)
    return labeled or transcript


def _render_speakers(utterances: list[dict[str, Any]]) -> str:
    """Join utterances into 'Спикер N: text' lines, merging same-speaker rows."""

    lines: list[str] = []
    current_speaker: Any = None
    current_text = ""

    for utterance in utterances:
        speaker = utterance.get("speaker")
        text = (utterance.get("transcript") or "").strip()
        if not text:
            continue

        if speaker != current_speaker and current_text:
            lines.append(f"{_speaker_label(current_speaker)}: {current_text}")
            current_text = text
        elif speaker == current_speaker:
            current_text = f"{current_text} {text}".strip()
        else:
            current_text = text
        current_speaker = speaker

    if current_text:
        lines.append(f"{_speaker_label(current_speaker)}: {current_text}")

    return "\n".join(lines)


def _speaker_label(speaker: Any) -> str:
    """Human-friendly speaker name; Deepgram numbers speakers from 0."""

    if isinstance(speaker, int):
        return f"Спикер {speaker + 1}"
    return "Спикер"


async def transcribe_file(file_path: Path, mime_type: str, api_key: str) -> str:
    """Send audio file to Deepgram and return the transcript."""

    # Reading the file in a thread keeps the async loop responsive.
    audio_bytes = await asyncio.to_thread(file_path.read_bytes)

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": mime_type,
    }
    params = {
        "model": "nova-3",
        "smart_format": "true",
        "language": "ru",
        # Speaker diarization: label who is talking.
        "diarize": "true",
        # Split into utterances so we can tell which speaker said what.
        "utterances": "true",
    }

    # 180s: long voice notes take a while to transcribe on Deepgram's side.
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            "https://api.deepgram.com/v1/listen",
            headers=headers,
            params=params,
            content=audio_bytes,
        )

    if response.status_code >= 400:
        logger.error("Deepgram error %s: %s", response.status_code, response.text)
        response.raise_for_status()

    payload = response.json()
    transcript = extract_transcript(payload)
    if not transcript:
        raise ValueError("Empty transcript received from Deepgram")
    return transcript
