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
    <p class="admin-note">
      Здесь появляется то, что ждёт твоего действия: заявки и выплаты партнёров,
      непрочитанные тикеты, сбой синхронизации с панелью.
    </p>
    <div class="att-list">
      <NuxtLink
        v-for="item in items"
        :key="item.label"
        :to="item.to"
        class="att-row"
        :class="{ empty: !item.count }"
      >
        <span>{{ item.label }}</span>
        <AdminBadge :tone="item.count ? item.tone || 'warning' : 'muted'">
          {{ item.count }}
        </AdminBadge>
      </NuxtLink>
    </div>
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
.att-list {
  display: grid;
  gap: 6px;
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
.att-row.empty {
  opacity: 0.55;
}
</style>
