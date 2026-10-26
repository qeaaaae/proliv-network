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
  position: relative;
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
  overflow: hidden;
  transition:
    transform 0.18s ease,
    background-color 0.18s ease,
    border-color 0.18s ease,
    box-shadow 0.18s ease;
}

.base-button::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    105deg,
    transparent 40%,
    rgba(125, 211, 252, 0.4) 50%,
    transparent 60%
  );
  transform: translateX(-130%);
  transition: transform 0.65s var(--ease-out);
  pointer-events: none;
}

.base-button:hover::after {
  transform: translateX(130%);
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
  transform: translateY(-1px);
  box-shadow: 0 10px 36px -8px rgba(125, 211, 252, 0.45);
}

.base-button--secondary {
  background: #23262b;
  color: var(--text);
  border: 1px solid var(--border);
}

.base-button--secondary:hover {
  background: #2c3036;
  transform: translateY(-1px);
  border-color: rgba(125, 211, 252, 0.4);
  box-shadow: 0 10px 30px -12px rgba(125, 211, 252, 0.25);
}

.base-button--small {
  min-height: 40px;
  padding: 0 18px;
  font-size: 14px;
}
</style>
