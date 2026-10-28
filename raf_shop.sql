\x off
SELECT s.subscription_id, s.user_id, u.telegram_id, s.panel_user_uuid, s.panel_subscription_uuid, s.status_from_panel,
       s.is_active, s.end_date, s.traffic_limit_bytes, s.hwid_device_limit, s.hwid_device_limit_is_override
FROM subscriptions s LEFT JOIN users u ON u.user_id = s.user_id
ORDER BY s.subscription_id;
SELECT user_id, telegram_id, username, panel_user_uuid FROM users ORDER BY user_id;
