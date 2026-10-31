<script setup lang="ts">
import { panelStatusLabel, panelStatusTone } from './format'

defineProps<{ status: string | null | undefined; banned?: boolean }>()
</script>

<template>
  <AdminBadge :tone="panelStatusTone(status, banned)">{{ panelStatusLabel(status, banned) }}</AdminBadge>
</template>
