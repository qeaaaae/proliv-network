# enable-qa-payment.ps1
# Идемпотентно добавляет QA-провайдер оплаты в shop/.env.
# Работает только в dev-режиме (APP_RUNTIME_MODE=dev в overlay backend).
# После запуска: docker compose ... up -d backend worker bot (пересоздание,
# env_file при restart не перечитывается).
param(
    [string]$EnvFile = "$PSScriptRoot\..\shop\.env",
    [string]$Secret = "proliv-qa-2026"
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $EnvFile)) {
    throw "Env file not found: $EnvFile"
}

$lines = Get-Content -LiteralPath $EnvFile
$add = @()

if ($lines -notmatch '^QA_PAYMENT_ENABLED=') {
    $add += 'QA_PAYMENT_ENABLED=True'
}
if ($lines -notmatch '^QA_PAYMENT_SECRET=') {
    $add += "QA_PAYMENT_SECRET=$Secret"
}

if ($add.Count -eq 0) {
    Write-Host "QA payment vars already present in $EnvFile - nothing to do"
    exit 0
}

# utf-8 без BOM, как остальной .env
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$existing = [System.IO.File]::ReadAllText($EnvFile)
$tail = if ($existing.EndsWith("`n")) { '' } else { "`n" }
[System.IO.File]::AppendAllText($EnvFile, $tail + ($add -join "`n") + "`n", $utf8NoBom)

Write-Host "Added to $EnvFile :"
$add | ForEach-Object { Write-Host "  $_" }
Write-Host "Now recreate services: docker compose -f shop/docker-compose.yml -f infra/minishop.compose.yml --env-file shop/.env up -d backend worker bot"
