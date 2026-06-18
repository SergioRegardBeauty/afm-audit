# Atlas For Men — Audit IA des appels service client

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.39+-FF4B4B?logo=streamlit&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-Sonnet%204.6-D97757?logo=anthropic&logoColor=white)
![Postgres](https://img.shields.io/badge/Postgres-16-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Status](https://img.shields.io/badge/Status-Phase%201%20en%20cours-yellow)
![License](https://img.shields.io/badge/License-Propriétaire-red)

Pipeline d'audit qualité IA des appels téléphoniques **Atlas For Men** (Commande Tél + SAV) sur les 5 marchés européens. Audit selon les grilles officielles AFM `BQ_1_CdesTel` (15 critères) et `BQ_4_Sav` (16 critères), via Claude Sonnet 4.6.

> ⚠️ **Repo privé Atlas For Men**. Contient prompts métier, méthodologie d'audit et configuration d'infrastructure. **Données clients (transcripts, recordings, audits remplis) jamais commit dans Git** — exigence RGPD documentée dans `.gitignore`.

---

## 🌐 Démo live

L'interface multi-user est déployée sur Streamlit Cloud :

**🔗 https://afm-audit.streamlit.app**

Identifiants de démo (à changer après 1ère connexion) :
- Username : `djibril` (admin) ou `sergio` (auditor)
- Password : voir gestionnaire de mots de passe interne

La page **📤 Auto-audit (upload CSV)** fonctionne immédiatement sans configuration Postgres : upload de CSV → classification automatique → audit Claude → pack Excel BQ téléchargeable.

---

## 🎯 Vue d'ensemble

Atlas For Men gère **~5 500 appels téléphoniques par mois** sur 5 marchés (FR, GB, DE, PL, CZ), répartis entre :
- 🛒 **Commande Tél** : nouvelle commande par téléphone
- 🛠️ **SAV** : suivi commande, remboursement, réclamation

Le projet automatise l'**audit qualité** de ces appels en :
1. Ingérant les transcripts CSV produits par HappyScribe (via n8n)
2. Classifiant chaque appel (pays + flow Cde Tél / SAV)
3. Lançant Claude Sonnet 4.6 sur chaque transcript avec la grille AFM
4. Produisant un fichier Excel BQ rempli (1 par pays × flow) avec scores critère par critère

Objectif final : **un IVR augmenté IA** déployé silencieusement sur 50 % du trafic Atlas, conçu à partir des patterns d'intents extraits du corpus audité.

---

## 📊 Statut d'avancement

| Phase | Statut | Détail |
|---|---|---|
| **0 — Cadrage** | ✅ Fait | Audit Dialoga + inventaire 459 services + 196 agents + grilles AFM |
| **1 — Conception (audit IA)** | 🟢 En cours | **2 202 / 5 533 audits livrés** (40 %, run v1 partiel par rate-limit Anthropic) |
| **1bis — Calibration humaine** | 🟡 Bloqué | En attente des **5-10 audits humains de référence** (cf. `kickoff/CHECKLIST.md` #9) |
| **2 — Test 100 appels live** | ⏳ Pas démarré | Nécessite Phase 1 + 1bis validées (audits IA ≥ 90 % d'accord avec grille humaine) |
| **3 — Déploiement progressif** | ⏳ Pas démarré | 5 % → 20 % → 50 % du trafic Atlas, kill switch sur dérive qualité |

**Cible totale** : 10–14 semaines pour atteindre 50 % du trafic.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  Source — Drive folder (hors repo, RGPD)                             │
│  ├── Transcription MP3/   5 538 CSV HappyScribe (5 pays)             │
│  └── Audio MP3/           15 637 MP3 (recordings Dialoga, ~3.2 GB)   │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Pipeline d'audit IA — ce repo                                       │
│                                                                      │
│  pipeline/         Scripts Python séquentiels                        │
│    ├── classify_and_sample.py     CSV → Cde Tél / SAV / Unknown      │
│    ├── auto_na_audits.py          NA auto pour <500 B (silences)     │
│    ├── make_subagent_chunks.py    Découpe en chunks pour subagents   │
│    └── fill_excel.py              JSON audits → Excel BQ par pays    │
│                                                                      │
│  prompts/          IP métier — grilles AFM officielles               │
│    ├── audit_cde_tel_v1.md        15 critères Commande Tél           │
│    └── audit_sav_v1.md            16 critères SAV                    │
│                                                                      │
│  n8n/              Workflow LangChain Drive → Claude → Sheets        │
│  kickoff/          Setup + repo prod-ready (Postgres + S3 + UI)      │
│  tools/            Scripts d'introspection / migration ponctuels     │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Outputs (hors repo, RGPD)                                           │
│  ├── output/<PAYS>/BQ_*.xlsx      Excels remplis par pays            │
│  ├── audits_ia/v1/<PAYS>/<flow>/  2 202 JSON d'audit (1 par appel)   │
│  ├── Google Sheet                 10 onglets pays × flow (live)      │
│  └── Postgres (Supabase / local)  5 473 transcripts + audits IA      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick start

### Pour explorer le code (5 min)

```bash
git clone https://github.com/SergioRegardBeauty/afm-audit.git
cd afm-audit
cat README.md kickoff/CHECKLIST.md output/SUMMARY.md
```

### Pour lancer l'interface web Streamlit (15 min)

L'interface multi-user permet à 5–10 collègues de lancer leurs audits eux-mêmes :

```powershell
cd kickoff/repo_skeleton

# 1. Postgres local via Docker
docker compose up -d postgres

# 2. Environnement Python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. .env (copier .env.example et remplir ANTHROPIC_API_KEY)
copy .env.example .env

# 4. Ingérer les 5 538 CSV dans Postgres
python scripts/ingest_local_transcripts.py --root "../../Transcription MP3" --use-manifest

# 5. Lancer l'interface web
streamlit run app/streamlit_app.py
# → http://localhost:8501
```

Détails dans [`kickoff/repo_skeleton/SETUP_POSTGRES.md`](kickoff/repo_skeleton/SETUP_POSTGRES.md).

### Pour déployer en production sur Scaleway (Paris, RGPD EU)

Voir [`kickoff/repo_skeleton/DEPLOY_CLOUD.md`](kickoff/repo_skeleton/DEPLOY_CLOUD.md). Budget ~21 €/mois infra fixe + API Anthropic à l'usage.

### Pour pipeliner sans UI (audit massif backend)

```powershell
python pipeline\auto_na_audits.py          # NA auto pour <500B
python pipeline\classify_and_sample.py     # Cde Tél vs SAV + manifest
python pipeline\make_subagent_chunks.py    # Chunks pour subagents
# … lancer audits IA via n8n ou subagents Claude …
python pipeline\fill_excel.py              # JSON → Excel BQ par pays
```

---

## 📈 Résultats du run v1 (livraison partielle)

D'après [`output/SUMMARY.md`](output/SUMMARY.md) :

| Pays | Cde Tél audités | SAV audités | Total audités | Disponible |
|------|---:|---:|---:|---:|
| FR | 775 | 370 | **1 145** | 2 465 |
| GB | 711 | 47 | **758** | 1 887 |
| DE | 185 | 69 | **254** | 1 124 |
| PL | 20 | 3 | **23** | 33 |
| CZ | 19 | 3 | **22** | 24 |
| **Total** | **1 710** | **492** | **2 202** | **5 533** |

**Patterns systémiques détectés** (cf. `output/SUMMARY.md`) :
- Accueil normé Atlas For Men : < 15 % de conformité (mais l'ASR Dialoga le transcrit mal massivement, donc à valider avec audio)
- Prise de congé normée : < 10 %
- Rebond commercial GB Cde Tél : ~50 % de SI (1 seule proposition au lieu de 2)
- PCI-DSS : annonce "I'll secure the line" présente, mais réactivation enregistrement quasi-jamais explicite

**Tous les SI doivent être revus manuellement** par un superviseur avec l'enregistrement audio avant toute action RH.

---

## 🧱 Stack technique

| Composant | Choix | Pourquoi |
|---|---|---|
| LLM | Anthropic Claude Sonnet 4.6 | Qualité grille AFM, multilingue (FR/EN/DE/PL/CZ) |
| ASR existant | HappyScribe (Whisper) | Transcripts CSV déjà produits par Sergio via n8n |
| Orchestration audit | n8n workflow + scripts Python | Trigger Drive → Claude → Sheets, ou pipeline manuel |
| Base de données | Postgres 16 + pgvector | Stockage transcripts + audits, prêt clustering embeddings |
| Stockage objet | MinIO local / Scaleway S3 EU | Backup CSV + MP3 dans bucket privé EU |
| Interface web | Streamlit + bcrypt + cookies | UI multi-user simple, déployable sur Streamlit Cloud ou VM |
| Hébergement | Local Docker → Scaleway Paris | RGPD EU obligatoire (recordings = PII voix) |

---

## 📚 Documentation détaillée

- **[`kickoff/CHECKLIST.md`](kickoff/CHECKLIST.md)** — Indispensables avant de lancer + statut de chaque pré-requis
- **[`output/SUMMARY.md`](output/SUMMARY.md)** — Résultats détaillés du run v1 (patterns, limitations, SI)
- **[`docs/audit_dialoga_2026-05-10.md`](docs/audit_dialoga_2026-05-10.md)** — Audit du portail Dialoga (459 services, 196 agents, capacités IA dispo)
- **[`docs/B2T_API_DISCOVERY.md`](docs/B2T_API_DISCOVERY.md)** — Discovery complet de l'API CRM B2T Atlas (28 opérations SOAP)
- **[`kickoff/repo_skeleton/SETUP_POSTGRES.md`](kickoff/repo_skeleton/SETUP_POSTGRES.md)** — Procédure setup DB locale + ingestion 5 538 CSV
- **[`kickoff/repo_skeleton/DEPLOY_CLOUD.md`](kickoff/repo_skeleton/DEPLOY_CLOUD.md)** — Déploiement Scaleway (Postgres + VM + Streamlit + HTTPS)
- **[`GITHUB_SETUP.md`](GITHUB_SETUP.md)** — Procédure clone repo + pre-commit hook anti-PII
- **[`n8n/README.md`](n8n/README.md)** — Workflow LangChain ChainLlm détaillé
- **[`kickoff/guides/`](kickoff/guides/)** — 7 guides setup (Docker, Anthropic, Drive, Postgres, S3, ASR)
- **[`CLAUDE.md`](CLAUDE.md)** — Guide pour les sessions Claude Code futures
- **[`AGENTS.md`](AGENTS.md)** — Configuration n8n-as-code

---

## 🔒 RGPD & sécurité

Le `.gitignore` exclut **toutes les données PII** :
- Recordings MP3 (voix clients = donnée biométrique RGPD art. 9)
- Transcripts CSV (contiennent noms, adresses, n° commande)
- Audits JSON et Excel remplis (contiennent PII des transcripts)
- Secrets : `.env`, `service_account*.json`, `users.yaml`
- Dumps SQL pouvant contenir PII

Un **pre-commit hook** (`.git-hooks/pre-commit`) bloque tout commit accidentel de ces fichiers. À activer après clone : `git config core.hooksPath .git-hooks`.

Hébergement obligatoire : **Union Européenne** (Paris ou Amsterdam) — Scaleway choisi par défaut.

---

## 👥 Équipe

- **Owner projet** : Djibril (dev@regardbeauty.com)
- **Pipeline n8n + transcripts** : Sergio Hazary (sergiohazary@gmail.com)
- **Stack IA** : Claude Sonnet 4.6 (Anthropic) — clé API Anthropic requise

---

_Repo géré avec [Claude Code](https://claude.com/claude-code) (Anthropic) — assistance technique sur la pipeline + l'infrastructure._
