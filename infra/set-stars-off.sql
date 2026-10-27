INSERT INTO app_setting_overrides (key, value, updated_at) VALUES ('STARS_ENABLED', 'false', now()) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now();
