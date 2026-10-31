<script setup lang="ts">
import '~/assets/admin.css'

const { call } = useAdminApi()
const gate = ref<'loading' | 'admin' | 'denied'>('loading')
provide('adminGate', gate)

const nav = [
  { to: '/admin', label: 'Дашборд' },
  { to: '/admin/users', label: 'Пользователи' },
  { to: '/admin/partners', label: 'Партнёры' },
  { to: '/admin/promos', label: 'Промокоды' },
  { to: '/admin/payments', label: 'Платежи' },
  { to: '/admin/broadcast', label: 'Рассылка' },
  { to: '/admin/support', label: 'Поддержка' },
  { to: '/admin/system', label: 'Система' },
]

onMounted(async () => {
  try {
    await call('health')
    gate.value = 'admin'
  } catch {
    gate.value = 'denied'
  }
})
</script>

<template>
  <div class="admin-shell">
    <div v-if="gate === 'loading'" class="admin-page"><p class="admin-note">Проверка доступа...</p></div>
    <div v-else-if="gate === 'denied'" class="admin-page">
      <section class="admin-card">
        <h2>Нет доступа</h2>
        <p class="admin-note">Раздел доступен только администраторам.</p>
      </section>
    </div>
    <template v-else>
      <nav class="admin-nav">
        <NuxtLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="admin-nav-link"
          :class="{ active: $route.path === item.to }"
        >
          {{ item.label }}
        </NuxtLink>
      </nav>
      <NuxtPage />
    </template>
  </div>
</template>

<style>
.admin-nav {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  gap: 4px;
  padding: 10px 12px;
  overflow-x: auto;
  background: rgba(11, 15, 23, 0.92);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--adm-border);
}
.admin-nav-link {
  padding: 8px 14px;
  border-radius: 10px;
  color: var(--adm-muted);
  font-size: 13px;
  text-decoration: none;
  white-space: nowrap;
}
.admin-nav-link:hover {
  color: var(--adm-text);
}
.admin-nav-link.active {
  color: var(--adm-accent);
  background: var(--adm-accent-soft);
}
</style>
