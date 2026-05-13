"""Smoke test : verifie que Postgres, MinIO et Anthropic sont accessibles."""
from __future__ import annotations

import sys
from pathlib import Path

# Ajouter src/ au PYTHONPATH si on lance le script depuis scripts/
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_config() -> bool:
    print("\n[1/4] Chargement config (.env)...", end=" ")
    try:
        from afm_audit.config import settings
        assert settings.anthropic_api_key.startswith("sk-ant-"), "Anthropic key manquante"
        print("OK")
        return True
    except Exception as e:
        print(f"ECHEC : {e}")
        return False


def test_postgres() -> bool:
    print("[2/4] Connexion Postgres + tables...", end=" ")
    try:
        from afm_audit.db import get_connection
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM information_schema.tables WHERE table_schema = 'public'")
            row = cur.fetchone()
            n = row["n"]
        assert n >= 5, f"5 tables attendues, trouve {n}"
        print(f"OK ({n} tables)")
        return True
    except Exception as e:
        print(f"ECHEC : {e}")
        return False


def test_minio() -> bool:
    print("[3/4] Connexion MinIO + bucket...", end=" ")
    try:
        from afm_audit.config import settings
        from afm_audit.storage import get_s3_client
        client = get_s3_client()
        buckets = client.list_buckets()
        names = [b["Name"] for b in buckets.get("Buckets", [])]
        assert settings.s3_bucket in names, f"bucket {settings.s3_bucket} introuvable"
        print(f"OK (bucket {settings.s3_bucket} trouve)")
        return True
    except Exception as e:
        print(f"ECHEC : {e}")
        return False


def test_anthropic() -> bool:
    print("[4/4] Appel Anthropic (ping minimal)...", end=" ")
    try:
        from anthropic import Anthropic
        from afm_audit.config import settings
        client = Anthropic(api_key=settings.anthropic_api_key)
        resp = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=20,
            messages=[{"role": "user", "content": "Reponds uniquement par 'pong'."}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text").strip().lower()
        assert "pong" in text, f"Reponse inattendue: {text!r}"
        print(f"OK (modele={settings.anthropic_model}, tokens={resp.usage.input_tokens}->{resp.usage.output_tokens})")
        return True
    except Exception as e:
        print(f"ECHEC : {e}")
        return False


def main() -> int:
    print("=== SMOKE TEST AFM Audit Pipeline ===")
    results = [
        test_config(),
        test_postgres(),
        test_minio(),
        test_anthropic(),
    ]
    print()
    if all(results):
        print("[OK] Tous les checks ont passe. Le pipeline est pret.")
        return 0
    print("[KO] Au moins un check a echoue. Voir les messages ci-dessus.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
