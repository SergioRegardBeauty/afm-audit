# Atlas For Men — Audit IA des appels service client

Pipeline d'audit qualité IA des appels téléphoniques **Atlas For Men** (Cde Tél + SAV) sur les marchés FR, GB, DE, PL, CZ. Génère des audits structurés selon les grilles AFM `BQ_1_CdesTel` et `BQ_4_Sav`.

> ⚠️ **Repo privé — propriétaire**. Contient des prompts et de la méthodologie métier confidentielle. Ne pas forker / partager.

## Vue d'ensemble

- **Volume traitable** : ~5500 transcripts (1 mois de données Dialoga, 5 pays)
- **LLM** : Anthropic Claude Sonnet 4.6
- **Grilles** : 15 critères Cde Tél (BQ_1), 16 critères SAV (BQ_4)
- **3 phases projet** : Conception → Test 100 appels (Dialoga flow isolé) → Prod 50%+

## Architecture

```
┌─────────────────────┐
│  Drive folder       │   transcripts CSV + recordings MP3 (Dialoga)
│  (data, hors repo)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Pipeline d'audit (ce repo)             │
│  ├── pipeline/        (Python scripts)  │
│  ├── prompts/         (grilles IA)      │
│  ├── n8n/             (workflows)       │
│  └── kickoff/         (infra & guides)  │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Outputs (hors repo, sur Drive/DB)      │
│  - Google Sheet : 10 onglets/pays-flux  │
│  - Excel BQ_1/BQ_4 par pays remplis     │
│  - JSON par audit (avec justifications) │
│  - Postgres : transcripts + audits      │
└─────────────────────────────────────────┘
```

## Structure du repo

| Dossier | Rôle |
|---------|------|
| `pipeline/` | Scripts Python : classification, échantillonnage, remplissage Excel |
| `prompts/` | Prompts AFM Cde Tél (v1) + SAV (v1) — IP métier |
| `n8n/` | Workflow n8n (Drive → Claude → Sheets) + Apps Script pour onglets |
| `kickoff/` | Squelette repo Python prod (Docker, Postgres, S3) + guides setup |
| `Audit_Dialoga_AtlasForMen_2026-05-10 (1).md` | Audit initial portail Dialoga (numéros, IVR, queues, agents, KPIs) |
| `BQ_1_CdesTel_10 (2).xlsx` | Template AFM Cde Tél (vide) |
| `BQ_4_Sav_10_ (2).xlsx` | Template AFM SAV (vide) |

## Ce qui est EXCLU du repo (RGPD + secret métier)

- ❌ Transcripts CSV bruts (dossiers `Atlas FR/`, `Atlas EN/`, etc.)
- ❌ Audits JSON générés (`audits_ia/v1/`, `output/<PAYS>/audits_json/`)
- ❌ Excel remplis avec données clients (`output/<PAYS>/BQ_*.xlsx`)
- ❌ Recordings MP3
- ❌ Service account JSON, clés API (`.env`, `service_account.json`)
- ❌ Snapshots Dialoga

Voir `.gitignore` pour la liste exhaustive.

## Démarrage rapide

### 1. Cloner et installer Python deps

```powershell
git clone git@github.com:<TON_USER>/afm-audit.git
cd afm-audit
python -m venv .venv
.venv\Scripts\activate
pip install -r kickoff/repo_skeleton/requirements.txt
```

### 2. Variables d'environnement

```powershell
cp kickoff/repo_skeleton/.env.example .env
# Editer .env avec ANTHROPIC_API_KEY, GOOGLE_APPLICATION_CREDENTIALS, ...
```

### 3. Récupérer les données (hors repo)

- Placer les transcripts CSV dans `corpus/` (gitignored) OU les laisser sur Google Drive
- Service account Google Drive (cf. `kickoff/guides/04_google_drive_service_account.md`)

### 4. Lancer un audit

```powershell
# Via Python local
python pipeline/classify_and_sample.py
python pipeline/fill_excel.py

# OU via n8n (recommandé pour automatisation)
# Cf. n8n/README.md
```

## Méthodologie d'audit

Voir `kickoff/CHECKLIST.md` pour la checklist complète et les 7 guides détaillés.

3 phases :

1. **Conception** : analyse historique + calibration sur gold standard humain (5-10 audits manuels)
2. **Test** : 100 appels routés via flow Dialoga isolé → audit IA → comparaison vs gold standard
3. **Production** : déploiement silencieux 50%+ trafic, kill switch si dérive qualité

## Coûts estimés

| Service | Mensuel | Total projet |
|---------|---------|--------------|
| Anthropic Claude (5533 audits) | — | ~110 € |
| Scaleway Postgres DB-DEV-S | 15 € | — |
| Scaleway Object Storage 50 GB | 1 € | — |
| Deepgram (optionnel, si retranscription) | — | ~90 € |

## Compliance

- **RGPD** : hébergement EU obligatoire (Postgres + S3 Scaleway région Paris/Amsterdam)
- **Traçabilité** : table `audit_log` Postgres pour qui lit quoi
- **Service account Drive** : lecture seule sur les dossiers ciblés uniquement
- **Pas de PII dans le repo Git** (le `.gitignore` couvre, vérifier avant chaque push)

## Status livraisons à date

- ✅ v1 partiel : 2202 audits livrés (40 % du corpus)
- ⏳ v2 cible : 5533 audits + calibration humaine + Postgres EU + S3
- 📋 Voir `kickoff/CHECKLIST.md` pour les indispensables à finaliser cette semaine

## Stack technique

- Python 3.11+
- Anthropic SDK
- google-api-python-client (Drive)
- psycopg + SQLAlchemy (Postgres)
- boto3 (S3-compatible)
- n8n (orchestration low-code)
- Docker Compose (POC local)

## Licence

Code propriétaire. Tous droits réservés. Aucune distribution sans autorisation écrite.
