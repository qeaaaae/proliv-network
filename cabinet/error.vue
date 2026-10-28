<script setup lang="ts">
import type { NuxtError } from '#app'

const props = defineProps<{ error: NuxtError }>()
</script>

<template>
  <div class="error-page">
    <ProlivLogo :height="30" />
    <h1>Что-то пошло не так</h1>
    <p class="muted">
      Ошибка {{ props.error.statusCode }}.
      {{ props.error.statusCode === 404 ? 'Страница не найдена.' : 'Попробуйте обновить страницу.' }}
    </p>
    <button class="btn btn--primary" @click="clearError({ redirect: '/' })">В кабинет</button>
  </div>
</template>

<style scoped>
.error-page {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 24px;
  text-align: center;
}
</style>
