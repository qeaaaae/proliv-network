# ============================================================
# infra/tunnels.ps1 - local dev tunnels for the minishop stack.
#
# Three cloudflared quick tunnels are needed for local dev:
#   1) bot webhook   -> http://localhost:8088  (WEBHOOK_BASE_URL,
#      Telegram calls setWebhook(WEBHOOK_BASE_URL + /tg/webhook))
#   2) cabinet app   -> http://localhost:8082  (PUBLIC_APP_URL and
#      SUBSCRIPTION_MINI_APP_URL - Mini App buttons require HTTPS)
#   3) landing site  -> http://localhost:8080  (REFERRAL_INFO_URL =
#      <landing>/offer#referral, stored in app_setting_overrides)
#
# trycloudflare URLs are ephemeral: every new tunnel run gives new
# random domains, so shop/.env is patched each run and the bot+backend
# containers must be recreated (`up -d`, NOT `restart` - restart does
# not re-read env_file).
#
# Requires infra\tools\cloudflared.exe (one-time download):
#   curl.exe -L -o infra\tools\cloudflared.exe https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
#
# Usage (from repo root):
#   powershell -ExecutionPolicy Bypass -File infra\tunnels.ps1
#   powershell -ExecutionPolicy Bypass -File infra\tunnels.ps1 -Stop
# ============================================================

param([switch]$Stop)

$root   = Split-Path $PSScriptRoot -Parent
$cf     = Join-Path $root 'infra\tools\cloudflared.exe'
$envFile = Join-Path $root 'shop\.env'
$logDir = Join-Path $env:TEMP 'proliv-tunnels'

if ($Stop) {
  Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
  Write-Host 'cloudflared stopped.' -ForegroundColor Yellow
  exit 0
}

if (-not (Test-Path $cf)) {
  Write-Host 'cloudflared.exe not found. Downloading...' -ForegroundColor Yellow
  New-Item -ItemType Directory -Force (Split-Path $cf -Parent) | Out-Null
  curl.exe -L -o $cf 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -m 180 -sS
  if (-not (Test-Path $cf)) { Write-Error 'cloudflared download failed'; exit 1 }
}

# Kill stale tunnels so URLs and .env stay in sync.
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
New-Item -ItemType Directory -Force $logDir | Out-Null

function Start-Tunnel([string]$Name, [int]$Port) {
  $out = Join-Path $logDir "$Name.out.log"
  $err = Join-Path $logDir "$Name.err.log"
  Remove-Item $out,$err -ErrorAction SilentlyContinue
  # http2: QUIC/UDP 7844 is blocked on this network (precheck FAIL).
  Start-Process -FilePath $cf -ArgumentList "tunnel --url http://localhost:$Port --no-autoupdate --protocol http2" `
    -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden -PassThru | Out-Null
  return $err  # cloudflared prints the assigned URL to stderr
}

function Get-TunnelUrl([string]$LogFile) {
  for ($i = 0; $i -lt 30; $i++) {
    if (Test-Path $LogFile) {
      $m = Select-String -Path $LogFile -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' |
           Select-Object -First 1
      if ($m) { return $m.Matches[0].Value }
    }
    Start-Sleep -Seconds 1
  }
  return $null
}

Write-Host '[1/4] bot webhook tunnel -> localhost:8088' -ForegroundColor Cyan
$botLog = Start-Tunnel 'bot' 8088

Write-Host '[2/4] cabinet tunnel -> localhost:8082' -ForegroundColor Cyan
$appLog = Start-Tunnel 'cabinet' 8082

Write-Host '[3/4] landing tunnel -> localhost:8080' -ForegroundColor Cyan
$landingLog = Start-Tunnel 'landing' 8080

$botUrl = Get-TunnelUrl $botLog
$appUrl = Get-TunnelUrl $appLog
$landingUrl = Get-TunnelUrl $landingLog

if (-not $botUrl -or -not $appUrl -or -not $landingUrl) {
  Write-Error "Tunnel URL not detected. Logs: $logDir"
  exit 1
}

Write-Host "  bot:     $botUrl" -ForegroundColor Green
Write-Host "  cabinet: $appUrl" -ForegroundColor Green
Write-Host "  landing: $landingUrl" -ForegroundColor Green

Write-Host '[4/4] patching shop/.env + REFERRAL_INFO_URL override' -ForegroundColor Cyan
if (-not (Test-Path $envFile)) { Write-Error "missing $envFile"; exit 1 }

$lines = Get-Content $envFile
function Set-Key($lines, [string]$key, [string]$value) {
  if ($lines -match "^$key=") { return $lines -replace "^$key=.*", "$key=$value" }
  return $lines + "$key=$value"
}
$lines = Set-Key $lines 'WEBHOOK_BASE_URL'         $botUrl
$lines = Set-Key $lines 'PUBLIC_APP_URL'           "$appUrl/"
$lines = Set-Key $lines 'SUBSCRIPTION_MINI_APP_URL' "$appUrl/"
Set-Content $envFile $lines -Encoding utf8

# REFERRAL_INFO_URL lives in app_setting_overrides (JSON-encoded value);
# update it so the 'Реф программа и бонусы' button points at this landing.
$refUrl = "$landingUrl/offer#referral"
$pg = 'remnawave-minishop-postgres'
$pgUp = (docker ps --format '{{.Names}}' | Select-String -SimpleMatch $pg)
if ($pgUp) {
  $sql = @"
INSERT INTO app_setting_overrides (key, value, updated_at)
VALUES ('REFERRAL_INFO_URL', '"$refUrl"', NOW())
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();
"@
  $sql | docker exec -i $pg psql -U remnawave_minishop -d remnawave_minishop | Out-Null
  Write-Host "  REFERRAL_INFO_URL -> $refUrl" -ForegroundColor Green
  Write-Host '  (bot/backend pick it up on next `up -d` recreate)' -ForegroundColor DarkGray
} else {
  Write-Host "  postgres container not up - set REFERRAL_INFO_URL to $refUrl manually" -ForegroundColor Yellow
}

Write-Host ''
Write-Host 'Done. Recreate services so env is re-read:' -ForegroundColor Green
Write-Host '  docker compose -f shop/docker-compose.yml -f infra/minishop.compose.yml --env-file shop/.env up -d bot backend' -ForegroundColor White
Write-Host ''
Write-Host 'Stop tunnels:  powershell -File infra\tunnels.ps1 -Stop' -ForegroundColor DarkGray
Write-Host "Tunnel logs:   $logDir" -ForegroundColor DarkGray
