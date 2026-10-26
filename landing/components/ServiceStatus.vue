<script setup lang="ts">
</script>

<template>
  <NuxtLink to="/status" class="service-status">
    <span class="status-dot" aria-hidden="true"></span>
    <span class="status-text">Всё работает</span>
  </NuxtLink>
</template>

<style scoped>
.service-status {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--text);
  text-decoration: none;
  transition: border-color 0.18s ease;
}

.service-status:hover {
  border-color: var(--border-strong);
}

.status-dot {
  position: relative;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #3ddc84;
  box-shadow:
    0 0 6px rgba(61, 220, 132, 0.8),
    0 0 14px rgba(61, 220, 132, 0.4);
}

.status-dot::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 1px solid rgba(61, 220, 132, 0.6);
  animation: status-ping 2.4s var(--ease-out) infinite;
}

@keyframes status-ping {
  0% {
    transform: scale(0.6);
    opacity: 0.9;
  }

  70%,
  100% {
    transform: scale(1.9);
    opacity: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .status-dot::after {
    animation: none;
    opacity: 0;
  }
}

.status-text {
  font-size: 14px;
  font-weight: 500;
}
</style>
