# Atlas For Men — Audit IA des appels service client

Pipeline d'audit qualité IA des appels téléphoniques Atlas For Men (Cde Tél + SAV) sur les marchés FR, GB, DE, PL, CZ.

## Stack

- **Python 3.11+**
- **Anthropic Claude Sonnet 4.6** pour l'audit IA selon la grille AFM
- **Google Drive** (service account) pour récupérer les transcripts CSV
- **Postgres** (EU, RGPD) pour persistance audits + traçabilité
- **S3-compatible** (Scaleway / MinIO) pour les recordings MP3
- **Docker Compose** pour le POC local

## Démarrage rapide (POC local)

```bash
# 1. Cloner et installer
git clone <ton-repo-prive> afm-audit && cd afm-audit
python -m venv .venv
.venv\Scripts\activate              # Windows
# source .venv/bin/activate          # Linux/Mac
pip install -r requirements.txt

# 2. Variables d'env
cp .env.example .env
# Éditer .env avec : ANTHROPIC_API_KEY, GOOGLE_APPLICATION_CREDENTIALS, etc.

# 3. Service account Google Drive
# Placer le fichier JSON du service account à la racine : service_account.json
# Partager les dossiers Drive avec l'email du service account (lecture seule)

# 4. Démarrer Postgres + MinIO local
docker compose up -d

# 5. Copier les prompts AFM (générés dans le projet principal)
cp -r ../prompts ./prompts

# 6. Lancer un audit batch
python scripts/run_audit_batch.py --folder-id <DRIVE_FOLDER_ID>

# 7. Tests
pytest
```

## Architecture

```
Drive folder (CSV transcripts)
       │
       ▼
┌──────────────────┐
│ src/afm_audit/   │
│  drive.py        │ ◄── service account Google Drive (lecture)
│  audit.py        │ ◄── pipeline : parse CSV + détection pays/flux
│  llm.py          │ ◄── Anthropic Claude (audit selon grille AFM)
│  db.py           │ ◄── Postgres (transcripts + audits)
│  storage.py      │ ◄── S3-compatible (recordings MP3 optionnel)
└──────────────────┘
       │
       ▼
┌──────────────────────┐
│ Postgres EU          │
│  - transcripts       │
│  - audits            │
│  - human_audits      │ ◄── gold standard pour calibration
│  - calibration_results│
│  - audit_log         │ ◄── RGPD : qui voit quoi
└──────────────────────┘
```

## Structure du repo

```
.
├── docker-compose.yml      ← Postgres + MinIO local
├── requirements.txt
├── .env.example
├── src/afm_audit/          ← package Python principal
│   ├── config.py           ← settings centralisés
│   ├── drive.py            ← client Google Drive
│   ├── llm.py              ← wrapper Anthropic
│   ├── audit.py            ← orchestrateur du pipeline
│   ├── db.py               ← accès Postgres
│   └── storage.py          ← client S3
├── sql/001_init.sql        ← schéma DB initial
├── scripts/                ← CLI batch
│   └── run_audit_batch.py
├── tests/
└── prompts/                ← (à copier depuis le projet parent)
    ├── audit_cde_tel_v1.md
    └── audit_sav_v1.md
```

## Variables d'environnement requises

Voir `.env.example`. Au minimum pour démarrer :
- `ANTHROPIC_API_KEY`
- `GOOGLE_APPLICATION_CREDENTIALS` (chemin vers le JSON service account)
- `DRIVE_FOLDER_IDS_TRANSCRIPTS`
- `DATABASE_URL`
- `S3_ACCESS_KEY` / `S3_SECRET_KEY` / `S3_BUCKET`

## RGPD et sécurité

- Hébergement Postgres **obligatoirement en UE** (Scaleway Paris/Amsterdam, OVH, etc.)
- Pas de PII dans le repo Git (le `.gitignore` exclut `data/`, `recordings/`, `transcripts/`)
- Le service account Google Drive a **lecture seule** sur les dossiers ciblés
- Toute action sensible loggée dans `audit_log` (table Postgres)
- Recordings MP3 chiffrés au repos via S3 server-side encryption

## Calibration humaine

Avant la mise en prod, valider avec des audits humains :
1. Importer 5+ audits humains dans la table `human_audits`
2. Lancer le même corpus via `run_audit_batch.py --audit-version=calibration`
3. Comparer écarts via la table `calibration_results`
4. Itérer le prompt si l'écart > 15 % sur la note totale
