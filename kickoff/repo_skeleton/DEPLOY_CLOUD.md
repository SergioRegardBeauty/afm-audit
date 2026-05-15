# Déploiement cloud Scaleway — Atlas For Men audit IA

Guide step-by-step pour migrer la stack du local Docker (PC Djibril) vers Scaleway Paris (RGPD natif). À suivre dans l'ordre.

**Cible** :
- Postgres managé (DB-DEV-S, ~15 €/mois)
- Object Storage privé (~0.05 €/mois pour 50 MB de CSV)
- VM de compute (DEV1-S, ~6 €/mois) qui héberge le repo + cron jobs
- **Total** : ~21 €/mois d'infra (hors API Anthropic à l'usage)

Toute la stack reste en région **Paris (fr-par)** : exigence RGPD du projet.

---

## Phase 1 — Compte Scaleway (10 min)

### 1.1 Création
Va sur https://console.scaleway.com/register, crée un compte personnel ou pro avec :
- Email pro
- Mot de passe fort (gestionnaire)
- Numéro de téléphone (SMS de vérification)

### 1.2 Validation paiement
Onglet `Billing` > ajoute une carte. **Aucun montant prélevé** tant que tu ne provisionnes rien.

### 1.3 2FA (obligatoire pour la prod)
Profil > `Account preferences` > `2FA`. Active avec une app (Authy, 1Password, Google Auth). Sauvegarde les codes de récupération offline.

### 1.4 Project + Organization
Par défaut Scaleway crée un projet `default` dans ton organization personnelle. C'est suffisant pour démarrer. Pas besoin de créer un projet séparé pour ce POC.

---

## Phase 2 — Provisionner Postgres (15 min, démarrage 5 min)

### 2.1 Création de la DB
Console > **Managed Databases** > **PostgreSQL** > `Create a database instance`.

| Champ | Valeur |
|---|---|
| Engine | **PostgreSQL 16** |
| Region | **fr-par (Paris)** |
| Node type | **DB-DEV-S** (1 vCPU, 2 GB RAM) — ~15 €/mois |
| Volume | **5 GB SSD** (largement suffisant : nos 5 473 transcripts pèsent ~50 MB en DB) |
| Username | `afm_audit` |
| Password | Génère un mot de passe fort (32 chars), copie-le dans un gestionnaire |
| Backups | Active **daily backups, 7 days retention** (gratuit sur DB-DEV-S) |
| Encryption | Activé par défaut (TLS+at-rest) |
| Network | **Public endpoint** activé (on filtrera par IP allow-list après) |

Clique `Create` → attends ~5 min que la DB soit `running`.

### 2.2 Récupérer l'endpoint
Une fois en running, onglet `Overview`. Récupère :
- **Endpoint** : ex `xxxxx.scw-db.amazonaws.com` ou `xxxxx.pg.scw.cloud:5432`
- **Username** : `afm_audit`
- **Password** : ce que tu as défini (à garder en gestionnaire)
- **Database** : par défaut `rdb` — tu créeras `afm_audit` dans une seconde

### 2.3 Restreindre l'accès par IP
Onglet `Allowed IPs` :
- Ajoute ton IP perso actuelle (pour le pg_restore depuis local). Récupère-la sur https://api.ipify.org
- Tu ajouteras l'IP de la VM Scaleway en phase 4
- Supprime `0.0.0.0/0` si présent (jamais d'accès Internet ouvert sur la DB)

### 2.4 Créer la base `afm_audit`
Depuis ton PC local (psql installé via Postgres ou via Docker) :
```powershell
docker exec -it afm_postgres psql -h <endpoint> -p 5432 -U afm_audit -d rdb
# tape le mot de passe Scaleway
```

Dans le prompt psql :
```sql
CREATE DATABASE afm_audit OWNER afm_audit;
\q
```

### 2.5 Charger le schéma
```powershell
docker run --rm -i `
    -v "${PWD}\sql:/sql:ro" `
    postgres:16-alpine `
    psql "postgresql://afm_audit:<MDP>@<endpoint>:5432/afm_audit?sslmode=require" `
    -f /sql/001_init.sql
```

Vérifier les tables :
```powershell
docker run --rm -it postgres:16-alpine `
    psql "postgresql://afm_audit:<MDP>@<endpoint>:5432/afm_audit?sslmode=require" `
    -c "\dt"
```

---

## Phase 3 — Object Storage (5 min)

### 3.1 Création du bucket
Console > **Object Storage** > `Create bucket`.

| Champ | Valeur |
|---|---|
| Bucket name | `afm-audit-transcripts` (le nom doit être unique mondialement, ajoute un suffixe si pris) |
| Region | **fr-par (Paris)** |
| Visibility | **Private** (jamais public) |
| Versioning | Désactivé pour économiser |

### 3.2 Créer une API key (pour les scripts)
Profil > **API Keys** > `Generate new API key`.
- Description : `afm-audit-prod`
- Access key + Secret key → copie dans le gestionnaire de mots de passe

### 3.3 Variables à noter
- `S3_ENDPOINT_URL` = `https://s3.fr-par.scw.cloud`
- `S3_BUCKET` = `afm-audit-transcripts` (ou ton nom)
- `S3_REGION` = `fr-par`
- `S3_ACCESS_KEY` = depuis l'API key
- `S3_SECRET_KEY` = depuis l'API key

---

## Phase 4 — VM compute (15 min)

### 4.1 Création
Console > **Instances** > `Create Instance`.

| Champ | Valeur |
|---|---|
| Region | **fr-par-1** |
| Type | **DEV1-S** (2 vCPU, 2 GB RAM, 20 GB SSD) — ~6 €/mois |
| Image | **Ubuntu 24.04 LTS** |
| Volume | 20 GB SSD (par défaut) |
| Name | `afm-audit-vm` |
| Tags | `project:afm-audit, env:prod` |
| SSH key | Si tu n'en as pas, génère-en une côté Windows : `ssh-keygen -t ed25519 -C "djibril@afm-audit"`. Colle le contenu de `~/.ssh/id_ed25519.pub` dans la console. |

Note l'**IP publique IPv4** de la VM (onglet Overview après création).

### 4.2 Ajouter l'IP de la VM à la whitelist Postgres
Console Postgres > `Allowed IPs` > ajoute l'IP de la VM `/32`.

### 4.3 SSH + setup de base
Depuis PowerShell (Windows 10/11 a `ssh` natif) :
```powershell
ssh root@<IP_VM>
```

Sur la VM :
```bash
# Mise à jour
apt update && apt upgrade -y

# Outils essentiels
apt install -y python3.12 python3.12-venv python3-pip postgresql-client git ca-certificates curl

# Créer l'user app (ne pas tourner en root)
useradd -m -s /bin/bash afm
usermod -aG sudo afm

# Configurer SSH pour 'afm' (copier la clé publique)
mkdir -p /home/afm/.ssh
cp /root/.ssh/authorized_keys /home/afm/.ssh/
chown -R afm:afm /home/afm/.ssh
chmod 700 /home/afm/.ssh
chmod 600 /home/afm/.ssh/authorized_keys

# Désactiver le login root SSH (sécurité)
sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl restart ssh
```

Sors et reconnecte en `afm@<IP_VM>` (vérifie que ça marche avant de fermer la session root).

### 4.4 Cloner le repo + installer deps
```bash
cd ~
git clone https://github.com/<ton-org>/afm-audit.git
cd afm-audit/kickoff/repo_skeleton

python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4.5 Créer le `.env` de production
```bash
cp .env.example .env
nano .env
```

Remplis avec les vraies valeurs (Postgres endpoint Scaleway, Object Storage credentials, Anthropic key). **Ne JAMAIS commit ce fichier**.

### 4.6 Vérifier la connexion à la prod
```bash
python scripts/smoke_test.py
```

Doit lister `OK` pour Postgres + MinIO/Scaleway S3 + Anthropic. Si une ligne est `ECHEC`, corrige le `.env` ou les permissions/IP.

---

## Phase 5 — Migrer les données du local vers la prod (30 min)

### 5.1 Dump de la DB locale
Depuis ton PC, vers un fichier `afm_audit_dump.sql` :

```powershell
docker exec afm_postgres pg_dump -U afm_audit -d afm_audit `
    --no-owner --no-acl --clean --if-exists `
    > afm_audit_dump.sql
```

Vérifie la taille (~50 MB attendu).

### 5.2 Restaurer sur Scaleway
```powershell
docker run --rm -i `
    -v "${PWD}:/work" `
    postgres:16-alpine `
    psql "postgresql://afm_audit:<MDP>@<endpoint>:5432/afm_audit?sslmode=require" `
    -f /work/afm_audit_dump.sql
```

Vérification :
```powershell
docker run --rm -it postgres:16-alpine `
    psql "postgresql://afm_audit:<MDP>@<endpoint>:5432/afm_audit?sslmode=require" `
    -c "SELECT COUNT(*) FROM transcripts;"
# Doit afficher 5473 (ou ton nombre local)
```

### 5.3 Upload des CSV vers le bucket
Sur la VM (ou ton PC local, plus rapide avec ta connexion) :
```bash
python scripts/upload_csv_to_bucket.py --root /path/to/Transcription\ MP3
```

(Le script `upload_csv_to_bucket.py` est dans le repo — il liste les CSV, calcule un sha256 pour idempotence, et upload via boto3 en parallèle.)

---

## Phase 6 — Sécurité prod (30 min)

### 6.1 SSL Postgres obligatoire
Dans ton `.env` VM, assure-toi que `DATABASE_URL` contient `?sslmode=require` :
```
DATABASE_URL=postgresql://afm_audit:MDP@xxxxx.pg.scw.cloud:5432/afm_audit?sslmode=require
```

### 6.2 IP allow-list Postgres restreinte
Console Postgres > `Allowed IPs` :
- ✅ IP VM Scaleway
- ✅ Ton IP perso (uniquement quand tu fais des opérations admin depuis local)
- ❌ Pas de `0.0.0.0/0`

### 6.3 Rotation des credentials
Documente dans `kickoff/repo_skeleton/docs/credentials_rotation.md` :
- Postgres : rotation tous les 6 mois (Console > `Reset password` puis update `.env` VM + redémarrer les scripts)
- Object Storage API key : rotation tous les 6 mois (générer une nouvelle, mettre à jour, supprimer l'ancienne)
- Anthropic API key : rotation tous les 6 mois ou en cas de fuite suspectée

### 6.4 Backups
- Postgres : auto-activé en phase 2.1 (7 jours retention). Tester un restore au moins une fois.
- Bucket S3 : pas critique car les CSV sources sont aussi en local et en DB. Activer versioning si tu commences à modifier des objets.
- Code : repo Git privé, pushé régulièrement.

### 6.5 Monitoring
Console Scaleway > Cockpit (option payante mais incluse à petite échelle) :
- Alertes CPU/RAM Postgres > 80%
- Alertes ratio connexions actives
- Alertes coût mensuel > 30 €

---

## Phase 7 — Orchestration des scripts sur la VM (15 min)

### 7.1 Script de relance audit IA en arrière-plan
Sur la VM, créer `/home/afm/run_audit_loop.sh` :
```bash
#!/bin/bash
cd /home/afm/afm-audit/kickoff/repo_skeleton
source .venv/bin/activate
python scripts/run_audit_batch.py --audit-version v2_prod 2>&1 | tee -a /var/log/afm-audit/run.log
```

```bash
sudo mkdir -p /var/log/afm-audit
sudo chown afm:afm /var/log/afm-audit
chmod +x /home/afm/run_audit_loop.sh
```

### 7.2 Cron (optionnel, pour automation)
`crontab -e` :
```cron
# Audit toutes les nuits à 02h00
0 2 * * * /home/afm/run_audit_loop.sh
# Refresh des vues matérialisées toutes les heures
0 * * * * /home/afm/refresh_views.sh
```

### 7.3 Vérification logs
```bash
tail -f /var/log/afm-audit/run.log
```

---

## Récap budget mensuel

| Item | Plan | Mensuel |
|---|---|---|
| Postgres DB-DEV-S | 1vCPU/2GB | 15.00 € |
| Object Storage 50 MB | privé Paris | 0.05 € |
| VM DEV1-S | 2vCPU/2GB | 5.99 € |
| **Total infra fixe** | | **~21 €/mois** |
| Anthropic API (usage) | Sonnet, ~5500 audits | ~50 € one-shot |
| Anthropic API courant | si phase 2/3 | ~5-15 €/mois |

Tu peux **descendre Postgres à arrêter** quand tu ne fais plus d'audit (mais ça casse les KPIs vivants). Ou utiliser Scaleway PaaS **Serverless Postgres** (~10 €/mois, factu à la requête) si la DB n'est pas sollicitée 24/7.

---

## Phase 8 — Interface Streamlit publique (collègues) (45 min)

### 8.1 Nom de domaine (optionnel mais propre)

Si tu as un nom de domaine (chez OVH, Gandi, Cloudflare…), crée un enregistrement DNS `A` qui pointe vers l'IP publique de la VM :
```
audit.tondomaine.fr   →   A   <IP_VM_Scaleway>
```

Sinon, tu peux y accéder directement par IP (https://<IP_VM>) — moins propre mais ça marche.

### 8.2 Installer nginx + certbot sur la VM

```bash
sudo apt install -y nginx certbot python3-certbot-nginx ufw
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 8.3 Préparer le fichier users.yaml sur la VM

```bash
cd /home/afm/afm-audit/kickoff/repo_skeleton/app
cp users.yaml.example users.yaml
# Générer les hash bcrypt pour chaque collègue :
python3 -c "import bcrypt; print(bcrypt.hashpw(b'leur_mdp', bcrypt.gensalt()).decode())"
# Coller le hash dans users.yaml
nano users.yaml
# Sécurise les permissions :
chmod 600 users.yaml
```

⚠️ Ne JAMAIS commit `users.yaml` — il est déjà dans `.gitignore`.

### 8.4 Service systemd pour Streamlit

```bash
sudo tee /etc/systemd/system/afm-streamlit.service > /dev/null <<'EOF'
[Unit]
Description=Atlas For Men audit interface (Streamlit)
After=network.target

[Service]
Type=simple
User=afm
WorkingDirectory=/home/afm/afm-audit/kickoff/repo_skeleton
Environment="PATH=/home/afm/afm-audit/kickoff/repo_skeleton/.venv/bin"
EnvironmentFile=/home/afm/afm-audit/kickoff/repo_skeleton/.env
ExecStart=/home/afm/afm-audit/kickoff/repo_skeleton/.venv/bin/streamlit run app/streamlit_app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now afm-streamlit
sudo systemctl status afm-streamlit
# Doit être "active (running)"
```

Test direct :
```bash
curl http://127.0.0.1:8501
# Doit retourner du HTML Streamlit
```

### 8.5 Reverse proxy nginx

```bash
sudo tee /etc/nginx/sites-available/afm-audit > /dev/null <<'EOF'
server {
    listen 80;
    server_name audit.tondomaine.fr;   # Remplacer par ton domaine ou _ pour IP

    # Streamlit a besoin de WebSockets
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    client_max_body_size 100M;
}
EOF

sudo ln -s /etc/nginx/sites-available/afm-audit /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Test : `http://audit.tondomaine.fr` ou `http://<IP_VM>` → tu vois le login Streamlit.

### 8.6 HTTPS gratuit via Let's Encrypt (nom de domaine requis)

```bash
sudo certbot --nginx -d audit.tondomaine.fr --email dev@regardbeauty.com --agree-tos --no-eff-email
```

Certbot modifie nginx automatiquement pour servir en HTTPS + redirection 80→443. Renouvellement auto via cron.

Test final : `https://audit.tondomaine.fr` → login Streamlit avec cadenas vert.

### 8.7 Partager l'URL aux collègues

Envoie à chaque collègue :
- L'URL : `https://audit.tondomaine.fr`
- Leur identifiant (clé `usernames` dans `users.yaml`)
- Leur mot de passe (que tu as utilisé pour générer le hash bcrypt). Demande-leur de le changer après 1ère connexion via une issue GitHub à toi.

### 8.8 Mises à jour de l'app

Quand tu push du code dans Git, sur la VM :
```bash
ssh afm@<IP_VM>
cd /home/afm/afm-audit
git pull origin main
sudo systemctl restart afm-streamlit
```

(Plus tard tu pourras automatiser ça avec une GitHub Action ou un webhook.)

---

## Prochaines étapes après le déploiement

1. **Faire tourner l'audit IA en masse** depuis la VM (script `run_audit_batch.py` à adapter pour lire la DB en prod plutôt que Drive)
2. **Importer les audits humains** dans `human_audits` (le bloquant projet)
3. **Calcul des `calibration_results`** pour mesurer l'agreement IA-vs-humain
4. **Phase 2 du plan global** : passer 100 appels en flow Dialoga isolé → DB Scaleway → audit live
