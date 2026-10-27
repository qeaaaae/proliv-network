import { requireUser } from '../utils/session'
import {
  hasShopBackend,
  shopFetch,
  type ShopMe,
  type ShopPlan,
  type ShopTopupOptions,
} from '../utils/backend'

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

  const [me, trafficOpts, deviceOpts] = await Promise.all([
    shopFetch<ShopMe>(event, '/api/me'),
    shopFetch<ShopTopupOptions>(event, '/api/tariffs/topup-options').catch(() => null),
    shopFetch<ShopTopupOptions>(event, '/api/devices/topup-options').catch(() => null),
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
  const extras: { id: string; title: string; price: number }[] = []
  for (const p of trafficOpts?.plans ?? []) {
    const gb = Number(p.traffic_gb ?? p.months ?? 0)
    if (!gb) continue
    extras.push({
      id: `${p.sale_mode === 'premium_topup' ? 'premium' : 'traffic'}-${gb}`,
      title: p.title || `+${gb} ГБ`,
      price: p.price ?? 0,
    })
  }
  for (const p of deviceOpts?.plans ?? []) {
    const count = Number(p.device_count ?? p.months ?? 0)
    if (!count) continue
    extras.push({
      id: `device-${count}`,
      title: p.title || `+${count} устройств`,
      price: p.price ?? 0,
    })
  }
  if (!extras.length) {
    // Фолбэк: пакеты устройств из карточки тарифа (/api/me -> plans)
    for (const p of main?.hwid_device_packages ?? []) {
      extras.push({
        id: `device-${p.device_count ?? p.id}`,
        title: p.title || `+${p.device_count} устройство`,
        price: p.price ?? 0,
      })
    }
  }

  const methods = (me.payment_methods ?? []).map((m) => ({
    id: m.id || '',
    title: m.name || m.id || '',
    icon: m.icon || (m.id === 'yookassa' ? '/images/payments/yookassa.svg' : ''),
  }))

  const specParts: string[] = []
  const gb = main?.monthly_gb ?? main?.traffic_gb
  if (gb) specParts.push(`${gb} ГБ/мес`)
  if (main?.device_count || main?.hwid_device_limit) {
    specParts.push(`${main.device_count ?? main.hwid_device_limit} устройств`)
  }

  return {
    plan: {
      name: me.subscription?.tariff_name || main?.tariff_name || 'Proliv Network',
      spec: specParts.join(', ') || main?.description || '',
    },
    periods,
    extras,
    methods,
  }
})
