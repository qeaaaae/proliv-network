<script setup lang="ts">
defineProps<{
  open: boolean
  title: string
  busy?: boolean
  confirmLabel?: string
  danger?: boolean
  disabled?: boolean
}>()
const emit = defineEmits<{ confirm: []; close: [] }>()
</script>

<template>
  <AdminModal :open="open" :title="title" @close="emit('close')">
    <slot />
    <template #footer>
      <button type="button" class="admin-btn ghost" :disabled="busy" @click="emit('close')">
        Отмена
      </button>
      <button
        type="button"
        class="admin-btn"
        :class="{ danger }"
        :disabled="busy || disabled"
        @click="emit('confirm')"
      >
        {{ busy ? 'Выполняется...' : confirmLabel || 'Подтвердить' }}
      </button>
    </template>
  </AdminModal>
</template>
