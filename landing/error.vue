<script setup lang="ts">
import type { NuxtError } from '#app'

const props = defineProps<{ error: NuxtError }>()

const is404 = computed(() => props.error?.statusCode === 404)

useHead({
  title: is404.value ? 'Страница не найдена - Proliv Network' : 'Ошибка - Proliv Network',
})
</script>

<template>
  <main class="error-page">
    <div class="content-frame">
      <div class="error-sheet sheet">
        <LightFlare />
        <ProlivLogo />
        <p class="error-code numeric">{{ error?.statusCode ?? 500 }}</p>
        <h1>{{ is404 ? 'Страница не найдена' : 'Что-то пошло не так' }}</h1>
        <p class="error-text">
          {{ is404 ? 'Такой страницы нет или она переехала.' : 'Попробуйте обновить страницу.' }}
        </p>
        <BaseButton href="/">На главную</BaseButton>
      </div>
    </div>
  </main>
</template>

<style scoped>
.error-page {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  padding: 48px 0;
}

.error-sheet {
  position: relative;
  text-align: center;
  padding: clamp(40px, 6vw, 72px) 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
}

.error-code {
  font-family: var(--font-display);
  font-size: clamp(56px, 10vw, 96px);
  font-weight: 600;
  color: var(--accent);
  line-height: 1;
  margin-top: 24px;
}

h1 {
  font-family: var(--font-display);
  font-size: clamp(22px, 3vw, 32px);
  font-weight: 600;
}

.error-text {
  color: var(--muted);
  font-size: 16px;
  margin-bottom: 8px;
}
</style>
