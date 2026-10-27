<script setup lang="ts">
const config = useRuntimeConfig()
</script>

<template>
  <BlueprintLayer />
  <header class="app-top">
    <a :href="config.public.landingUrl" class="app-top__logo" aria-label="Proliv Network - на главную">
      <ProlivLogo :height="32" />
    </a>
    <UserChip />
  </header>
  <main class="app-main">
    <slot />
  </main>
  <BottomNav />
</template>
