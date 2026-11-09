# infra/seed - Proliv-брендинг minishop (локальный стенд)

> **ТОЛЬКО local/dev.** Целится в контейнеры `remnawave-minishop-*`
> (docker compose `shop/docker-compose.yml` + `infra/minishop.compose.yml`).
> На проде те же значения заводятся через админку Web App - см.
> `infra/branding.md`.

## Файлы

| Файл | Куда попадает | Что задаёт |
|------|---------------|-----------|
| `tariffs.json` | `/app/data/tariffs.json` (volume `shop-data`) | каталог: 1 тариф `proliv` - 179 ₽/30 дн, 90/180/365 дн со скидкой, 500 ГБ/мес с переносом остатка до 150 ГБ (MONTH_ROLLING + `traffic_rollover_cap_gb`), устройства без лимита, топ-апы трафика |
| `locales-overrides.json` | `/app/data/locales-overrides.json` | тексты бота: приветствие, кнопки, реф-сообщения (ru+en) |
| `settings.sql` | БД `app_setting_overrides` | `WEBAPP_TITLE`, `START_COMMAND_DESCRIPTION`, `WEBAPP_PRIMARY_COLOR=#7dd3fc`, `TRIAL_ENABLED=false`, `SUPPORT_LINK` и пр. |
| `themes/proliv/` | `/app/data/themes/proliv/` (volume `shop-data`) | тема `proliv`: тёмная палитра лендинга (#0a0c0e/#13161a), радиусы 14/20, Manrope + Unbounded (Google Fonts подгружает сам SPA); `default:true` + `WEBAPP_DEFAULT_THEME=proliv` |
| `brand-apply.py` | внутри backend-контейнера | пишет `/app/data/webapp-logo/uploads/logo-<sha>.png` + фавикон-сет `/app/data/webapp-logo/favicons/<sha>/` штатными хелперами админки; печатает URL для оверрайдов |
| `../assets/proliv-drop.{svg,png}` | источник лого | капля Proliv на прозрачном фоне 512x512; `proliv-drop.png` скармливается `brand-apply.py` и идёт в `WEBAPP_LOGO_URL`/`WEBAPP_LOGO_FAVICON_URL` |
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
- Цены финальные (утверждены 2026-10-26): `30/90/180/365` дн = `179/499/949/1799 ₽`,
  топ-апы 100/500 ГБ = 49/149 ₽; устройства - без лимита, докупки устройств нет.

## Что сид НЕ покрывает (только админка/руками)

- Оферта и политика ПД - managed-документы в админке.
- Меню-кнопки - **Внешний вид** / `MENU_BUTTONS_JSON`.
- BotFather: аватар, описания, список команд, menu button - `infra/branding.md` §5.

Лого/фавикон и тема `proliv` покрываются `brand-apply.py` + `themes/proliv/`
(на проде применено 2026-11-02). Альтернатива - **Админка → Внешний вид**.

## Откат

- Файлы: удалить `/app/data/tariffs.json` / `locales-overrides.json` в volume
  (вернутся дефолты) или перезаписать нужным содержимым через админку.
- Настройки: `DELETE FROM app_setting_overrides WHERE key IN (...)` -
  вернутся значения из `shop/.env`.
