# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project at a glance

Pipeline d'audit qualité IA des appels téléphoniques **Atlas For Men** (Cde Tél + SAV) sur 5 marchés (FR, GB, DE, PL, CZ). Les transcripts CSV produits par HappyScribe via n8n sont notés selon les grilles officielles AFM (`BQ_1_CdesTel` pour les commandes tel, `BQ_4_Sav` pour le SAV) à l'aide de **Claude Sonnet 4.6**. Cible v2 : 5 533 audits ; v1 partiel livré = 2 202 audits.

Le projet vit en 3 phases : Conception (calibration sur gold standard humain) → Test (100 appels routés via flow Dialoga isolé) → Production (déploiement silencieux ≥ 50 % trafic, kill switch sur dérive qualité).

Le `README.md` et `kickoff/CHECKLIST.md` sont les deux documents de référence — toujours s'aligner sur eux avant de partir dans une direction qui pourrait dévier du plan.

## Architecture du repo

```
pipeline/   scripts Python séquentiels (classify → chunk → audit → fill_excel)
prompts/    audit_cde_tel_v1.md + audit_sav_v1.md — IP métier, prompts officiels
n8n/        workflow LangChain ChainLlm (Drive → Claude → Sheets) + Apps Script
kickoff/    CHECKLIST + 7 guides setup + repo_skeleton (Python prod-ready)
output/     Excel BQ remplis par pays (gitignored)
audits_ia/  JSON par audit (gitignored)
corpus/     transcripts CSV bruts (gitignored)
docs/       décisions et notes projet
```

Le data flow par défaut est **CSV transcripts (corpus/) → classify_and_sample.py → manifest.json → make_subagent_chunks.py → audit IA (subagents ou Claude direct via n8n) → JSON dans audits_ia/v1/ → fill_excel.py → output/{PAYS}/BQ_*.xlsx**.

## Conventions critiques

### RGPD — `.gitignore` non négociable
Le `.gitignore` exclut **toutes les données PII** : transcripts CSV (`Atlas FR/`, `Atlas EN/`, etc.), audits JSON (`audits_ia/`, `output/*/audits_json/`), recordings (`**/*.mp3`), Excel remplis (`output/*/BQ_*.xlsx`), secrets (`.env`, `service_account*.json`). **Ne jamais commit ces fichiers**. Vérifier `git status` avant chaque push.

### n8nac — `AGENTS.md` impose des règles
- Toujours exécuter `npx --yes n8nac ...` depuis le context root (cette racine), jamais depuis un sous-dossier
- Ne jamais éditer à la main `n8nac-config.json`, `~/.n8n-manager`, ni les fichiers secrets n8n-manager
- Avant toute commande workflow, faire en séquence : `n8nac workspace migrate --json` puis `n8nac workspace status --json` ; utiliser `workflowDir` retourné tel quel (chemin opaque, ne pas le reconstruire)
- L'agent de référence pour n8n est `.github/agents/n8n-architect.agent.md` (skill fallback dans `.agents/skills/n8n-architect/SKILL.md`)

### Grilles AFM — sources de vérité
- Templates Excel **vides** : `BQ_1_CdesTel_10 (2).xlsx` (Cde Tél, 15 critères) et `BQ_4_Sav_10_ (2).xlsx` (SAV, 16 critères). Ne jamais modifier ces fichiers — `fill_excel.py` les copie puis remplit.
- Mapping critère → cellule Excel codé en dur dans `pipeline/fill_excel.py` (constantes `CDE_TEL_COLS` / `SAV_COLS`).
- Prompts IA : `prompts/audit_cde_tel_v1.md` et `prompts/audit_sav_v1.md`. **Toute modification de la grille AFM impose de patcher conjointement** : le prompt, le mapping Excel, le format JSON consommé par `fill_excel.py`. Versionner via le suffixe (`_v2`, etc.).

### Méta métier à respecter dans tout audit
- Clientèle AFM = **senior 60+**, sensible à l'accueil et au climat
- Norme d'accueil : « Atlas for Men, [prénom], bonjour » — l'ASR Dialoga la **transcrit mal massivement** (« la plateforme », « la classe formelle », « Atlas Amenities », « Atlas Forman »...). Ne **pas sanctionner sur cette base sans validation audio** (cf. `output/SUMMARY.md` section "Erreurs ASR systémiques flaggées")
- Paiement CB = enregistrement DOIT être désactivé pendant dictée puis réactivé (PCI-DSS, SI grave sinon)
- Code avantage = à demander en début de commande systématiquement

## Commandes principales

### Setup initial
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r kickoff/repo_skeleton/requirements.txt
copy kickoff\repo_skeleton\.env.example .env
# remplir .env : ANTHROPIC_API_KEY, GOOGLE_APPLICATION_CREDENTIALS, ...
```

### Pipeline d'audit (séquence canonique, depuis la racine)
```powershell
python pipeline\auto_na_audits.py         # 1. NA auto pour <500B (silences/raccrochés)
python pipeline\classify_and_sample.py    # 2. Cde Tél vs SAV + manifest.json
python pipeline\make_subagent_chunks.py   # 3. découpe en chunks pour subagents
python pipeline\make_subagent_lists.py    # 3b. liste pays/flux pour prompts subagent
# 4. Audit IA — soit subagents Claude (manuel), soit n8n workflow (auto)
python pipeline\fill_excel.py             # 5. JSON → Excel BQ par pays
```

### n8n (workflow Drive → Claude → Sheets)
```powershell
npx --yes n8nac workspace migrate --json
npx --yes n8nac workspace status --json
# puis les commandes pull/push/validate selon besoin
```

### Repo skeleton Python (kickoff/repo_skeleton/, projet prod-ready à pousser sur GitHub privé)
```powershell
cd kickoff\repo_skeleton
python scripts\smoke_test.py            # vérifie env + accès Drive + Anthropic
python scripts\audit_local_file.py      # un audit one-shot
python scripts\run_audit_batch.py       # batch avec Postgres + S3
```

## Quand modifier quoi

| Besoin | Fichiers à toucher |
|---|---|
| Ajouter un pays | `pipeline/classify_and_sample.py` (`COUNTRY_MAP`) + `pipeline/fill_excel.py` (`COUNTRIES`) + dossier `output/<XX>/` |
| Modifier un critère AFM | `prompts/audit_*_v{N+1}.md` + `pipeline/fill_excel.py` (`*_COLS`) + bump version dans le JSON schema |
| Changer le seuil "fichier silence" | Constante `< 500` octets dans `pipeline/auto_na_audits.py` et `classify_and_sample.py` — garder cohérent |
| Ajouter un check post-audit | `pipeline/` (nouveau script) — ne pas pourrir `fill_excel.py` qui est déjà long |
| Changer le modèle LLM | n8n node "Audit Claude" pour la voie automatisée ; `kickoff/repo_skeleton/src/afm_audit/llm.py` pour la voie Python |

## État du livrable v1

D'après `output/SUMMARY.md` : 2202 audits livrés sur 5533 disponibles (40 %), interrompus 3 fois par le rate-limit Anthropic. Restent ~3206 audits à faire (1860 conversations courtes 500B-3KB + 1118 complètes ≥3KB). Les **SI détectées (rebond commercial GB, PCI-DSS, délai SAV)** doivent être revus manuellement avant toute action RH.

Limitations connues v1 : transcript-only (pas d'audio), pas de gold standard humain (point #9 de la CHECKLIST = bloquant), diarisation ASR imparfaite, 7 JSONs GB SAV corrompus à reprendre.

## Documentation pointer

- État réel des inputs/livrables : [`README.md`](README.md) et [`kickoff/CHECKLIST.md`](kickoff/CHECKLIST.md)
- Résultats du run v1 + patterns détectés : [`output/SUMMARY.md`](output/SUMMARY.md)
- Audit initial du portail Dialoga (numéros, IVR, queues, KPIs) : [`docs/audit_dialoga_2026-05-10.md`](docs/audit_dialoga_2026-05-10.md)
- Workflow n8n détaillé : [`n8n/README.md`](n8n/README.md)
- Guides setup (Docker, Anthropic, Drive, Postgres, S3, ASR) : [`kickoff/guides/`](kickoff/guides/)
