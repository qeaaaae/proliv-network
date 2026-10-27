import { randomUUID } from 'node:crypto'
import { readBody } from 'h3'
import { requireUser } from '../utils/session'
import { hasShopBackend, shopFetch, type ShopMe, type ShopPartnerOverview } from '../utils/backend'

// Балансовые операции. 'days' - покупка периода подписки целиком с внутреннего
// баланса (method=balance); 'pay' - частичная оплата балансом в чекауте;
// 'withdraw' - заявка на вывод партнёрского баланса (отдельная программа
// /api/partner/*, требует включённой партнёрки и реквизитов).
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const body = await readBody<{
    action?: string
    amount?: number
    method?: string
    network?: string
    requisites?: Record<string, string>
  }>(event)
  const amount = Math.max(0, Math.floor(Number(body?.amount) || 0))

  switch (body?.action) {
    case 'days': {
      // Балансом можно оплатить только сконфигурированный период - берём
      // самый длинный период, который покрывает сумма (совпадает с превью
      // на фронте).
      const me = await shopFetch<ShopMe>(event, '/api/me')
      const planDays = (p: { duration_days?: number; months?: number }) =>
        p.duration_days ?? Math.round((p.months ?? 1) * 30)
      const affordable = (me.plans ?? [])
        .filter((p) => (p.sale_mode ?? 'subscription') === 'subscription' && (p.price ?? 0) > 0)
        .sort((a, b) => planDays(b) - planDays(a))
        .find((p) => (p.price ?? 0) <= amount)
      if (!affordable) {
        throw createError({ statusCode: 400, statusMessage: 'Недостаточно бонусов для обмена на дни' })
      }
      const days = planDays(affordable)
      const payload: Record<string, unknown> = {
        method: 'balance',
        sale_mode: 'subscription',
        duration_days: days,
      }
      if (affordable.tariff_key) payload.tariff_key = affordable.tariff_key
      if (affordable.months) payload.months = affordable.months
      const res = await shopFetch<{ ok?: boolean; paid?: boolean; payment_id?: number }>(
        event,
        '/api/payments',
        { method: 'POST', body: payload },
      )
      const after = await shopFetch<ShopMe>(event, '/api/me')
      return { ok: Boolean(res.ok), balance: Number(after.balance?.amount ?? 0), days }
    }
    case 'pay': {
      // Частичная оплата покупки балансом делается в чекауте (balance_source)
      throw createError({ statusCode: 400, statusMessage: 'Оплату балансом выбирайте при оформлении подписки' })
    }
    case 'withdraw': {
      // Вывод - заявка партнёрской программы (баланс partner, не бонусный).
      // method_id/валюта/минимум берутся из /api/partner/overview.
      const methodId = (body?.method || '').trim().toLowerCase()
      if (!methodId) throw createError({ statusCode: 400, statusMessage: 'Выберите способ вывода' })
      if (amount < 1) throw createError({ statusCode: 400, statusMessage: 'Укажите сумму вывода' })

      const partner = await shopFetch<ShopPartnerOverview>(event, '/api/partner/overview').catch(() => null)
      const method = (partner?.withdrawal_methods ?? []).find(
        (m) => m.id === methodId && m.enabled !== false,
      )
      if (!partner?.program_enabled || !partner?.withdrawals_enabled || !method) {
        throw createError({ statusCode: 400, statusMessage: 'Способ вывода недоступен' })
      }
      const scale = method.currency_scale ?? 2
      const amountMinor = Math.round(amount * 10 ** scale)
      if (method.min_amount_minor && amountMinor < method.min_amount_minor) {
        throw createError({
          statusCode: 400,
          statusMessage: `Минимальная сумма вывода - ${(method.min_amount_minor / 10 ** scale).toFixed(0)} ${method.debit_currency ?? ''}`,
        })
      }
      if (method.max_amount_minor && amountMinor > method.max_amount_minor) {
        throw createError({
          statusCode: 400,
          statusMessage: `Максимальная сумма вывода - ${(method.max_amount_minor / 10 ** scale).toFixed(0)} ${method.debit_currency ?? ''}`,
        })
      }
      // Реквизиты: только поля, объявленные в методе (+ network для crypto)
      const allowed = new Set([...(method.fields ?? []).map((f) => f.id || ''), 'network'])
      const requisites: Record<string, string> = {}
      for (const [k, v] of Object.entries(body?.requisites ?? {})) {
        const key = k.trim().toLowerCase()
        if (allowed.has(key) && String(v ?? '').trim()) requisites[key] = String(v).trim()
      }
      const missing = (method.fields ?? []).filter((f) => f.required !== false && !requisites[f.id || ''])
      if (missing.length) {
        throw createError({
          statusCode: 400,
          statusMessage: `Заполните реквизиты: ${missing.map((f) => f.label || f.id).join(', ')}`,
        })
      }

      const res = await shopFetch<{ ok?: boolean }>(event, '/api/partner/withdrawals', {
        method: 'POST',
        body: {
          method_id: method.id,
          amount_minor: amountMinor,
          currency: method.debit_currency || 'RUB',
          requisites,
          network: (body?.network || '').trim().toLowerCase() || undefined,
          idempotency_key: randomUUID(),
        },
      })
      const me = await shopFetch<ShopMe>(event, '/api/me')
      return { ok: Boolean(res.ok ?? true), balance: Number(me.balance?.amount ?? 0) }
    }
    default:
      throw createError({ statusCode: 400, statusMessage: 'Unknown action' })
  }
})
