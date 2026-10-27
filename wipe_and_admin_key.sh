#!/usr/bin/env bash
set -euo pipefail
TS=$(date +%Y%m%d-%H%M%S)
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
API="http://127.0.0.1:3443/api"

papi() { # papi METHOD PATH [DATA]
  local method="$1" path="$2" data="${3:-}"
  if [ -n "$data" ]; then
    curl -s -X "$method" -H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' \
      -H 'X-Forwarded-Proto: https' -H 'Content-Type: application/json' -d "$data" "$API$path"
  else
    curl -s -X "$method" -H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' \
      -H 'X-Forwarded-Proto: https' "$API$path"
  fi
}

echo "===== STEP 0: backup ====="
mkdir -p /root/backups
docker exec remnawave-minishop-postgres pg_dump -U remnawave_minishop -d remnawave_minishop -Fc -f /tmp/pw.dump
docker cp remnawave-minishop-postgres:/tmp/pw.dump "/root/backups/minishop_pre_wipe_${TS}.dump"
ls -la "/root/backups/minishop_pre_wipe_${TS}.dump"

echo "===== STEP 1: panel users BEFORE wipe ====="
curl -s -H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' "$API/users?size=100" -o /tmp/panel_users.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/panel_users.json'))
r=d.get('response',d)
us=r.get('users',r if isinstance(r,list) else r.get('items',[]))
for u in us:
    print(u.get('uuid'),'|',u.get('username'),'|',u.get('status'),'| hwid:',u.get('hwidDeviceLimit'),'| sub:',str(u.get('subscriptionUrl'))[:70])
PY

echo "===== STEP 2: wipe minishop business tables ====="
docker exec -i remnawave-minishop-postgres psql -U remnawave_minishop -d remnawave_minishop <<'SQL'
BEGIN;
TRUNCATE TABLE
  account_aliases, account_cleanup_intents,
  ad_attributions, ad_audit, ad_auth_contexts, ad_campaigns, ad_external_metrics,
  ad_import_batches, ad_links, ad_match_candidates, ad_offer_activations,
  ad_promo_bindings, ad_purchase_attributions, ad_spend_entries, ad_touchpoints,
  ad_utm_rules, ad_visits,
  admin_broadcast_deliveries, admin_broadcasts,
  auto_renew_cycles, cleaned_trial_identities, email_verification_codes,
  extension_operations, extension_orders, extension_presentation,
  flexible_traffic_limits, hwid_device_purchases,
  legacy_import_mappings, legacy_referral_codes,
  message_images, message_logs,
  partner_applications, partner_audit_events, partner_clients, partner_commissions,
  partner_ledger_entries, partner_profiles, partner_withdrawals,
  payments, platega_subscriptions, promo_code_activations, promo_codes,
  provider_mandates, qr_login_requests, referral_period_accruals,
  rollypay_subscriptions, security_throttles,
  subscription_access_rotations, subscription_gifts,
  subscription_lifecycle_notifications, subscription_notifications,
  subscriptions, support_ticket_messages, support_tickets,
  tariff_changes, traffic_topups, traffic_warnings,
  tribute_entitlements, tribute_product_purchases,
  tribute_shop_webhook_events, tribute_webhook_events,
  user_balance_ledger_entries, user_billing, user_device_names,
  user_email_addresses, user_external_identities, user_panel_squad_overrides,
  user_passkey_credentials, user_payment_methods, user_telegram_avatars,
  wata_subscriptions, webauthn_challenges
CASCADE;
DELETE FROM users WHERE user_id <> 1000000000000;
COMMIT;
SELECT 'users left' AS t, count(*) FROM users
UNION ALL SELECT 'subscriptions', count(*) FROM subscriptions
UNION ALL SELECT 'promo_codes', count(*) FROM promo_codes
UNION ALL SELECT 'payments', count(*) FROM payments
UNION ALL SELECT 'app_setting_overrides (kept)', count(*) FROM app_setting_overrides
UNION ALL SELECT 'schema_migrations (kept)', count(*) FROM schema_migrations
UNION ALL SELECT 'account_roles (kept)', count(*) FROM account_roles;
SQL

echo "===== STEP 3: flush minishop redis ====="
docker exec remnawave-minishop-redis redis-cli flushdb

echo "===== STEP 4: delete orphaned panel users ====="
for uuid in $(python3 -c "
import json
d=json.load(open('/tmp/panel_users.json'))
r=d.get('response',d)
us=r.get('users',r if isinstance(r,list) else r.get('items',[]))
print(' '.join(str(u.get('uuid')) for u in us if u.get('uuid')))
"); do
  echo "-- delete $uuid"
  papi DELETE "/users/$uuid" | head -c 200; echo
done

echo "===== STEP 5: internal squads ====="
curl -s -H "Authorization: Bearer $JWT" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' "$API/internal-squads" -o /tmp/squads.json
python3 - <<'PY'
import json
d=json.load(open('/tmp/squads.json'))
r=d.get('response',d)
sq=r.get('internalSquads',r if isinstance(r,list) else r.get('items',[]))
for s in sq:
    print(s.get('uuid'),'|',s.get('name'))
PY
