# Guide 02 — Repo Git privé (5 min)

## Option A — GitHub privé (recommandé)

### 1. Installer gh CLI (optionnel mais pratique)
```powershell
winget install --id GitHub.cli
gh auth login
```

### 2. Créer le repo privé

Depuis le dossier `f:\WORK\Audit_Dialoga_AtlasForMen_2026\kickoff\repo_skeleton\` :

```powershell
cd "f:\WORK\Audit_Dialoga_AtlasForMen_2026\kickoff\repo_skeleton"
git init -b main
git add .
git commit -m "Initial commit : squelette pipeline audit IA AFM"

# Avec gh CLI (auto-création du repo) :
gh repo create afm-audit --private --source=. --push

# OU sans gh CLI, à la main sur github.com :
# 1. https://github.com/new → repo "afm-audit", privé, sans README
# 2. Copier les commandes proposées par GitHub :
git remote add origin git@github.com:<TON_USER>/afm-audit.git
git push -u origin main
```

### 3. Inviter les collaborateurs

`Settings → Collaborators → Add people`. Donne le rôle "Write" aux devs, "Admin" à toi.

### 4. Ajouter les secrets GitHub Actions (plus tard)

Quand on activera la CI :
- `Settings → Secrets and variables → Actions`
- Ajouter : `ANTHROPIC_API_KEY_TEST`, `GOOGLE_SERVICE_ACCOUNT_JSON_B64`

## Option B — GitLab self-host

Si tu veux self-héberger pour des raisons RGPD strictes (audit IA sur données client) :

```powershell
# Docker compose local pour GitLab :
# Voir https://docs.gitlab.com/ee/install/docker.html
# OU GitLab.com Premium pour avoir le repo en région EU
```

## Recommandation

**GitHub privé** suffit pour ce projet :
- Le code en lui-même ne contient pas de PII
- Les transcripts CSV / audits restent dans Drive + Postgres EU
- Le `.gitignore` exclut `data/`, `*.csv`, `*.mp3`, etc.

⚠️ **VÉRIFIE bien avant chaque push** que tu n'as pas commit accidentellement :
- `service_account.json`
- `.env`
- Des CSV de transcripts

Le `.gitignore` du squelette exclut tout ça, mais reste vigilant.
