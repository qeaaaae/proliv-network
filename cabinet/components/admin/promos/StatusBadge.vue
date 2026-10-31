<script setup lang="ts">
// Статус промокода - та же логика, что в боте (get_promo_status_emoji_and_text):
// истёк по дате -> исчерпан по лимиту -> активен -> выключен.
const props = defineProps<{
  promo: {
    is_active: boolean
    valid_until: string | null
    current_activations: number
    max_activations: number
  }
}>()

type Tone = 'default' | 'success' | 'warning' | 'danger' | 'muted'

const status = computed<{ tone: Tone; label: string }>(() => {
  const p = props.promo
  const until = p.valid_until ? new Date(p.valid_until).getTime() : null
  if (until !== null && Number.isFinite(until) && until < Date.now()) {
    return { tone: 'warning', label: 'Истёк' }
  }
  if (p.current_activations >= p.max_activations) {
    return { tone: 'muted', label: 'Исчерпан' }
  }
  if (p.is_active) {
    return { tone: 'success', label: 'Активен' }
  }
  return { tone: 'danger', label: 'Выключен' }
})
</script>

<template>
  <AdminBadge :tone="status.tone">{{ status.label }}</AdminBadge>
</template>
