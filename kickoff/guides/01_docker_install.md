# Guide 01 — Installation Docker Desktop (Windows)

## Pourquoi
Docker permet de faire tourner Postgres + MinIO en local pour le POC, sans installer ces services sur ton OS.

## Installation (10 min)

1. **Télécharge Docker Desktop pour Windows** : https://docs.docker.com/desktop/install/windows-install/
2. Lance l'installeur → coche "Use WSL 2 instead of Hyper-V" (recommandé)
3. Reboot le PC (Docker requiert l'activation de la virtualisation)
4. Lance Docker Desktop → accepte les CGU → skip le login (pas obligatoire)
5. Vérifie dans un PowerShell :
   ```powershell
   docker --version
   docker compose version
   ```

## Test de fumée

```powershell
docker run --rm hello-world
```

Si tu vois "Hello from Docker!" → ✅ tout est prêt.

## Si erreur "WSL 2 not installed"

```powershell
wsl --install
wsl --set-default-version 2
# Reboot
```

## Pour démarrer Postgres + MinIO local après

Depuis le dossier `repo_skeleton/` :
```powershell
docker compose up -d
docker compose ps
```

Tu auras :
- Postgres dispo sur `localhost:5432`
- MinIO API sur `localhost:9000`, console web sur `http://localhost:9001` (login `minioadmin` / `minioadmin`)

## Ressources

- Docker Desktop : https://www.docker.com/products/docker-desktop/
- WSL 2 setup : https://learn.microsoft.com/en-us/windows/wsl/install
