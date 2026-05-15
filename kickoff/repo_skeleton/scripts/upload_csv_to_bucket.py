"""Upload CSV transcripts → S3-compatible bucket (Scaleway Object Storage).

Idempotent : skip si l'objet existe déjà avec le bon ETag (md5).
Reprend l'arborescence : <pays>/<basename>.mp3.csv.

Usage :
    python scripts/upload_csv_to_bucket.py --root "/path/to/Transcription MP3"
    python scripts/upload_csv_to_bucket.py --root "../.." --pays FR,GB --dry-run

Dépendances : boto3 (déjà dans requirements.txt).
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import boto3
import click
from botocore.exceptions import ClientError

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from afm_audit.audit import detect_pays_langue  # noqa: E402
from afm_audit.config import settings  # noqa: E402


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        use_ssl=settings.s3_use_ssl,
    )


def md5_file(path: Path) -> str:
    h = hashlib.md5()  # noqa: S324 — only used as ETag check, not for security
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@click.command()
@click.option("--root", "root_path", type=click.Path(exists=True, file_okay=False),
              required=True, help="Dossier racine contenant les CSV.")
@click.option("--pays", type=str, default="",
              help="Filtrer par pays détecté (ex: 'FR' ou 'FR,GB').")
@click.option("--limit", type=int, default=0, help="0 = pas de limite.")
@click.option("--dry-run", is_flag=True, help="Liste les fichiers sans upload.")
def main(root_path: str, pays: str, limit: int, dry_run: bool) -> None:
    root = Path(root_path)
    pays_filter = {p.strip().upper() for p in pays.split(",") if p.strip()} if pays else None

    s3 = None if dry_run else get_s3_client()
    bucket = settings.s3_bucket

    click.echo(f"=== Upload CSV → s3://{bucket}/ ===")
    click.echo(f"  Endpoint : {settings.s3_endpoint_url}")
    click.echo(f"  Region   : {settings.s3_region}")
    click.echo(f"  Pays     : {sorted(pays_filter) if pays_filter else 'tous'}")
    click.echo(f"  Dry-run  : {dry_run}")

    if not dry_run:
        # Vérifier que le bucket existe
        try:
            s3.head_bucket(Bucket=bucket)
        except ClientError as e:
            raise click.ClickException(f"Bucket '{bucket}' inaccessible : {e}")

    csv_files = sorted(root.rglob("*.mp3.csv"))
    click.echo(f"  CSV détectés : {len(csv_files)}")

    stats = {"uploaded": 0, "skipped_same": 0, "skipped_filter": 0, "errors": 0}

    for i, path in enumerate(csv_files, 1):
        if limit and (stats["uploaded"] + stats["skipped_same"]) >= limit:
            break

        country, _ = detect_pays_langue(path.name)
        if pays_filter and country not in pays_filter:
            stats["skipped_filter"] += 1
            continue

        key = f"{country}/{path.name}"

        if dry_run:
            click.echo(f"  [dry] {key}  ({path.stat().st_size} B)")
            stats["uploaded"] += 1
            continue

        # Idempotence : compare md5 avec l'ETag s'il existe
        local_md5 = md5_file(path)
        try:
            head = s3.head_object(Bucket=bucket, Key=key)
            remote_etag = head["ETag"].strip('"')
            if remote_etag == local_md5:
                stats["skipped_same"] += 1
                if i % 200 == 0:
                    click.echo(f"  ({i}/{len(csv_files)}) {stats}")
                continue
        except ClientError as e:
            if e.response["Error"]["Code"] not in ("404", "NoSuchKey", "NotFound"):
                click.echo(f"  ! {key}: head error {e}")
                stats["errors"] += 1
                continue
            # 404 = pas encore uploadé, on continue

        try:
            s3.upload_file(str(path), bucket, key,
                          ExtraArgs={"ContentType": "text/csv", "ServerSideEncryption": "AES256"})
            stats["uploaded"] += 1
            if stats["uploaded"] % 100 == 0:
                click.echo(f"  +{stats['uploaded']} CSV uploadés ({i}/{len(csv_files)})")
        except ClientError as e:
            click.echo(f"  ! {key}: upload error {e}")
            stats["errors"] += 1

    click.echo("\n=== STATS FINALES ===")
    for k, v in stats.items():
        click.echo(f"  {k:18s} : {v}")
    if dry_run:
        click.echo("\n  (Dry-run : rien n'a été uploadé. Relance sans --dry-run pour persister.)")


if __name__ == "__main__":
    main()
