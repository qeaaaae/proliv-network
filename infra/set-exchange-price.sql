INSERT INTO app_setting_overrides (key, value, updated_at) VALUES ('BONUS_EXCHANGE_DAY_PRICE', '7', now()) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now();
