"""Wrapper Anthropic — audit IA d'un transcript selon la grille AFM (Cde Tel ou SAV)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from anthropic import Anthropic

from .config import settings


_client = Anthropic(api_key=settings.anthropic_api_key)


def load_prompt_template(flow: str) -> str:
    """Charge le prompt template ('cde_tel' ou 'sav') depuis prompts/."""
    fname = f"audit_{flow}_v1.md"
    path = settings.prompts_dir / fname
    if not path.exists():
        raise FileNotFoundError(
            f"Prompt template introuvable : {path}. "
            f"Copie depuis le repo principal prompts/audit_{flow}_v1.md"
        )
    return path.read_text(encoding="utf-8")


def audit_transcript(transcript_text: str, *, flow: str, file_name: str, pays: str,
                     langue: str, model: str | None = None) -> dict:
    """
    Audite un transcript via Claude et renvoie le JSON parse.
    Renvoie egalement le hash du prompt (pour traceability) et la reponse brute.

    `model` override : si None, utilise settings.anthropic_model. L'interface Streamlit
    permet de choisir Haiku/Sonnet à la volée par appel.
    """
    template = load_prompt_template(flow)

    full_prompt = (
        template
        + "\n\n## CONTEXTE DE CET APPEL\n"
        + f"- Fichier : {file_name}\n- Pays : {pays}\n- Langue : {langue}\n"
        + "\n## TRANSCRIPT\n"
        + transcript_text
    )

    prompt_hash = hashlib.sha256(full_prompt.encode("utf-8")).hexdigest()
    model_used = model or settings.anthropic_model

    response = _client.messages.create(
        model=model_used,
        max_tokens=settings.anthropic_max_tokens,
        temperature=0.1,
        messages=[{"role": "user", "content": full_prompt}],
    )

    raw_text = "".join(b.text for b in response.content if b.type == "text")

    # Parse JSON depuis la reponse
    try:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start < 0 or end < start:
            raise ValueError("Pas de JSON dans la reponse")
        parsed = json.loads(raw_text[start : end + 1])
    except (json.JSONDecodeError, ValueError) as e:
        parsed = {
            "_parse_error": str(e),
            "_raw_text": raw_text[:500],
            "criteres": {},
            "totaux": {},
            "commentaire_global": "Echec parsing JSON IA",
            "SI_detectees": [],
        }

    return {
        "parsed": parsed,
        "raw_text": raw_text,
        "prompt_hash": prompt_hash,
        "model": model_used,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
