<script setup lang="ts">
import { X } from '@lucide/vue'

defineProps<{ open: boolean; title?: string }>()
const emit = defineEmits<{ close: [] }>()
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="modal-backdrop" @click.self="emit('close')">
        <div class="modal" role="dialog" aria-modal="true">
          <header class="modal__head">
            <h3>{{ title }}</h3>
            <button class="icon-btn" aria-label="Закрыть" @click="emit('close')">
              <X :size="17" />
            </button>
          </header>
          <div class="modal__body">
            <slot />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
