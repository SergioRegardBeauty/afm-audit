# Migration Postgres local Docker → Scaleway Managed Database
#
# Usage:
#   .\migrate_db_to_scaleway.ps1 -ScalewayEndpoint xxxxx.pg.scw.cloud -ScalewayPassword "..."
#
# Pré-requis:
#   - Docker Desktop tournant
#   - Le container afm_postgres actif avec les données ingérées
#   - IP allow-list Scaleway autorise ton IP actuelle (cf phase 2.3 du DEPLOY_CLOUD.md)
#   - La base "afm_audit" déjà créée sur Scaleway + schéma chargé (phase 2.4-2.5)

param(
    [Parameter(Mandatory=$true)][string]$ScalewayEndpoint,
    [Parameter(Mandatory=$true)][string]$ScalewayPassword,
    [int]$ScalewayPort = 5432,
    [string]$ScalewayDb = "afm_audit",
    [string]$ScalewayUser = "afm_audit",
    [string]$DumpFile = "afm_audit_dump.sql"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Migration Postgres local → Scaleway ===" -ForegroundColor Cyan
Write-Host "  Source : container Docker 'afm_postgres'"
Write-Host "  Cible  : $ScalewayUser@$ScalewayEndpoint:$ScalewayPort/$ScalewayDb"
Write-Host ""

# 1. Dump local
Write-Host "[1/3] Dump local → $DumpFile ..." -NoNewline
$dumpPath = Join-Path (Get-Location) $DumpFile
docker exec afm_postgres pg_dump -U afm_audit -d afm_audit --no-owner --no-acl --clean --if-exists `
    | Out-File -Encoding utf8 -FilePath $dumpPath
$size = (Get-Item $dumpPath).Length / 1024 / 1024
Write-Host (" OK ({0:N1} MB)" -f $size) -ForegroundColor Green

# 2. Restore Scaleway
Write-Host "[2/3] Restore vers Scaleway via Docker postgres:16-alpine ..." -NoNewline
$cwd = (Get-Location).Path -replace "\\","/"
$connStr = "postgresql://${ScalewayUser}:${ScalewayPassword}@${ScalewayEndpoint}:${ScalewayPort}/${ScalewayDb}?sslmode=require"

docker run --rm `
    -v "${cwd}:/work" `
    -e PGPASSWORD=$ScalewayPassword `
    postgres:16-alpine `
    psql $connStr -f /work/$DumpFile -v ON_ERROR_STOP=1 `
    2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host " ECHEC" -ForegroundColor Red
    Write-Host "Code: $LASTEXITCODE — relance le restore manuellement pour voir l'erreur:" -ForegroundColor Yellow
    Write-Host "docker run --rm -v `"${cwd}:/work`" -e PGPASSWORD=*** postgres:16-alpine psql `"$connStr`" -f /work/$DumpFile"
    exit 1
}
Write-Host " OK" -ForegroundColor Green

# 3. Validation
Write-Host "[3/3] Validation : COUNT(*) FROM transcripts ..." -NoNewline
$count = docker run --rm `
    -e PGPASSWORD=$ScalewayPassword `
    postgres:16-alpine `
    psql $connStr -t -c "SELECT COUNT(*) FROM transcripts;" 2>&1
$count = $count.Trim()
Write-Host " $count transcripts en prod" -ForegroundColor Green

Write-Host ""
Write-Host "Migration terminée. Prochaines étapes:" -ForegroundColor Cyan
Write-Host "  - Update le .env de la VM avec DATABASE_URL=$connStr"
Write-Host "  - Lance scripts/smoke_test.py sur la VM pour valider l'accès"
Write-Host "  - Supprime le dump local après vérification: Remove-Item $dumpPath"
