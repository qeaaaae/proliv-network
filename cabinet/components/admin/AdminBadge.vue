<script setup lang="ts">
defineProps<{ tone?: 'default' | 'success' | 'warning' | 'danger' | 'muted' }>()
</script>

<template>
  <span class="adm-badge" :class="`tone-${tone || 'default'}`"><slot /></span>
</template>

<style scoped>
.adm-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid var(--adm-border, #232c3d);
  color: var(--adm-text, #e8ecf4);
  white-space: nowrap;
}
.tone-success {
  color: var(--adm-success, #34d399);
  border-color: rgba(52, 211, 153, 0.4);
}
.tone-warning {
  color: var(--adm-warning, #fbbf24);
  border-color: rgba(251, 191, 36, 0.4);
}
.tone-danger {
  color: var(--adm-danger, #f87171);
  border-color: rgba(248, 113, 113, 0.4);
}
.tone-muted {
  color: var(--adm-muted, #8b95a8);
}
</style>
