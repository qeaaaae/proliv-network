<script setup lang="ts">
import { CheckCircle2, Gift, LoaderCircle, XCircle } from '@lucide/vue'

useHead({ title: 'Пробный период - Proliv Network' })

interface TrialResult {
  activated?: boolean
  days_left?: number
  message_key?: string
}

interface TrialOverview {
  trialDays?: number
  trialAvailable?: boolean
  trialPaymentEnabled?: boolean
  trialPrice?: number
  trialMethods?: string[]
}

const fmt = useFormat()
const { push } = useToast()

const state = ref<'loading' | 'pending' | 'offer' | 'ok' | 'fail'>('loading')
const message = ref('')
const days = ref(3)
const price = ref(0)
const methods = ref<string[]>([])
const payPending = ref(false)

onMounted(async () => {
  try {
    const ov = await $fetch<TrialOverview>('/api/overview')
    days.value = ov?.trialDays ?? 3
    price.value = ov?.trialPrice ?? 0
    methods.value = ov?.trialMethods ?? []
    if (ov?.trialAvailable === false) {
      state.value = 'fail'
      message.value = 'Пробный период уже использован или недоступен'
      return
    }
    if (ov?.trialPaymentEnabled && price.value > 0) {
      state.value = 'offer'
      return
    }
  } catch {
    // без overview пробуем бесплатный путь
  }
  await activateFree()
})

async function activateFree() {
  state.value = 'pending'
  try {
    const res = await $fetch<TrialResult>('/api/trial', { method: 'POST' })
    if (res?.activated === false) throw new Error(res.message_key || 'failed')
    state.value = 'ok'
    message.value =
      typeof res?.days_left === 'number'
        ? `Подписка активна - осталось ${res.days_left} дн.`
        : 'Пробный период активирован'
  } catch (e) {
    state.value = 'fail'
    message.value =
      (e as { data?: { statusMessage?: string } }).data?.statusMessage ||
      'Не удалось активировать пробный период'
  }
}

async function payTrial() {
  if (payPending.value) return
  payPending.value = true
  try {
    const res = await $fetch<{ paymentUrl?: string | null }>('/api/checkout', {
      method: 'POST',
      body: { saleMode: 'trial', method: methods.value[0] || 'yookassa' },
    })
    if (res?.paymentUrl) {
      window.location.href = res.paymentUrl
      return
    }
    push('Не удалось создать платёж', 'error')
  } catch (e) {
    push((e as { data?: { statusMessage?: string } }).data?.statusMessage ?? 'Ошибка оплаты', 'error')
  } finally {
    payPending.value = false
  }
}
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-kicker">Proliv Network</div>
        <h1>Пробный период</h1>
      </div>
    </div>

    <section class="panel">
      <div class="panel--pad stack" style="align-items: center; text-align: center; padding: 40px 20px">
        <template v-if="state === 'loading' || state === 'pending'">
          <LoaderCircle :size="28" class="spinner" />
          <p class="muted">Активируем пробный период...</p>
        </template>
        <template v-else-if="state === 'offer'">
          <Gift :size="32" style="color: var(--accent)" />
          <h2 style="margin: 0">{{ days }} {{ fmt.plural(days, 'день', 'дня', 'дней') }} за {{ price }} ₽</h2>
          <p class="muted" style="margin: 0">
            Полный доступ к сервису. Пробный период активируется сразу после оплаты.
          </p>
          <button class="btn btn--primary" :disabled="payPending" @click="payTrial">
            <LoaderCircle v-if="payPending" :size="16" class="spinner" />
            Оплатить {{ price }} ₽
          </button>
        </template>
        <template v-else-if="state === 'ok'">
          <CheckCircle2 :size="32" style="color: var(--accent)" />
          <h2 style="margin: 0">Триал активирован</h2>
          <p class="muted" style="margin: 0">{{ message }}</p>
          <NuxtLink class="btn btn--primary" to="/">В кабинет</NuxtLink>
        </template>
        <template v-else>
          <XCircle :size="32" style="color: var(--danger, #f87171)" />
          <h2 style="margin: 0">Не получилось</h2>
          <p class="muted" style="margin: 0">{{ message }}</p>
          <NuxtLink class="btn btn--ghost" to="/">В кабинет</NuxtLink>
        </template>
      </div>
    </section>
  </div>
</template>
