"""Access control helpers."""

from __future__ import annotations


def is_allowed_user(user_id: int | None, admin_id: int) -> bool:
    """Return True when the user is allowed to use the bot."""

    return user_id is not None and user_id == admin_id
