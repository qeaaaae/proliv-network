// Типы контрактов minishop admin API для раздела "Платежи" + хелперы отображения.
// Источники: shop/backend/bot/app/web/admin_api_impl/payment_schemas.py
// (PaymentOut, PaymentDetailOut), schemas.py (AdminPaymentsListOut),
// AdminPaymentFinalizeBody/AdminPaymentReverseBody.

export interface AdminPaymentPurchase {
  kind: string
  amount: number
  unit: string
  scope: string | null
  mode: string
}

export interface AdminPayment {
  payment_id: number
  user_id: number
  user_minishop_id: string | null
  user_label: string
  telegram_id: number | null
  traffic_regular_gb: number | null
  traffic_premium_gb: number | null
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
  period_semantics: string | null
  sale_mode: string | null
  tariff_key: string | null
  purchased_gb: number | string | null
  purchased_hwid_devices: number | null
  purchases: AdminPaymentPurchase[]
  promo_code_id: number | null
  promo_discount_percent: number | null
  checkout_discount_amount: number | null
  fulfillment_source: string | null
  created_at: string | null
}

export interface AdminPaymentDetail extends AdminPayment {
  balance_enabled: boolean
  yookassa_payment_id: string | null
  idempotence_key: string | null
  promo_code: string | null
  checkout_base_amount: number | null
  fulfilled_at: string | null
  fulfilled_by_admin_id: number | null
  fulfillment_note: string | null
  promo_conflict_override: boolean
  reversed_at: string | null
  reversed_by_admin_id: number | null
  reversal_note: string | null
  promo_usage_restored: boolean
  can_manual_finalize: boolean
  manual_finalize_requires_promo_confirmation: boolean
  manual_finalize_requires_context_confirmation: boolean
  manual_finalize_warnings: string[]
  can_reverse: boolean
  reversal_block_reason: string | null
  updated_at: string | null
}

export interface AdminPaymentsListResponse {
  payments: AdminPayment[]
  page: number
  page_size: number
  total: number
}

// Данные формы ручного действия из DetailModal -> страница мапит их на
// AdminPaymentFinalizeBody / AdminPaymentReverseBody.
export interface AdminPaymentActionSubmit {
  mode: 'finalize' | 'reverse'
  reason: string
  confirmPromoConflict: boolean
  confirmSubscriptionEndChange: boolean
  restorePromoUsage: boolean
  refundToBalance: boolean
  withoutReason: boolean
}

export type AdminPaymentBadgeTone = 'default' | 'success' | 'warning' | 'danger' | 'muted'

// Статусы Payment.status в БД: succeeded, succeeded_pending_finalization,
// succeeded_pending_review, pending_<provider>, refunded, failed*, canceled,
// creation_unknown/failed_creation (см. db/dal/payment_dal.py и провайдеры).
export function paymentStatusTone(status: string | null | undefined): AdminPaymentBadgeTone {
  const s = (status || '').trim().toLowerCase()
  if (s === 'succeeded' || s === 'completed') return 'success'
  if (
    s === 'failed' ||
    s.startsWith('failed_') ||
    s === 'canceled' ||
    s === 'cancelled' ||
    s === 'creation_unknown' ||
    s === 'refunded'
  ) {
    return 'danger'
  }
  if (!s) return 'muted'
  // pending_*, succeeded_pending_*, processing, review и прочие незавершённые
  return 'warning'
}

export function paymentStatusLabel(status: string | null | undefined): string {
  const s = (status || '').trim().toLowerCase()
  if (!s) return '—'
  if (s === 'succeeded' || s === 'completed') return 'Оплачен'
  if (s === 'succeeded_pending_finalization') return 'Оплачен · применяем покупку'
  if (s === 'succeeded_pending_review') return 'Оплачен · нужна проверка'
  if (s === 'refunded') return 'Возвращён'
  if (s === 'canceled' || s === 'cancelled') return 'Отменён'
  if (s === 'creation_unknown' || s === 'failed_creation') return 'Ошибка создания'
  if (s === 'failed' || s.startsWith('failed_')) return 'Ошибка'
  if (s.startsWith('pending')) return 'Ожидает оплаты'
  return status || '—'
}

export function paymentMoney(
  amount: number | string | null | undefined,
  currency?: string | null,
): string {
  const sym = currency === 'RUB' ? '₽' : currency || ''
  const num = Number(amount || 0)
  const formatted = new Intl.NumberFormat('ru-RU', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num)
  return `${formatted} ${sym}`.trim()
}

export function paymentProviderLabel(provider: string | null | undefined): string {
  const raw = (provider || '').trim()
  if (raw === 'admin_gift') return 'От администратора'
  if (raw === 'promo') return 'Промокод'
  if (raw === 'partner_balance' || raw === 'balance') return 'Баланс'
  return raw || '—'
}

export function formatGbAmount(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') return ''
  const n = Number(value)
  if (Number.isNaN(n)) return ''
  if (Math.abs(n - Math.round(n)) < 1e-9) return String(Math.round(n))
  return String(Math.round(n * 100) / 100)
}

type PaymentDescriptionRow = Pick<
  AdminPayment,
  'sale_mode' | 'description' | 'traffic_regular_gb' | 'traffic_premium_gb'
>

export function paymentDescription(p: PaymentDescriptionRow): string {
  if (p.sale_mode === 'balance_topup') return 'Пополнение баланса'
  const regularGb = p.traffic_regular_gb
  const premiumGb = p.traffic_premium_gb
  if (regularGb !== null && regularGb !== undefined && premiumGb === null) {
    return `Пакет трафика ${formatGbAmount(regularGb)} ГБ (обычный)`
  }
  if (premiumGb !== null && premiumGb !== undefined && regularGb === null) {
    return `Пакет трафика ${formatGbAmount(premiumGb)} ГБ (премиум)`
  }
  const raw = (p.description || '').trim()
  return raw || '—'
}

type PaymentDiscountRow = Pick<
  AdminPayment,
  'checkout_discount_amount' | 'promo_discount_percent' | 'currency'
>

export function paymentDiscount(p: PaymentDiscountRow): string {
  const amount = Number(p.checkout_discount_amount || 0)
  const percent = Number(p.promo_discount_percent || 0)
  const pct = percent > 0 ? `${Math.round(percent * 100) / 100}%` : ''
  if (amount > 0) {
    const amountLabel = `−${paymentMoney(amount, p.currency)}`
    return pct ? `${amountLabel} (${pct})` : amountLabel
  }
  return pct ? `−${pct}` : '—'
}

type PaymentPurchasesRow = Pick<
  AdminPayment,
  'purchases' | 'traffic_regular_gb' | 'traffic_premium_gb' | 'purchased_hwid_devices'
>

// Подписи позиций покупки - аналог paymentPurchaseDisplay в shop frontend.
export function paymentPurchaseLabels(p: PaymentPurchasesRow): string[] {
  const source: AdminPaymentPurchase[] = p.purchases?.length
    ? p.purchases
    : [
        ...(p.traffic_regular_gb !== null && p.traffic_regular_gb !== undefined
          ? [{ kind: 'traffic', amount: Number(p.traffic_regular_gb), unit: 'gb', scope: 'regular', mode: 'topup' }]
          : []),
        ...(p.traffic_premium_gb !== null && p.traffic_premium_gb !== undefined
          ? [{ kind: 'traffic', amount: Number(p.traffic_premium_gb), unit: 'gb', scope: 'premium', mode: 'topup' }]
          : []),
        ...(p.purchased_hwid_devices && Number(p.purchased_hwid_devices) > 0
          ? [{ kind: 'hwid_devices', amount: Number(p.purchased_hwid_devices), unit: 'device', scope: null, mode: 'topup' }]
          : []),
      ]
  return source.flatMap((purchase) => {
    const amount = formatGbAmount(purchase.amount)
    if (!amount) return []
    const kind = (purchase.kind || '').toLowerCase()
    const scope = (purchase.scope || '').toLowerCase()
    const mode = (purchase.mode || 'topup').toLowerCase()
    if (kind === 'traffic' && mode === 'limit' && scope === 'premium') {
      return [`Премиум-лимит · ${amount} ГБ`]
    }
    if (kind === 'traffic' && mode === 'limit') return [`Лимит трафика · ${amount} ГБ`]
    if (kind === 'traffic' && scope === 'premium') return [`Премиум · +${amount} ГБ`]
    if (kind === 'traffic') return [`Трафик · +${amount} ГБ`]
    if (kind === 'hwid_devices') return [`Устройства · +${amount}`]
    const unit = (purchase.unit || '').trim()
    return [`${kind || 'Прочее'} · ${amount}${unit ? ` ${unit}` : ''}`]
  })
}

const SALE_MODE_LABELS: Record<string, string> = {
  subscription: 'Подписка',
  traffic: 'Пакет трафика',
  traffic_package: 'Пакет трафика',
  topup: 'Докупка трафика',
  premium_topup: 'Премиум-трафик',
  hwid_devices: 'Устройства (HWID)',
  balance_topup: 'Пополнение баланса',
  gift: 'Подарок',
  extension: 'Продление',
}

export function saleModeLabel(saleMode: string | null | undefined): string {
  const raw = (saleMode || '').trim()
  if (!raw) return '—'
  const base = (raw.split('@', 1)[0] || '').split('|', 1)[0]?.toLowerCase() || ''
  return SALE_MODE_LABELS[base] || raw
}

// Коды manual_finalize_warnings -> текст (см. payment_fulfillment.payment_action_state).
export function paymentWarningLabel(code: string): string {
  switch (code) {
    case 'active_subscription_end_changed':
      return 'Дата окончания подписки изменилась. Перед начислением сохранённой покупки проверьте историю платежа и подписки.'
    case 'entitlement_context_conflict':
      return 'Подписка или тариф больше не соответствуют покупке. Сверьте платёж перед начислением.'
    case 'promo_used_by_another_payment':
      return 'Промокод уже использован в другом платеже.'
    case 'provider_payment_id_missing':
      return 'Нет ID платежа у провайдера - проверьте списание вручную.'
    case 'provider_status_not_failed':
      return 'Текущий статус провайдера не является окончательной ошибкой.'
    case 'purchase_context_missing':
      return 'В платеже не хватает неизменяемых данных о покупке.'
    default:
      return code
  }
}

// Коды reversal_block_reason -> текст.
export function reversalBlockLabel(code: string | null | undefined): string {
  switch (code) {
    case 'fulfillment_snapshot_missing':
      return 'Для этого платежа нет снимков состояния, поэтому безопасный откат недоступен.'
    case 'payment_already_reversed':
      return 'Платёж уже отменён.'
    case 'gift_already_claimed':
      return 'Подарок уже активирован получателем - откат недоступен.'
    case 'extension_refund_required':
      return 'Продление отменяется через возврат заказа у провайдера.'
    case 'payment_not_succeeded':
    default:
      return 'Можно отменить только успешно проведённый платёж.'
  }
}

// Коды ошибок { ok:false, error } из payments routes -> текст для админа.
export function paymentErrorText(code: string | null | undefined): string {
  switch (code) {
    case 'not_found':
    case 'invalid_payment':
      return 'Платёж не найден.'
    case 'payment_fulfillment_unavailable':
      return 'Сервисы проведения платежа недоступны.'
    case 'payment_entitlement_context_changed':
      return 'Сохранённая покупка конфликтует с текущей подпиской или тарифом - проведение заблокировано.'
    case 'payment_manual_finalize_unavailable':
      return 'Этот платёж нельзя провести вручную.'
    case 'payment_subscription_end_confirmation_required':
      return 'Срок подписки изменился - отметьте подтверждение и повторите.'
    case 'promo_conflict_confirmation_required':
      return 'Промокод уже использован другим платежом - отметьте переопределение и повторите.'
    case 'payment_manual_finalize_failed':
      return 'Не удалось провести платёж.'
    case 'invalid_payment_reverse_reason':
      return 'Укажите причину отмены (минимум 3 символа) или отметьте "Без причины".'
    case 'invalid_payload':
      return 'Некорректные данные запроса - проверьте поля формы.'
    case 'payment_not_succeeded':
      return 'Можно отменить только успешно проведённый платёж.'
    case 'payment_already_reversed':
      return 'Платёж уже отменён.'
    case 'payment_reversal_conflict':
      return 'Эффекты платежа были изменены позже - безопасная отмена невозможна.'
    case 'payment_reversal_panel_failed':
      return 'Не удалось синхронизировать отменённые начисления с панелью.'
    case 'fulfillment_snapshot_missing':
    case 'fulfillment_snapshot_invalid':
      return 'Нет корректных снимков состояния - безопасный откат недоступен.'
    case 'balance_topup_credit_missing':
      return 'Не найдена запись начисления на баланс для отката.'
    case 'gift_already_claimed':
      return 'Подарок уже активирован получателем - откат недоступен.'
    case 'extension_refund_required':
      return 'Продление отменяется через возврат заказа у провайдера.'
    case 'payment_reverse_unavailable':
      return 'Этот платёж нельзя отменить.'
    default:
      return `Ошибка: ${code || 'request_failed'}`
  }
}

export function isPaymentReasonValid(reason: string, withoutReason = false): boolean {
  return withoutReason || reason.trim().length >= 3
}
