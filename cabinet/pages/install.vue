<script setup lang="ts">
import {
  ArrowRight,
  CircleCheck,
  Download,
  Laptop,
  LifeBuoy,
  Link2,
  Monitor,
  Plus,
  Smartphone,
  Wifi,
} from '@lucide/vue'
import QRCode from 'qrcode'

useHead({ title: 'Инструкция - Proliv Network' })

interface Overview {
  subscription: { subscriptionUrl?: string } | null
}

const route = useRoute()
const { data, status, refresh } = useFetch<Overview>('/api/overview', { lazy: true })
const subscriptionUrl = computed(() => data.value?.subscription?.subscriptionUrl ?? '')
const happDeepLink = computed(
  () => `happ://add/${encodeURIComponent(subscriptionUrl.value)}`,
)
const incyDeepLink = computed(
  () => `incy://add/${encodeURIComponent(subscriptionUrl.value)}`,
)

type PlatformId = 'ios' | 'android' | 'windows' | 'macos'

const platforms: { id: PlatformId; label: string; icon: typeof Smartphone }[] = [
  { id: 'ios', label: 'iPhone', icon: Smartphone },
  { id: 'android', label: 'Android', icon: Smartphone },
  { id: 'windows', label: 'Windows', icon: Monitor },
  { id: 'macos', label: 'macOS', icon: Laptop },
]

const platform = ref<PlatformId>('ios')

function detectPlatform(): PlatformId {
  const q = String(route.query.platform ?? '').toLowerCase()
  if (platforms.some((p) => p.id === q)) return q as PlatformId
  const ua = navigator.userAgent
  if (/iPhone|iPad|iPod/i.test(ua)) return 'ios'
  if (/Android/i.test(ua)) return 'android'
  if (/Macintosh|Mac OS X/i.test(ua)) return 'macos'
  return 'windows'
}

onMounted(() => {
  platform.value = detectPlatform()
})

const platformIndex = computed(() =>
  Math.max(
    0,
    platforms.findIndex((p) => p.id === platform.value),
  ),
)
// platforms - статичный список из 4 элементов, index всегда валиден
const platformMeta = computed(() => platforms[platformIndex.value] ?? platforms[0]!)
const platformLabel = computed(() => platformMeta.value.label)
const platformEls = ref<unknown[]>([])
const { indicator } = usePillIndicator(platformEls, platformIndex)

const storeLinks: Record<PlatformId, { label: string; href: string }[]> = {
  ios: [
    {
      label: 'Happ в App Store',
      href: 'https://apps.apple.com/us/app/happ-proxy-utility/id6504287215',
    },
    {
      label: 'INCY в App Store',
      href: 'https://apps.apple.com/us/app/incy/id6756943388',
    },
  ],
  android: [
    {
      label: 'Скачать Happ (APK)',
      href: 'https://github.com/Happ-proxy/happ-android/releases/latest/download/Happ.apk',
    },
    {
      label: 'INCY в Google Play',
      href: 'https://play.google.com/store/apps/details?id=llc.itdev.incy',
    },
  ],
  windows: [
    {
      label: 'Happ для Windows',
      href: 'https://github.com/Happ-proxy/happ-desktop/releases/latest/download/setup-Happ.x64.exe',
    },
    {
      label: 'INCY для Windows',
      href: 'https://github.com/INCY-DEV/incy-platforms/releases/download/latest/incy-windows-setup.exe',
    },
  ],
  macos: [
    {
      label: 'Happ для macOS',
      href: 'https://github.com/Happ-proxy/happ-desktop/releases/latest/download/Happ.macOS.universal.dmg',
    },
    {
      label: 'INCY для macOS (M-серия)',
      href: 'https://github.com/INCY-DEV/incy-platforms/releases/download/latest/incy-macos-arm64.dmg',
    },
    {
      label: 'INCY для macOS (Intel)',
      href: 'https://github.com/INCY-DEV/incy-platforms/releases/download/latest/incy-macos-intel.dmg',
    },
  ],
}

const storeNote: Record<PlatformId, string> = {
  ios: 'Подойдёт любое из двух приложений - Happ или INCY, наша ссылка работает в обоих.',
  android:
    'Happ временно нет в Google Play: скачайте APK и запустите файл, либо поставьте INCY - наша ссылка работает и там.',
  windows: 'Откройте скачанный файл и установите приложение.',
  macos: 'Откройте скачанный файл и перетащите приложение в папку «Программы». Для INCY выбирайте версию по процессору: на большинстве новых Mac - M-серия.',
}

const permissionNote: Record<PlatformId, string> = {
  ios: 'При первом включении iPhone спросит разрешение на добавление VPN - нажмите «Разрешить» и введите код блокировки.',
  android: 'При первом включении телефон попросит подтвердить подключение VPN - нажмите «ОК».',
  windows: 'Если Windows спросит доступ к сети или VPN - разрешите.',
  macos: 'Если система попросит разрешить добавление VPN-конфигурации - согласитесь.',
}

const step1Title: Record<PlatformId, string> = {
  ios: 'Установите приложение',
  android: 'Установите приложение',
  windows: 'Установите приложение',
  macos: 'Установите приложение',
}

const manualAddNote = computed(() => {
  if (platform.value === 'android')
    return 'Или вручную: в Happ нажмите «+» вверху экрана, в INCY - откройте «Провайдеры» и добавьте ссылку там.'
  if (platform.value === 'ios')
    return 'Или вручную: в Happ нажмите «+» вверху экрана и вставьте ссылку, в INCY - откройте «Провайдеры» и добавьте ссылку там.'
  if (platform.value === 'windows' || platform.value === 'macos')
    return 'Или вручную: в Happ нажмите «+» возле списка профилей и вставьте ссылку, в INCY - откройте «Провайдеры» и добавьте ссылку там.'
  return 'Или вручную: в окне Happ нажмите «+» возле списка профилей, вставьте ссылку и нажмите «Готово».'
})

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
</script>

<template>
  <div>
    <div class="page-head">
      <div class="page-kicker">Инструкция</div>
      <h1>Как подключить Proliv Network</h1>
      <p>Три шага - займёт пару минут. Выберите своё устройство:</p>
    </div>

    <section v-if="status === 'pending'" class="panel" aria-hidden="true">
      <div class="panel--pad stack">
        <div class="skel" style="height: 44px" />
        <div class="skel" style="height: 20px; width: 45%" />
        <div class="skel" style="height: 12px" />
        <div class="skel" style="height: 44px" />
        <div class="skel" style="height: 12px; width: 60%" />
      </div>
    </section>

    <section v-else-if="status === 'error'" class="panel">
      <FetchError @retry="refresh" />
    </section>

    <section v-else-if="!subscriptionUrl" class="panel">
      <div class="empty">
        <div class="empty__icon"><Wifi :size="24" /></div>
        <h2>Активной подписки пока нет</h2>
        <p>Оформите подписку - и здесь появится ваша личная ссылка для подключения</p>
        <NuxtLink to="/purchases" class="btn btn--primary">
          Тарифы
          <ArrowRight :size="16" />
        </NuxtLink>
      </div>
    </section>

    <template v-else>
      <div
        class="pills install-platforms"
        :class="{ 'has-pill': indicator.ready }"
        role="tablist"
        aria-label="Ваше устройство"
      >
        <div
          class="pills__indicator"
          :class="{ 'is-ready': indicator.ready }"
          :style="{ transform: `translateX(${indicator.x}px)`, width: `${indicator.w}px` }"
          aria-hidden="true"
        />
        <button
          v-for="p in platforms"
          :key="p.id"
          ref="platformEls"
          type="button"
          role="tab"
          class="pills__item"
          :class="{ 'is-active': p.id === platform }"
          :aria-selected="p.id === platform"
          @click="platform = p.id"
        >
          <component :is="p.icon" :size="15" style="vertical-align: -3px; margin-right: 5px" />
          {{ p.label }}
        </button>
      </div>

      <section class="panel" style="margin-top: 14px">
        <div class="panel__title">
          <component :is="platformMeta.icon" :size="17" />
          Подключение - {{ platformLabel }}
        </div>

        <ol class="steps">
          <li class="step">
            <span class="step__num">1</span>
            <div class="step__body">
              <div class="step__title">{{ step1Title[platform] }}</div>
              <p class="step__text">Это бесплатное приложение, через него работает VPN.</p>
              <div class="step__actions step__actions--row">
                <a
                  v-for="link in storeLinks[platform]"
                  :key="link.href"
                  :href="link.href"
                  target="_blank"
                  rel="noopener"
                  class="btn btn--ghost"
                >
                  <Download :size="15" />
                  {{ link.label }}
                </a>
              </div>
              <p class="step__note">{{ storeNote[platform] }}</p>
            </div>
          </li>

          <li class="step">
            <span class="step__num">2</span>
            <div class="step__body">
              <div class="step__title">Добавьте подписку в приложение</div>
              <p class="step__text">
                Нажмите кнопку - приложение откроется и подписка добавится сама.
              </p>
              <div class="step__actions step__actions--row">
                <a :href="happDeepLink" class="btn btn--primary">
                  <Plus :size="16" />
                  Добавить в Happ
                </a>
                <a :href="incyDeepLink" class="btn btn--ghost">
                  <Plus :size="16" />
                  В Incy
                </a>
              </div>
              <CopyField :value="subscriptionUrl" style="margin-top: 12px" />
              <p class="step__note">{{ manualAddNote }}</p>
            </div>
          </li>

          <li class="step">
            <span class="step__num">3</span>
            <div class="step__body">
              <div class="step__title">Включите VPN</div>
              <p class="step__text">
                В приложении нажмите большую круглую кнопку по центру экрана - появится статус
                «Подключено». Страну меняйте в списке серверов.
              </p>
              <p class="step__note">{{ permissionNote[platform] }}</p>
            </div>
          </li>

          <li class="step step--final">
            <span class="step__num"><CircleCheck :size="16" /></span>
            <div class="step__body">
              <div class="step__title">Готово</div>
              <p class="step__text">
                Интернет теперь идёт через Proliv. Выключить - той же кнопкой в приложении.
              </p>
            </div>
          </li>
        </ol>
      </section>

      <section class="panel" style="margin-top: 14px">
        <div class="panel__title">
          <Link2 :size="17" />
          Подписка QR-кодом
        </div>
        <div class="panel--pad stack">
          <div v-if="qrSrc" class="qr-box"><img :src="qrSrc" alt="QR подписки" /></div>
          <p class="muted" style="font-size: 12px">
            Удобно, если настраиваете второе устройство: откройте Happ на нём, нажмите «+» и
            отсканируйте код с этого экрана.
          </p>
        </div>
      </section>

      <section class="panel" style="margin-top: 14px">
        <NuxtLink to="/support" class="row-line row-line--clickable" style="border-top: 0">
          <span class="row-line__icon"><LifeBuoy :size="16" /></span>
          <span class="row-line__body">
            <span class="row-line__label">Не получается?</span>
            <span class="row-line__hint">Напишите в поддержку - поможем настроить</span>
          </span>
          <ArrowRight :size="16" class="row-line__chev" />
        </NuxtLink>
      </section>
    </template>
  </div>
</template>
