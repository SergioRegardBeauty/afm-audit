# Kickoff Atlas For Men — Checklist d'indispensables

Date : 2026-05-12

## A. INDISPENSABLE POUR DÉMARRER (cette semaine)

| # | Item | Status | Action requise |
|---|------|--------|----------------|
| 1 | Python 3.11+ | ✅ Python 3.13.12 installé | Rien |
| 2 | Docker | ❌ Pas installé | [Installer Docker Desktop](guides/01_docker_install.md) |
| 3 | Git | ✅ Git 2.53 installé | Rien |
| 4 | Claude Code | ✅ Tu l'utilises maintenant via VS Code | Rien |
| 5 | Repo Git privé | ⏳ Squelette généré dans `kickoff/repo_skeleton/` | [Pousser sur GitHub privé](guides/02_git_repo_setup.md) |
| 6 | Clé API Anthropic | ⏳ À créer (tu en as une pour n8n, à dupliquer ou réutiliser) | [Guide](guides/03_anthropic_api_key.md) |
| 7 | Service account Google Drive | ⏳ À créer | [Guide pas-à-pas](guides/04_google_drive_service_account.md) |
| 8 | CSV transcripts complets | ✅ Présents dans le projet (5533 CSV, 5 pays) | Rien — déjà dans le repo |
| 9 | Échantillon de ~5 audits humains existants | ❓ **À me fournir** | Voir question en bas |

## B. POUR LA PRODUCTION (semaines 2-4)

| # | Item | Status | Action requise |
|---|------|--------|----------------|
| 10 | Postgres EU (RGPD) | ⏳ Choix à faire : local Docker (POC) ou Scaleway managé (prod) | [Guide](guides/05_postgres_setup.md) |
| 11 | Stockage objet S3-compatible EU | ⏳ Choix à faire : Scaleway Object Storage (~5 €/mois) ou MinIO self-host | [Guide](guides/06_s3_storage.md) |
| 12 | Clé API Deepgram ou AssemblyAI | ⏳ Décision après QA des CSV existants (si retranscription nécessaire) | [Guide comparatif](guides/07_asr_providers.md) |

## Statut global

**Bloquant immédiat (à faire dans les 48h) :**
1. Installer Docker (≈10 min)
2. Créer clé API Anthropic ou retrouver celle déjà utilisée dans n8n (≈5 min)
3. Créer le service account Google Drive (≈15 min)
4. Pousser le repo Git privé (≈5 min, je te génère le contenu)
5. **Me fournir les 5 audits humains** (≈15 min pour les exporter)

**Non bloquant (semaine 2+) :**
6. Postgres / S3 : on peut démarrer en local Docker pour la POC, on migrera après
7. ASR : on décide après QA des CSV existants (déjà faite — voir [output/SUMMARY.md](../output/SUMMARY.md))

## Pré-générés dans ce kickoff

```
kickoff/
├── CHECKLIST.md                          ← ce fichier
├── repo_skeleton/                        ← squelette du repo Git à pousser
│   ├── .gitignore
│   ├── .env.example
│   ├── docker-compose.yml                ← Postgres + MinIO en local pour POC
│   ├── requirements.txt                  ← deps Python
│   ├── README.md
│   ├── src/afm_audit/                    ← package Python
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── drive.py                      ← stub Google Drive client
│   │   ├── llm.py                        ← stub Anthropic client
│   │   ├── audit.py                      ← logique audit (réutilise prompts/audit_*_v1.md)
│   │   ├── db.py                         ← schéma Postgres
│   │   └── storage.py                    ← stub S3 client
│   ├── sql/001_init.sql                  ← schéma DB initial
│   ├── scripts/run_audit_batch.py
│   └── tests/test_audit.py
└── guides/                               ← guides pas-à-pas par item
    ├── 01_docker_install.md
    ├── 02_git_repo_setup.md
    ├── 03_anthropic_api_key.md
    ├── 04_google_drive_service_account.md
    ├── 05_postgres_setup.md
    ├── 06_s3_storage.md
    └── 07_asr_providers.md
```

## Question à toi

Les **5 audits humains** déjà faits par tes équipes selon la grille — tu en as ? Idéalement :
- Au format Excel BQ_1 / BQ_4 rempli à la main par un superviseur
- 5 lignes minimum (idéalement 3 Cde Tél + 2 SAV)
- Avec les notes et commentaires d'un évaluateur humain

C'est mon **training set** pour mesurer l'écart IA vs humain et calibrer le prompt. Sans ce gold standard, je ne peux pas garantir la qualité avant la mise en prod.

Si tu n'en as pas, deux options :
- (a) Faire auditer 5 appels par un superviseur AFM dès cette semaine (1-2h de travail)
- (b) Démarrer sans calibration et accepter un risque qualité plus élevé en phase Test

Réponds-moi sur ces deux points pour qu'on avance :
1. Est-ce que tu as des audits humains existants ?
2. Si non, est-ce qu'AFM peut en produire 5 cette semaine ?
