<script setup lang="ts">
defineProps<{ title: string; note?: string }>()
</script>

<template>
  <div class="admin-page-head">
    <div class="admin-page-head-title">
      <h1>{{ title }}</h1>
      <p v-if="note" class="admin-note">{{ note }}</p>
    </div>
    <div v-if="$slots.default" class="admin-row">
      <slot />
    </div>
  </div>
</template>
