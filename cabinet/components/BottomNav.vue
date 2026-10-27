<script setup lang="ts">
import { CircleUserRound, CreditCard, MessageCircle, Radio, Users } from '@lucide/vue'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const route = useRoute()

const tabs = [
  { to: '/', icon: Radio, label: 'Подписка' },
  { to: '/purchases', icon: CreditCard, label: 'Покупки' },
  { to: '/referrals', icon: Users, label: 'Рефералы' },
  { to: '/account', icon: CircleUserRound, label: 'Аккаунт' },
  { to: '/support', icon: MessageCircle, label: 'Поддержка' },
]

const isActive = (to: string) =>
  to === '/' ? route.path === '/' : route.path === to || route.path.startsWith(`${to}/`)

const linkEls = ref<unknown[]>([])
const pill = ref({ x: 0, w: 0, ready: false })

async function syncPill() {
  await nextTick()
  const idx = tabs.findIndex((t) => isActive(t.to))
  const raw = linkEls.value?.[idx]
  // ref на NuxtLink возвращает инстанс компонента - нужен $el
  const el = raw instanceof HTMLElement ? raw : (raw as { $el?: unknown })?.$el
  if (!(el instanceof HTMLElement)) return
  pill.value = { x: el.offsetLeft, w: el.offsetWidth, ready: true }
}

onMounted(() => {
  syncPill()
  window.addEventListener('resize', syncPill)
})
onBeforeUnmount(() => window.removeEventListener('resize', syncPill))
watch(() => route.path, syncPill)
</script>

<template>
  <nav class="fab-nav" :class="{ 'has-pill': pill.ready }" aria-label="Разделы кабинета">
    <div
      class="fab-nav__pill"
      :class="{ 'is-ready': pill.ready }"
      :style="{ transform: `translateX(${pill.x}px)`, width: `${pill.w}px` }"
      aria-hidden="true"
    />
    <NuxtLink
      v-for="tab in tabs"
      :key="tab.to"
      ref="linkEls"
      :to="tab.to"
      class="fab-nav__link"
      :class="{ 'is-active': isActive(tab.to) }"
    >
      <component :is="tab.icon" :size="19" :stroke-width="2" />
      <span>{{ tab.label }}</span>
    </NuxtLink>
  </nav>
</template>
