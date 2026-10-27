<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary'
    size?: 'default' | 'small'
    href?: string
  }>(),
  { variant: 'primary', size: 'default', href: undefined },
)
</script>

<template>
  <component
    :is="href ? 'a' : 'button'"
    :href="href"
    :type="href ? undefined : 'button'"
    class="base-button"
    :class="[`base-button--${variant}`, { 'base-button--small': size === 'small' }]"
  >
    <span><slot /></span>
  </component>
</template>

<style scoped>
.base-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 52px;
  padding: 0 28px;
  border-radius: 999px;
  font-weight: 600;
  font-size: 16px;
  white-space: nowrap;
  transition:
    transform 0.18s ease,
    background-color 0.18s ease,
    border-color 0.18s ease,
    box-shadow 0.18s ease;
}

.base-button:active {
  transform: translateY(1px) scale(0.99);
}

.base-button--primary {
  background: #f5f6f8;
  color: #0b0c0e;
}

.base-button--primary:hover {
  background: #ffffff;
  box-shadow: 0 8px 32px -8px rgba(255, 255, 255, 0.35);
}

.base-button--secondary {
  background: #23262b;
  color: var(--text);
  border: 1px solid var(--border);
}

.base-button--secondary:hover {
  background: #2c3036;
  border-color: var(--border-strong);
}

.base-button--small {
  min-height: 40px;
  padding: 0 18px;
  font-size: 14px;
}
</style>
