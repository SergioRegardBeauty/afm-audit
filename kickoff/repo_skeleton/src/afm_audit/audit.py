"""Pipeline d'audit : Drive -> parse CSV -> Claude -> Postgres."""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass

from .config import settings
from .db import get_connection, insert_audit, upsert_transcript
from .drive import DriveFile, download_file_text, list_files_in_folder
from .llm import audit_transcript

PAYS_FROM_PREFIX = [
    (re.compile(r"^00330|^0033\d"), "FR", "fr"),
    (re.compile(r"^00440|^0044\d"), "GB", "en"),
    (re.compile(r"^00490|^0049\d"), "DE", "de"),
    (re.compile(r"^00480|^0048\d"), "PL", "pl"),
    (re.compile(r"^00420|^0042\d"), "CZ", "cs"),
]

SAV_KEYWORDS = re.compile(
    r"remboursement|rembours|reclamation|r[ée]clamation|j['e]ai pass[ée] (une )?commande|"
    r"o[uù] est ma commande|retour(ner)?|refund|return my|complaint|"
    r"wo ist meine bestellung|erstattung|reklamation|zwrot|reklamacja|reklamac|vr[áa]cen",
    re.IGNORECASE,
)


@dataclass
class CsvParsed:
    text: str
    duree: int


def detect_pays_langue(file_name: str) -> tuple[str, str]:
    for pattern, pays, lang in PAYS_FROM_PREFIX:
        if pattern.search(file_name):
            return pays, lang
    return "FR", "fr"


def detect_flow(text: str) -> str:
    return "sav" if SAV_KEYWORDS.search(text) else "cde_tel"


def parse_csv_transcript(csv_content: str) -> CsvParsed:
    reader = csv.DictReader(io.StringIO(csv_content), delimiter=";")
    lines: list[str] = []
    last_end = 0.0
    first_start = -1.0

    def parse_time(s: str) -> float:
        if not s:
            return 0.0
        parts = s.split(":")
        try:
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            if len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            return float(parts[0])
        except (ValueError, IndexError):
            return 0.0

    for row in reader:
        text_col = (
            row.get("Text") or row.get("text") or row.get("Texte")
            or row.get("Transcription") or row.get("transcription") or ""
        ).strip().strip('"')
        if not text_col:
            continue
        speaker = (row.get("Speaker") or row.get("Orateur") or row.get("speaker") or "").strip()
        start = parse_time(row.get("Start time", "") or row.get("start_time", ""))
        end = parse_time(row.get("End time", "") or row.get("end_time", ""))
        if end > last_end:
            last_end = end
        if first_start < 0 or start < first_start:
            first_start = start
        lines.append(f"[{start:.2f}] {speaker}: {text_col}" if speaker else text_col)

    duree = int(last_end - max(first_start, 0)) if last_end > 0 else 0
    return CsvParsed(text="\n".join(lines), duree=duree)


def audit_one_file(drive_file: DriveFile, audit_version: str = "v2_python") -> dict:
    """Pipeline complet pour un fichier."""
    csv_content = download_file_text(drive_file.id)
    parsed_csv = parse_csv_transcript(csv_content)
    pays, langue = detect_pays_langue(drive_file.name)
    flow = detect_flow(parsed_csv.text)
    n_tel_match = re.match(r"^(\d{8,15})_", drive_file.name)
    n_tel = n_tel_match.group(1) if n_tel_match else None
    n_appel = re.sub(r"\.(mp3\.csv|csv|mp3)$", "", drive_file.name)

    with get_connection() as conn:
        transcript_id = upsert_transcript(
            conn,
            drive_file_id=drive_file.id, file_name=drive_file.name,
            pays=pays, langue=langue, n_tel=n_tel, n_appel=n_appel,
            size_bytes=drive_file.size, flow=flow,
            raw_text=parsed_csv.text, duree_secondes=parsed_csv.duree,
        )

        if drive_file.size < 500:
            # File trop court : NA partout, pas d'API call
            return {"transcript_id": str(transcript_id), "skipped": "too_short"}

        result = audit_transcript(
            parsed_csv.text, flow=flow, file_name=drive_file.name, pays=pays, langue=langue,
        )

        audit_id = insert_audit(
            conn,
            transcript_id=transcript_id, audit_version=audit_version,
            llm_model=result["model"], prompt_hash=result["prompt_hash"], flow=flow,
            parsed=result["parsed"], raw_llm_response=result["raw_text"],
        )

    return {
        "transcript_id": str(transcript_id), "audit_id": str(audit_id),
        "input_tokens": result["input_tokens"], "output_tokens": result["output_tokens"],
        "flow": flow, "pays": pays,
    }


def audit_drive_folder(folder_id: str, audit_version: str = "v2_python") -> list[dict]:
    files = list_files_in_folder(folder_id)
    results = []
    for f in files:
        if f.mime_type.startswith("application/vnd.google-apps."):
            continue  # skip dossiers / Sheets / shortcuts
        if not (f.name.endswith(".csv") or f.name.endswith(".mp3.csv")):
            continue
        try:
            results.append(audit_one_file(f, audit_version=audit_version))
        except Exception as e:
            results.append({"file_name": f.name, "error": str(e)})
    return results
