"""CLI : lance un batch d'audit sur un dossier Drive."""
from __future__ import annotations

import click

from afm_audit.audit import audit_drive_folder
from afm_audit.config import settings


@click.command()
@click.option("--folder-id", default=None, help="ID du dossier Drive (defaut: premier de DRIVE_FOLDER_IDS_TRANSCRIPTS).")
@click.option("--audit-version", default="v2_python", help="Tag d'audit (ex: v1, v2_calibration).")
def main(folder_id: str | None, audit_version: str) -> None:
    folder_id = folder_id or (settings.transcripts_folder_ids or [None])[0]
    if not folder_id:
        raise click.UsageError("Pas de folder_id : passe --folder-id ou remplis DRIVE_FOLDER_IDS_TRANSCRIPTS.")

    click.echo(f"Audit du dossier Drive {folder_id} (version={audit_version})")
    results = audit_drive_folder(folder_id, audit_version=audit_version)

    ok = sum(1 for r in results if "audit_id" in r)
    skipped = sum(1 for r in results if r.get("skipped"))
    errors = sum(1 for r in results if "error" in r)
    click.echo(f"\nTermine : {ok} audites / {skipped} skipped (trop courts) / {errors} erreurs")

    if errors:
        click.echo("\nErreurs :")
        for r in results:
            if "error" in r:
                click.echo(f"  - {r.get('file_name', '?')} : {r['error'][:100]}")


if __name__ == "__main__":
    main()
