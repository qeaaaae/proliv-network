<script setup lang="ts">
import { AlertCircle, CheckCircle2 } from '@lucide/vue'

const { toasts } = useToast()
</script>

<template>
  <TransitionGroup name="toast" tag="div" class="toasts">
    <div v-for="t in toasts" :key="t.id" class="toast" :class="`toast--${t.type}`">
      <AlertCircle v-if="t.type === 'error'" :size="16" />
      <CheckCircle2 v-else :size="16" />
      <span>{{ t.text }}</span>
    </div>
  </TransitionGroup>
</template>
