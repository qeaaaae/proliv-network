<script setup lang="ts">
// Карточка платежа: все поля PaymentDetailOut + ручные действия
// (POST /finalize и /reverse через emit 'action' - запрос делает страница).
import {
  formatGbAmount,
  isPaymentReasonValid,
  paymentDescription,
  paymentDiscount,
  paymentMoney,
  paymentProviderLabel,
  paymentPurchaseLabels,
  paymentStatusLabel,
  paymentStatusTone,
  paymentWarningLabel,
  reversalBlockLabel,
  saleModeLabel,
} from './types'
import type { AdminPaymentActionSubmit, AdminPaymentDetail } from './types'

const props = defineProps<{
  open: boolean
  payment: AdminPaymentDetail | null
  loading: boolean
  busy: boolean
  errorText: string
}>()
const emit = defineEmits<{ close: []; action: [payload: AdminPaymentActionSubmit] }>()

const { dateTime } = useFormat()

const actionMode = ref<'finalize' | 'reverse' | null>(null)
const reason = ref('')
const withoutReason = ref(false)
const confirmPromo = ref(false)
const confirmEndChange = ref(false)
const restorePromo = ref(true)
const refundBalance = ref(true)

// Сброс формы действия при смене платежа или после успешного действия
// (меняются status/fulfilled_at/reversed_at); при ошибке поля те же -> форма
// остаётся, можно поправить чекбоксы и повторить.
watch(
  () => [
    props.open,
    props.payment?.payment_id,
    props.payment?.status,
    props.payment?.fulfilled_at,
    props.payment?.reversed_at,
  ],
  () => resetAction(),
)

function resetAction() {
  actionMode.value = null
  reason.value = ''
  withoutReason.value = false
  confirmPromo.value = false
  confirmEndChange.value = false
  restorePromo.value = true
  refundBalance.value = true
}

function startAction(mode: 'finalize' | 'reverse') {
  resetAction()
  actionMode.value = mode
}

const isGift = computed(() => (props.payment?.sale_mode || '').split('|').includes('gift'))

const purchases = computed(() =>
  props.payment ? paymentPurchaseLabels(props.payment) : [],
)

const showActions = computed(() => {
  const p = props.payment
  if (!p || props.loading) return false
  return Boolean(
    actionMode.value ||
      p.can_manual_finalize ||
      p.can_reverse ||
      p.status === 'succeeded' ||
      p.manual_finalize_warnings?.includes('entitlement_context_conflict'),
  )
})

const submitDisabled = computed(() => {
  if (props.busy || !actionMode.value) return true
  if (!isPaymentReasonValid(reason.value, actionMode.value === 'reverse' && withoutReason.value)) {
    return true
  }
  if (actionMode.value === 'finalize') {
    if (props.payment?.manual_finalize_requires_promo_confirmation && !confirmPromo.value) {
      return true
    }
    if (
      props.payment?.manual_finalize_requires_context_confirmation &&
      !confirmEndChange.value
    ) {
      return true
    }
  }
  return false
})

function submit() {
  if (!actionMode.value || submitDisabled.value) return
  emit('action', {
    mode: actionMode.value,
    reason: reason.value.trim(),
    confirmPromoConflict: confirmPromo.value,
    confirmSubscriptionEndChange: confirmEndChange.value,
    restorePromoUsage: restorePromo.value,
    refundToBalance: refundBalance.value,
    withoutReason: withoutReason.value,
  })
}

function v(x: unknown): string {
  return x === null || x === undefined || x === '' ? '—' : String(x)
}

function dt(x: string | null | undefined): string {
  return x ? dateTime(x) : '—'
}

function fulfillmentLabel(source: string | null | undefined): string {
  if (source === 'admin') return 'Администратор'
  if (source) return 'Платёжный провайдер'
  return '—'
}

function durationText(p: AdminPaymentDetail): string {
  if (p.subscription_duration_days) return `${p.subscription_duration_days} дн.`
  return p.subscription_duration_months ? `${p.subscription_duration_months} мес.` : ''
}

function trafficText(p: AdminPaymentDetail): string {
  const parts: string[] = []
  if (p.traffic_regular_gb !== null && p.traffic_regular_gb !== undefined) {
    parts.push(`Основной: ${formatGbAmount(p.traffic_regular_gb)} ГБ`)
  }
  if (p.traffic_premium_gb !== null && p.traffic_premium_gb !== undefined) {
    parts.push(`Премиум: ${formatGbAmount(p.traffic_premium_gb)} ГБ`)
  }
  return parts.join(' · ')
}
</script>

<template>
  <AdminModal
    :open="open"
    :title="payment ? `Платёж #${payment.payment_id}` : 'Платёж'"
    @close="emit('close')"
  >
    <div v-if="payment" class="detail">
      <div class="sum">
        <strong class="sum-amount">{{ paymentMoney(payment.amount, payment.currency) }}</strong>
        <div class="badges">
          <AdminBadge :tone="paymentStatusTone(payment.status)">
            {{ paymentStatusLabel(payment.status) }}
          </AdminBadge>
          <AdminBadge v-if="payment.provider" tone="muted">
            {{ paymentProviderLabel(payment.provider) }}
          </AdminBadge>
          <AdminBadge v-if="payment.fulfillment_source === 'admin'" tone="warning">
            Проведён вручную
          </AdminBadge>
        </div>
        <small class="admin-note">{{ paymentDescription(payment) }}</small>
      </div>

      <section class="sec">
        <h3>Пользователь</h3>
        <dl class="meta">
          <div><dt>Имя</dt><dd>{{ v(payment.user_label) }}</dd></div>
          <div><dt>Minishop ID</dt><dd class="mono">{{ v(payment.user_minishop_id) }}</dd></div>
          <div><dt>User ID</dt><dd class="mono">{{ payment.user_id }}</dd></div>
          <div><dt>Telegram ID</dt><dd class="mono">{{ v(payment.telegram_id) }}</dd></div>
        </dl>
      </section>

      <section class="sec">
        <h3>Платёж</h3>
        <dl class="meta">
          <div><dt>Сумма</dt><dd>{{ paymentMoney(payment.amount, payment.currency) }}</dd></div>
          <div><dt>Статус</dt><dd>{{ paymentStatusLabel(payment.status) }}</dd></div>
          <div><dt>Создан</dt><dd>{{ dt(payment.created_at) }}</dd></div>
          <div><dt>Обновлён</dt><dd>{{ dt(payment.updated_at) }}</dd></div>
          <div><dt>Проведён кем</dt><dd>{{ fulfillmentLabel(payment.fulfillment_source) }}</dd></div>
          <div><dt>Проведён</dt><dd>{{ dt(payment.fulfilled_at) }}</dd></div>
          <div v-if="payment.fulfilled_by_admin_id">
            <dt>ID администратора проведения</dt>
            <dd class="mono">{{ payment.fulfilled_by_admin_id }}</dd>
          </div>
          <div v-if="payment.fulfillment_note">
            <dt>Причина проведения</dt>
            <dd>{{ payment.fulfillment_note }}</dd>
          </div>
          <div v-if="payment.reversed_at">
            <dt>Отменён</dt>
            <dd>{{ dt(payment.reversed_at) }}</dd>
          </div>
          <div v-if="payment.reversed_by_admin_id">
            <dt>ID администратора отмены</dt>
            <dd class="mono">{{ payment.reversed_by_admin_id }}</dd>
          </div>
          <div v-if="payment.reversal_note">
            <dt>Причина отмены</dt>
            <dd>{{ payment.reversal_note }}</dd>
          </div>
          <div><dt>Описание</dt><dd>{{ paymentDescription(payment) }}</dd></div>
        </dl>
      </section>

      <section class="sec">
        <h3>Провайдер</h3>
        <dl class="meta">
          <div><dt>Провайдер</dt><dd>{{ paymentProviderLabel(payment.provider) }}</dd></div>
          <div><dt>ID у провайдера</dt><dd class="mono">{{ v(payment.provider_payment_id) }}</dd></div>
          <div v-if="payment.provider_payment_url">
            <dt>Ссылка на оплату</dt>
            <dd>
              <a
                class="link"
                :href="payment.provider_payment_url"
                target="_blank"
                rel="noopener noreferrer"
                >Открыть</a
              >
            </dd>
          </div>
          <div v-if="payment.yookassa_payment_id">
            <dt>YooKassa ID</dt>
            <dd class="mono">{{ payment.yookassa_payment_id }}</dd>
          </div>
          <div>
            <dt>Ключ идемпотентности</dt>
            <dd class="mono">{{ v(payment.idempotence_key) }}</dd>
          </div>
        </dl>
      </section>

      <section class="sec">
        <h3>Состав покупки</h3>
        <div v-if="purchases.length" class="chips">
          <AdminBadge v-for="(c, i) in purchases" :key="i" tone="muted">{{ c }}</AdminBadge>
        </div>
        <dl class="meta">
          <div><dt>Тип продажи</dt><dd>{{ saleModeLabel(payment.sale_mode) }}</dd></div>
          <div v-if="payment.tariff_key">
            <dt>Тариф</dt>
            <dd class="mono">{{ payment.tariff_key }}</dd>
          </div>
          <div v-if="durationText(payment)">
            <dt>Период</dt>
            <dd>{{ durationText(payment) }}</dd>
          </div>
          <div v-if="trafficText(payment)">
            <dt>Трафик</dt>
            <dd>{{ trafficText(payment) }}</dd>
          </div>
          <div><dt>Скидка</dt><dd>{{ paymentDiscount(payment) }}</dd></div>
          <div v-if="payment.promo_code">
            <dt>Промокод</dt>
            <dd class="mono">{{ payment.promo_code }}</dd>
          </div>
          <div v-if="payment.checkout_base_amount !== null && payment.checkout_base_amount !== undefined">
            <dt>Сумма до скидки</dt>
            <dd>{{ paymentMoney(payment.checkout_base_amount, payment.currency) }}</dd>
          </div>
        </dl>
      </section>

      <section v-if="showActions" class="sec">
        <h3>Ручные действия</h3>
        <template v-if="!actionMode">
          <div class="admin-row">
            <button
              v-if="payment.can_manual_finalize"
              type="button"
              class="admin-btn"
              :disabled="busy"
              @click="startAction('finalize')"
            >
              Провести платёж
            </button>
            <button
              v-if="payment.can_reverse"
              type="button"
              class="admin-btn danger"
              :disabled="busy"
              @click="startAction('reverse')"
            >
              Отменить платёж
            </button>
          </div>
          <p
            v-if="payment.manual_finalize_warnings?.includes('entitlement_context_conflict')"
            class="admin-note"
          >
            {{ paymentWarningLabel('entitlement_context_conflict') }}
          </p>
          <p v-else-if="payment.status === 'succeeded' && !payment.can_reverse" class="admin-note">
            {{ reversalBlockLabel(payment.reversal_block_reason) }}
          </p>
        </template>

        <div v-else class="confirm">
          <p class="confirm-text">
            {{
              actionMode === 'finalize'
                ? 'Начислить пользователю все зафиксированные в платеже покупки?'
                : 'Откатить только эффекты, зафиксированные для этого платежа?'
            }}
          </p>

          <ul
            v-if="actionMode === 'finalize' && payment.manual_finalize_warnings?.length"
            class="warn-list"
          >
            <li v-for="w in payment.manual_finalize_warnings" :key="w">
              {{ paymentWarningLabel(w) }}
            </li>
          </ul>

          <label
            v-if="actionMode === 'finalize' && payment.manual_finalize_requires_promo_confirmation"
            class="admin-check"
          >
            <input v-model="confirmPromo" type="checkbox" :disabled="busy" />
            <span>Применить сохранённые условия промокода и записать дополнительное использование</span>
          </label>

          <label
            v-if="actionMode === 'finalize' && payment.manual_finalize_requires_context_confirmation"
            class="admin-check"
          >
            <input v-model="confirmEndChange" type="checkbox" :disabled="busy" />
            <span>История проверена: эта покупка ещё не начислена. Применить её к текущей подписке.</span>
          </label>

          <label v-if="actionMode === 'reverse' && payment.promo_code_id" class="admin-check">
            <input v-model="restorePromo" type="checkbox" :disabled="busy" />
            <span>Вернуть это использование промокоду</span>
          </label>

          <template v-if="actionMode === 'reverse' && isGift">
            <label class="admin-check">
              <input v-model="refundBalance" type="checkbox" :disabled="busy" />
              <span>Вернуть полную оплаченную сумму подарка на баланс покупателя</span>
            </label>
            <p v-if="refundBalance && !payment.balance_enabled" class="admin-note">
              Баланс выключен. Средства останутся на балансе покупателя и станут доступны после его
              включения.
            </p>
          </template>

          <label class="reason-field">
            <span>Причина</span>
            <textarea
              v-model="reason"
              rows="3"
              maxlength="500"
              :disabled="busy"
              placeholder="Укажите, почему требуется ручное действие"
            />
          </label>

          <label v-if="actionMode === 'reverse'" class="admin-check">
            <input v-model="withoutReason" type="checkbox" :disabled="busy" />
            <span>Без причины</span>
          </label>

          <div class="admin-row end">
            <button type="button" class="admin-btn ghost" :disabled="busy" @click="resetAction">
              Назад
            </button>
            <button
              type="button"
              class="admin-btn"
              :class="{ danger: actionMode === 'reverse' }"
              :disabled="submitDisabled"
              @click="submit"
            >
              {{ busy ? 'Выполнение...' : 'Подтвердить' }}
            </button>
          </div>
        </div>
      </section>

      <p v-if="loading" class="admin-note">Обновление данных...</p>
      <p v-if="errorText" class="admin-note admin-error">{{ errorText }}</p>
    </div>

    <p v-else-if="loading" class="admin-note">Загрузка...</p>
    <p v-else-if="errorText" class="admin-note admin-error">{{ errorText }}</p>
    <p v-else class="admin-note">Нет данных платежа</p>

    <template #footer>
      <button type="button" class="admin-btn ghost" @click="emit('close')">Закрыть</button>
    </template>
  </AdminModal>
</template>

<style scoped>
.detail {
  display: grid;
  gap: 14px;
}
.sum {
  display: grid;
  gap: 6px;
}
.sum-amount {
  font-size: 22px;
}
.badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.sec {
  display: grid;
  gap: 8px;
}
.sec > h3 {
  margin: 0;
  font-size: 13px;
  color: var(--adm-muted, #8b95a8);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.meta {
  display: grid;
  gap: 6px;
  margin: 0;
}
.meta > div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}
.meta dt {
  color: var(--adm-muted, #8b95a8);
  flex-shrink: 0;
}
.meta dd {
  margin: 0;
  text-align: right;
  min-width: 0;
  overflow-wrap: anywhere;
}
.mono {
  font-family: ui-monospace, monospace;
  font-size: 12px;
}
.link {
  color: var(--adm-accent, #3b82f6);
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.confirm {
  display: grid;
  gap: 12px;
}
.confirm-text {
  margin: 0;
}
.warn-list {
  display: grid;
  gap: 6px;
  margin: 0;
  padding: 10px 12px 10px 28px;
  border-radius: 10px;
  border: 1px solid rgba(251, 191, 36, 0.45);
  background: rgba(251, 191, 36, 0.1);
  font-size: 13px;
}
.reason-field {
  display: grid;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
}
.reason-field textarea {
  width: 100%;
  resize: vertical;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--adm-border, #232c3d);
  background: var(--adm-bg, #0b0f17);
  color: inherit;
  font: inherit;
  font-size: 14px;
}
.end {
  justify-content: flex-end;
}
</style>
