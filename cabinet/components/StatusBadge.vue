<script setup lang="ts">
const props = defineProps<{ status: 'open' | 'answered' | 'closed' }>()

const map = {
  open: { cls: 'badge--accent', label: 'Открыто' },
  answered: { cls: 'badge--amber', label: 'Есть ответ' },
  closed: { cls: 'badge--muted', label: 'Закрыто' },
} as const
</script>

<template>
  <span class="badge" :class="map[status].cls">{{ map[status].label }}</span>
</template>
