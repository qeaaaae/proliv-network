<script setup lang="ts">
export interface AttentionItem {
  label: string
  count: number
  to: string
  tone?: 'warning' | 'danger' | 'muted'
}

const props = defineProps<{ items: AttentionItem[] }>()

const total = computed(() => props.items.reduce((sum, item) => sum + item.count, 0))
</script>

<template>
  <section class="admin-card" :class="{ att: total }">
    <div class="att-head">
      <h2>Требует внимания</h2>
      <AdminBadge :tone="total ? 'warning' : 'success'">{{ total }}</AdminBadge>
    </div>
    <template v-if="total">
      <NuxtLink
        v-for="item in items.filter((i) => i.count > 0)"
        :key="item.label"
        :to="item.to"
        class="att-row"
      >
        <span>{{ item.label }}</span>
        <AdminBadge :tone="item.tone || 'warning'">{{ item.count }}</AdminBadge>
      </NuxtLink>
    </template>
    <p v-else class="admin-note">Всё спокойно: заявок, выплат и тикетов нет.</p>
  </section>
</template>

<style scoped>
.att {
  border-color: rgba(251, 191, 36, 0.25);
}
.att-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.att-head h2 {
  margin: 0;
}
.att-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 10px;
  border-radius: 10px;
  background: var(--adm-card-2, #1a1e24);
  color: inherit;
  text-decoration: none;
}
.att-row:hover {
  outline: 1px solid var(--adm-accent);
}
</style>
