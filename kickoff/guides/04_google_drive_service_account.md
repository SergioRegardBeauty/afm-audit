# Guide 04 — Service account Google Drive (15 min)

Pour que le pipeline Python lise les transcripts CSV depuis Drive sans intervention manuelle.

## Pourquoi un service account et pas OAuth user ?

| | OAuth user | Service account |
|--|------------|-----------------|
| Setup | Token expire toutes les 60 min, refresh manuel | Clé JSON permanente |
| Sécurité | Compte personnel | Identité dédiée (audit trail clair) |
| Production | ❌ Pas viable (réfresh) | ✅ Fonctionne en daemon/cron |

→ Service account obligatoire pour un pipeline automatisé.

## Étapes (15 min)

### 1. Créer un projet Google Cloud

1. https://console.cloud.google.com → **Select Project** → **New Project**
2. Nom : `afm-audit-pipeline`
3. Organization : ton org Google Workspace (ou "No organization")
4. → **Create**

### 2. Activer l'API Drive

1. Dans le projet : menu hamburger → **APIs & Services** → **Library**
2. Search "Google Drive API" → **Enable**

### 3. Créer le service account

1. **APIs & Services** → **Credentials** → **+ Create Credentials** → **Service account**
2. Nom : `afm-audit-drive-reader`
3. Description : `Service account pour lecture Drive AFM (audit IA)`
4. → **Create and continue**
5. Rôles : **aucun** (on donne l'accès directement aux dossiers Drive ciblés, principe du moindre privilège)
6. → **Done**

### 4. Générer la clé JSON

1. **Credentials** → clique sur le service account créé
2. Onglet **Keys** → **Add Key** → **Create new key** → **JSON** → **Create**
3. Le fichier `afm-audit-pipeline-XXXXXXXXX.json` télécharge automatiquement
4. **Renomme-le** `service_account.json`
5. **Place-le** à la racine du repo `afm-audit/` (couvert par `.gitignore`)

### 5. Partager les dossiers Drive avec le service account

Le service account a une adresse email du type :
```
afm-audit-drive-reader@afm-audit-pipeline.iam.gserviceaccount.com
```

(Tu la trouves dans le JSON sous la clé `client_email`, ou dans la console GCP)

Pour CHAQUE dossier Drive contenant tes transcripts :
1. Clic droit sur le dossier → **Share**
2. Coller l'email du service account
3. Permission : **Viewer** (lecture seule)
4. Décocher "Notify people" (optionnel)
5. → **Share**

### 6. Tester l'accès

```powershell
cd repo_skeleton
.venv\Scripts\activate
pip install -r requirements.txt

# Test rapide
python -c "from afm_audit.drive import list_files_in_folder; print(list_files_in_folder('TON_FOLDER_ID')[:3])"
```

Si tu vois 3 fichiers → ✅ tout est OK.

Si `Permission denied` → vérifie que tu as bien partagé le dossier avec l'email du service account.

## RGPD : ce que voit / fait le service account

| Action | Permis ? |
|--------|----------|
| Lister les fichiers d'un dossier partagé | ✅ |
| Lire le contenu d'un fichier | ✅ |
| Modifier un fichier | ❌ (Viewer uniquement) |
| Accéder à d'autres dossiers Drive | ❌ |
| Lire les emails / Calendar | ❌ |

Tu peux **révoquer** l'accès à tout moment :
- Sur un dossier : **Share** → supprimer l'email → **Save**
- Globalement : supprimer le service account dans la console GCP

## Coût

Le service account et l'API Drive sont **gratuits** dans la limite de 1000 req/100s/user (largement au-dessus de tes besoins).

## Si tu utilises Google Workspace

Pour les comptes Workspace strictement contrôlés, l'admin doit autoriser le service account au niveau du domaine :
1. Admin Console → **Security** → **API controls** → **Domain-wide delegation**
2. Ajouter le Client ID du service account avec le scope `https://www.googleapis.com/auth/drive.readonly`

Ce n'est pas obligatoire si tu partages chaque dossier manuellement (étape 5).
