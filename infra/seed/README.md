# infra/seed - Proliv-брендинг minishop (локальный стенд)

> **ТОЛЬКО local/dev.** Целится в контейнеры `remnawave-minishop-*`
> (docker compose `shop/docker-compose.yml` + `infra/minishop.compose.yml`).
> На проде те же значения заводятся через админку Web App - см.
> `infra/branding.md`.

## Файлы

| Файл | Куда попадает | Что задаёт |
|------|---------------|-----------|
| `tariffs.json` | `/app/data/tariffs.json` (volume `shop-data`) | каталог: 1 тариф `proliv` - 179 ₽/30 дн, 90/180/365 дн со скидкой, 1 ТБ, 5 устройств, топ-апы |
| `locales-overrides.json` | `/app/data/locales-overrides.json` | тексты бота: приветствие, кнопки, реф-сообщения (ru+en) |
| `settings.sql` | БД `app_setting_overrides` | `WEBAPP_TITLE`, `START_COMMAND_DESCRIPTION`, `WEBAPP_PRIMARY_COLOR=#7dd3fc`, `TRIAL_ENABLED=false`, `SUPPORT_LINK` и пр. |
| `seed.ps1` | - | копирует файлы через `docker cp`, прогоняет SQL, рестартует backend+worker |

## Запуск (из корня репо, PowerShell)

```powershell
pwsh -File infra/seed/seed.ps1
```

Предусловие: стек уже поднят
(`docker compose -f shop/docker-compose.yml -f infra/minishop.compose.yml up -d --build`).

## Перед применением - ОБЯЗАТЕЛЬНО заменить

- `tariffs.json` → `squad_uuids`: `REPLACE_ME_*` на реальные UUID
  Internal Squads из Remnawave (UK/EE/DE). Взять в админке панели или через
  `GET /api/admin/panel/internal-squads`; редактор тарифов в админке умеет
  подгружать их списком.
- `settings.sql` → `SUPPORT_LINK`: реальный канал/бот поддержки.
- Цены 3/6/12 мес (`499/949/1799`), топ-апы и цена +1 устройства (29 ₽) -
  плейсхолдеры, утвердить финальные.

## Что сид НЕ покрывает (только админка/руками)

- Лого и фавикон - **Админка → Внешний вид** (или `WEBAPP_LOGO_URL`).
- Оферта и политика ПД - managed-документы в админке.
- Тема/шрифты/меню-кнопки - **Внешний вид** / `MENU_BUTTONS_JSON`.
- BotFather: аватар, описания, список команд, menu button - `infra/branding.md` §5.

## Откат

- Файлы: удалить `/app/data/tariffs.json` / `locales-overrides.json` в volume
  (вернутся дефолты) или перезаписать нужным содержимым через админку.
- Настройки: `DELETE FROM app_setting_overrides WHERE key IN (...)` -
  вернутся значения из `shop/.env`.
