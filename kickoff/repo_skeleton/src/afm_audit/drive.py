"""Client Google Drive — liste fichiers, telecharge CSV/MP3 via service account."""
from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from .config import settings


SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


@dataclass
class DriveFile:
    id: str
    name: str
    mime_type: str
    size: int
    parent_id: str | None = None


def _get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        str(settings.google_application_credentials), scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def list_files_in_folder(folder_id: str, page_size: int = 1000) -> list[DriveFile]:
    service = _get_drive_service()
    files: list[DriveFile] = []
    page_token: str | None = None

    while True:
        resp = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="nextPageToken, files(id, name, mimeType, size, parents)",
            pageSize=page_size,
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()
        for f in resp.get("files", []):
            files.append(DriveFile(
                id=f["id"],
                name=f["name"],
                mime_type=f.get("mimeType", ""),
                size=int(f.get("size", 0)),
                parent_id=(f.get("parents") or [None])[0],
            ))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return files


def download_file(file_id: str, dest: Path) -> Path:
    service = _get_drive_service()
    request = service.files().get_media(fileId=file_id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    dest.write_bytes(buf.getvalue())
    return dest


def download_file_text(file_id: str) -> str:
    """Telecharge un fichier texte (CSV) en memoire et renvoie son contenu."""
    service = _get_drive_service()
    request = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue().decode("utf-8", errors="replace")
