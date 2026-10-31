<script setup lang="ts">
const props = defineProps<{
  pendingApplications: number
  requestedWithdrawals: number
}>()

const total = computed(() => props.pendingApplications + props.requestedWithdrawals)
</script>

<template>
  <section class="admin-card" :class="{ att: total }">
    <div class="att-head">
      <h2>Требует внимания</h2>
      <AdminBadge :tone="total ? 'warning' : 'success'">{{ total }}</AdminBadge>
    </div>
    <template v-if="total">
      <div class="att-row">
        <span>Заявки в партнёрскую программу</span>
        <AdminBadge :tone="pendingApplications ? 'warning' : 'muted'">
          {{ pendingApplications }}
        </AdminBadge>
      </div>
      <div class="att-row">
        <span>Заявки на вывод средств</span>
        <AdminBadge :tone="requestedWithdrawals ? 'warning' : 'muted'">
          {{ requestedWithdrawals }}
        </AdminBadge>
      </div>
      <NuxtLink class="att-link" to="/admin/partners">Открыть раздел «Партнёры»</NuxtLink>
    </template>
    <p v-else class="admin-note">Нет ожидающих заявок - всё спокойно.</p>
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
  border-radius: 8px;
  background: var(--adm-card-2, #1a2231);
}
.att-link {
  font-size: 12px;
  color: var(--adm-accent, #3b82f6);
  text-decoration: none;
  justify-self: start;
}
.att-link:hover {
  text-decoration: underline;
}
</style>
