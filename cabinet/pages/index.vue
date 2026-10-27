<script setup lang="ts">
import {
  ArrowRight,
  CalendarDays,
  Cpu,
  Gauge,
  Gift,
  Laptop,
  LoaderCircle,
  Monitor,
  Plug,
  QrCode,
  Radio,
  RefreshCcw,
  Smartphone,
  Trash2,
  Tv,
  Wifi,
} from '@lucide/vue'
import QRCode from 'qrcode'
import type { Device, Subscription } from '~/server/utils/store'

const { push } = useToast()
const fmt = useFormat()
const { user } = useAuth()

interface Overview {
  subscription: Subscription | null
  bonusBalance: number
  trialDays?: number
  trialAvailable?: boolean
}

const { data, refresh } = await useFetch<Overview>('/api/overview')

const sub = computed(() => data.value?.subscription ?? null)
const trafficPct = computed(() =>
  sub.value?.trafficLimitGb
    ? Math.min(100, Math.round((sub.value.trafficUsedGb / sub.value.trafficLimitGb) * 100))
    : 0,
)

const connectOpen = ref(false)
const qrOpen = ref(false)
const qrSrc = ref('')

async function showQr() {
  if (!sub.value) return
  qrSrc.value = await QRCode.toDataURL(sub.value.subscriptionUrl, {
    margin: 1,
    width: 200,
    color: { dark: '#000000', light: '#ffffff' },
  })
  qrOpen.value = true
}

const platforms = [
  {
    name: 'iOS / Android',
    icon: Smartphone,
    note: 'Happ - магазин приложений',
    href: 'https://www.happ.su/main/ru',
  },
  {
    name: 'Windows / macOS',
    icon: Monitor,
    note: 'Happ - десктопная версия',
    href: 'https://www.happ.su/main/ru',
  },
]

const LOCATION_NAMES: Record<string, string> = {
  ee: 'Таллин',
  gb: 'Лондон',
  de: 'Франкфурт',
}

const locationPending = ref(false)

async function setLocation(loc: string) {
  if (loc === sub.value?.location || locationPending.value) return
  locationPending.value = true
  try {
    const res = await $fetch<{ locationName: string }>('/api/location', {
      method: 'POST',
      body: { location: loc },
    })
    push(`Локация переключена: ${res.locationName}`)
    await refresh()
  } catch (e) {
    push((e as { data?: { statusMessage?: string } }).data?.statusMessage ?? 'Не удалось переключить', 'error')
  } finally {
    locationPending.value = false
  }
}

const DEVICE_ICONS: Record<Device['platform'], typeof Smartphone> = {
  ios: Smartphone,
  android: Smartphone,
  windows: Monitor,
  macos: Laptop,
  tvos: Tv,
  linux: Cpu,
  other: Monitor,
}

const reissueOpen = ref(false)
const reissuePending = ref(false)

async function reissueLink() {
  if (reissuePending.value) return
  reissuePending.value = true
  try {
    await $fetch('/api/subscription/reissue', { method: 'POST' })
    push('Ссылка перевыпущена, старые устройства отвязаны')
    reissueOpen.value = false
    await refresh()
  } finally {
    reissuePending.value = false
  }
}

async function removeDevice(id: string) {
  try {
    await $fetch(`/api/devices/${id}/delete`, { method: 'POST' })
    push('Устройство отвязано')
    await refresh()
  } catch (e) {
    push((e as { data?: { statusMessage?: string } }).data?.statusMessage ?? 'Не удалось отвязать', 'error')
  }
}

const trialPending = ref(false)

const trialDays = computed(() => data.value?.trialDays ?? 3)

async function activateTrial() {
  if (trialPending.value) return
  trialPending.value = true
  try {
    await $fetch('/api/trial', { method: 'POST' })
    push(`Пробный период активирован - ${trialDays.value} ${fmt.plural(trialDays.value, 'день', 'дня', 'дней')} бесплатно`)
    await refresh()
  } catch (e) {
    push((e as { data?: { statusMessage?: string } }).data?.statusMessage ?? 'Не удалось активировать', 'error')
  } finally {
    trialPending.value = false
  }
}
</script>

<template>
  <div>
    <div class="page-head">
      <div class="page-kicker">Личный кабинет</div>
      <h1>Добро пожаловать{{ user?.name ? `, ${user.name}` : '' }}</h1>
    </div>

    <!-- Нет подписки -->
    <section v-if="!sub" class="panel">
      <div class="empty">
        <div class="empty__icon"><Wifi :size="24" /></div>
        <h2>Активной подписки пока нет</h2>
        <p>
          {{ data?.trialAvailable ? `Попробуйте ${trialDays} ${fmt.plural(trialDays, 'день', 'дня', 'дней')} бесплатно или выберите тариф` : 'Выберите тариф, чтобы начать' }}
        </p>
        <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap">
          <button
            v-if="data?.trialAvailable"
            class="btn btn--primary"
            :disabled="trialPending"
            @click="activateTrial"
          >
            <LoaderCircle v-if="trialPending" :size="16" class="spinner" />
            <Gift v-else :size="16" />
            {{ trialDays }} {{ fmt.plural(trialDays, 'день', 'дня', 'дней') }} бесплатно
          </button>
          <NuxtLink to="/purchases" class="btn btn--ghost">
            Тарифы
            <ArrowRight :size="16" />
          </NuxtLink>
        </div>
        <div style="margin-top: 18px">
          <a class="link" href="https://t.me/prolivnet_bot" target="_blank" rel="noopener">
            Прокси для Telegram - подключить
          </a>
        </div>
      </div>
    </section>

    <template v-else>
      <!-- Карточка подписки -->
      <section class="panel">
        <div class="panel__title">
          <Radio :size="17" />
          {{ sub.plan }}
          <span class="badge badge--green" style="margin-left: auto">
            Активна · {{ fmt.daysLeft(sub.until) }} {{ fmt.plural(fmt.daysLeft(sub.until), 'день', 'дня', 'дней') }}
          </span>
        </div>
        <div class="panel--pad stack">
          <div>
            <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px">
              <span class="muted">Трафик</span>
              <span class="numeric">
                {{ sub.trafficUsedGb }} / {{ sub.trafficLimitGb }} ГБ
                <span class="muted">· сброс {{ fmt.date(sub.resetAt) }}</span>
              </span>
            </div>
            <div class="progress">
              <div class="progress__bar" :style="{ width: `${trafficPct}%` }" />
            </div>
          </div>

          <div style="display: flex; gap: 8px; flex-wrap: wrap">
            <button class="btn btn--primary" @click="connectOpen = true">
              <Plug :size="16" />
              Подключиться
            </button>
            <button class="btn btn--ghost" @click="showQr">
              <QrCode :size="16" />
              QR
            </button>
            <NuxtLink to="/purchases" class="btn btn--ghost">Продлить</NuxtLink>
          </div>
        </div>

        <!-- Локация -->
        <div class="row-line row-line--loc">
          <span class="row-line__icon"><Radio :size="15" /></span>
          <span class="row-line__body">
            <span class="row-line__label">Локация</span>
            <span class="row-line__hint">Точка выхода в приложении</span>
          </span>
          <span class="pills" style="max-width: none; margin: 0">
            <button
              v-for="loc in sub.locations"
              :key="loc"
              class="pills__item pills__item--flag"
              :class="{ 'is-active': sub.location === loc }"
              :disabled="locationPending"
              @click="setLocation(loc)"
            >
              <img :src="`/images/flags/${loc}.svg`" :alt="loc.toUpperCase()" width="18" height="13" />
              {{ LOCATION_NAMES[loc] ?? loc.toUpperCase() }}
            </button>
          </span>
        </div>

        <!-- Устройства -->
        <div class="panel--pad" style="border-top: 1px solid var(--line); padding-bottom: 14px">
          <div class="devices-head">
            <span class="devices-head__title">
              <Smartphone :size="15" />
              Устройства
              <span class="muted numeric">{{ sub.devices.length }} / {{ sub.deviceLimit }}</span>
            </span>
            <button class="btn btn--ghost btn--sm" @click="reissueOpen = true">
              <RefreshCcw :size="13" />
              Перевыпустить ссылку
            </button>
          </div>
          <div v-if="sub.devices.length" class="devices-list">
            <div v-for="d in sub.devices" :key="d.id" class="device-row">
              <span class="device-row__icon"><component :is="DEVICE_ICONS[d.platform] ?? Monitor" :size="15" /></span>
              <span class="device-row__body">
                <span class="device-row__name">{{ d.name }}</span>
                <span class="device-row__hint">HWID {{ d.hwid }} · {{ fmt.date(d.lastSeen) }}</span>
              </span>
              <button class="device-row__del" title="Отвязать" @click="removeDevice(d.id)">
                <Trash2 :size="14" />
              </button>
            </div>
          </div>
          <p v-else class="muted" style="font-size: 12px; margin-top: 10px">
            Устройства появятся после первого подключения
          </p>
        </div>
      </section>

      <!-- Статы -->
      <section class="grid-3" style="margin-top: 14px">
        <div class="stat">
          <div class="stat__label"><Gauge :size="14" />Трафик</div>
          <div class="stat__value numeric">{{ sub.trafficUsedGb }} ГБ</div>
          <div class="stat__sub">из {{ sub.trafficLimitGb }} ГБ в месяц</div>
        </div>
        <div class="stat">
          <div class="stat__label"><Smartphone :size="14" />Устройства</div>
          <div class="stat__value numeric">{{ sub.devices.length }} / {{ sub.deviceLimit }}</div>
          <div class="stat__sub">
            <span v-for="(d, i) in sub.devices.slice(0, 2)" :key="d.id">
              {{ i ? ' · ' : '' }}{{ d.name }}
            </span>
          </div>
        </div>
        <div class="stat">
          <div class="stat__label"><CalendarDays :size="14" />Оплачено до</div>
          <div class="stat__value">{{ fmt.date(sub.until) }}</div>
          <div class="stat__sub">
            <span class="flags">
              <img v-for="loc in sub.locations" :key="loc" :src="`/images/flags/${loc}.svg`" :alt="loc.toUpperCase()" />
            </span>
          </div>
        </div>
      </section>

      <!-- Бонусный счёт тизер -->
      <section class="panel" style="margin-top: 14px">
        <NuxtLink to="/referrals" class="row-line row-line--clickable" style="border-top: 0">
          <span class="row-line__icon"><Gift :size="16" /></span>
          <span class="row-line__body">
            <span class="row-line__label">Бонусный счёт</span>
            <span class="row-line__hint">Приглашайте друзей и получайте 15% с их оплат</span>
          </span>
          <span class="row-line__value numeric">{{ fmt.rub(data?.bonusBalance ?? 0) }}</span>
        </NuxtLink>
      </section>
    </template>

    <!-- Модалка подключения -->
    <AppModal :open="connectOpen" title="Подключиться" @close="connectOpen = false">
      <div class="stack">
        <CopyField v-if="sub" :value="sub.subscriptionUrl" qr @qr="showQr" />
        <a
          v-for="p in platforms"
          :key="p.name"
          :href="p.href"
          target="_blank"
          rel="noopener"
          class="method"
        >
          <span class="method__mark"><component :is="p.icon" :size="17" /></span>
          <span>
            {{ p.name }}
            <div class="muted" style="font-size: 12px; font-weight: 400">{{ p.note }}</div>
          </span>
        </a>
        <p class="muted" style="font-size: 12px">
          Добавьте ссылку подписки в приложение - конфиги всех локаций подтянутся автоматически.
        </p>
      </div>
    </AppModal>

    <!-- Модалка QR -->
    <AppModal :open="qrOpen" title="QR-код подписки" @close="qrOpen = false">
      <div class="qr-box"><img v-if="qrSrc" :src="qrSrc" alt="QR подписки" /></div>
      <p class="muted" style="margin-top: 14px; font-size: 12px; text-align: center">
        Отсканируйте из приложения Happ или аналогичного клиента
      </p>
    </AppModal>

    <!-- Модалка перевыпуска ссылки -->
    <AppModal :open="reissueOpen" title="Перевыпустить ссылку" @close="reissueOpen = false">
      <div class="stack">
        <p class="muted" style="font-size: 13px">
          Старая ссылка подписки перестанет работать, все устройства будут отвязаны.
          Приложения нужно будет подключить заново по новой ссылке.
        </p>
        <button class="btn btn--primary btn--block" :disabled="reissuePending" @click="reissueLink">
          <LoaderCircle v-if="reissuePending" :size="15" class="spinner" />
          Перевыпустить
        </button>
      </div>
    </AppModal>
  </div>
</template>
