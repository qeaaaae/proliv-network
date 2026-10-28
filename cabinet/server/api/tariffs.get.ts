import { requireUser } from '../utils/session'
import {
  hasShopBackend,
  shopFetch,
  type ShopMe,
  type ShopPlan,
  type ShopTopupOptions,
} from '../utils/backend'

interface ShopBalance {
  enabled?: boolean
  currency_scale?: number
  sources?: { id?: string; available?: boolean; amount_minor?: number }[]
}

function planDays(p: ShopPlan): number {
  return p.duration_days ?? Math.round((p.months ?? 1) * 30)
}

// Тарифы и допы: периоды подписки из /api/me -> plans, докупки трафика и
// устройств из /api/tariffs/topup-options + /api/devices/topup-options
// (эндпоинты требуют активной подписки/тарифного конфига - при недоступности
// отдаём то, что есть в карточке плана).
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }

  const [me, trafficOpts, deviceOpts, balance] = await Promise.all([
    shopFetch<ShopMe>(event, '/api/me'),
    shopFetch<ShopTopupOptions>(event, '/api/tariffs/topup-options').catch(() => null),
    shopFetch<ShopTopupOptions>(event, '/api/devices/topup-options').catch(() => null),
    shopFetch<ShopBalance>(event, '/api/balance').catch(() => null),
  ])
  const plans = me.plans ?? []
  const main =
    plans.find((p) => p.tariff_key && p.tariff_key === me.subscription?.tariff_key) ??
    plans.find((p) => p.id === 'default' || p.is_default_tariff) ??
    plans[0]

  const periods = plans
    .filter((p) => (p.sale_mode ?? 'subscription') === 'subscription')
    .map((p, i) => {
      const days = planDays(p)
      return {
        id: p.id || `${p.tariff_key || 'plan'}:${days}:${i}`,
        days,
        // legacy-планы: title = длительность; тарифные: subtitle = длительность
        label: p.subtitle || p.title || `${days} дней`,
        price: p.price ?? 0,
        oldPrice: null as number | null,
      }
    })

  // Докупки: трафик-пакеты (обычные + premium) и пакеты устройств.
  const deviceUnits = (n: number) =>
    n % 10 === 1 && n % 100 !== 11
      ? 'устройство'
      : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20)
        ? 'устройства'
        : 'устройств'
  const bareTitle = (t: string | undefined) => !t || /^\+\d+$/.test(t.trim())
  const extras: { id: string; kind: 'traffic' | 'device'; title: string; price: number }[] = []
  for (const p of trafficOpts?.plans ?? []) {
    const gb = Number(p.traffic_gb ?? p.months ?? 0)
    if (!gb) continue
    extras.push({
      id: `${p.sale_mode === 'premium_topup' ? 'premium' : 'traffic'}-${gb}`,
      kind: 'traffic',
      title: bareTitle(p.title) ? `+${gb} ГБ` : (p.title ?? ''),
      price: p.price ?? 0,
    })
  }
  for (const p of deviceOpts?.plans ?? []) {
    const count = Number(p.device_count ?? p.months ?? 0)
    if (!count) continue
    extras.push({
      id: `device-${count}`,
      kind: 'device',
      title: bareTitle(p.title) ? `+${count} ${deviceUnits(count)}` : (p.title ?? ''),
      price: p.price ?? 0,
    })
  }
  if (!extras.length) {
    // Фолбэк: пакеты устройств из карточки тарифа (/api/me -> plans)
    for (const p of main?.hwid_device_packages ?? []) {
      const count = Number(p.device_count ?? 0)
      extras.push({
        id: `device-${p.device_count ?? p.id}`,
        kind: 'device',
        title: bareTitle(p.title) ? `+${count} ${deviceUnits(count)}` : (p.title ?? ''),
        price: p.price ?? 0,
      })
    }
  }

  // minishop в icon шлёт lucide-имя для своего webapp, а не URL - поэтому
  // логотипы мапим по id провайдера на локальные svg; абсолютный URL
  // (если админ задал свой) пропускаем как есть.
  const METHOD_ICONS: Record<string, string> = {
    yookassa: '/images/payments/yookassa.svg',
    cryptobot: '/images/payments/cryptobot.svg',
    heleket: '/images/payments/heleket.svg',
  }
  const methods = (me.payment_methods ?? []).map((m) => ({
    id: m.id || '',
    title: m.name || m.id || '',
    icon:
      METHOD_ICONS[m.id ?? ''] ??
      (m.icon && /^https?:\/\//.test(m.icon) ? m.icon : ''),
  }))

  const specParts: string[] = []
  const gb = main?.monthly_gb ?? main?.traffic_gb
  if (gb) specParts.push(`${gb} ГБ/мес`)
  if (main?.device_count || main?.hwid_device_limit) {
    specParts.push(`${main.device_count ?? main.hwid_device_limit} устройств`)
  }

  // Балансы для галочки «списать бонусы» в чекауте: user = бонусный счёт,
  // partner = комиссии партнёрки. available флаг уже учитывает enabled и
  // ненулевой остаток; партнёр - ещё и balance_payment_enabled.
  const scale = balance?.currency_scale ?? 2
  const srcAmount = (id: string) => {
    if (balance?.enabled === false) return 0
    const s = balance?.sources?.find((x) => x.id === id)
    return s?.available ? (s.amount_minor ?? 0) / 10 ** scale : 0
  }

  return {
    plan: {
      name: me.subscription?.tariff_name || main?.tariff_name || 'Proliv Network',
      spec: specParts.join(', ') || main?.description || '',
      devices: main?.device_count ?? main?.hwid_device_limit ?? 0,
    },
    periods,
    extras,
    methods,
    balances: { user: srcAmount('user'), partner: srcAmount('partner') },
    suggestedPromoCode: me.suggested_promo_code ?? null,
    friendDiscountPercent: Number(me.referral?.friend_discount_percent ?? 0),
  }
})
