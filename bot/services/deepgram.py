"""Deepgram transcription service."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

import httpx


logger = logging.getLogger(__name__)


def extract_transcript(payload: dict[str, Any]) -> str:
    """Extract the transcript from Deepgram response payload."""

    try:
        channels = payload["results"]["channels"]
        alternatives = channels[0]["alternatives"]
        return alternatives[0]["transcript"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Unexpected Deepgram response format") from exc


async def transcribe_file(file_path: Path, mime_type: str, api_key: str) -> str:
    """Send audio file to Deepgram and return the transcript."""

    # Reading the file in a thread keeps the async loop responsive.
    audio_bytes = await asyncio.to_thread(file_path.read_bytes)

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": mime_type,
    }
    params = {
        "model": "nova-2",
        "smart_format": "true",
        "language": "ru",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
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
