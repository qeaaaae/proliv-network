import { requireUser } from '../utils/session'
import { hasShopBackend, shopFetch, type ShopMe, type ShopPartnerOverview } from '../utils/backend'
import type { BonusEntry } from '../utils/store'

interface ShopBalanceEntry {
  entry_id?: number
  kind?: string
  reason?: string | null
  amount_minor?: number
  created_at?: string | null
  state?: string
}

interface ShopWithdrawal {
  withdrawal_id?: number
  method_id?: string
  method_snapshot?: { label?: string }
  amount_minor?: number
  currency?: string
  currency_scale?: number
  status?: string
  masked_requisites?: string
  requested_at?: string
}

const WITHDRAWAL_TITLES: Record<string, string> = {
  requested: 'Заявка на вывод',
  processing: 'Вывод в обработке',
  paid: 'Вывод выплачен',
  failed: 'Вывод не прошёл',
  rejected: 'Вывод отклонён',
  canceled: 'Вывод отменён',
}

// Реферальный кабинет: ссылка и счётчики из /api/me, партнёрский баланс,
// методы и история выводов - из /api/partner/*. Ledger-баланса юзера upstream
// наружу не отдаёт (snapshot без history) - история собирается из выводов.
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }

  const [me, partner, withdrawals] = await Promise.all([
    shopFetch<ShopMe>(event, '/api/me'),
    // Партнёрка может быть выключена - тогда вывод просто недоступен
    shopFetch<ShopPartnerOverview>(event, '/api/partner/overview').catch(() => null),
    shopFetch<{ withdrawals?: ShopWithdrawal[] }>(event, '/api/partner/withdrawals').catch(
      () => null,
    ),
  ])
  const ref = me.referral ?? {}
  const history = (me.balance?.history ?? []) as ShopBalanceEntry[]

  const bonusHistory: BonusEntry[] = history.map((e) => ({
    id: `b-${e.entry_id ?? Math.random().toString(36).slice(2)}`,
    kind: (e.amount_minor ?? 0) >= 0 ? 'in' : 'out',
    title: e.reason || e.kind || 'Операция',
    amount: Math.abs(e.amount_minor ?? 0) / 100,
    at: e.created_at || '',
  }))

  const methods = (partner?.withdrawal_methods ?? [])
    .filter((m) => m.enabled !== false)
    .sort((a, b) => (a.min_amount_minor ?? 0) - (b.min_amount_minor ?? 0))
    .map((m) => ({
      id: m.id || '',
      label: m.label || m.id || '',
      type: m.type || '',
      currency: m.debit_currency || 'RUB',
      scale: m.currency_scale ?? 2,
      minAmount: (m.min_amount_minor ?? 0) / 10 ** (m.currency_scale ?? 2),
      maxAmount: m.max_amount_minor ? m.max_amount_minor / 10 ** (m.currency_scale ?? 2) : null,
      fields: (m.fields ?? []).map((f) => ({
        id: f.id || '',
        label: f.label || f.id || '',
        required: f.required !== false,
        placeholder: f.placeholder || '',
      })),
      networks: (m.networks ?? []).map((n) => ({ id: n.id || '', label: n.label || n.id || '' })),
      helpText: m.help_text || '',
    }))

  // Баланс партнёрки - в валюте первого доступного метода вывода
  const partnerBalance =
    partner?.balances?.find((b) => b.currency === methods[0]?.currency) ?? partner?.balances?.[0]

  // Заявки на вывод - реальная история списаний партнёрского баланса
  for (const w of withdrawals?.withdrawals ?? []) {
    const scale = w.currency_scale ?? 2
    bonusHistory.push({
      id: `w-${w.withdrawal_id}`,
      kind: 'out',
      title: `${WITHDRAWAL_TITLES[w.status || ''] ?? 'Вывод'}${w.masked_requisites ? ` · ${w.masked_requisites}` : ''}`,
      amount: Math.abs(w.amount_minor ?? 0) / 10 ** scale,
      at: w.requested_at || '',
    })
  }
  bonusHistory.sort((a, b) => b.at.localeCompare(a.at))

  const earned =
    partnerBalance?.lifetime_earned_minor != null
      ? partnerBalance.lifetime_earned_minor / 10 ** (partnerBalance.currency_scale ?? 2)
      : bonusHistory.filter((b) => b.kind === 'in').reduce((s, b) => s + b.amount, 0)

  const withdrawMin = methods.reduce(
    (min, m) => (m.minAmount > 0 && m.minAmount < min ? m.minAmount : min),
    Number.POSITIVE_INFINITY,
  )

  // Реальные условия программы - из бэкенда:
  // - процент с оплат друзей = commission_bps партнёрского профиля (1500 = 15%)
  // - скидка другу = friend_discount_percent на первую покупку подписки
  const commissionBps = partner?.profile?.commission_bps
  const bonusDetails = (ref.bonus_details ?? [])
    .map((d) => ({
      title: d.title || '',
      inviterDays: Number(d.inviter_days ?? 0),
      friendDays: Number(d.friend_days ?? 0),
    }))
    .filter((d) => d.inviterDays > 0 || d.friendDays > 0)

  return {
    link: ref.bot_link || ref.webapp_link || '',
    percent: commissionBps != null ? commissionBps / 100 : null,
    friendWelcomeDays: Number(ref.welcome_bonus_days ?? 0),
    friendDiscountPercent: Number(ref.friend_discount_percent ?? 0),
    exchangeDayPrice:
      ref.exchange_day_price != null && ref.exchange_day_price > 0
        ? Number(ref.exchange_day_price)
        : null,
    bonusDetails,
    invited: ref.invited_count ?? 0,
    earned,
    bonusBalance: Number(me.balance?.amount ?? 0),
    bonusHistory,
    partner: {
      enabled: Boolean(partner?.program_enabled),
      withdrawalsEnabled: Boolean(partner?.withdrawals_enabled) && methods.length > 0,
      balanceAvailable: partnerBalance
        ? (partnerBalance.available_minor ?? 0) / 10 ** (partnerBalance.currency_scale ?? 2)
        : null,
      balanceCurrency: partnerBalance?.currency ?? 'RUB',
      methods,
    },
    rates: {
      withdrawMin: Number.isFinite(withdrawMin) ? withdrawMin : 500,
    },
  }
})
