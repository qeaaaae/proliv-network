# ============================================================
# ProlivVPN - мастер настройки env (dev-стенд)
# Запуск: powershell -ExecutionPolicy Bypass -File infra\setup-env.ps1
# Пустой Enter = пропустить ключ (остаётся текущее значение).
# ============================================================
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$shopEnv = Join-Path $root 'shop\.env'
$prolivEnv = Join-Path $root 'proliv.env'
$shopExample = Join-Path $root 'infra\minishop.env.example'
$prolivExample = Join-Path $root 'proliv.env.example'

function Ensure-File($path, $example) {
  if (-not (Test-Path $path)) {
    Copy-Item $example $path
    Write-Host "  создан $path из шаблона" -ForegroundColor Yellow
  }
}

function Read-Env($path) { [IO.File]::ReadAllLines($path) }

function Get-EnvKey($lines, $key) {
  foreach ($l in $lines) { if ($l -match "^$([regex]::Escape($key))=(.*)$") { return $Matches[1] } }
  return $null
}

function Set-EnvKey($path, $key, $value) {
  $lines = Read-Env $path
  $found = $false
  $out = foreach ($l in $lines) {
    if ($l -match "^$([regex]::Escape($key))=") { $found = $true; "$key=$value" } else { $l }
  }
  if (-not $found) { $out += "$key=$value" }
  [IO.File]::WriteAllText($path, ($out -join "`r`n") + "`r`n", (New-Object Text.UTF8Encoding($false)))
  Write-Host "  $key -> $path" -ForegroundColor Green
}

function Ask($label, $default = '') {
  $hint = if ($default) { " [$default]" } else { '' }
  $v = Read-Host "$label$hint"
  if ([string]::IsNullOrWhiteSpace($v)) { return $default }
  return $v.Trim()
}

Write-Host "`n=== ProlivVPN env setup ===" -ForegroundColor Cyan
Write-Host "Пустой Enter = пропустить (не менять).`n"

Ensure-File $shopEnv $shopExample
Ensure-File $prolivEnv $prolivExample

$shopLines = Read-Env $shopEnv
$prolivLines = Read-Env $prolivEnv

# ---------- Шаг 1: Telegram-бот ----------
Write-Host "`n[1] Telegram-бот (токен от @BotFather)" -ForegroundColor Cyan
$bot = Ask 'BOT_TOKEN (из @BotFather, Enter = пропустить бота целиком)'
if ($bot) {
  Set-EnvKey $shopEnv 'BOT_TOKEN' $bot
  Set-EnvKey $shopEnv 'TELEGRAM_ENABLED' 'True'
  Set-EnvKey $shopEnv 'TELEGRAM_LOGIN_ENABLED' 'True'
  Set-EnvKey $prolivEnv 'NUXT_BOT_TOKEN' $bot
  if (-not (Get-EnvKey $prolivLines 'NUXT_SESSION_SECRET')) {
    $sec = -join ((48..57)+(97..122) | Get-Random -Count 48 | ForEach-Object {[char]$_})
    Set-EnvKey $prolivEnv 'NUXT_SESSION_SECRET' $sec
  }
}

# ---------- Шаг 2: Панель ----------
Write-Host "`n[2] Remnawave панель" -ForegroundColor Cyan
Write-Host "    Ключ: http://localhost:3443 -> Settings -> API Tokens -> scope '*'" -ForegroundColor DarkGray
$pk = Ask 'PANEL_API_KEY'
if ($pk) {
  Set-EnvKey $shopEnv 'PANEL_API_KEY' $pk
  Set-EnvKey $shopEnv 'PANEL_WRITE_MODE' 'live'
}

$wh = Ask 'Включить вебхук панели -> minishop? (y/n)' 'y'
if ($wh -eq 'y') {
  $existing = Get-EnvKey $prolivLines 'WEBHOOK_SECRET_HEADER'
  if (-not $existing) {
    $existing = -join ((48..57)+(97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
  }
  Set-EnvKey $prolivEnv 'WEBHOOK_ENABLED' 'true'
  Set-EnvKey $prolivEnv 'WEBHOOK_URL' 'http://remnawave-minishop-backend:8080/webhook/panel'
  Set-EnvKey $prolivEnv 'WEBHOOK_SECRET_HEADER' $existing
  Set-EnvKey $shopEnv 'PANEL_WEBHOOK_SECRET' $existing
}

# ---------- Шаг 3: публичный URL (туннель) ----------
Write-Host "`n[3] Публичный URL для вебхуков (туннель/домен)" -ForegroundColor Cyan
Write-Host "    Локально: cloudflared tunnel --url http://localhost:8088 -> https://xxx.trycloudflare.com" -ForegroundColor DarkGray
$wbu = Ask 'WEBHOOK_BASE_URL (Enter = без вебхуков извне)'
if ($wbu) { Set-EnvKey $shopEnv 'WEBHOOK_BASE_URL' $wbu }

# ---------- Шаг 4: YooKassa ----------
Write-Host "`n[4] YooKassa (тест-магазин ок)" -ForegroundColor Cyan
$ykid = Ask 'YOOKASSA_SHOP_ID'
if ($ykid) {
  $yksec = Ask 'YOOKASSA_SECRET_KEY'
  if (-not $yksec) { Write-Host '  без SECRET_KEY пропускаю блок' -ForegroundColor Yellow }
  else {
    Set-EnvKey $shopEnv 'YOOKASSA_ENABLED' 'True'
    Set-EnvKey $shopEnv 'YOOKASSA_SHOP_ID' $ykid
    Set-EnvKey $shopEnv 'YOOKASSA_SECRET_KEY' $yksec
    $ret = Ask 'YOOKASSA_RETURN_URL' 'http://127.0.0.1:8082/'
    if ($ret) { Set-EnvKey $shopEnv 'YOOKASSA_RETURN_URL' $ret }
    $rcpt = Ask 'YOOKASSA_DEFAULT_RECEIPT_EMAIL (email для чеков)'
    if ($rcpt) { Set-EnvKey $shopEnv 'YOOKASSA_DEFAULT_RECEIPT_EMAIL' $rcpt }
  }
}

# ---------- Шаг 5: Мой Налог (фискализация, опционально) ----------
Write-Host "`n[5] Фискализация Мой Налог (опционально)" -ForegroundColor Cyan
$inn = Ask 'NALOGO_INN (ИНН самозанятого, Enter = пропустить)'
if ($inn) {
  $np = Ask 'NALOGO_PASSWORD'
  if ($np) { Set-EnvKey $shopEnv 'NALOGO_INN' $inn; Set-EnvKey $shopEnv 'NALOGO_PASSWORD' $np }
}

Write-Host "`n=== Готово. Пересоздать контейнеры: ===" -ForegroundColor Cyan
Write-Host "`$env:WEB_SERVER_PORT='8087'; docker compose -f shop/docker-compose.yml -f infra/minishop.compose.yml --env-file shop/.env --profile bot up -d backend worker bot"
Write-Host "docker compose --env-file proliv.env --profile app up -d remnawave cabinet"
Write-Host "`nСквады/тарифы потом: infra\seed\seed.ps1 (см. infra\branding.md)" -ForegroundColor DarkGray
