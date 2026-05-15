# Setup Postgres + ingestion CSV → DB

Procédure end-to-end pour démarrer la base, créer le schéma et ingérer les 5 538 transcripts CSV de `Transcription MP3/`.

Tout tourne en local via Docker. Aucun service cloud n'est requis pour ce premier setup (Scaleway / S3 / Anthropic API arrivent ensuite).

---

## 1. Pré-requis (à valider une seule fois)

- ✅ **Docker Desktop** lancé (vérifie l'icône baleine dans la barre des tâches Windows ou `docker ps` doit répondre).
- ✅ **Python 3.11+** (`python --version`).
- ✅ Le fichier `.env` rempli dans ce dossier (`kickoff/repo_skeleton/.env`). Au minimum :
  ```
  POSTGRES_DB=afm_audit
  POSTGRES_USER=afm_audit
  POSTGRES_PASSWORD=<un_mdp_local>
  DATABASE_URL=postgresql://afm_audit:<même_mdp>@localhost:5432/afm_audit
  ```

---

## 2. Démarrer Postgres (premier lancement)

```powershell
cd kickoff\repo_skeleton
docker compose up -d postgres
```

- Au **premier** démarrage seulement, Postgres charge automatiquement le schéma depuis `sql/001_init.sql` (via le volume mount `./sql:/docker-entrypoint-initdb.d:ro` du docker-compose).
- Aux redémarrages suivants, le schéma est conservé (volume `postgres_data`).

**Vérifier que c'est bien démarré :**

```powershell
docker ps --filter "name=afm_postgres"
docker exec afm_postgres pg_isready -U afm_audit
# Réponse attendue : "/var/run/postgresql:5432 - accepting connections"
```

**Vérifier que les tables sont créées :**

```powershell
docker exec -it afm_postgres psql -U afm_audit -d afm_audit -c "\dt"
# Doit lister : transcripts, audits, human_audits, calibration_results, audit_log
```

---

## 3. Installer les dépendances Python

```powershell
cd kickoff\repo_skeleton
python -m pip install -r requirements.txt
```

(Si tu préfères un venv : `python -m venv .venv` puis `.venv\Scripts\activate` avant `pip install`.)

---

## 4. Tester l'ingestion à blanc (50 fichiers, sans écrire en DB)

```powershell
cd kickoff\repo_skeleton
python scripts\ingest_local_transcripts.py `
    --root "..\..\Transcription MP3" `
    --dry-run --limit 50 --use-manifest
```

Sortie attendue (extrait) :
```
=== Ingestion CSV → Postgres ===
  CSV détectés : 5538
  Manifest chargé : 4254 entrées avec flow pré-classifié
  …
  Ingérés OK       : 50
  Skipped (vide)   : 11
  Par pays         : FR=31, GB=19
  Par flow         : cde_tel=44, sav=6
```

Si tu vois ça, le parsing + classification fonctionnent ✅.

---

## 5. Lancer l'ingestion réelle (toute la base)

```powershell
cd kickoff\repo_skeleton
python scripts\ingest_local_transcripts.py `
    --root "..\..\Transcription MP3" `
    --use-manifest --batch-size 200
```

Estimation : ~5 538 fichiers × ~10 ms = **~1 minute** wall-clock.

Le script affiche la progression tous les 200 inserts. Idempotent grâce à `ON CONFLICT (drive_file_id) DO UPDATE` — tu peux le relancer sans rien casser.

---

## 6. Requêtes de validation

```powershell
docker exec -it afm_postgres psql -U afm_audit -d afm_audit
```

```sql
-- Volume par pays × flow
SELECT pays, flow, COUNT(*) AS n,
       SUM(size_bytes)/1024/1024 AS total_mb,
       AVG(duree_secondes)::int  AS duree_moy_s
FROM transcripts
GROUP BY pays, flow
ORDER BY pays, flow;

-- Histogramme tailles transcripts
SELECT
  CASE
    WHEN size_bytes < 500   THEN 'NA (<500B)'
    WHEN size_bytes < 3000  THEN 'court (500B-3KB)'
    ELSE 'complet (>=3KB)'
  END AS bucket,
  COUNT(*)
FROM transcripts GROUP BY bucket ORDER BY MIN(size_bytes);

-- Distribution horaire (selon timestamp dans n_appel)
SELECT
  pays,
  EXTRACT(HOUR FROM TO_TIMESTAMP(SUBSTRING(n_appel FROM '_(\d{14})$'), 'YYYYMMDDHH24MISS')) AS heure,
  COUNT(*) AS n
FROM transcripts
WHERE n_appel ~ '_\d{14}$'
GROUP BY pays, heure
ORDER BY pays, heure;
```

---

## 7. Arrêter / redémarrer Postgres

```powershell
docker compose stop postgres        # arrêt propre, conserve les données
docker compose start postgres       # redémarrage rapide
docker compose down                 # arrêt complet (conserve les données via le volume nommé)
docker compose down -v              # ⚠️ supprime AUSSI les données — utile pour repartir de zéro
```

---

## Architecture du schéma (`sql/001_init.sql`)

```
transcripts
  ├── id  (UUID)
  ├── drive_file_id  UNIQUE  ('local:<filename>' pour ingestion locale)
  ├── pays, langue, n_tel, n_appel, duree_secondes, size_bytes
  ├── flow  (cde_tel | sav | unknown)
  └── raw_text  (transcript concaténé pour passage au LLM ensuite)

audits  (1 audit = 1 passage prompt+modèle)
  ├── transcript_id  → transcripts
  ├── audit_version, llm_model, prompt_hash, flow
  ├── note_totale_sur_10, note_sur_100, note_zero_par_SI, si_count
  ├── criteres_jsonb  (15-16 critères structurés)
  ├── si_jsonb        (liste SI détectées)
  └── raw_llm_response

human_audits  (gold standard humain pour calibration)
  ├── transcript_id  → transcripts
  ├── evaluateur, date_audit, flow, note_totale_sur_10
  └── criteres_jsonb, commentaire, source_excel_file

calibration_results  (écart IA vs humain)
  ├── human_audit_id, ia_audit_id  → audits / human_audits
  ├── ecart_note_totale, ecart_par_critere, agreement_global

audit_log  (RGPD : qui accède à quoi)
  └── actor, action, target_id, target_type, details, created_at

VIEW v_latest_audits  (dernier audit par transcript)
```

Toutes les tables ont déjà leurs index (GIN sur les JSONB, B-tree sur les filtres fréquents pays/flow/timestamp).

---

## Prochaine étape (Phase 1.2 du plan global)

Une fois les 5 538 transcripts en DB, le passage suivant est :

1. Coder/relancer le passage IA → table `audits` (script existant `scripts/run_audit_batch.py` à adapter pour boucler sur les transcripts en DB plutôt que sur Drive)
2. Importer la grille humaine (5-10 audits que tu m'as promis) → table `human_audits`
3. Calculer la table `calibration_results` (écart IA vs humain)
4. Si convergence ≥ 90 % : feu vert pour Phase 2 (Test 100 appels via Dialoga)

C'est le critère bloquant du plan original (cf `kickoff/CHECKLIST.md` ligne 9).
