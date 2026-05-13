"""Audit local : pipeline complet sur un fichier CSV local (sans Drive).

Usage :
    python scripts/audit_local_file.py --csv "../../Atlas FR - 1521 csv - .../00330232294598_20260108175347.mp3.csv"
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import click

# Ajoute src/ au PYTHONPATH si lance depuis scripts/
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from afm_audit.audit import detect_flow, detect_pays_langue, parse_csv_transcript  # noqa: E402
from afm_audit.config import settings  # noqa: E402
from afm_audit.db import get_connection, insert_audit, upsert_transcript  # noqa: E402
from afm_audit.llm import audit_transcript  # noqa: E402


@click.command()
@click.option("--csv", "csv_path", type=click.Path(exists=True, dir_okay=False), required=True, help="Chemin vers le fichier CSV transcript.")
@click.option("--audit-version", default="local_test_v1", help="Tag de version pour l'audit.")
@click.option("--output", "out_dir", type=click.Path(file_okay=False), default="./local_audits_out", help="Dossier de sortie pour les JSON.")
def main(csv_path: str, audit_version: str, out_dir: str) -> None:
    path = Path(csv_path).resolve()
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    click.echo(f"=== AUDIT LOCAL : {path.name} ===\n")

    # 1. Parse CSV
    click.echo("[1/4] Lecture + parsing CSV...", nl=False)
    csv_content = path.read_text(encoding="utf-8", errors="replace")
    parsed_csv = parse_csv_transcript(csv_content)
    click.echo(f" OK ({len(parsed_csv.text)} chars, {parsed_csv.duree}s)")

    # 2. Détection pays + flow
    pays, langue = detect_pays_langue(path.name)
    flow = detect_flow(parsed_csv.text)
    click.echo(f"[2/4] Détection : pays={pays} / langue={langue} / flow={flow}")

    if len(parsed_csv.text) < 100:
        click.echo("  ! Transcript trop court (< 100 chars), abandon.")
        return

    n_tel_match = re.match(r"^(\d{8,15})_", path.name)
    n_tel = n_tel_match.group(1) if n_tel_match else None
    n_appel = re.sub(r"\.(mp3\.csv|csv|mp3)$", "", path.name)

    # 3. Persistance + audit IA
    click.echo("[3/4] Upsert transcript en DB + appel Claude...", nl=False)
    with get_connection() as conn:
        transcript_id = upsert_transcript(
            conn,
            drive_file_id=f"local:{path.name}",
            file_name=path.name, pays=pays, langue=langue,
            n_tel=n_tel, n_appel=n_appel,
            size_bytes=path.stat().st_size, flow=flow,
            raw_text=parsed_csv.text, duree_secondes=parsed_csv.duree,
        )

        result = audit_transcript(
            parsed_csv.text, flow=flow, file_name=path.name, pays=pays, langue=langue,
        )

        audit_id = insert_audit(
            conn,
            transcript_id=transcript_id, audit_version=audit_version,
            llm_model=result["model"], prompt_hash=result["prompt_hash"], flow=flow,
            parsed=result["parsed"], raw_llm_response=result["raw_text"],
        )
    click.echo(f" OK (tokens {result['input_tokens']}->{result['output_tokens']})")

    # 4. Sauvegarde JSON pour inspection humaine
    out_file = out_path / f"{n_appel}.json"
    out_file.write_text(json.dumps(result["parsed"], indent=2, ensure_ascii=False), encoding="utf-8")
    click.echo(f"[4/4] JSON sauve : {out_file}")

    # Résumé
    parsed = result["parsed"]
    totaux = parsed.get("totaux", {}) or {}
    SI = parsed.get("SI_detectees", []) or []

    click.echo("\n--- RÉSUMÉ ---")
    click.echo(f"  Transcript ID : {transcript_id}")
    click.echo(f"  Audit ID      : {audit_id}")
    click.echo(f"  Flow          : {flow}")
    click.echo(f"  Note /10      : {totaux.get('note_totale_sur_10', 'N/A')}")
    click.echo(f"  Note /100     : {totaux.get('note_sur_100', 'N/A')}")
    click.echo(f"  SI            : {len(SI)} (note zero par SI: {bool(totaux.get('note_zero_par_SI'))})")
    if SI:
        for s in SI:
            click.echo(f"    - {s.get('critere','?')} ({s.get('gravite','?')})")
    click.echo(f"\n  Commentaire   : {(parsed.get('commentaire_global') or '')[:240]}")
    click.echo(f"\n[OK] Audit complet pour {path.name}")


if __name__ == "__main__":
    main()
