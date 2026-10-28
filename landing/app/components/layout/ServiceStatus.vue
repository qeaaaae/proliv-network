<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { statusUrl } from '~/data/product'
import { resolveServiceStatus, type ServiceState } from '~/utils/serviceStatus'
import NavigationButton from '~/components/ui/NavigationButton.vue'

const { t } = useI18n()
const state = ref<ServiceState>('unknown')
const label = computed(() => ({
  operational: t('footer.serviceStates.operational'),
  partial: t('footer.serviceStates.partial'),
  down: t('footer.serviceStates.down'),
  unknown: t('footer.serviceStates.unknown')
})[state.value])
let request: AbortController | undefined
let timer: ReturnType<typeof setInterval> | undefined

async function refresh() {
  if (document.visibilityState !== 'visible' || request) return
  const controller = new AbortController()
  request = controller
  try {
    const options = { signal: controller.signal, timeout: 5000, retry: 0 }
    state.value = resolveServiceStatus(await $fetch<unknown>('/status-data/status.json', options))
  } catch {
    state.value = 'unknown'
  } finally {
    request = undefined
  }
}

onMounted(() => {
  void refresh()
  timer = setInterval(refresh, 60_000)
  document.addEventListener('visibilitychange', refresh)
})

onBeforeUnmount(() => {
  clearInterval(timer)
  request?.abort()
  document.removeEventListener('visibilitychange', refresh)
})
</script>

<template>
  <NavigationButton
    v-if="state !== 'unknown'"
    class="service-status"
    :data-state="state"
    :target="statusUrl"
    :aria-label="`${t('footer.status')}: ${label}`"
  >
    <span class="service-status__dot" aria-hidden="true" />
    <span aria-live="polite" aria-atomic="true">{{ label }}</span>
  </NavigationButton>
</template>

<style scoped>
.service-status {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 9px 16px;
  color: var(--fg-secondary);
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  background: var(--control);
  border: 1px solid var(--line);
  border-radius: var(--radius-pill);
  transition: color 200ms var(--ease), border-color 200ms var(--ease), background-color 200ms var(--ease);
}

.service-status:hover {
  color: var(--fg);
  background: var(--control-hover);
  border-color: var(--line-strong);
}

.service-status__dot {
  flex: none;
  width: 8px;
  height: 8px;
  background-color: var(--fg-tertiary);
  border-radius: 50%;
}

.service-status[data-state='operational'] .service-status__dot {
  animation: service-status-pulse 2.4s ease-in-out infinite;
}

.service-status[data-state='partial'] .service-status__dot {
  background-color: var(--fg-secondary);
}

.service-status[data-state='down'] .service-status__dot {
  background-color: var(--danger);
}

@keyframes service-status-pulse {
  0%, 100% {
    background-color: var(--plate);
    box-shadow: 0 0 6px rgb(125 211 252 / 65%), 0 0 14px rgb(125 211 252 / 30%);
  }
  50% {
    background-color: #fff;
    box-shadow: 0 0 6px rgb(255 255 255 / 60%), 0 0 14px rgb(255 255 255 / 25%);
  }
}
</style>
