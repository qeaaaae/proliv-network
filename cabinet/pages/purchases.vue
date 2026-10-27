<script setup lang="ts">
import {
  Check,
  CreditCard,
  Gauge,
  Globe,
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
  plan: { name: string; spec: string }
  periods: { id: string; days: number; label: string; price: number; oldPrice: number | null }[]
  extras: { id: string; kind: 'traffic' | 'device'; title: string; price: number }[]
  methods: { id: string; title: string; icon: string | null }[]
}

const { data } = await useFetch<Tariffs>('/api/tariffs')
const { data: ordersData, refresh: refreshOrders } = await useFetch<{ orders: Order[] }>('/api/orders')

const period = ref('')
const method = ref('')
const gift = ref(false)
const giftTo = ref('')
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

const selectedPeriod = computed(
  () => data.value?.periods.find((p) => p.id === period.value) ?? data.value?.periods[0],
)

function goToPayment(res: { paymentUrl?: string | null; paid?: boolean }) {
  if (res.paymentUrl) window.location.href = res.paymentUrl
}

async function checkout() {
  pending.value = true
  try {
    const res = await $fetch<{ paymentUrl: string | null; paid?: boolean }>('/api/checkout', {
      method: 'POST',
      body: {
        planId: selectedPeriod.value?.id,
        periodDays: selectedPeriod.value?.days,
        method: method.value,
        gift: gift.value,
        giftTo: gift.value ? giftTo.value.trim() : undefined,
      },
    })
    if (res.paymentUrl) {
      goToPayment(res)
      return
    }
    push(
      res.paid
        ? 'Оплачено'
        : gift.value
          ? 'Заказ создан - подарочный код придёт после оплаты'
          : 'Заказ создан',
    )
    await refreshOrders()
  } catch (e) {
    push((e as { data?: { statusMessage?: string } }).data?.statusMessage ?? 'Не удалось создать платёж', 'error')
  } finally {
    pending.value = false
  }
}

async function buyExtra(id: string) {
  try {
    const res = await $fetch<{ paymentUrl: string | null; paid?: boolean }>('/api/checkout', {
      method: 'POST',
      body: { extra: id, method: method.value },
    })
    if (res.paymentUrl) {
      goToPayment(res)
      return
    }
    push(res.paid ? 'Оплачено' : 'Заказ создан')
    await refreshOrders()
  } catch (e) {
    push((e as { data?: { statusMessage?: string } }).data?.statusMessage ?? 'Не удалось создать платёж', 'error')
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

    <div class="grid-2">
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
            <span class="plan-feat"><Gauge :size="13" />1000 ГБ/мес</span>
            <span class="plan-feat"><Smartphone :size="13" />5 устройств</span>
            <span class="plan-feat"><Globe :size="13" />3 локации</span>
            <span class="plan-feat"><ShieldCheck :size="13" />VLESS Reality</span>
          </div>

          <div class="field">
            <span>Срок подписки</span>
            <div class="pills">
              <button
                v-for="p in data?.periods"
                :key="p.id"
                class="pills__item"
                :class="{ 'is-active': selectedPeriod?.id === p.id }"
                @click="period = p.id"
              >
                {{ p.label }}
                <small v-if="p.oldPrice">−{{ Math.round((1 - p.price / p.oldPrice) * 100) }}%</small>
              </button>
            </div>
          </div>

          <div style="display: flex; align-items: center; gap: 14px; flex-wrap: wrap">
            <label class="check">
              <input v-model="gift" type="checkbox" />
              <span class="check__box"><Check :size="13" :stroke-width="3" /></span>
              Оформить в подарок
            </label>
            <input
              v-if="gift"
              v-model="giftTo"
              class="input input--sm"
              style="flex: 1; min-width: 180px"
              placeholder="Email друга (необязательно)"
            />
          </div>
        </div>
      </section>

      <!-- Оплата -->
      <section class="panel panel--fill">
        <div class="panel__title">К оплате</div>
        <div class="panel--pad stack panel--pad--fill">
          <div>
            <span class="price-now numeric">{{ fmt.rub(selectedPeriod?.price ?? 0) }}</span>
            <span v-if="selectedPeriod?.oldPrice" class="price-old numeric">
              {{ fmt.rub(selectedPeriod.oldPrice) }}
            </span>
          </div>

          <div class="sum-lines">
            <div class="sum-line">
              <span class="muted">{{ data?.plan.name }} · {{ selectedPeriod?.label }}</span>
              <span class="numeric">{{ fmt.rub(selectedPeriod?.price ?? 0) }}</span>
            </div>
            <div v-if="(data?.methods?.length ?? 0) === 1" class="sum-line">
              <span class="muted">Способ оплаты</span>
              <span>{{ data?.methods?.[0]?.title }}</span>
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
        <button class="btn btn--ghost btn--sm" @click="buyExtra(e.id)">Купить</button>
      </div>
    </section>

    <!-- История покупок -->
    <section v-if="ordersData?.orders?.length" class="panel" style="margin-top: 14px">
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
          <span class="order-status" :class="`order-status--${o.status}`">{{ ORDER_STATUS[o.status] }}</span>
        </div>
      </div>
    </section>
  </div>
</template>
