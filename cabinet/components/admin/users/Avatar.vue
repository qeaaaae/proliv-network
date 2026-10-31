<script setup lang="ts">
import { userDisplayName } from './format'
import type { AdminUser } from './types'

const props = withDefaults(defineProps<{ user: AdminUser | null | undefined; size?: number }>(), {
  size: 40,
})

const failed = ref(false)
const src = computed(() => props.user?.avatar_url || props.user?.telegram_photo_url || '')
const initial = computed(() => (userDisplayName(props.user).replace('@', '').charAt(0) || '?').toUpperCase())

watch(src, () => {
  failed.value = false
})
</script>

<template>
  <span class="adm-users-avatar" :style="{ width: `${size}px`, height: `${size}px` }">
    <img v-if="src && !failed" :src="src" :alt="userDisplayName(user)" loading="lazy" @error="failed = true" />
    <span v-else class="adm-users-avatar-fallback">{{ initial }}</span>
  </span>
</template>

<style scoped>
.adm-users-avatar {
  display: inline-flex;
  flex: 0 0 auto;
  border-radius: 50%;
  overflow: hidden;
  background: var(--adm-card-2, #1a2231);
  border: 1px solid var(--adm-border, #232c3d);
}
.adm-users-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.adm-users-avatar-fallback {
  margin: auto;
  font-weight: 700;
  color: var(--adm-muted, #8b95a8);
}
</style>
