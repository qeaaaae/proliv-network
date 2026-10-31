// Типы контрактов minishop admin API для раздела "Пользователи".
// Источники: shop/backend/bot/app/web/admin_api_impl/{user_schemas,schemas,
// payment_schemas,squad_override_schemas,subscription_plan_schemas}.py

export interface AdminUser {
  user_id: number
  account_id: string | null
  minishop_id: string | null
  panel_username: string | null
  panel_username_state: string | null
  telegram_id: number | null
  telegram_photo_url: string | null
  username: string | null
  first_name: string | null
  last_name: string | null
  email: string | null
  language_code: string | null
  is_banned: boolean
  registration_date: string | null
  panel_user_uuid: string | null
  referral_code: string | null
  referred_by_id: number | null
  avatar_url: string | null
}

export interface AdminPremiumTraffic {
  state: 'none' | 'unlimited' | 'good' | 'warn' | 'critical' | string
  unlimited?: boolean
  used_bytes?: number | null
  limit_bytes?: number | null
  percent?: number | null
}

export interface AdminSubscriptionPlan {
  kind: 'tariff' | 'trial' | 'unassigned'
  tariff_key: string | null
  tariff_names: Record<string, string>
  is_configured: boolean
  is_enabled: boolean | null
  is_active: boolean
}

export interface AdminUserListItem extends AdminUser {
  panel_status: string | null
  subscription_expires_at: string | null
  panel_status_expired_at?: string | null
  premium_traffic: AdminPremiumTraffic
  subscription_plan: AdminSubscriptionPlan | null
  payments_total_amount: number
  payments_count: number
  payments_currency: string | null
  invited_users_count: number
  user_balance_amount_minor: number
  partner_balance_amount_minor: number
}

export interface AdminTariffOption {
  tariff_key: string
  tariff_names: Record<string, string>
  is_configured: boolean
  is_enabled: boolean | null
}

export interface AdminUsersListResponse {
  users: AdminUserListItem[]
  page: number
  page_size: number
  total: number
  tariff_options: AdminTariffOption[]
  user_balance_enabled: boolean
  partner_balance_enabled: boolean
  balance_currency: string
  balance_currency_scale: number
}

export interface AdminSubscription {
  subscription_id: number
  panel_user_uuid: string | null
  panel_subscription_uuid: string | null
  start_date: string | null
  end_date: string | null
  duration_months: number | null
  duration_days: number | null
  period_semantics: string | null
  is_active: boolean
  status_from_panel: string | null
  traffic_limit_bytes: number | null
  traffic_used_bytes: number | null
  tier_baseline_bytes: number | null
  topup_balance_bytes: number | null
  premium_used_bytes: number | null
  premium_limit_bytes: number
  premium_baseline_bytes: number | null
  premium_topup_balance_bytes: number | null
  premium_topup_used_bytes: number | null
  premium_bonus_bytes: number
  regular_bonus_bytes: number
  regular_unlimited_override: boolean
  premium_unlimited_override: boolean
  premium_is_limited: boolean
  hwid_device_limit: number | null
  extra_hwid_devices: number
  tariff_key: string | null
  tariff_binding_source: string | null
  tariff_bound_at: string | null
  tariff_binding_note: string | null
  display_label: string | null
  is_trial: boolean
  auto_renew_enabled: boolean
  provider: string | null
  is_throttled: boolean
  billing_model: string | null
  traffic_limit_strategy: string | null
  traffic_strategy_editable: boolean
  traffic_strategy_lock_reason: string | null
}

export interface AdminUserTrial {
  used: boolean
  count: number
  first_activated_at: string | null
  latest_activated_at: string | null
  latest_end_date: string | null
  active: boolean
  last_reset_at: string | null
}

export interface AdminPayment {
  payment_id: number
  user_id: number
  user_minishop_id: string | null
  user_label: string
  telegram_id: number | null
  provider: string | null
  funding_source: string
  provider_payment_id: string | null
  provider_payment_url: string | null
  amount: number
  currency: string | null
  status: string | null
  description: string | null
  subscription_duration_months: number | null
  subscription_duration_days: number | null
  sale_mode: string | null
  tariff_key: string | null
  created_at: string | null
}

export interface AdminBalanceSource {
  id: string
  available: boolean
  recurring_available: boolean
  adjustable: boolean
  convertible?: boolean
  status?: string | null
  amount_minor: number
  amount: string
  currency: string
}

export interface AdminBalanceEntry {
  entry_id: number
  source_id: string
  amount_minor: number
  kind: string
  state: string
  reason: string | null
  reference_type: string
  reference_id: string
  created_at: string | null
}

export interface AdminBalance {
  ok?: boolean
  enabled: boolean
  recurring_enabled?: boolean
  currency: string
  currency_scale: number
  amount_minor: number
  amount: string
  sources: AdminBalanceSource[]
  history?: AdminBalanceEntry[]
}

export interface AdminHwidDevices {
  current_devices: number | null
  max_devices: number | null
}

export interface AdminTelegramNotifications {
  status: string
  checked_at: string | null
  enabled_at: string | null
  blocked_at: string | null
}

export interface AdminNotificationPreferences {
  marketing_email: boolean
  marketing_telegram: boolean
  system_email: boolean
  system_telegram: boolean
}

export interface AdminPanelSquadItem {
  uuid: string
  label: string | null
  source: string
  last_seen_at: string | null
}

export interface AdminPanelSquadOverrides {
  panel_user_uuid: string | null
  panel_snapshot_available: boolean
  managed_internal_squads: AdminPanelSquadItem[]
  manual_internal_squads: AdminPanelSquadItem[]
  effective_internal_squad_uuids: string[]
  external: {
    mode: string
    default_uuid: string | null
    manual_uuid: string | null
    effective_uuid: string | null
    source: string | null
    last_seen_at: string | null
  }
}

export interface AdminPartnerAttribution {
  partner_id: number
  partner_user_id: number | null
  display_label: string
  public_client_id: string
  source: string
  attributed_at: string
}

export interface AdminReferralInfo {
  code: string | null
  bot_link: string | null
  webapp_link: string | null
  inviter: AdminUser | null
  invitees_total: number
}

export interface AdminUserDetail {
  user: AdminUser
  has_relationships: boolean
  active_subscription: AdminSubscription | null
  subscriptions: AdminSubscription[]
  trial: AdminUserTrial
  total_paid: number
  recent_payments: AdminPayment[]
  log_count: number
  balance: AdminBalance
  subscription_url: string | null
  panel_user_url: string | null
  install_share_url: string | null
  last_vpn_connected_at: string | null
  vpn_connection_status: string
  hwid_devices: AdminHwidDevices
  telegram_notifications: AdminTelegramNotifications
  notification_preferences: AdminNotificationPreferences
  panel_squad_overrides: AdminPanelSquadOverrides | null
  partner_attribution: AdminPartnerAttribution | null
  referral: AdminReferralInfo
}

export interface AdminUserReferralsResponse {
  user: AdminUser
  inviter: AdminUser | null
  invitees: AdminUser[]
  total: number
  page: number
  page_size: number
}

export interface AdminMergeContext {
  user_id: number
  auth_identities: {
    provider: string
    email: string | null
    email_verified: boolean
    display_name: string | null
  }[]
  verified_emails: string[]
  passkey_count: number
  password_available: boolean
  merge_eligibility: { allowed: boolean; reason: string | null }
}

export interface AdminLogEntry {
  log_id: number
  user_id: number | null
  user_label: string | null
  telegram_username: string | null
  telegram_first_name: string | null
  email: string | null
  event_type: string | null
  content: string | null
  is_admin_event: boolean
  target_user_id: number | null
  target_user_label: string | null
  timestamp: string | null
}

export interface AdminLogsResponse {
  logs: AdminLogEntry[]
  page: number
  page_size: number
  total: number
}

export interface AdminInternalSquad {
  uuid: string
  name: string
  members_count: number | string | null
  active_inbounds_count: number | string | null
}
