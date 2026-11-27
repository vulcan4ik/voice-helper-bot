"""LLM summarization service (OpenAI-compatible chat completions API)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from bot.utils.config import Config


logger = logging.getLogger(__name__)

# Max dialogue size for a single LLM request. Bigger dialogues are summarized
# in parts and then merged into a final summary.
MAX_REQUEST_CHARS = 60_000

# What the conspect should look like.
SYSTEM_PROMPT = (
    "Ты делаешь краткий конспект беседы по расшифровкам голосовых сообщений. "
    "Отвечай на русском языке в формате markdown. Структура конспекта: "
    "1) Основные мысли; 2) Решения; 3) Задачи (TODO); 4) Цитаты (2-3 самые важные). "
    "Не выдумывай факты, которых нет в тексте беседы."
)


def _split_dialogue(text: str, max_len: int = MAX_REQUEST_CHARS) -> list[str]:
    """Split a long dialogue into chunks that fit into one request."""

    if len(text) <= max_len:
        return [text]
    return [text[start : start + max_len] for start in range(0, len(text), max_len)]


def extract_content(payload: dict[str, Any]) -> str:
    """Extract the model answer from a chat completions response payload."""

    try:
        content = payload["choices"][0]["message"]["content"]
        return content.strip()
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise ValueError("Unexpected LLM response format") from exc


async def _chat(text: str, config: Config) -> str:
    """One LLM request: send a dialogue chunk, get its summary back."""

    headers = {"Authorization": f"Bearer {config.llm_api_key}"}
    payload = {
        "model": config.llm_model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    }
    url = f"{config.llm_base_url.rstrip('/')}/chat/completions"

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code >= 400:
        logger.error("LLM error %s: %s", response.status_code, response.text)
        response.raise_for_status()

    return extract_content(response.json())


async def summarize_dialogue(dialogue_text: str, config: Config) -> str:
    """Build a conspect for the whole dialogue."""

    if not config.llm_api_key:
        raise RuntimeError(
            "LLM_API_KEY не настроен. Добавь ключ в .env и перезапусти бота."
        )

    parts = _split_dialogue(dialogue_text)
    if len(parts) == 1:
        return await _chat(parts[0], config)

    # Long dialogue: summarize each part first, then merge the summaries.
    logger.info(
        "Dialogue is long (%d chars), summarizing in %d parts",
        len(dialogue_text),
        len(parts),
    )
    partial_summaries = []
    for part in parts:
        partial_summaries.append(await _chat(part, config))

    combined = "\n\n".join(partial_summaries)
    return await _chat(combined, config)
