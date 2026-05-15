# Setup GitHub privé — Atlas For Men audit IA

Procédure pour créer le repo GitHub privé et faire le premier push **sans risque RGPD** (le `.gitignore` + le pre-commit hook bloquent les MP3 / CSV / audits / secrets).

⚠️ **Avant de commencer**, vérifie que tu n'as PAS encore initialisé Git sur ce dossier. Sinon va à l'étape 6 directement.

---

## 1. Créer un compte GitHub si tu n'en as pas

https://github.com/signup. Compte perso gratuit suffit (les repos privés sont gratuits depuis 2019).

Active 2FA dans `Settings > Password and authentication` (obligatoire pour un projet pro).

---

## 2. Créer le repo privé

https://github.com/new

| Champ | Valeur |
|---|---|
| Repository name | `afm-audit-ia` |
| Description | `Atlas For Men — audit IA des appels (Cde Tel + SAV)` |
| Visibility | **Private** (jamais Public) |
| Initialize with README | **Non** (on a déjà un README local) |
| Add .gitignore | **Non** (on a déjà notre `.gitignore` sur mesure) |
| License | None ou "All rights reserved" |

Note l'URL HTTPS du repo (ex: `https://github.com/djibril/afm-audit-ia.git`).

---

## 3. Configurer l'authentification (token personnel)

Crée un Personal Access Token classique : https://github.com/settings/tokens/new

| Champ | Valeur |
|---|---|
| Note | `afm-audit-laptop` |
| Expiration | 90 jours |
| Scopes | ✅ `repo` (full control of private repositories) — c'est tout |

Génère, copie le token (commence par `ghp_...`). **Tu ne le reverras plus** — colle-le dans ton gestionnaire de mots de passe.

(Plus tard, sur la VM Scaleway, génère un autre token séparé pour la machine.)

---

## 4. Installer Git si pas déjà fait

```powershell
# Vérifier
git --version

# Sinon installer via winget
winget install --id Git.Git -e
```

Identifier l'utilisateur Git localement (une fois) :
```powershell
git config --global user.name "Djibril (ton nom)"
git config --global user.email "dev@regardbeauty.com"
```

---

## 5. Activer le pre-commit hook anti-PII

Le fichier `.git-hooks/pre-commit` (déjà dans le projet) bloque tout commit qui contiendrait :
- Des MP3 / WAV / Opus / M4A (recordings PII)
- Des `*.mp3.csv` (transcripts HappyScribe)
- Des CSV qui ressemblent à des transcripts (détection par header)
- Des `service_account*.json` / `.env` / `*.pem` (secrets)
- Des `*_dump.sql` / `pg_dump_*.sql` (peuvent contenir PII)
- `users.yaml` (hash bcrypt)
- Les Excel remplis dans `output/*/BQ_*.xlsx`

**Active-le maintenant** (une seule fois, dans le repo) :

```powershell
cd f:\WORK\Audit_Dialoga_AtlasForMen_2026
git config core.hooksPath .git-hooks
```

Sur Linux/Mac il faudrait aussi un `chmod +x .git-hooks/pre-commit` — sur Windows c'est automatique via Git Bash.

---

## 6. Initialiser le repo + premier commit

```powershell
cd f:\WORK\Audit_Dialoga_AtlasForMen_2026

# Initialiser
git init -b main
git config core.hooksPath .git-hooks

# Vérifier ce qui SERA committé (doit exclure les MP3 / CSV / audits / .env)
git status
```

**Avant de stage**, vérifie que `git status` ne liste PAS :
- `Transcription MP3/...`
- `Audio MP3/...`
- `audits_ia/...`
- `corpus/...`
- `output/_selection/.../*.mp3` ni `*.csv` (sauf README.md et SELECTION_MANIFEST.csv)
- `output/*/BQ_*.xlsx`
- `.env` ou `service_account.json`
- `kickoff/repo_skeleton/app/users.yaml`

Si l'un d'eux apparaît : **STOP**, on doit corriger le `.gitignore` avant tout commit. Préviens-moi.

Si tout est propre, stage et commit :

```powershell
git add .
git status   # re-vérifier ce qui est staged
git commit -m "Initial commit : pipeline audit IA Atlas For Men (code only, no PII)"
```

Le pre-commit hook va valider qu'aucun PII ne passe.

---

## 7. Connecter au remote GitHub et pousser

```powershell
git remote add origin https://github.com/<ton-user>/afm-audit-ia.git
git branch -M main
git push -u origin main
```

À l'invite de mot de passe : colle le **Personal Access Token** (`ghp_...`), pas ton mot de passe GitHub habituel.

Sur GitHub, rafraîchis la page du repo — tu dois voir tous les fichiers code (pipeline, prompts, kickoff, etc.) **sans aucune donnée PII**.

---

## 8. Inviter tes collègues

Sur GitHub `Settings > Collaborators > Add people`. Ajoute leurs handles. Ils recevront un email d'invitation et auront ensuite accès lecture/écriture selon le rôle choisi.

⚠️ **Avant de les inviter**, communique-leur que :
- Ils ne doivent **jamais** committer de PII (le hook les bloquera mais autant être clair)
- Ils doivent activer le pre-commit hook après clone : `git config core.hooksPath .git-hooks`
- Le `.env` et `users.yaml` ne sont jamais dans Git — il faut les recréer en local après clone

---

## 9. Si tu réalises qu'un fichier sensible a été committé par erreur

```powershell
# Si pas encore push :
git reset HEAD~1                        # défait le dernier commit (garde les fichiers)
git restore --staged <fichier_sensible> # retire du staging
# Modifier .gitignore puis recommit

# Si déjà push : c'est plus douloureux mais faisable
# 1. Supprime le fichier sur GitHub
# 2. Force-rewrite l'historique localement :
#    pip install git-filter-repo
#    git filter-repo --path <fichier> --invert-paths
# 3. git push --force origin main
# 4. Considère le fichier comme PUBLIC et fait tourner ses secrets (rotation key/password)
```

**Préviens-moi immédiatement** si ça t'arrive — on traitera l'incident avec le bon process.

---

## 10. Workflow normal après le 1er push

```powershell
# Récupérer les changements des collègues
git pull origin main

# Faire ton travail (modifier code, scripts, doc)
# … pas toucher aux MP3/CSV/audits

git status                  # vérifier ce qui change
git add <fichiers>          # stage sélectivement
git commit -m "feat: description courte"
git push origin main
```

Si le pre-commit hook bloque : lis le message — il dit exactement quel fichier est interdit. Retire-le du staging avec `git restore --staged <fichier>` et corrige `.gitignore` si besoin.
