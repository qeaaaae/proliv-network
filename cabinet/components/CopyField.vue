<script setup lang="ts">
import { Check, Copy, QrCode } from '@lucide/vue'

const props = defineProps<{ value: string; qr?: boolean }>()
const emit = defineEmits<{ qr: [] }>()

const { push } = useToast()
const copied = ref(false)

async function copy() {
  try {
    await navigator.clipboard.writeText(props.value)
    copied.value = true
    push('Скопировано')
    setTimeout(() => (copied.value = false), 1500)
  } catch {
    push('Не удалось скопировать', 'error')
  }
}
</script>

<template>
  <div class="copyfield">
    <span class="copyfield__text" :title="value">{{ value }}</span>
    <button v-if="qr" class="icon-btn" title="QR-код" aria-label="QR-код" @click="emit('qr')">
      <QrCode :size="16" />
    </button>
    <button class="icon-btn" title="Скопировать" aria-label="Скопировать" @click="copy">
      <Check v-if="copied" :size="16" class="accent" />
      <Copy v-else :size="16" />
    </button>
  </div>
</template>
