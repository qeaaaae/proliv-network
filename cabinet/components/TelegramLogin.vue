<script setup lang="ts">
const props = defineProps<{ botUsername: string }>()
const emit = defineEmits<{ auth: [user: Record<string, unknown>] }>()

const root = ref<HTMLElement>()

onMounted(() => {
  const w = window as unknown as { onTelegramAuth?: (u: Record<string, unknown>) => void }
  w.onTelegramAuth = (user) => emit('auth', user)

  const script = document.createElement('script')
  script.src = 'https://telegram.org/js/telegram-widget.js?22'
  script.async = true
  script.setAttribute('data-telegram-login', props.botUsername)
  script.setAttribute('data-size', 'large')
  script.setAttribute('data-radius', '20')
  script.setAttribute('data-onauth', 'onTelegramAuth(user)')
  script.setAttribute('data-request-access', 'write')
  root.value?.appendChild(script)
})
</script>

<template>
  <div ref="root" />
</template>
