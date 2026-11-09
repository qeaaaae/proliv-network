import { randomUUID } from 'node:crypto'
import { readBody } from 'h3'
import { requireUser } from '../utils/session'
import { hasShopBackend, shopFetch, type ShopMe, type ShopPartnerOverview } from '../utils/backend'

interface ShopBalanceSources {
  currency_scale?: number
  sources?: { id?: string; available?: boolean; amount_minor?: number }[]
}

const exchangeErrors: Record<string, string> = {
  bonus_exchange_unavailable: 'Обмен бонусов сейчас недоступен',
  bonus_exchange_insufficient: 'Недостаточно бонусов для обмена',
  bonus_exchange_failed: 'Обмен не удался, попробуйте позже',
}

function exchangeFail(e: unknown): never {
  const data = (e as { data?: { error?: string; message?: string } })?.data
  const code = typeof data?.error === 'string' ? data.error : ''
  throw createError({
    statusCode: (e as { statusCode?: number })?.statusCode ?? 400,
    statusMessage: exchangeErrors[code] ?? data?.message ?? 'Обмен не удался',
  })
}

// Балансовые операции. 'days' - обмен бонусов на дни подписки
// (/api/referral/exchange, 1 день = BONUS_EXCHANGE_DAY_PRICE); 'pay' - частичная
// оплата балансом в чекауте; 'withdraw' - заявка на вывод партнёрского баланса
// (отдельная программа /api/partner/*, требует включённой партнёрки и реквизитов).
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const body = await readBody<{
    action?: string
    amount?: number
    days?: number
    method?: string
    network?: string
    requisites?: Record<string, string>
  }>(event)
  const amount = Math.max(0, Math.floor(Number(body?.amount) || 0))

  switch (body?.action) {
    case 'days': {
      // Обмен на дни идёт с любого счёта: сначала бонусный кошелёк,
      // остаток - партнёрский (source - vendored-патч upstream exchange).
      const days = Math.max(1, Math.floor(Number(body?.days ?? body?.amount) || 0))
      const [me, bal] = await Promise.all([
        shopFetch<ShopMe>(event, '/api/me').catch(() => null),
        shopFetch<ShopBalanceSources>(event, '/api/balance').catch(() => null),
      ])
      const scale = bal?.currency_scale ?? 2
      const priceMinor = Math.round(Number(me?.referral?.exchange_day_price ?? 0) * 10 ** scale)
      const srcMinor = (id: string) => {
        const s = bal?.sources?.find((x) => x.id === id)
        return s?.available ? (s.amount_minor ?? 0) : 0
      }

      let userDays = days
      let partnerDays = 0
      if (priceMinor > 0) {
        userDays = Math.min(days, Math.floor(srcMinor('user') / priceMinor))
        partnerDays = days - userDays
        if (partnerDays > Math.floor(srcMinor('partner') / priceMinor)) {
          throw createError({ statusCode: 400, statusMessage: exchangeErrors.bonus_exchange_insufficient })
        }
      }

      let ok = true
      if (userDays > 0) {
        const res = await shopFetch<{ ok?: boolean }>(event, '/api/referral/exchange', {
          method: 'POST',
          body: { days: userDays, source: 'user' },
        }).catch(exchangeFail)
        ok = ok && Boolean(res.ok)
      }
      if (partnerDays > 0) {
        const res = await shopFetch<{ ok?: boolean }>(event, '/api/referral/exchange', {
          method: 'POST',
          body: { days: partnerDays, source: 'partner' },
        }).catch(exchangeFail)
        ok = ok && Boolean(res.ok)
      }
      const after = await shopFetch<ShopMe>(event, '/api/me')
      return { ok, balance: Number(after.balance?.amount ?? 0), days }
    }
    case 'pay': {
      // Частичная оплата балансом - галочка «Списать бонусы» в чекауте
      // (/api/checkout принимает balanceSource -> balance_source).
      throw createError({ statusCode: 400, statusMessage: 'Включите списание бонусов галочкой при оформлении подписки' })
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
