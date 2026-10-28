BEGIN;
UPDATE subscriptions
SET regular_unlimited_override = true,
    traffic_limit_bytes = 0,
    hwid_device_limit = 10,
    hwid_device_limit_is_override = true
WHERE subscription_id = 3 AND panel_subscription_uuid = 'WKA2c2STkbrb5LHf';
SELECT subscription_id, regular_unlimited_override, traffic_limit_bytes, hwid_device_limit, hwid_device_limit_is_override
FROM subscriptions WHERE subscription_id = 3;
COMMIT;
