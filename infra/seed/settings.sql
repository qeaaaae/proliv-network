-- ============================================================
-- Proliv Network - brand/settings seed for minishop
-- Контейнер remnawave-minishop-postgres (local и прод).
--
-- Таблица app_setting_overrides: key TEXT PK, value TEXT = JSON-encoded
-- значение (см. backend/db/dal/app_settings_dal.py::_encode).
-- Оверрайды имеют приоритет над shop/.env.
-- ============================================================

BEGIN;

INSERT INTO app_setting_overrides (key, value, updated_at)
VALUES
  -- Название сервиса: <title>, og-теги, {brand} в письмах
  ('WEBAPP_TITLE',                '"Proliv Network"',                    now()),
  -- Описание /start в меню команд бота
  ('START_COMMAND_DESCRIPTION',   '"Proliv Network - главное меню"',     now()),
  -- Язык по умолчанию
  ('DEFAULT_LANGUAGE',            '"ru"',                                now()),
  -- Фирменный акцент webapp (= --accent в landing/cabinet)
  ('WEBAPP_PRIMARY_COLOR',        '"#7dd3fc"',                           now()),
  -- Раздел "Мои устройства" (лимит устройств виден юзеру)
  ('MY_DEVICES_SECTION_ENABLED',  'true',                                now()),
  -- Страница статуса серверов выкл, пока нечего показывать
  ('SERVER_STATUS_ENABLED',       'false',                               now()),
  -- Поддержка: канал Proliv
  ('SUPPORT_LINK',                '"https://t.me/prolivnet"',            now())
ON CONFLICT (key) DO UPDATE
  SET value = EXCLUDED.value,
      updated_at = now();

-- Намеренно НЕ сидируем (env/админка - правильнее):
--   SUBSCRIPTION_MINI_APP_URL   - задаётся в shop/.env (https://app.proliv.net на проде)
--   WEBAPP_LOGO_URL             - лучше загрузить лого через админку "Внешний вид"
--   PRIVACY_POLICY_URL          - лучше managed-документ (Админка -> Документы)
--   USER_AGREEMENT_URL          - лучше managed-документ (Админка -> Документы)
-- Если всё же нужны внешние ссылки, раскомментировать и подставить:
-- INSERT INTO app_setting_overrides (key, value, updated_at) VALUES
--   ('PRIVACY_POLICY_URL', '"https://proliv.net/legal/policy"', now()),
--   ('USER_AGREEMENT_URL', '"https://proliv.net/legal/terms"',  now())
-- ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now();

COMMIT;
