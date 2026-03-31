"""Google Drive integration for saving voice notes."""

from __future__ import annotations

import asyncio
from datetime import datetime
import io
import logging
from pathlib import Path
from typing import Any, Literal

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

from bot.models.voice_note import VoiceNote
from bot.utils.config import Config


logger = logging.getLogger(__name__)


TextFormat = Literal["md", "txt"]


def build_document(
    note: VoiceNote,
    audio_link: str | None,
    text_format: TextFormat,
) -> str:
    """Create the text body for a saved note."""

    created_at = note.created_at.strftime("%Y-%m-%d %H:%M")
    if text_format == "txt":
        audio_section = f"\n\nФайл: {audio_link}" if audio_link else ""
        return (
            "Voice Note\n\n"
            f"Дата: {created_at}\n\n"
            "Текст:\n"
            f"{note.transcript}"
            f"{audio_section}\n"
        )

    audio_section = f"\n\n## Файл\n{audio_link}" if audio_link else ""
    return (
        "# Voice Note\n\n"
        f"Дата: {created_at}\n\n"
        "## Текст\n"
        f"{note.transcript}"
        f"{audio_section}\n"
    )


async def save_note(
    note: VoiceNote,
    save_audio: bool,
    config: Config,
    text_format: TextFormat = "md",
) -> str:
    """Save the note to Google Drive and return a link to the text file."""

    return await asyncio.to_thread(
        _save_note_sync, note, save_audio, config, text_format
    )


def _save_note_sync(
    note: VoiceNote,
    save_audio: bool,
    config: Config,
    text_format: TextFormat,
) -> str:
    """Blocking Google Drive calls executed in a worker thread."""

    scopes = ["https://www.googleapis.com/auth/drive.file"]
    credentials = _build_credentials(config, scopes)
    service = build(
        "drive",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )

    folder_id = _get_or_create_date_folder(
        service=service,
        date=note.created_at,
        parent_id=config.google_drive_parent_id,
        shared_drive_id=config.google_shared_drive_id,
    )

    audio_link = None
    if save_audio:
        audio_file_id = _upload_audio(service, note, folder_id)
        audio_link = f"https://drive.google.com/file/d/{audio_file_id}/view"

    text_body = build_document(note, audio_link, text_format)
    suffix = "txt" if text_format == "txt" else "md"
    text_name = note.created_at.strftime(f"voice-note-%Y%m%d-%H%M%S.{suffix}")
    mime_type = "text/plain" if text_format == "txt" else "text/markdown"
    text_id = _upload_text(
        service=service,
        folder_id=folder_id,
        filename=text_name,
        content=text_body,
        mime_type=mime_type,
    )

    return f"https://drive.google.com/file/d/{text_id}/view"


def describe_drive_error(error: Exception) -> str | None:
    """Return a human-friendly Drive error message when possible."""

    if not isinstance(error, HttpError):
        return None

    status = getattr(getattr(error, "resp", None), "status", None)
    raw_error = str(error)

    reason = _extract_error_reason(error)
    if status == 401:
        return "Ошибка авторизации Google Drive. Проверь OAuth токен или доступ."
    if status == 403 and reason == "storageQuotaExceeded":
        return "Недостаточно места в Google Drive. Освободи место или используй другой диск."
    if status == 403 and "Service Accounts do not have storage quota" in raw_error:
        return (
            "Сервисные аккаунты не имеют квоты хранения. "
            "Нужен Shared Drive или OAuth-делегирование."
        )
    if status == 403 and (
        reason == "accessNotConfigured" or "accessNotConfigured" in raw_error
    ):
        return (
            "Google Drive API отключен для проекта. "
            "Включи drive.googleapis.com в Google Cloud и подожди несколько минут."
        )
    if status == 403 and reason == "insufficientPermissions":
        return "Нет прав на запись в Google Drive. Проверь доступ сервисного аккаунта."
    if status == 404 and reason == "notFound":
        return "Папка или файл в Google Drive не найдены. Проверь настройки папки."
    return None


def _extract_error_reason(error: HttpError) -> str | None:
    """Extract the primary error reason from a Google API error."""

    try:
        details = error.error_details or []
        if details:
            reason = details[0].get("reason")
            if reason:
                return reason
    except AttributeError:
        return None
    return None


def _build_credentials(config: Config, scopes: list[str]) -> Credentials:
    """Create Google credentials using OAuth or service account."""

    if config.google_oauth_client_file:
        return _load_oauth_credentials(
            client_file=Path(config.google_oauth_client_file),
            token_file=_resolve_token_file(config),
            scopes=scopes,
        )

    return service_account.Credentials.from_service_account_file(
        config.google_service_account_file,
        scopes=scopes,
    )


def _resolve_token_file(config: Config) -> Path:
    """Pick a token file path for OAuth credentials."""

    if config.google_oauth_token_file:
        return Path(config.google_oauth_token_file)

    if config.google_oauth_client_file:
        return Path(config.google_oauth_client_file).with_name("token.json")

    return Path("token.json")


def _load_oauth_credentials(
    client_file: Path,
    token_file: Path,
    scopes: list[str],
) -> Credentials:
    """Load OAuth credentials from disk, refreshing if possible."""

    if token_file.exists():
        credentials = Credentials.from_authorized_user_file(
            str(token_file),
            scopes=scopes,
        )
    else:
        raise RuntimeError(
            "Отсутствует OAuth токен. Создай его через scripts/google_oauth.py"
        )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token_file.write_text(credentials.to_json(), encoding="utf-8")

    return credentials


def _get_or_create_date_folder(
    service: Any,
    date: datetime,
    parent_id: str | None,
    shared_drive_id: str | None,
) -> str:
    """Return a Drive folder id for the given date, creating if needed."""

    folder_name = date.strftime("%Y-%m-%d")
    effective_parent_id = parent_id or shared_drive_id
    query_parts = [
        "mimeType='application/vnd.google-apps.folder'",
        "trashed=false",
        f"name='{folder_name}'",
    ]
    if effective_parent_id:
        query_parts.append(f"'{effective_parent_id}' in parents")

    query = " and ".join(query_parts)
    list_kwargs: dict[str, Any] = {
        "q": query,
        "fields": "files(id, name)",
        "supportsAllDrives": True,
        "includeItemsFromAllDrives": True,
    }
    if shared_drive_id:
        list_kwargs["corpora"] = "drive"
        list_kwargs["driveId"] = shared_drive_id

    result = service.files().list(**list_kwargs).execute()
    files = result.get("files", [])
    if files:
        return files[0]["id"]

    metadata: dict[str, Any] = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if effective_parent_id:
        metadata["parents"] = [effective_parent_id]

    folder = service.files().create(
        body=metadata,
        fields="id",
        supportsAllDrives=True,
    ).execute()
    return folder["id"]


def _upload_audio(service: Any, note: VoiceNote, folder_id: str) -> str:
    """Upload the audio file to Drive and return its file id."""

    media = MediaFileUpload(note.file_path, mimetype=note.mime_type, resumable=False)
    metadata: dict[str, Any] = {
        "name": note.original_filename,
        "parents": [folder_id],
    }
    uploaded = service.files().create(
        body=metadata,
        media_body=media,
        fields="id",
        supportsAllDrives=True,
    ).execute()
    return uploaded["id"]


def _upload_text(
    service: Any,
    folder_id: str,
    filename: str,
    content: str,
    mime_type: str,
) -> str:
    """Upload the text file to Drive and return its file id."""

    media_stream = io.BytesIO(content.encode("utf-8"))
    media = MediaIoBaseUpload(media_stream, mimetype=mime_type, resumable=False)
    metadata: dict[str, Any] = {
        "name": filename,
        "parents": [folder_id],
    }
    uploaded = service.files().create(
        body=metadata,
        media_body=media,
        fields="id",
        supportsAllDrives=True,
    ).execute()
    return uploaded["id"]
