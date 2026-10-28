<script setup lang="ts">
import { ArrowRight, Monitor, Plug, Smartphone, Wifi } from '@lucide/vue'
import QRCode from 'qrcode'

useHead({ title: 'Подключение - Proliv Network' })

interface Overview {
  subscription: { subscriptionUrl?: string } | null
}

const { data, status } = useFetch<Overview>('/api/overview', { lazy: true })
const subscriptionUrl = computed(() => data.value?.subscription?.subscriptionUrl ?? '')

const qrSrc = ref('')
watch(
  subscriptionUrl,
  async (url) => {
    if (!url) {
      qrSrc.value = ''
      return
    }
    qrSrc.value = await QRCode.toDataURL(url, {
      margin: 1,
      width: 200,
      color: { dark: '#000000', light: '#ffffff' },
    })
  },
  { immediate: true },
)

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
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-kicker">Proliv Network</div>
        <h1>Подключение</h1>
      </div>
    </div>

    <section v-if="status === 'pending'" class="panel" aria-hidden="true">
      <div class="panel--pad stack">
        <div class="skel" style="height: 20px; width: 45%" />
        <div class="skel" style="height: 12px" />
        <div class="skel" style="height: 44px" />
        <div class="skel" style="height: 12px; width: 60%" />
      </div>
    </section>

    <section v-else-if="!subscriptionUrl" class="panel">
      <div class="empty">
        <div class="empty__icon"><Wifi :size="24" /></div>
        <h2>Активной подписки пока нет</h2>
        <p>Оформите подписку, чтобы получить ссылку для подключения</p>
        <NuxtLink to="/purchases" class="btn btn--primary">
          Тарифы
          <ArrowRight :size="16" />
        </NuxtLink>
      </div>
    </section>

    <template v-else>
      <section class="panel">
        <div class="panel__title">
          <Smartphone :size="17" />
          Шаг 1 - приложение
        </div>
        <div class="panel--pad stack">
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
        </div>
      </section>

      <section class="panel" style="margin-top: 14px">
        <div class="panel__title">
          <Plug :size="17" />
          Шаг 2 - добавьте подписку
        </div>
        <div class="panel--pad stack">
          <CopyField :value="subscriptionUrl" />
          <div v-if="qrSrc" class="qr-box"><img :src="qrSrc" alt="QR подписки" /></div>
          <p class="muted" style="font-size: 12px">
            В приложении нажмите «+» и выберите импорт по ссылке - конфиги всех локаций подтянутся
            автоматически. С другого устройства удобно сканировать QR-код.
          </p>
        </div>
      </section>
    </template>
  </div>
</template>
