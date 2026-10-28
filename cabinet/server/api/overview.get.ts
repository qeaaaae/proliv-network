import { requireUser } from '../utils/session'
import { bytesToGb, hasShopBackend, mapDevice, shopFetch, type ShopDevice, type ShopMe } from '../utils/backend'
import { LOCATION_IDS } from '../utils/store'

export default defineEventHandler(async (event) => {
  const user = requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }

  const [me, dev] = await Promise.all([
    shopFetch<ShopMe>(event, '/api/me'),
    shopFetch<{ devices?: ShopDevice[]; max_devices?: number | null }>(event, '/api/devices').catch(() => null),
  ])

  // Подписка считается только при active=true: upstream присылает объект и для
  // неактивной подписки (status INACTIVE) - без дат и ссылок.
  const sub = me.subscription?.active ? me.subscription : null
  const devices = (dev?.devices ?? []).map(mapDevice)
  const subscription = sub
    ? {
        plan: sub.tariff_name || 'Proliv Network',
        until: sub.end_date || '',
        trafficUsedGb: bytesToGb(sub.traffic_used_bytes),
        trafficLimitGb: bytesToGb(sub.traffic_limit_bytes),
        resetAt: sub.traffic_next_reset_at || sub.end_date || '',
        devices,
        deviceLimit: dev?.max_devices ?? sub.max_devices ?? 0,
        locations: [...LOCATION_IDS],
        subscriptionUrl: sub.config_link || sub.connect_url || '',
      }
    : null

  return {
    user: {
      id: me.user?.id ?? user.id,
      name: me.user?.first_name || user.name,
      username: me.user?.username ?? user.username,
      photoUrl: me.user?.telegram_photo_url || user.photoUrl,
    },
    subscription,
    bonusBalance: Number(me.balance?.amount ?? 0),
    trialDays: Number(me.settings?.trial_duration_days ?? 3) || 3,
    trialAvailable: Boolean(me.settings?.trial_available),
    trialPaymentEnabled: Boolean(me.settings?.trial_payment_enabled),
    trialPrice:
      Number((me.settings?.trial_payment_plan as { price?: unknown } | undefined)?.price ?? 0) || 0,
    trialCurrency:
      String((me.settings?.trial_payment_plan as { currency?: unknown } | undefined)?.currency ?? 'RUB'),
    // upstream не фильтрует available_payment_method_ids по видимости
    // провайдера (enabled/configured) - первым лежит выключенный метод
    // (напр. freekassa) и чекаут падает payment_unavailable. Пересекаем
    // с me.payment_methods - он уже отфильтрован по is_visible_for_user.
    trialMethods: (() => {
      const visible = new Set(
        (me.payment_methods ?? []).map((m) => String(m.id || '')).filter(Boolean),
      )
      const planIds = (
        me.settings?.trial_payment_plan as
          | { available_payment_method_ids?: unknown[] }
          | undefined
      )?.available_payment_method_ids
      const ids = Array.isArray(planIds) ? planIds.map(String) : []
      const usable = ids.filter((id) => visible.has(id))
      return usable.length ? usable : [...visible]
    })(),
  }
})
