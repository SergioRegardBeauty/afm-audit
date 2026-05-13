"""Acces Postgres minimal pour persister transcripts + audits."""
from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from .config import settings


def get_connection() -> psycopg.Connection:
    return psycopg.connect(settings.database_url, row_factory=dict_row)


def upsert_transcript(conn: psycopg.Connection, *, drive_file_id: str, file_name: str,
                      pays: str, langue: str, n_tel: str | None, n_appel: str,
                      size_bytes: int, flow: str | None, raw_text: str | None,
                      duree_secondes: int | None = None) -> UUID:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO transcripts (drive_file_id, file_name, pays, langue, n_tel, n_appel,
                                    size_bytes, flow, raw_text, duree_secondes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (drive_file_id) DO UPDATE SET
                file_name = EXCLUDED.file_name,
                flow = EXCLUDED.flow,
                raw_text = EXCLUDED.raw_text,
                duree_secondes = EXCLUDED.duree_secondes
            RETURNING id
            """,
            (drive_file_id, file_name, pays, langue, n_tel, n_appel,
             size_bytes, flow, raw_text, duree_secondes),
        )
        row = cur.fetchone()
        conn.commit()
        return row["id"]  # type: ignore


def insert_audit(conn: psycopg.Connection, *, transcript_id: UUID, audit_version: str,
                 llm_model: str, prompt_hash: str, flow: str, parsed: dict[str, Any],
                 raw_llm_response: str) -> UUID:
    meta = parsed.get("metadata") or {}
    totaux = parsed.get("totaux") or {}
    SI = parsed.get("SI_detectees") or []
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO audits (transcript_id, audit_version, llm_model, prompt_hash, flow,
                                agent, n_client, type, demande_client,
                                note_totale_sur_10, note_sur_100, note_zero_par_SI, si_count,
                                commentaire_global, commentaire_traduit_fr,
                                criteres_jsonb, si_jsonb, raw_llm_response)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                transcript_id, audit_version, llm_model, prompt_hash, flow,
                meta.get("agent"), meta.get("n_client"), meta.get("type"),
                meta.get("demande_client"),
                totaux.get("note_totale_sur_10"),
                totaux.get("note_sur_100"),
                bool(totaux.get("note_zero_par_SI", False)),
                len(SI) if isinstance(SI, list) else 0,
                parsed.get("commentaire_global"),
                parsed.get("commentaire_traduit_fr"),
                json.dumps(parsed.get("criteres") or {}),
                json.dumps(SI),
                raw_llm_response,
            ),
        )
        row = cur.fetchone()
        conn.commit()
        return row["id"]  # type: ignore
