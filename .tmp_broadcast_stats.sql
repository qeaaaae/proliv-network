\pset footer off
SELECT '== events today (MSK day) ==' AS x;
SELECT ml.event_type, count(*) AS n
FROM message_logs ml
WHERE ml."timestamp" >= (date_trunc('day', now() AT TIME ZONE 'Europe/Moscow') AT TIME ZONE 'Europe/Moscow')
GROUP BY ml.event_type
ORDER BY n DESC;

SELECT '== user-facing sends detail ==' AS x;
SELECT ml.event_type,
       u.telegram_id,
       u.username,
       u.first_name,
       left(ml.content, 80) AS content,
       to_char(ml."timestamp" AT TIME ZONE 'Europe/Moscow', 'HH24:MI') AS msk
FROM message_logs ml
LEFT JOIN users u ON u.user_id = ml.target_user_id
WHERE ml."timestamp" >= (date_trunc('day', now() AT TIME ZONE 'Europe/Moscow') AT TIME ZONE 'Europe/Moscow')
  AND ml.event_type IN (
    'trial_convert_offer', 'stale_connection_notice',
    'winback_survey_sent', 'notrial_survey_sent',
    'telegram_subscription_notification_sent',
    'telegram_traffic_warning_sent', 'telegram_traffic_reset_notice_sent',
    'telegram_device_notification_sent', 'telegram_torrent_notification_sent'
  )
ORDER BY ml.event_type, ml."timestamp";

SELECT '== subscription_notifications markers today ==' AS x;
SELECT sn.notification_key, count(*) AS n
FROM subscription_notifications sn
WHERE sn.sent_at >= (date_trunc('day', now() AT TIME ZONE 'Europe/Moscow') AT TIME ZONE 'Europe/Moscow')
GROUP BY sn.notification_key
ORDER BY n DESC;
