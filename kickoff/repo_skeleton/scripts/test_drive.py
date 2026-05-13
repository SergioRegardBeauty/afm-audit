"""Test connexion Google Drive : liste les premiers fichiers du dossier transcripts."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from afm_audit.config import settings  # noqa: E402
from afm_audit.drive import list_files_in_folder  # noqa: E402


def main() -> int:
    print("=== TEST CONNEXION DRIVE ===\n")

    # 1. Vérifier le fichier service account
    sa_path = Path(settings.google_application_credentials)
    print(f"[1/3] Service account JSON : {sa_path}", end=" ")
    if not sa_path.exists():
        print(f"\n  ECHEC : fichier introuvable. Place 'service_account.json' a la racine de repo_skeleton/.")
        return 1
    print(f"OK ({sa_path.stat().st_size} bytes)")

    # 2. Vérifier qu'on a au moins un folder ID
    folders = settings.transcripts_folder_ids
    print(f"[2/3] DRIVE_FOLDER_IDS_TRANSCRIPTS : {folders}", end=" ")
    if not folders:
        print(f"\n  ECHEC : aucun folder ID dans .env. Mets DRIVE_FOLDER_IDS_TRANSCRIPTS=<id>.")
        return 1
    print("OK")

    # 3. Lister le contenu du premier dossier
    folder_id = folders[0]
    print(f"\n[3/3] Liste des fichiers du dossier {folder_id}...")
    try:
        files = list_files_in_folder(folder_id)
    except Exception as e:
        print(f"  ECHEC : {e}")
        print("\n  -> Verifie que tu as PARTAGE le dossier Drive avec l'email du service account.")
        print(f"  -> Email du SA : voir 'client_email' dans {sa_path.name}")
        return 1

    print(f"  {len(files)} fichiers trouves dans le dossier.")
    if files:
        print("\n  Echantillon (5 premiers) :")
        for f in files[:5]:
            size_kb = f.size / 1024 if f.size else 0
            print(f"    - {f.name} ({size_kb:.1f} KB) [{f.mime_type}]")
    else:
        print("  ! Dossier vide. Verifie que le folder_id est bon et qu'il contient des CSV.")

    print(f"\n[OK] Connexion Drive fonctionnelle. {len(files)} fichiers accessibles.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
