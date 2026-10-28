<script setup lang="ts">
import {
  Check,
  CreditCard,
  Gauge,
  LoaderCircle,
  Plus,
  ReceiptText,
  ShieldCheck,
  Smartphone,
  Star,
} from '@lucide/vue'
import type { Order } from '~/server/utils/store'

const { push } = useToast()
const fmt = useFormat()

interface Tariffs {
  plan: { name: string; spec: string; devices: number }
  periods: { id: string; days: number; label: string; price: number; oldPrice: number | null }[]
  extras: { id: string; kind: 'traffic' | 'device'; title: string; price: number }[]
  methods: { id: string; title: string; icon: string | null }[]
  balances?: { user: number; partner: number }
  suggestedPromoCode?: string | null
  friendDiscountPercent?: number
}

const { data, status, refresh } = useFetch<Tariffs>('/api/tariffs', { lazy: true })
const { data: ordersData, refresh: refreshOrders } = useFetch<{ orders: Order[] }>(
  '/api/orders',
  { lazy: true },
)

const route = useRoute()
const period = ref('')
const method = ref('')
const balanceSource = ref<'' | 'user' | 'partner'>('')
const pending = ref(false)
const brokenIcons = ref(new Set<string>())

// Способ оплаты - первый из вернувшихся с бэкенда
watch(
  () => data.value?.methods,
  (methods) => {
    if (!method.value || !methods?.some((m) => m.id === method.value)) {
      method.value = methods?.[0]?.id ?? ''
    }
  },
  { immediate: true },
)

// ?duration=365 (лендинг "12 месяцев") - предвыбираем период по дням
watch(
  () => data.value?.periods,
  (periods) => {
    const days = Number(route.query.duration)
    if (!days || !periods?.length || period.value) return
    const match = periods.find((p) => p.days === days)
    if (match) period.value = match.id
  },
  { immediate: true },
)

const selectedPeriod = computed(
  () => data.value?.periods.find((p) => p.id === period.value) ?? data.value?.periods[0],
)

// Реферальная скидка друга: бэкенд сам применит персональный промокод в
// чекауте - показываем итог заранее, чтобы цена на оплате не удивила.
const friendDiscountAmount = computed(() => {
  const pct = data.value?.friendDiscountPercent ?? 0
  const price = selectedPeriod.value?.price ?? 0
  return data.value?.suggestedPromoCode && pct > 0 ? (price * pct) / 100 : 0
})
const finalPrice = computed(
  () => Math.max(0, (selectedPeriod.value?.price ?? 0) - friendDiscountAmount.value),
)

// ?balance=1 (кнопка «Оплатить бонусами» в рефералке) - сразу включаем
// списание: сначала бонусный счёт, если он пуст - партнёрский баланс.
watch(
  () => data.value?.balances,
  (b) => {
    if (balanceSource.value || route.query.balance !== '1') return
    balanceSource.value = (b?.user ?? 0) > 0 ? 'user' : (b?.partner ?? 0) > 0 ? 'partner' : ''
  },
  { immediate: true },
)
function toggleBalance(source: 'user' | 'partner') {
  balanceSource.value = balanceSource.value === source ? '' : source
}

const periodEls = ref<unknown[]>([])
const periodIndex = computed(() => {
  const idx = (data.value?.periods ?? []).findIndex((p) => p.id === selectedPeriod.value?.id)
  return idx < 0 ? 0 : idx
})
const { indicator: periodPill } = usePillIndicator(periodEls, periodIndex)

function goToPayment(res: { paymentUrl?: string | null; paid?: boolean }) {
  if (res.paymentUrl) window.location.href = res.paymentUrl
}

async function checkout() {
  if (pending.value) return
  pending.value = true
  try {
    const res = await $fetch<{ paymentUrl: string | null; paid?: boolean }>('/api/checkout', {
      method: 'POST',
      body: {
        planId: selectedPeriod.value?.id,
        periodDays: selectedPeriod.value?.days,
        method: method.value,
        balanceSource: balanceSource.value || undefined,
      },
    })
    if (res.paymentUrl) {
      goToPayment(res)
      return
    }
    push(res.paid ? 'Оплачено' : 'Заказ создан')
    await refreshOrders()
  } catch (e) {
    push((e as { data?: { statusMessage?: string } }).data?.statusMessage ?? 'Не удалось создать платёж', 'error')
  } finally {
    pending.value = false
  }
}

async function buyExtra(id: string) {
  if (pending.value) return
  pending.value = true
  try {
    const res = await $fetch<{ paymentUrl: string | null; paid?: boolean }>('/api/checkout', {
      method: 'POST',
      body: { extra: id, method: method.value, balanceSource: balanceSource.value || undefined },
    })
    if (res.paymentUrl) {
      goToPayment(res)
      return
    }
    push(res.paid ? 'Оплачено' : 'Заказ создан')
    await refreshOrders()
  } catch (e) {
    push((e as { data?: { statusMessage?: string } }).data?.statusMessage ?? 'Не удалось создать платёж', 'error')
  } finally {
    pending.value = false
  }
}

const cancelPending = ref('')
async function cancelOrder(id: string) {
  if (cancelPending.value) return
  cancelPending.value = id
  try {
    await $fetch(`/api/payments/${encodeURIComponent(id)}/cancel`, { method: 'POST' })
    push('Платёж отменён')
    await refreshOrders()
  } catch (e) {
    push((e as { data?: { statusMessage?: string } }).data?.statusMessage ?? 'Не удалось отменить', 'error')
  } finally {
    cancelPending.value = ''
  }
}

const ORDER_STATUS: Record<Order['status'], string> = {
  paid: 'Оплачен',
  pending: 'Ожидает оплаты',
  refunded: 'Возврат',
  failed: 'Не прошёл',
}
</script>

<template>
  <div>
    <div class="page-head">
      <div class="page-kicker">Подписка</div>
      <h1>Покупки</h1>
    </div>

    <!-- Загрузка -->
    <section v-if="status === 'pending'" class="panel" aria-hidden="true">
      <div class="panel--pad stack">
        <div class="skel" style="height: 20px; width: 45%" />
        <div class="skel" style="height: 12px" />
        <div class="skel" style="height: 44px" />
        <div class="skel" style="height: 12px; width: 60%" />
        <div class="skel" style="height: 44px" />
      </div>
    </section>

    <section v-else-if="status === 'error'" class="panel">
      <FetchError @retry="refresh" />
    </section>

    <div v-else class="grid-2">
      <!-- Тариф -->
      <section class="panel">
        <div class="panel__title"><CreditCard :size="17" />Подписка</div>
        <div class="panel--pad panel--pad--spread">
          <div>
            <h2 style="font-family: var(--font-display); font-size: 18px; font-weight: 600">
              {{ data?.plan.name }}
            </h2>
            <p class="muted" style="margin-top: 6px; font-size: 13px">{{ data?.plan.spec }}</p>
          </div>

          <div class="plan-feats">
            <span class="plan-feat">
              <Smartphone :size="13" />{{ data?.plan.devices ?? 0 }}
              {{ fmt.plural(data?.plan.devices ?? 0, 'устройство', 'устройства', 'устройств') }}
            </span>
            <span class="plan-feat"><ShieldCheck :size="13" />VLESS Reality</span>
          </div>

          <div class="field">
            <span>Срок подписки</span>
            <div class="pills" :class="{ 'has-pill': periodPill.ready }">
              <div
                class="pills__indicator"
                :class="{ 'is-ready': periodPill.ready }"
                :style="{ transform: `translateX(${periodPill.x}px)`, width: `${periodPill.w}px` }"
                aria-hidden="true"
              />
              <button
                v-for="p in data?.periods"
                :key="p.id"
                ref="periodEls"
                class="pills__item"
                :class="{ 'is-active': selectedPeriod?.id === p.id }"
                @click="period = p.id"
              >
                {{ p.label }}
                <small v-if="p.oldPrice">−{{ Math.round((1 - p.price / p.oldPrice) * 100) }}%</small>
              </button>
            </div>
          </div>

        </div>
      </section>

      <!-- Оплата -->
      <section class="panel panel--fill">
        <div class="panel__title">К оплате</div>
        <div class="panel--pad stack panel--pad--fill">
          <div>
            <span class="price-now numeric">{{ fmt.rub(finalPrice) }}</span>
            <span v-if="selectedPeriod?.oldPrice || friendDiscountAmount > 0" class="price-old numeric">
              {{ fmt.rub(selectedPeriod?.oldPrice ?? selectedPeriod?.price ?? 0) }}
            </span>
          </div>

          <div class="sum-lines">
            <div class="sum-line">
              <span class="muted">{{ data?.plan.name }} · {{ selectedPeriod?.label }}</span>
              <span class="numeric">{{ fmt.rub(selectedPeriod?.price ?? 0) }}</span>
            </div>
            <div v-if="friendDiscountAmount > 0" class="sum-line">
              <span class="muted">Скидка по приглашению</span>
              <span class="numeric accent">−{{ fmt.rub(friendDiscountAmount) }}</span>
            </div>
            <div v-if="(data?.methods?.length ?? 0) === 1" class="sum-line">
              <span class="muted">Способ оплаты</span>
              <span class="sum-line__method">
                <img
                  v-if="data?.methods?.[0]?.icon && !brokenIcons.has(data.methods[0].id)"
                  :src="data.methods[0].icon"
                  :alt="data.methods[0].title"
                  :title="data.methods[0].title"
                  @error="brokenIcons.add(data.methods[0].id)"
                />
                <template v-else>{{ data?.methods?.[0]?.title }}</template>
              </span>
            </div>
          </div>

          <div v-if="(data?.methods?.length ?? 0) > 1" class="field">
            <span>Способ оплаты</span>
            <div class="methods">
              <button
                v-for="m in data?.methods"
                :key="m.id"
                class="method"
                :class="{ 'is-active': method === m.id }"
                @click="method = m.id"
              >
                <span class="method__mark">
                  <img
                    v-if="m.icon && !brokenIcons.has(m.id)"
                    :src="m.icon"
                    :alt="m.title"
                    @error="brokenIcons.add(m.id)"
                  />
                  <Star v-else :size="17" class="accent" />
                </span>
                {{ m.title }}
                <Check class="method__check" :size="17" />
              </button>
            </div>
          </div>

          <div
            v-if="(data?.balances?.user ?? 0) > 0 || (data?.balances?.partner ?? 0) > 0"
            style="display: flex; flex-direction: column; gap: 10px"
          >
            <label v-if="(data?.balances?.user ?? 0) > 0" class="check">
              <input
                type="checkbox"
                :checked="balanceSource === 'user'"
                @change="toggleBalance('user')"
              />
              <span class="check__box"><Check :size="13" :stroke-width="3" /></span>
              Списать бонусы · до {{ fmt.rub(data?.balances?.user ?? 0) }}
            </label>
            <label v-if="(data?.balances?.partner ?? 0) > 0" class="check">
              <input
                type="checkbox"
                :checked="balanceSource === 'partner'"
                @change="toggleBalance('partner')"
              />
              <span class="check__box"><Check :size="13" :stroke-width="3" /></span>
              Списать партнёрский баланс · до {{ fmt.rub(data?.balances?.partner ?? 0) }}
            </label>
          </div>

          <button
            class="btn btn--primary btn--block"
            style="margin-top: auto"
            :disabled="pending || !method"
            @click="checkout"
          >
            <LoaderCircle v-if="pending" :size="16" class="spinner" />
            {{ method ? 'Перейти к оплате' : 'Оплата картой скоро будет доступна' }}
          </button>
        </div>
      </section>
    </div>

    <!-- Докупка -->
    <section v-if="data?.extras?.length" class="panel" style="margin-top: 14px">
      <div class="panel__title"><Plus :size="17" />Докупить к подписке</div>
      <div v-for="e in data?.extras" :key="e.id" class="row-line">
        <span class="row-line__icon">
          <Smartphone v-if="e.kind === 'device'" :size="15" />
          <Gauge v-else :size="15" />
        </span>
        <span class="row-line__body">
          <span class="row-line__label">{{ e.title }}</span>
          <span class="row-line__hint">{{ e.kind === 'device' ? 'Доп. устройства к подписке' : 'Доп. трафик на месяц' }}</span>
        </span>
        <span class="row-line__value numeric" style="font-size: 14px">{{ fmt.rub(e.price) }}</span>
        <button class="btn btn--ghost btn--sm" :disabled="pending" @click="buyExtra(e.id)">Купить</button>
      </div>
    </section>

    <!-- История покупок -->
    <section v-if="ordersData?.orders?.length" id="orders" class="panel" style="margin-top: 14px">
      <div class="panel__title"><ReceiptText :size="17" />История покупок</div>
      <div>
        <div v-for="o in ordersData.orders" :key="o.id" class="row-line">
          <span class="row-line__icon"><ReceiptText :size="15" /></span>
          <span class="row-line__body">
            <span class="row-line__label">{{ o.title }}</span>
            <span class="row-line__hint">{{ o.id }} · {{ fmt.date(o.at) }}</span>
          </span>
          <span class="row-line__value numeric" style="margin-right: 10px">
            {{ o.amount ? fmt.rub(o.amount) : '—' }}
          </span>
          <a
            v-if="o.status === 'pending' && o.checkoutUrl"
            :href="o.checkoutUrl"
            target="_blank"
            rel="noopener"
            class="btn btn--ghost btn--sm"
            style="margin-right: 8px"
          >
            Оплатить
          </a>
          <button
            v-if="o.status === 'pending'"
            class="btn btn--ghost btn--sm"
            style="margin-right: 8px"
            :disabled="cancelPending === o.id"
            @click="cancelOrder(o.id)"
          >
            <LoaderCircle v-if="cancelPending === o.id" :size="13" class="spinner" />
            Отменить
          </button>
          <span class="order-status" :class="`order-status--${o.status}`">{{ ORDER_STATUS[o.status] }}</span>
        </div>
      </div>
    </section>
  </div>
</template>
