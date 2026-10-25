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
  border-radius: var(--radius-control);
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
  background: var(--accent);
  color: var(--accent-ink);
  box-shadow: 0 0 0 0 rgba(125, 211, 252, 0);
}

.base-button--primary:hover {
  background: #a5e2fd;
  box-shadow: 0 8px 32px -8px rgba(125, 211, 252, 0.45);
}

.base-button--secondary {
  background: transparent;
  color: var(--text);
  border: 1px solid var(--border-strong);
}

.base-button--secondary:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.2);
}

.base-button--small {
  min-height: 40px;
  padding: 0 18px;
  font-size: 14px;
  border-radius: 12px;
}
</style>
