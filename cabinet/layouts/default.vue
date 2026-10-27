<script setup lang="ts">
import { ArrowLeft } from '@lucide/vue'

const config = useRuntimeConfig()
</script>

<template>
  <header class="app-top">
    <a :href="config.public.landingUrl" class="app-top__back">
      <ArrowLeft :size="15" />
      На главную
    </a>
    <UserChip />
  </header>
  <main class="app-main">
    <slot />
  </main>
  <BottomNav />
</template>
