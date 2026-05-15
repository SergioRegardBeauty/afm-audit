"""Ingestion CSV transcripts local → Postgres.

Scanne récursivement un dossier de CSV (HappyScribe) et insère chaque transcript
dans la table `transcripts`. Idempotent grâce à `upsert_transcript` (ON CONFLICT
sur `drive_file_id` qui vaut `local:<basename>`).

Utilise les helpers existants :
- `afm_audit.audit.parse_csv_transcript` (parse + durée)
- `afm_audit.audit.detect_pays_langue` (depuis indicatif tel)
- `afm_audit.audit.detect_flow`        (mots-clés multilingues)
- `afm_audit.db.upsert_transcript`     (insert en DB)

Usage :
    python scripts/ingest_local_transcripts.py \
        --root "../../Transcription MP3" \
        --batch-size 100

Options :
    --limit N        : n'ingère que N fichiers (pour tester)
    --pays FR,GB     : ne traite que ces pays (filtre sur PAYS détecté)
    --use-manifest   : reprend la classification depuis pipeline/manifest.json
                       (évite de re-classifier 5000+ fois)
    --dry-run        : parse + classifie, mais n'écrit pas en DB
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import click

# Ajouter src/ au PYTHONPATH si lancé depuis scripts/
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from afm_audit.audit import detect_flow, detect_pays_langue, parse_csv_transcript  # noqa: E402
from afm_audit.db import get_connection, upsert_transcript  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MANIFEST_PATH = PROJECT_ROOT / "pipeline" / "manifest.json"


def load_flow_from_manifest() -> dict[str, str]:
    """Build a mapping {csv_basename → flow} from pipeline/manifest.json.
    Returns empty dict if the manifest is missing."""
    if not MANIFEST_PATH.exists():
        click.echo(f"  (manifest absent à {MANIFEST_PATH}, classification dynamique)")
        return {}
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    by_name: dict[str, str] = {}
    # The manifest has two useful views: `sample` (cap 10 per flow) and the raw
    # per-pays catalog under `details` if present. We extract from `sample`
    # plus the `entries` dump if available.
    sample = data.get("sample", {})
    for country, flows in sample.items():
        for flow_key, items in flows.items():
            for it in items:
                name = it.get("name") or Path(it.get("path", "")).name
                if name:
                    by_name[name] = flow_key
    return by_name


def n_tel_from_filename(name: str) -> str | None:
    m = re.match(r"^(\d{8,15})_", name)
    return m.group(1) if m else None


def n_appel_from_filename(name: str) -> str:
    return re.sub(r"\.(mp3\.csv|csv|mp3)$", "", name)


@click.command()
@click.option("--root", "root_path", type=click.Path(exists=True, file_okay=False),
              required=True, help="Dossier racine contenant les CSV (récursif).")
@click.option("--batch-size", type=int, default=100,
              help="Nombre de transcripts par commit (défaut 100).")
@click.option("--limit", type=int, default=0,
              help="0 = pas de limite ; N = arrête après N fichiers.")
@click.option("--pays", type=str, default="",
              help="Filtre CSV par pays détecté (ex: 'FR' ou 'FR,DE').")
@click.option("--use-manifest", is_flag=True,
              help="Reprend la classification flow depuis pipeline/manifest.json.")
@click.option("--dry-run", is_flag=True,
              help="Parse et classifie, mais n'écrit rien en DB.")
def main(root_path: str, batch_size: int, limit: int, pays: str,
         use_manifest: bool, dry_run: bool) -> None:
    root = Path(root_path)
    pays_filter = {p.strip().upper() for p in pays.split(",") if p.strip()} if pays else None

    click.echo(f"=== Ingestion CSV → Postgres ===")
    click.echo(f"  Racine    : {root}")
    click.echo(f"  Pays      : {sorted(pays_filter) if pays_filter else 'tous'}")
    click.echo(f"  Dry-run   : {dry_run}")
    click.echo(f"  Manifest  : {use_manifest}")

    flow_by_name = load_flow_from_manifest() if use_manifest else {}
    if use_manifest:
        click.echo(f"  Manifest chargé : {len(flow_by_name)} entrées avec flow pré-classifié")

    csv_files = sorted(root.rglob("*.mp3.csv"))
    if not csv_files:
        click.echo(f"  Aucun *.mp3.csv trouvé sous {root}")
        return
    click.echo(f"  CSV détectés : {len(csv_files)}")

    stats: dict[str, int] = {"ok": 0, "skipped_filter": 0, "skipped_empty": 0,
                              "errors": 0, "by_pays_FR": 0, "by_pays_GB": 0,
                              "by_pays_DE": 0, "by_pays_PL": 0, "by_pays_CZ": 0,
                              "by_flow_cde_tel": 0, "by_flow_sav": 0}

    t0 = time.time()
    conn = None
    try:
        if not dry_run:
            conn = get_connection()

        for i, path in enumerate(csv_files, 1):
            if limit and stats["ok"] + stats["skipped_filter"] >= limit:
                break
            name = path.name

            # Détection pays + langue depuis le nom de fichier
            country, langue = detect_pays_langue(name)
            if pays_filter and country not in pays_filter:
                stats["skipped_filter"] += 1
                continue

            try:
                csv_content = path.read_text(encoding="utf-8", errors="replace")
                parsed = parse_csv_transcript(csv_content)
            except Exception as e:
                click.echo(f"  ! {name}: parse error: {e}")
                stats["errors"] += 1
                continue

            if not parsed.text:
                stats["skipped_empty"] += 1
                continue

            # Flow : depuis le manifest si disponible, sinon classif dynamique
            flow = flow_by_name.get(name) or detect_flow(parsed.text)

            if dry_run:
                stats["ok"] += 1
                stats[f"by_pays_{country}"] = stats.get(f"by_pays_{country}", 0) + 1
                stats[f"by_flow_{flow}"] = stats.get(f"by_flow_{flow}", 0) + 1
                if stats["ok"] <= 5 or stats["ok"] % 500 == 0:
                    click.echo(f"  [dry] {country}/{flow} {name} (dur={parsed.duree}s, "
                               f"len={len(parsed.text)}c)")
                continue

            try:
                assert conn is not None
                upsert_transcript(
                    conn,
                    drive_file_id=f"local:{name}",
                    file_name=name,
                    pays=country,
                    langue=langue,
                    n_tel=n_tel_from_filename(name),
                    n_appel=n_appel_from_filename(name),
                    size_bytes=path.stat().st_size,
                    flow=flow,
                    raw_text=parsed.text,
                    duree_secondes=parsed.duree,
                )
                stats["ok"] += 1
                stats[f"by_pays_{country}"] = stats.get(f"by_pays_{country}", 0) + 1
                stats[f"by_flow_{flow}"] = stats.get(f"by_flow_{flow}", 0) + 1

                if stats["ok"] % batch_size == 0:
                    elapsed = time.time() - t0
                    rate = stats["ok"] / elapsed if elapsed else 0
                    click.echo(f"  +{stats['ok']:>5d} transcripts ingérés "
                               f"({rate:.0f}/s, {elapsed:.0f}s)")
            except Exception as e:
                click.echo(f"  ! {name}: db error: {e}")
                stats["errors"] += 1

    finally:
        if conn:
            conn.close()

    elapsed = time.time() - t0
    click.echo(f"\n=== STATS FINALES ===")
    click.echo(f"  Durée totale     : {elapsed:.1f}s")
    click.echo(f"  Ingérés OK       : {stats['ok']}")
    click.echo(f"  Filtre pays      : {stats['skipped_filter']}")
    click.echo(f"  Skipped (vide)   : {stats['skipped_empty']}")
    click.echo(f"  Erreurs          : {stats['errors']}")
    click.echo(f"  Par pays         : "
               + ", ".join(f"{k.split('_')[-1]}={v}"
                          for k, v in stats.items() if k.startswith("by_pays_") and v))
    click.echo(f"  Par flow         : "
               + ", ".join(f"{k.split('_', 2)[-1]}={v}"
                          for k, v in stats.items() if k.startswith("by_flow_") and v))

    if dry_run:
        click.echo("\n  (Dry-run : rien n'a été écrit en DB. Relance sans --dry-run pour persister.)")


if __name__ == "__main__":
    main()
