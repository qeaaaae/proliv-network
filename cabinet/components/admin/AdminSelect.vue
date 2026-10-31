<script setup lang="ts">
const props = defineProps<{
  modelValue: string
  items: { value: string; label: string }[]
  placeholder?: string
}>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const open = ref(false)
const root = ref<HTMLElement>()

const current = computed(
  () => props.items.find((item) => item.value === props.modelValue)?.label || props.placeholder || '',
)

function pick(value: string) {
  emit('update:modelValue', value)
  open.value = false
}

function onDocClick(e: MouseEvent) {
  if (root.value && !root.value.contains(e.target as Node)) open.value = false
}
onMounted(() => document.addEventListener('click', onDocClick))
onUnmounted(() => document.removeEventListener('click', onDocClick))
</script>

<template>
  <div ref="root" class="adm-select" :class="{ open }">
    <button type="button" class="adm-select-trigger" @click="open = !open">
      <span>{{ current }}</span>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="m6 9 6 6 6-6" />
      </svg>
    </button>
    <div v-if="open" class="adm-select-menu">
      <button
        v-for="item in items"
        :key="item.value"
        type="button"
        class="adm-select-option"
        :class="{ active: item.value === modelValue }"
        @click="pick(item.value)"
      >
        {{ item.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.adm-select {
  position: relative;
  width: 100%;
}
.adm-select-trigger {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--adm-border, #232c3d);
  background: var(--adm-bg, #0b0f17);
  color: inherit;
  font-size: 14px;
  cursor: pointer;
}
.adm-select.open .adm-select-trigger {
  border-color: var(--adm-accent, #3b82f6);
}
.adm-select-menu {
  position: absolute;
  z-index: 40;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  max-height: 240px;
  overflow: auto;
  display: grid;
  gap: 2px;
  padding: 6px;
  border-radius: 12px;
  border: 1px solid var(--adm-border, #232c3d);
  background: var(--adm-card, #141a26);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45);
}
.adm-select-option {
  padding: 9px 10px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: inherit;
  font-size: 13px;
  text-align: left;
  cursor: pointer;
}
.adm-select-option:hover {
  background: var(--adm-accent-soft, rgba(59, 130, 246, 0.14));
}
.adm-select-option.active {
  background: var(--adm-accent-soft, rgba(59, 130, 246, 0.14));
  color: var(--adm-accent, #3b82f6);
}
</style>
