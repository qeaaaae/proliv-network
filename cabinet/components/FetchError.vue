<script setup lang="ts">
import { RefreshCcw } from '@lucide/vue'

const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <div class="empty">
    <div class="empty__icon"><RefreshCcw :size="22" /></div>
    <h2>Не удалось загрузить данные</h2>
    <p>Проверьте соединение и попробуйте ещё раз</p>
    <button class="btn btn--primary" @click="emit('retry')">Повторить</button>
  </div>
</template>
