# Guide 06 — Stockage objet S3-compatible EU

## Pourquoi du S3 ?

- Stocker les **recordings MP3** (1 mois = ~50-100 GB selon ton volume)
- Stocker les **transcripts CSV** archivés (~100 MB)
- Audit immuable : chaque fichier a un hash, on peut prouver qu'il n'a pas été modifié
- Hébergement EU pour RGPD

## Option A — MinIO local (POC, 0 €)

Déjà dans le `docker-compose.yml`. Démarrer :

```powershell
docker compose up -d minio minio-init
```

Console web : http://localhost:9001 (login `minioadmin` / `minioadmin`)
API S3 : `http://localhost:9000`
Bucket auto-créé : `afm-audit-recordings`

Connection string dans `.env` :
```
S3_ENDPOINT_URL=http://localhost:9000
S3_BUCKET=afm-audit-recordings
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_USE_SSL=false
```

Le client `afm_audit.storage` utilise boto3 → marche identiquement avec MinIO et Scaleway.

## Option B — Scaleway Object Storage (recommandé prod, ~5 €/mois)

### Étapes

1. https://console.scaleway.com → **Object Storage** → **Create a bucket**
2. Region : **FR-PAR** (Paris) ou **NL-AMS** (Amsterdam)
3. Bucket name : `afm-audit-recordings` (globalement unique → préfixer avec ton org si besoin : `acme-afm-audit-recordings`)
4. Visibility : **Private**
5. **Object Lock** : activer (immuabilité pour audit/conformité)
6. → **Create**

### Générer les API keys

1. **Identity & Access Management (IAM)** → **API Keys** → **Generate new API key**
2. Description : `afm-audit-pipeline`
3. **Object Storage** scope avec accès **Read & Write** sur le bucket créé
4. Sauvegarder `Access Key` et `Secret Key` (jamais réaffichés)

### Connection string

```
S3_ENDPOINT_URL=https://s3.fr-par.scw.cloud
S3_BUCKET=afm-audit-recordings
S3_REGION=fr-par
S3_ACCESS_KEY=SCWXXXXXXXXXX
S3_SECRET_KEY=YYYYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY
S3_USE_SSL=true
```

### Tarif estimé pour AFM

- Stockage : 50 GB × 0.012 €/GB/mois = **0.60 €/mois**
- Bandwidth sortant : ~0 € si on consomme uniquement depuis le pipeline (download interne)
- Requêtes : négligeable (1 PUT par recording, ~5000 requêtes/mois = 0.025 €)
- **Total : ~1 €/mois** (et plafonné à 5 €/mois même si volume × 5)

## Option C — OVH Object Storage / OVH S3

Similaire à Scaleway, prix équivalents. Documentation : https://docs.ovh.com/

## Option D — AWS S3 EU

Possible mais déconseillé pour ce projet :
- Tarif US-Europe pas favorable
- Soumis au Cloud Act US (même pour des données stockées en UE) → enjeu RGPD non trivial

## Bonnes pratiques

### 1. Lifecycle policy

Supprimer automatiquement les recordings après X mois (conformité Dialoga rétention) :
```python
# Via boto3
client.put_bucket_lifecycle_configuration(Bucket="afm-audit-recordings", LifecycleConfiguration={
    "Rules": [{
        "ID": "DeleteRecordingsAfter90Days",
        "Status": "Enabled",
        "Prefix": "recordings/",
        "Expiration": {"Days": 90},
    }]
})
```

### 2. Server-side encryption

Tous les objets chiffrés au repos :
```python
client.put_object(Bucket=..., Key=..., Body=..., ServerSideEncryption="AES256")
```

Le wrapper `afm_audit.storage.upload_file()` peut être étendu pour activer ça par défaut.

### 3. Versioning + Object Lock

Pour les audits IA (immuabilité) :
- Versioning **ON** → chaque PUT crée une nouvelle version
- Object Lock **Compliance mode** → impossible de supprimer pendant N jours (utile pour disputes/conformité)

### 4. Pas de PII dans les noms de fichiers

❌ `recordings/Jean_Dupont_06_12_34_56_78.mp3`
✅ `recordings/2026/01/15/<uuid>.mp3` (avec mapping uuid→client dans Postgres uniquement)

## Recommandation

| Phase | Choix |
|-------|-------|
| **POC / Conception** | MinIO local Docker |
| **Test (100 appels)** | Scaleway Object Storage |
| **Production** | Scaleway Object Storage + Object Lock + Lifecycle |
