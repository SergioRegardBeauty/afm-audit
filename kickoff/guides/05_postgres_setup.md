# Guide 05 — Postgres EU (RGPD obligatoire)

## Pourquoi RGPD ?

Les audits contiennent du contenu d'appels client (PII potentielle : nom, numéro de téléphone, numéro de commande, adresse) → l'hébergement DB doit être en UE.

## Option A — POC local (Docker, 0 €)

Déjà configuré dans le `docker-compose.yml` du squelette. Démarrer :

```powershell
cd repo_skeleton
docker compose up -d postgres
docker compose logs -f postgres   # Ctrl+C pour quitter
```

Connection string :
```
DATABASE_URL=postgresql://afm_audit:CHANGE_ME_LOCAL_ONLY@localhost:5432/afm_audit
```

⚠️ **Seulement pour le POC local**. Pas de PII production dedans.

## Option B — Scaleway Database (recommandé prod, ~15 €/mois)

Hébergement Paris/Amsterdam, conforme RGPD, géré.

### Étapes

1. https://console.scaleway.com → **Database** → **Create a Database Instance**
2. Engine : **PostgreSQL 16**
3. Region : **France (Paris) FR-PAR** ou **Pays-Bas (Amsterdam) NL-AMS**
4. Type : **DB-DEV-S** (1 CPU, 2 GB RAM, 10 GB SSD) → **~15 €/mois**
5. Configuration :
   - Database name : `afm_audit`
   - User : `afm_audit`
   - Password : (générer fort et sauvegarder dans un password manager)
6. Network : **Public IP** (avec ACL stricte) ou **Private Network**
7. → **Create Database Instance** (~5 min de provisioning)

### Récupérer la connection string

Console Scaleway → ta DB → **Connection** → copier la `Connection string`. Format :
```
postgresql://afm_audit:PASSWORD@xxx.database.cloud.scaleway.com:PORT/afm_audit?sslmode=require
```

### Initialiser le schéma

```powershell
# Copier le SQL initial sur l'instance distante
psql "postgresql://..." -f sql/001_init.sql

# OU via Python (dépendances déjà installées)
python -c "
from afm_audit.config import settings
import psycopg
with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
    with open('sql/001_init.sql') as f:
        cur.execute(f.read())
    conn.commit()
print('Schema OK')
"
```

### Sécurité

- **SSL forcé** : Scaleway fournit `sslmode=require` par défaut
- **ACL IP** : restreindre les IPs autorisées (whitelist ton IP de dev + IPs de prod)
- **Backup** : Scaleway fait des backups quotidiens automatiques (rétention 7 jours par défaut)
- **Pas de PII en clair** : envisager pgcrypto pour chiffrer les colonnes sensibles (déjà installé via `CREATE EXTENSION pgcrypto`)

## Option C — OVH Managed Postgres (alternative, similaire)

https://www.ovhcloud.com/fr/public-cloud/postgresql/ — 15-25 €/mois selon plan.

## Option D — Cloud SQL Google Cloud (déconseillé)

Possible mais le service est US-centric — vérifier que la région est strictement EU (ex: `europe-west1` Belgique). Plus cher (~30 €/mois minimum).

## Recommandation

| Phase | Choix |
|-------|-------|
| **POC / Conception** | Docker local |
| **Test (100 appels)** | Scaleway DB-DEV-S |
| **Production (50%+ trafic)** | Scaleway DB-GP-S ou DB-PRO-S (~50-100 €/mois) |

## Migration POC → Prod

```powershell
# 1. Dump local
docker exec afm_postgres pg_dump -U afm_audit afm_audit > backup.sql

# 2. Restore vers Scaleway
psql "postgresql://...scaleway..." < backup.sql

# 3. Update .env avec nouvelle DATABASE_URL
```
