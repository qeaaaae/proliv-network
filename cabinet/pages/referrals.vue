<script setup lang="ts">
import {
  CalendarPlus,
  ChevronRight,
  Coins,
  Gift,
  History,
  Link2,
  Percent,
  ShoppingCart,
  Users,
  Wallet,
} from '@lucide/vue'
import QRCode from 'qrcode'

const { push } = useToast()
const fmt = useFormat()

interface WithdrawMethod {
  id: string
  label: string
  type: string
  currency: string
  scale: number
  minAmount: number
  maxAmount: number | null
  fields: { id: string; label: string; required: boolean; placeholder: string }[]
  networks: { id: string; label: string }[]
  helpText: string
}

interface ReferralData {
  link: string
  percent: number | null
  friendWelcomeDays: number
  friendDiscountPercent: number
  exchangeDayPrice: number | null
  bonusDetails: { title: string; inviterDays: number; friendDays: number }[]
  invited: number
  earned: number
  bonusBalance: number
  bonusHistory: { id: string; kind: 'in' | 'out'; title: string; amount: number; at: string }[]
  partner: {
    enabled: boolean
    withdrawalsEnabled: boolean
    balanceAvailable: number | null
    balanceCurrency: string
    methods: WithdrawMethod[]
  }
  rates: { withdrawMin: number }
}

const maxBonusDays = (list: ReferralData['bonusDetails'], key: 'inviterDays' | 'friendDays') =>
  Math.max(0, ...(list ?? []).map((d) => d[key]))

const { data, status, refresh } = useFetch<ReferralData>('/api/referral', { lazy: true })

// Обмен бонусов на дни - слайдер от 1 до максимума по цене дня из бэкенда.
const maxExchangeDays = computed(() => {
  const price = data.value?.exchangeDayPrice
  if (!price || price <= 0) return 0
  return Math.floor((data.value?.bonusBalance ?? 0) / price)
})
const exchangeCost = computed(() => {
  const price = data.value?.exchangeDayPrice ?? 0
  return exchangeDays.value * price
})

const qrOpen = ref(false)
const qrSrc = ref('')
const historyOpen = ref(false)
const daysOpen = ref(false)
const withdrawOpen = ref(false)

const exchangeDays = ref(1)
const withdrawAmount = ref<number | null>(null)
const withdrawMethod = ref('')
const withdrawNetwork = ref('')
const withdrawRequisites = ref<Record<string, string>>({})
const busy = ref(false)

// «Оплатить бонусами» - галочка списания в чекауте; доступно при любом
// ненулевом балансе (бонусный счёт или партнёрский).
const payableBalance = computed(
  () => (data.value?.bonusBalance ?? 0) + (data.value?.partner?.balanceAvailable ?? 0),
)

const withdrawMethods = computed(() => data.value?.partner?.methods ?? [])
const currentWithdrawMethod = computed(
  () => withdrawMethods.value.find((m) => m.id === withdrawMethod.value) ?? withdrawMethods.value[0],
)

// Вывод идёт с партнёрского баланса, не с бонусного
const withdrawAvailable = computed(() => data.value?.partner?.balanceAvailable ?? null)
const withdrawInsufficient = computed(
  () =>
    withdrawAvailable.value !== null &&
    withdrawAvailable.value < (data.value?.rates.withdrawMin ?? 0),
)

// Что получает приглашённый друг - реальные условия из бэкенда:
// скидка на первую покупку и/или приветственные дни.
const friendBenefit = computed(() => {
  const d = data.value
  if (!d) return null
  if (d.friendDiscountPercent > 0) {
    return { value: `${d.friendDiscountPercent}%`, hint: 'скидка на первую покупку' }
  }
  if (d.friendWelcomeDays > 0) {
    return { value: `+${d.friendWelcomeDays} дн.`, hint: 'при регистрации' }
  }
  const days = maxBonusDays(d.bonusDetails ?? [], 'friendDays')
  return days > 0 ? { value: `до +${days} дн.`, hint: 'за покупку' } : null
})

const methodEls = ref<unknown[]>([])
const networkEls = ref<unknown[]>([])
const methodIndex = computed(() =>
  Math.max(
    0,
    withdrawMethods.value.findIndex((m) => m.id === currentWithdrawMethod.value?.id),
  ),
)
const networkIndex = computed(() =>
  Math.max(
    0,
    (currentWithdrawMethod.value?.networks ?? []).findIndex((n) => n.id === withdrawNetwork.value),
  ),
)
const { indicator: methodPill } = usePillIndicator(methodEls, methodIndex)
const { indicator: networkPill } = usePillIndicator(networkEls, networkIndex)

watch(withdrawOpen, (open) => {
  if (!open) return
  withdrawMethod.value = withdrawMethods.value[0]?.id ?? ''
  withdrawNetwork.value = withdrawMethods.value[0]?.networks?.[0]?.id ?? ''
  withdrawRequisites.value = {}
})
watch(currentWithdrawMethod, (m) => {
  withdrawNetwork.value = m?.networks?.[0]?.id ?? ''
  withdrawRequisites.value = {}
})
watch(daysOpen, (open) => {
  if (open) exchangeDays.value = Math.min(exchangeDays.value, Math.max(1, maxExchangeDays.value))
})

async function showQr() {
  if (!data.value) return
  qrSrc.value = await QRCode.toDataURL(data.value.link, {
    margin: 1,
    width: 200,
    color: { dark: '#000000', light: '#ffffff' },
  })
  qrOpen.value = true
}

async function bonus(action: string, amount: number | null, method?: string) {
  if (busy.value) return
  busy.value = true
  try {
    const body: Record<string, unknown> = { action, amount: amount ?? 0, method }
    if (action === 'days') body.days = amount ?? 0
    if (action === 'withdraw') {
      body.requisites = withdrawRequisites.value
      if (withdrawNetwork.value) body.network = withdrawNetwork.value
    }
    await $fetch('/api/bonus', { method: 'POST', body })
    await refresh()
    push('Готово')
    daysOpen.value = withdrawOpen.value = false
    exchangeDays.value = 1
    withdrawAmount.value = null
    withdrawRequisites.value = {}
  } catch (e) {
    push((e as { data?: { statusMessage?: string } }).data?.statusMessage ?? 'Ошибка', 'error')
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div>
    <div class="page-head">
      <div class="page-kicker">Бонусы</div>
      <h1>Реферальная система</h1>
    </div>

    <!-- Загрузка -->
    <section v-if="status === 'pending'" class="panel" aria-hidden="true">
      <div class="panel--pad stack">
        <div class="skel" style="height: 44px" />
        <div class="skel" style="height: 12px" />
        <div class="skel" style="height: 12px; width: 65%" />
        <div class="skel" style="height: 34px; width: 40%" />
        <div class="skel" style="height: 12px; width: 80%" />
      </div>
    </section>

    <div v-else class="grid-2">
      <!-- Ссылка и условия -->
      <section class="panel link-panel">
        <div class="panel__title">
          <Link2 :size="17" />
          Ваша ссылка
          <small>отправьте другу или покажите QR</small>
        </div>
        <div class="panel--pad">
          <CopyField v-if="data" :value="data.link" qr @qr="showQr" />
        </div>
        <div class="row-line">
          <span class="row-line__icon"><Percent :size="15" /></span>
          <span class="row-line__body">
            <span class="row-line__label">Вы получаете</span>
            <span class="row-line__hint">с каждой оплаты друга</span>
          </span>
          <span class="row-line__value accent">{{ data?.percent ?? '—' }}%</span>
        </div>
        <div v-if="data?.bonusDetails?.length" class="row-line">
          <span class="row-line__icon"><CalendarPlus :size="15" /></span>
          <span class="row-line__body">
            <span class="row-line__label">И бонусные дни</span>
            <span class="row-line__hint">за покупку периода другом</span>
          </span>
          <span class="row-line__value accent">
            до +{{ maxBonusDays(data.bonusDetails, 'inviterDays') }} дн.
          </span>
        </div>
        <div v-if="friendBenefit" class="row-line">
          <span class="row-line__icon"><Gift :size="15" /></span>
          <span class="row-line__body">
            <span class="row-line__label">Друг получает</span>
            <span class="row-line__hint">{{ friendBenefit.hint }}</span>
          </span>
          <span class="row-line__value accent">{{ friendBenefit.value }}</span>
        </div>
        <div class="row-line">
          <span class="row-line__icon"><Users :size="15" /></span>
          <span class="row-line__body">
            <span class="row-line__label">Друзей приглашено</span>
          </span>
          <span class="row-line__value numeric">{{ data?.invited ?? 0 }}</span>
        </div>
        <div class="row-line">
          <span class="row-line__icon"><Coins :size="15" /></span>
          <span class="row-line__body">
            <span class="row-line__label">Начислено за друзей</span>
          </span>
          <span class="row-line__value numeric">{{ fmt.rub(data?.earned ?? 0) }}</span>
        </div>
      </section>

      <!-- Бонусный счёт -->
      <section class="panel">
        <div class="panel__title">
          <Wallet :size="17" />
          Бонусный счёт
          <small>к выводу {{ fmt.rub(data?.partner?.balanceAvailable ?? 0) }}</small>
        </div>
        <div class="panel--pad" style="text-align: center">
          <div class="price-now numeric" style="font-size: 34px">
            {{ fmt.rub(data?.bonusBalance ?? 0) }}
          </div>
        </div>
        <button
          class="row-line row-line--clickable"
          style="width: 100%; text-align: left"
          :disabled="maxExchangeDays < 1"
          @click="daysOpen = true"
        >
          <span class="row-line__icon"><CalendarPlus :size="15" /></span>
          <span class="row-line__body">
            <span class="row-line__label">Обменять на дни</span>
            <span class="row-line__hint">
              {{
                data?.exchangeDayPrice
                  ? maxExchangeDays > 0
                    ? `1 день = ${fmt.rub(data.exchangeDayPrice)} · хватит на ${maxExchangeDays} дн.`
                    : `1 день = ${fmt.rub(data.exchangeDayPrice)} · не хватает бонусов`
                  : 'обмен временно недоступен'
              }}
            </span>
          </span>
          <ChevronRight :size="17" class="row-line__chev" />
        </button>
        <button
          class="row-line row-line--clickable"
          style="width: 100%; text-align: left"
          :disabled="payableBalance <= 0"
          @click="navigateTo('/purchases?balance=1')"
        >
          <span class="row-line__icon"><ShoppingCart :size="15" /></span>
          <span class="row-line__body">
            <span class="row-line__label">Оплатить бонусами</span>
            <span class="row-line__hint">
              {{ payableBalance > 0 ? 'спишется при покупке подписки' : 'сначала накопите бонусы' }}
            </span>
          </span>
          <ChevronRight :size="17" class="row-line__chev" />
        </button>
        <button
          class="row-line row-line--clickable"
          style="width: 100%; text-align: left"
          :disabled="!data?.partner?.withdrawalsEnabled || withdrawInsufficient"
          @click="withdrawOpen = true"
        >
          <span class="row-line__icon"><Wallet :size="15" /></span>
          <span class="row-line__body">
            <span class="row-line__label">Вывести</span>
            <span class="row-line__hint">
              {{
                !data?.partner?.withdrawalsEnabled
                  ? 'Вывод временно недоступен'
                  : withdrawInsufficient
                    ? `нужно минимум ${fmt.rub(data?.rates.withdrawMin ?? 0)}`
                    : `${data.partner.methods.map((m) => m.label).join(' или ') || 'На реквизиты'}, от ${fmt.rub(data?.rates.withdrawMin ?? 500)}`
              }}
            </span>
          </span>
          <ChevronRight :size="17" class="row-line__chev" />
        </button>
        <button class="row-line row-line--clickable" style="width: 100%; text-align: left" @click="historyOpen = true">
          <span class="row-line__icon"><History :size="15" /></span>
          <span class="row-line__body">
            <span class="row-line__label">История бонусов</span>
            <span class="row-line__hint">начисления, траты и выводы</span>
          </span>
          <ChevronRight :size="17" class="row-line__chev" />
        </button>
      </section>
    </div>

    <!-- QR ссылки -->
    <AppModal :open="qrOpen" title="QR реферальной ссылки" @close="qrOpen = false">
      <div class="qr-box"><img v-if="qrSrc" :src="qrSrc" alt="QR" /></div>
    </AppModal>

    <!-- Обмен бонусов на дни подписки -->
    <AppModal :open="daysOpen" title="Обменять бонусы на дни" @close="daysOpen = false">
      <div class="stack">
        <div class="exchange-days-out">
          <div class="price-now numeric">{{ exchangeDays }} дн.</div>
          <p class="muted" style="margin: 4px 0 0; font-size: 13px">
            спишется {{ fmt.rub(exchangeCost) }} · 1 день =
            {{ fmt.rub(data?.exchangeDayPrice ?? 0) }}
          </p>
        </div>
        <input
          v-model.number="exchangeDays"
          class="slider"
          type="range"
          min="1"
          :max="Math.max(1, maxExchangeDays)"
          step="1"
        />
        <div class="slider-marks muted">
          <span>1</span>
          <span>{{ maxExchangeDays }} дн.</span>
        </div>
        <button
          class="btn btn--primary btn--block"
          :disabled="busy || maxExchangeDays < 1 || exchangeDays < 1 || exchangeDays > maxExchangeDays"
          @click="bonus('days', exchangeDays)"
        >
          Обменять
        </button>
      </div>
    </AppModal>

    <!-- Вывод (партнёрский баланс) -->
    <AppModal :open="withdrawOpen" title="Вывод средств" @close="withdrawOpen = false">
      <div class="stack">
        <p v-if="withdrawAvailable !== null" class="muted" style="font-size: 13px; margin: 0">
          Доступно к выводу: {{ fmt.rub(withdrawAvailable) }} {{ data?.partner?.balanceCurrency }}
        </p>
        <div v-if="withdrawMethods.length" class="pills" :class="{ 'has-pill': methodPill.ready }">
          <div
            class="pills__indicator"
            :class="{ 'is-ready': methodPill.ready }"
            :style="{ transform: `translateX(${methodPill.x}px)`, width: `${methodPill.w}px` }"
            aria-hidden="true"
          />
          <button
            v-for="m in withdrawMethods"
            :key="m.id"
            ref="methodEls"
            class="pills__item"
            :class="{ 'is-active': currentWithdrawMethod?.id === m.id }"
            @click="withdrawMethod = m.id"
          >
            {{ m.label }}
          </button>
        </div>
        <p v-if="currentWithdrawMethod?.helpText" class="muted" style="font-size: 12px; margin: 0">
          {{ currentWithdrawMethod.helpText }}
        </p>
        <div class="field">
          <span>
            Сумма {{ currentWithdrawMethod ? `(${currentWithdrawMethod.currency}, от ${fmt.rub(currentWithdrawMethod.minAmount)})` : '' }}
          </span>
          <input
            v-model.number="withdrawAmount"
            class="input numeric"
            type="number"
            :min="currentWithdrawMethod?.minAmount ?? 0"
            :max="withdrawAvailable ?? undefined"
            :placeholder="String(currentWithdrawMethod?.minAmount ?? 500)"
          />
        </div>
        <div v-for="f in currentWithdrawMethod?.fields ?? []" :key="f.id" class="field">
          <span>{{ f.label || f.id }}<template v-if="f.required"> *</template></span>
          <input v-model="withdrawRequisites[f.id]" class="input" :placeholder="f.placeholder" />
        </div>
        <div v-if="(currentWithdrawMethod?.networks?.length ?? 0) > 0" class="field">
          <span>Сеть</span>
          <div class="pills" :class="{ 'has-pill': networkPill.ready }">
            <div
              class="pills__indicator"
              :class="{ 'is-ready': networkPill.ready }"
              :style="{ transform: `translateX(${networkPill.x}px)`, width: `${networkPill.w}px` }"
              aria-hidden="true"
            />
            <button
              v-for="n in currentWithdrawMethod?.networks ?? []"
              :key="n.id"
              ref="networkEls"
              class="pills__item"
              :class="{ 'is-active': withdrawNetwork === n.id }"
              @click="withdrawNetwork = n.id"
            >
              {{ n.label }}
            </button>
          </div>
        </div>
        <button
          class="btn btn--primary btn--block"
          :disabled="
            busy ||
            !withdrawAmount ||
            !currentWithdrawMethod ||
            withdrawAmount < (currentWithdrawMethod.minAmount ?? 0) ||
            (withdrawAvailable !== null && withdrawAmount > withdrawAvailable)
          "
          @click="bonus('withdraw', withdrawAmount, currentWithdrawMethod?.id)"
        >
          Оставить заявку
        </button>
      </div>
    </AppModal>

    <!-- История -->
    <AppModal :open="historyOpen" title="История бонусов" @close="historyOpen = false">
      <ul class="stack" style="gap: 10px">
        <li
          v-for="h in data?.bonusHistory"
          :key="h.id"
          style="display: flex; justify-content: space-between; gap: 10px; font-size: 13px"
        >
          <span>
            {{ h.title }}
            <span class="muted" style="display: block; font-size: 11px">{{ fmt.dateTime(h.at) }}</span>
          </span>
          <span class="numeric" :class="h.kind === 'in' ? 'accent' : 'muted'" style="font-weight: 600; white-space: nowrap">
            {{ h.kind === 'in' ? '+' : '−' }}{{ fmt.rub(h.amount) }}
          </span>
        </li>
        <li v-if="!data?.bonusHistory.length" class="muted" style="font-size: 13px">Пока пусто</li>
      </ul>
    </AppModal>
  </div>
</template>
