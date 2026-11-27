import pytest

from bot.services.llm import _split_dialogue, extract_content


def test_split_dialogue_short() -> None:
    assert _split_dialogue("привет") == ["привет"]


def test_split_dialogue_long() -> None:
    text = "а" * 25
    parts = _split_dialogue(text, max_len=10)

    assert len(parts) == 3
    assert "".join(parts) == text


def test_extract_content_ok() -> None:
    payload = {"choices": [{"message": {"content": "  Конспект беседы  "}}]}

    assert extract_content(payload) == "Конспект беседы"


def test_extract_content_bad() -> None:
    with pytest.raises(ValueError):
        extract_content({"choices": []})
