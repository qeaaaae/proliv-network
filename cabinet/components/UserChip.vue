<script setup lang="ts">
import { LogOut } from '@lucide/vue'

const { user, logout } = useAuth()

// /api/account/avatar отдаёт 404, если у юзера нет фото в Telegram -
// в этом случае показываем первую букву имени.
const avatarFailed = ref(false)
watch(
  () => user.value?.photoUrl,
  () => {
    avatarFailed.value = false
  },
)
</script>

<template>
  <div v-if="user" class="app-top__right">
    <div class="user-chip">
      <span class="user-chip__avatar">
        <img
          v-if="user.photoUrl && !avatarFailed"
          :src="user.photoUrl"
          :alt="user.name"
          @error="avatarFailed = true"
        />
        <template v-else>{{ user.name.slice(0, 1).toUpperCase() }}</template>
      </span>
      <span class="user-chip__meta">
        <span class="user-chip__name">{{ user.name }}</span>
        <span class="user-chip__id numeric">ID {{ user.id }}</span>
      </span>
    </div>
    <button class="icon-btn" title="Выйти" aria-label="Выйти" @click="logout">
      <LogOut :size="17" />
    </button>
  </div>
</template>
