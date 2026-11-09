<script setup lang="ts">
// Строка состояния списка: ошибка > загрузка > пусто. Рендерит максимум одну строку.
defineProps<{
  loading?: boolean
  error?: string
  empty?: boolean
  loadingText?: string
  emptyText?: string
}>()
</script>

<template>
  <p v-if="loading" class="admin-note">{{ loadingText || 'Загрузка...' }}</p>
  <p v-else-if="error" class="admin-note admin-error">{{ error }}</p>
  <p v-else-if="empty" class="admin-note">{{ emptyText || 'Нет данных' }}</p>
</template>
