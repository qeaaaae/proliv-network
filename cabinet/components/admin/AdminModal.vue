<script setup lang="ts">
defineProps<{ open: boolean; title: string }>()
const emit = defineEmits<{ close: [] }>()

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}
onMounted(() => document.addEventListener('keydown', onKey))
onUnmounted(() => document.removeEventListener('keydown', onKey))
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="adm-modal-backdrop" @click.self="emit('close')">
      <div class="adm-modal" role="dialog" :aria-label="title">
        <header>
          <strong>{{ title }}</strong>
          <button type="button" class="adm-modal-x" aria-label="Закрыть" @click="emit('close')">✕</button>
        </header>
        <div class="adm-modal-body"><slot /></div>
        <footer v-if="$slots.footer" class="adm-modal-footer"><slot name="footer" /></footer>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.adm-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: grid;
  place-items: center;
  padding: 16px;
  background: rgba(4, 7, 12, 0.7);
  backdrop-filter: blur(3px);
}
.adm-modal {
  width: min(560px, 100%);
  max-height: 85dvh;
  overflow: auto;
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: var(--radius-card, 20px);
  border: 1px solid var(--adm-border, #232c3d);
  background: var(--adm-card, #141a26);
}
.adm-modal header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
}
.adm-modal-x {
  border: 0;
  background: transparent;
  color: var(--adm-muted, #8b95a8);
  cursor: pointer;
  font-size: 14px;
}
.adm-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
