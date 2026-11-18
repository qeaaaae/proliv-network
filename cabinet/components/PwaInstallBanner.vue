<script setup lang="ts">
import { Share, SquarePlus, X, Download } from '@lucide/vue'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const STORAGE_KEY = 'proliv_pwa_banner_dismissed'

const { user } = useAuth()
const visible = ref(false)
const deferredPrompt = ref<BeforeInstallPromptEvent | null>(null)
const isIos = ref(false)

function alreadyInstalled(): boolean {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true
  )
}

function onBeforeInstall(e: Event) {
  e.preventDefault()
  deferredPrompt.value = e as BeforeInstallPromptEvent
  visible.value = true
}

async function install() {
  const p = deferredPrompt.value
  if (!p) return
  await p.prompt()
  const { outcome } = await p.userChoice
  deferredPrompt.value = null
  if (outcome === 'accepted') visible.value = false
}

function dismiss() {
  visible.value = false
  localStorage.setItem(STORAGE_KEY, '1')
}

onMounted(() => {
  if (alreadyInstalled() || localStorage.getItem(STORAGE_KEY)) return
  const ua = navigator.userAgent
  isIos.value = /iPhone|iPad|iPod/i.test(ua) && !/CriOS|FxiOS|EdgiOS|OPiOS/i.test(ua)
  window.addEventListener('beforeinstallprompt', onBeforeInstall)
  window.addEventListener('appinstalled', () => {
    visible.value = false
    localStorage.setItem(STORAGE_KEY, '1')
  })
  if (isIos.value) visible.value = true
})

onBeforeUnmount(() => window.removeEventListener('beforeinstallprompt', onBeforeInstall))
</script>

<template>
  <Transition name="pwab">
    <div v-if="visible && user" class="pwab" role="dialog" aria-label="Установить приложение">
      <div class="pwab__icon"><Download :size="18" /></div>
      <div class="pwab__body">
        <div class="pwab__title">Вынесите кабинет на главный экран</div>
        <div v-if="isIos" class="pwab__text">
          Нажмите <Share :size="13" style="vertical-align: -2px" /> «Поделиться», затем
          <SquarePlus :size="13" style="vertical-align: -2px" /> «На экран "Домой"»
        </div>
        <div v-else class="pwab__text">Будет открываться как приложение, а не вкладка браузера</div>
      </div>
      <button v-if="!isIos" type="button" class="btn btn--primary pwab__btn" @click="install">
        Установить
      </button>
      <button type="button" class="pwab__close" aria-label="Закрыть" @click="dismiss">
        <X :size="16" />
      </button>
    </div>
  </Transition>
</template>

<style scoped>
.pwab {
  position: fixed;
  left: var(--gutter);
  right: var(--gutter);
  bottom: calc(96px + env(safe-area-inset-bottom));
  z-index: 60;
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 520px;
  margin: 0 auto;
  padding: 12px 12px 12px 14px;
  border-radius: var(--radius-card);
  border: 1px solid var(--border-strong);
  background: var(--card);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45);
}
.pwab__icon {
  flex: none;
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: var(--accent-soft);
  color: var(--accent);
}
.pwab__body {
  flex: 1;
  min-width: 0;
}
.pwab__title {
  font-size: 13.5px;
  font-weight: 650;
  line-height: 1.3;
}
.pwab__text {
  font-size: 12px;
  color: var(--fg-secondary);
  line-height: 1.4;
  margin-top: 2px;
}
.pwab__btn {
  flex: none;
  padding: 8px 14px;
  font-size: 13px;
}
.pwab__close {
  flex: none;
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
}
.pwab__close:hover {
  background: var(--control);
  color: var(--text);
}
.pwab-enter-active,
.pwab-leave-active {
  transition: opacity 0.25s var(--ease), transform 0.25s var(--ease);
}
.pwab-enter-from,
.pwab-leave-to {
  opacity: 0;
  transform: translateY(12px);
}
@media (min-width: 720px) {
  .pwab {
    left: auto;
    right: var(--gutter);
    bottom: var(--gutter);
    width: 420px;
  }
}
</style>
