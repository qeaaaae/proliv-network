# ============================================================
# Proliv Network - seed для minishop
# ТОЛЬКО локальный/dev стенд (docker compose с infra/minishop.compose.yml).
# НЕ запускать на проде. Скрипт НЕ меняет код и .env-файлы.
#
# Что делает:
#   1) копирует tariffs.json и locales-overrides.json в /app/data
#      (named volume remnawave-minishop-shop-data, общий для backend/worker)
#   2) применяет settings.sql к БД (app_setting_overrides)
#   3) рестартует backend+worker, чтобы подхватить оверрайды
#
# Запуск из корня репо (PowerShell):
#   pwsh -File infra/seed/seed.ps1
#
# Предусловия: стек minishop уже поднят, миграции пройдены.
# ============================================================

$ErrorActionPreference = 'Stop'

$BackendContainer  = 'remnawave-minishop-backend'
$PostgresContainer = 'remnawave-minishop-postgres'
$RestartContainers = @('remnawave-minishop-backend', 'remnawave-minishop-worker')

$SeedDir = $PSScriptRoot
$Tariffs  = Join-Path $SeedDir 'tariffs.json'
$Locales  = Join-Path $SeedDir 'locales-overrides.json'
$Settings = Join-Path $SeedDir 'settings.sql'

# --- 0. Проверки -----------------------------------------------------------

foreach ($f in @($Tariffs, $Locales, $Settings)) {
    if (-not (Test-Path $f)) { throw "Нет файла: $f" }
}

$running = docker ps --format '{{.Names}}' 2>$null
if ($LASTEXITCODE -ne 0) { throw 'docker недоступен' }
foreach ($c in @($BackendContainer, $PostgresContainer)) {
    if ($running -notcontains $c) {
        throw "Контейнер $c не запущен. Сначала: docker compose -f shop/docker-compose.yml -f infra/minishop.compose.yml up -d --build"
    }
}

$raw = Get-Content $Tariffs -Raw
if ($raw -match 'REPLACE_ME_') {
    Write-Warning 'В tariffs.json остались REPLACE_ME_* squad_uuids - каталог валиден, но подписки не выдадутся, пока не подставить реальные Internal Squad UUID из Remnawave (Админка -> Система -> Тарифы подгружает их из панели).'
    $reply = Read-Host 'Продолжить с плейсхолдерами? [y/N]'
    if ($reply -notmatch '^(y|yes)$') { Write-Host 'Отменено.'; exit 1 }
}

# --- 1. Файлы в /app/data (shop-data volume) --------------------------------

Write-Host '-> tariffs.json -> /app/data/tariffs.json'
docker cp $Tariffs "${BackendContainer}:/app/data/tariffs.json"

Write-Host '-> locales-overrides.json -> /app/data/locales-overrides.json'
docker cp $Locales "${BackendContainer}:/app/data/locales-overrides.json"

# --- 2. SQL в app_setting_overrides -----------------------------------------
# Креды берём из env самого postgres-контейнера (shop/.env не читаем).

Write-Host '-> settings.sql -> app_setting_overrides'
docker cp $Settings "${PostgresContainer}:/tmp/proliv-settings.sql"
docker exec $PostgresContainer sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/proliv-settings.sql'
if ($LASTEXITCODE -ne 0) { throw 'psql завершился с ошибкой' }

# --- 3. Рестарт backend+worker ----------------------------------------------

Write-Host '-> restart backend + worker'
docker restart $RestartContainers | Out-Null

Write-Host ''
Write-Host 'Готово. Проверка:'
Write-Host '  - Web App:      http://localhost:8086  (заголовок = Proliv Network)'
Write-Host '  - Админка:      Система -> Тарифы / Переводы / Настройки, Внешний вид'
Write-Host '  - Дальше:       лого в "Внешний вид", сквады в tariffs.json, BotFather (infra/branding.md §5)'
