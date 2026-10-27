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
  percent: number
  friendDiscount: number
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
  rates: { dayPrice: number; maxPayShare: number; withdrawMin: number }
}

const { data, refresh } = await useFetch<ReferralData>('/api/referral')
// Периоды подписки - для честной оценки обмена бонусов (покупка плана с баланса)
const { data: tariffs } = await useFetch<{
  periods: { id: string; days: number; label: string; price: number }[]
}>('/api/tariffs')

// Обмен идёт покупкой периода: бэкенд берёт самый длинный план, который
// покрывает сумма - показываем его заранее.
const coveredPeriod = computed(() => {
  const amount = daysAmount.value ?? 0
  if (!amount) return null
  const affordable = (tariffs.value?.periods ?? [])
    .filter((p) => p.price > 0 && p.price <= amount)
    .sort((a, b) => b.days - a.days)
  return affordable[0] ?? null
})
const minPeriodPrice = computed(() =>
  Math.min(...(tariffs.value?.periods ?? []).filter((p) => p.price > 0).map((p) => p.price)),
)

const qrOpen = ref(false)
const qrSrc = ref('')
const historyOpen = ref(false)
const daysOpen = ref(false)
const withdrawOpen = ref(false)
const payOpen = ref(false)

const daysAmount = ref<number | null>(null)
const withdrawAmount = ref<number | null>(null)
const withdrawMethod = ref('')
const withdrawNetwork = ref('')
const withdrawRequisites = ref<Record<string, string>>({})
const payAmount = ref<number | null>(null)
const busy = ref(false)

const withdrawMethods = computed(() => data.value?.partner?.methods ?? [])
const currentWithdrawMethod = computed(
  () => withdrawMethods.value.find((m) => m.id === withdrawMethod.value) ?? withdrawMethods.value[0],
)

// Вывод идёт с партнёрского баланса, не с бонусного
const withdrawAvailable = computed(() => data.value?.partner?.balanceAvailable ?? null)

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
    if (action === 'withdraw') {
      body.requisites = withdrawRequisites.value
      if (withdrawNetwork.value) body.network = withdrawNetwork.value
    }
    await $fetch('/api/bonus', { method: 'POST', body })
    await refresh()
    push('Готово')
    daysOpen.value = withdrawOpen.value = payOpen.value = false
    daysAmount.value = withdrawAmount.value = payAmount.value = null
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

    <div class="grid-2">
      <!-- Ссылка и условия -->
      <section class="panel">
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
          <span class="row-line__value accent">{{ data?.percent }}%</span>
        </div>
        <div class="row-line">
          <span class="row-line__icon"><Gift :size="15" /></span>
          <span class="row-line__body">
            <span class="row-line__label">Друг получает</span>
            <span class="row-line__hint">скидка на первую покупку</span>
          </span>
          <span class="row-line__value accent">{{ data?.friendDiscount }}%</span>
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
          <small>можно вывести {{ fmt.rub(data?.bonusBalance ?? 0) }}</small>
        </div>
        <div class="panel--pad" style="text-align: center">
          <div class="price-now numeric" style="font-size: 34px">
            {{ fmt.rub(data?.bonusBalance ?? 0) }}
          </div>
        </div>
        <button class="row-line row-line--clickable" style="width: 100%; text-align: left" @click="daysOpen = true">
          <span class="row-line__icon"><CalendarPlus :size="15" /></span>
          <span class="row-line__body">
            <span class="row-line__label">Обменять на подписку</span>
            <span class="row-line__hint">оплатить период с баланса бонусов</span>
          </span>
          <ChevronRight :size="17" class="row-line__chev" />
        </button>
        <button class="row-line row-line--clickable" style="width: 100%; text-align: left" @click="payOpen = true">
          <span class="row-line__icon"><ShoppingCart :size="15" /></span>
          <span class="row-line__body">
            <span class="row-line__label">Оплатить бонусами</span>
            <span class="row-line__hint">до {{ data?.rates.maxPayShare }}% стоимости покупки</span>
          </span>
          <ChevronRight :size="17" class="row-line__chev" />
        </button>
        <button
          class="row-line row-line--clickable"
          style="width: 100%; text-align: left"
          :disabled="!data?.partner?.withdrawalsEnabled"
          @click="withdrawOpen = true"
        >
          <span class="row-line__icon"><Wallet :size="15" /></span>
          <span class="row-line__body">
            <span class="row-line__label">Вывести</span>
            <span class="row-line__hint">
              {{
                data?.partner?.withdrawalsEnabled
                  ? `${data.partner.methods.map((m) => m.label).join(' или ') || 'На реквизиты'}, от ${fmt.rub(data?.rates.withdrawMin ?? 500)}`
                  : 'Вывод временно недоступен'
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

    <!-- Обмен на период подписки (оплата плана с внутреннего баланса) -->
    <AppModal :open="daysOpen" title="Обменять бонусы на подписку" @close="daysOpen = false">
      <div class="stack">
        <div class="field">
          <span>Сумма бонусов</span>
          <input v-model.number="daysAmount" class="input numeric" type="number" min="1" :max="data?.bonusBalance" placeholder="250" />
        </div>
        <p v-if="daysAmount && coveredPeriod" class="muted" style="font-size: 13px">
          Хватит на период «{{ coveredPeriod.label }}» - {{ fmt.rub(coveredPeriod.price) }}
        </p>
        <p v-else-if="daysAmount && Number.isFinite(minPeriodPrice)" class="muted" style="font-size: 13px">
          Минимальный период стоит {{ fmt.rub(minPeriodPrice) }}
        </p>
        <button class="btn btn--primary btn--block" :disabled="busy || !daysAmount" @click="bonus('days', daysAmount)">
          Обменять
        </button>
      </div>
    </AppModal>

    <!-- Оплата бонусами -->
    <AppModal :open="payOpen" title="Оплатить бонусами" @close="payOpen = false">
      <div class="stack">
        <div class="field">
          <span>Сколько бонусов списать</span>
          <input v-model.number="payAmount" class="input numeric" type="number" min="1" :max="data?.bonusBalance" placeholder="100" />
        </div>
        <button class="btn btn--primary btn--block" :disabled="busy || !payAmount" @click="bonus('pay', payAmount)">
          Списать
        </button>
      </div>
    </AppModal>

    <!-- Вывод (партнёрский баланс) -->
    <AppModal :open="withdrawOpen" title="Вывод средств" @close="withdrawOpen = false">
      <div class="stack">
        <p v-if="withdrawAvailable !== null" class="muted" style="font-size: 13px; margin: 0">
          Доступно к выводу: {{ fmt.rub(withdrawAvailable) }} {{ data?.partner?.balanceCurrency }}
        </p>
        <div v-if="withdrawMethods.length > 1" class="pills">
          <button
            v-for="m in withdrawMethods"
            :key="m.id"
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
          <div class="pills">
            <button
              v-for="n in currentWithdrawMethod?.networks ?? []"
              :key="n.id"
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
          :disabled="busy || !withdrawAmount || !currentWithdrawMethod"
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
